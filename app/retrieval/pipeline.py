"""Full retrieval pipeline orchestrator."""

from time import perf_counter

from app.generation.llm import generate_answer
from app.knowledge_graph.graph import KnowledgeGraph
from app.models.schemas import ChatResponse, RetrievalTrace, SourceCitation
from app.observability.audit import audit_logger
from app.observability.logging import get_logger
from app.observability.langfuse_client import flush as langfuse_flush
from app.observability.langfuse_client import log_generation
from app.observability.tracing import trace_request, trace_span
from app.retrieval.classifier import classify_query
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.reranker import Reranker
from app.retrieval.router import route_sources
from app.security.rbac import filter_authorized_doc_ids
from app.security.sensitive_data import process_sensitive_text
from app.storage.document_store import DocumentStore

logger = get_logger(__name__)


class RetrievalPipeline:
    def __init__(self):
        self.hybrid = HybridRetriever()
        self.reranker = Reranker()
        self.doc_store = DocumentStore()
        self.kg = KnowledgeGraph()

    def process(self, query: str, user_id: str, role: str) -> ChatResponse:
        start = perf_counter()

        with trace_request("chat_query", user_id=user_id, metadata={"role": role, "query": query[:200]}):
            return self._process_inner(query, user_id, role, start)

    def _process_inner(self, query: str, user_id: str, role: str, start: float) -> ChatResponse:
        with trace_span("intent_classification"):
            query_type = classify_query(query)

        with trace_span("rbac_validation"):
            all_meta = self.doc_store.get_all_metadata()
            authorized_docs = filter_authorized_doc_ids(all_meta, role)
            if not authorized_docs and all_meta:
                audit_logger.log(user_id, role, "rbac_check", "denied", query)
                return ChatResponse(
                    answer="Access Denied: Insufficient permissions.",
                    sources=[],
                    retrieval_trace=RetrievalTrace(
                        query_type=query_type,
                        routed_sources=[],
                        retrieved_documents=[],
                        authorized_doc_count=0,
                    ),
                    latency_ms=(perf_counter() - start) * 1000,
                )

        with trace_span("source_routing"):
            routed = route_sources(query_type, query)

        with trace_span("hybrid_retrieval"):
            candidates = self.hybrid.retrieve(query, role)

        with trace_span("knowledge_graph"):
            kg_context = self.kg.multi_hop_query(query)

        with trace_span("reranking"):
            reranked = self.reranker.rerank(query, candidates)

        context_parts = []
        sources: list[SourceCitation] = []
        retrieved_docs: list[str] = []
        blocked_sensitive = False

        for item in reranked:
            text = item.get("text", "")
            processed, denial, action = process_sensitive_text(text, role)

            if action == "skipped":
                continue

            if action == "blocked":
                blocked_sensitive = True
                audit_logger.log(
                    user_id, role, "sensitive_data_check", "denied", query, {"reason": denial}
                )
                return ChatResponse(
                    answer=denial or "Access Denied: Insufficient permissions.",
                    sources=[],
                    retrieval_trace=RetrievalTrace(
                        query_type=query_type,
                        routed_sources=routed,
                        retrieved_documents=[],
                        authorized_doc_count=len(authorized_docs),
                        blocked_sensitive=True,
                    ),
                    latency_ms=(perf_counter() - start) * 1000,
                )

            text = processed or text
            context_parts.append(f"[{item.get('source', 'unknown')}]\n{text}")
            src = item.get("source", "unknown")
            if src not in retrieved_docs:
                retrieved_docs.append(src)
            confidence = item.get("rerank_score", item.get("hybrid_score", 0.5))
            if isinstance(confidence, float) and confidence > 1:
                confidence = min(confidence / 10, 1.0)
            sources.append(
                SourceCitation(
                    document_id=item.get("document_id", ""),
                    source=src,
                    confidence=round(float(confidence), 2),
                    snippet=text[:200],
                )
            )

        if kg_context:
            context_parts.append("[Knowledge Graph]\n" + "\n".join(kg_context))

        context = "\n\n---\n\n".join(context_parts)
        if not context.strip():
            answer = "I could not find sufficient information."
        else:
            with trace_span("answer_generation"):
                answer = generate_answer(query, context)
            from app.observability import tracing as tracing_mod
            log_generation(tracing_mod._active_langfuse_trace, "answer", query, answer, {"sources": retrieved_docs})

        langfuse_flush()

        audit_logger.log(
            user_id, role, "chat_query", "success", query,
            {"query_type": query_type, "sources": retrieved_docs},
        )

        latency = (perf_counter() - start) * 1000
        logger.info("query_processed", query_type=query_type, latency_ms=latency)

        return ChatResponse(
            answer=answer,
            sources=sources,
            retrieval_trace=RetrievalTrace(
                query_type=query_type,
                routed_sources=routed,
                retrieved_documents=retrieved_docs,
                authorized_doc_count=len(authorized_docs),
                blocked_sensitive=blocked_sensitive,
            ),
            latency_ms=round(latency, 2),
        )
