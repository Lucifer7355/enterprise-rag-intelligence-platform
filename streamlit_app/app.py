"""Streamlit dashboard with JWT login + SSO support."""

import requests
import streamlit as st

API_URL = st.sidebar.text_input("API URL", "http://localhost:8000")

st.set_page_config(page_title="Enterprise RAG", page_icon="🏢", layout="wide", initial_sidebar_state="expanded")

# Handle SSO callback token in URL
query_params = st.query_params
if query_params.get("token") and "access_token" not in st.session_state:
    st.session_state.access_token = query_params["token"]
    st.session_state.username = query_params.get("user", "sso_user")
    st.session_state.role = query_params.get("role", "Engineering")
    st.session_state.user_id = query_params.get("user", "sso_user")
    st.query_params.clear()


def api_get(path: str):
    headers = {}
    if st.session_state.get("access_token"):
        headers["Authorization"] = f"Bearer {st.session_state.access_token}"
    try:
        return requests.get(f"{API_URL}{path}", headers=headers, timeout=30)
    except Exception as e:
        st.error(f"API unreachable: {e}")
        return None


def api_post(path: str, data: dict):
    headers = {"Content-Type": "application/json"}
    if st.session_state.get("access_token"):
        headers["Authorization"] = f"Bearer {st.session_state.access_token}"
    try:
        return requests.post(f"{API_URL}{path}", json=data, headers=headers, timeout=120)
    except Exception as e:
        st.error(f"API unreachable: {e}")
        return None


def show_login():
    st.title("🏢 Enterprise RAG — Login")
    auth_resp = api_get("/auth/status")
    demo_users = []
    sso_enabled = False
    if auth_resp and auth_resp.ok:
        data = auth_resp.json()
        demo_users = data.get("demo_users", [])
        sso_enabled = data.get("sso_enabled", False)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Sign In")
        with st.form("login_form"):
            username = st.text_input("Username", value="admin")
            password = st.text_input("Password", type="password", value="admin123")
            if st.form_submit_button("Login", type="primary"):
                resp = api_post("/auth/login", {"username": username.strip(), "password": password})
                if resp is None:
                    st.error(f"Cannot reach API at {API_URL}. Start the server: uvicorn app.main:app --port 8000")
                elif resp.status_code == 404:
                    st.error("Auth endpoint not found — restart the API server to load the latest code.")
                elif resp.ok:
                    data = resp.json()
                    st.session_state.access_token = data["access_token"]
                    st.session_state.username = data["username"]
                    st.session_state.role = data["role"]
                    st.session_state.user_id = data["user_id"]
                    st.rerun()
                elif resp.status_code == 401:
                    st.error("Invalid credentials. Try admin / admin123")
                else:
                    st.error(f"Login failed ({resp.status_code}): {resp.text[:200]}")

        if demo_users:
            st.info(f"**Demo accounts:** {', '.join(demo_users)} (password: see SUBMISSION.md)")

    with col2:
        st.subheader("Enterprise SSO")
        if sso_enabled:
            st.link_button("Login with SSO", f"{API_URL}/auth/sso/login")
        else:
            st.caption("SSO not configured. Set `SSO_CLIENT_ID` and `SSO_DISCOVERY_URL` to enable OIDC.")
            st.markdown("""
            Supports: **Google**, **Azure AD**, **Okta** via OpenID Connect.
            Configure in `config/auth.yaml`.
            """)

    st.stop()


if "access_token" not in st.session_state:
    show_login()

st.title("🏢 Enterprise RAG — Plug & Play")
st.sidebar.success(f"Logged in as **{st.session_state.username}** ({st.session_state.role})")
if st.sidebar.button("Logout"):
    for key in ["access_token", "username", "role", "user_id"]:
        st.session_state.pop(key, None)
    st.rerun()

roles_resp = api_get("/roles")
ROLES = roles_resp.json().get("roles", [st.session_state.role]) if roles_resp and roles_resp.ok else [st.session_state.role]

tab_chat, tab_sources, tab_connectors, tab_audit, tab_eval, tab_config, tab_obs = st.tabs(
    ["💬 Chat", "📂 Sources", "🔌 Connectors", "🔒 Audit", "📊 Evaluation", "⚙️ Config", "📡 Observability"]
)

with st.sidebar:
    st.header("Session")
    user_id = st.session_state.user_id
    role = st.session_state.role
    st.caption(f"Role from login: **{role}**")
    st.divider()
    if st.button("🔄 Re-ingest All"):
        with st.spinner("Ingesting..."):
            resp = api_post("/ingest", {"regenerate_synthetic": False, "force_reindex": True})
            if resp and resp.ok:
                st.success(resp.json().get("message", "Done"))
    if st.button("♻️ Reload Config"):
        resp = api_post("/config/reload", {})
        if resp and resp.ok:
            st.success("Config reloaded")

with tab_chat:
    st.subheader("Ask a Question")
    query = st.text_area("Your question", placeholder="e.g. Show failed payment incidents")
    if st.button("Send", type="primary") and query:
        with st.spinner("Searching..."):
            resp = api_post("/chat", {"query": query, "user_id": user_id, "role": role})
            if resp and resp.ok:
                data = resp.json()
                st.markdown("### Answer")
                st.write(data["answer"])
                st.caption(f"Latency: {data['latency_ms']}ms | Type: {data['retrieval_trace']['query_type']}")
                st.markdown("### Sources")
                for src in data.get("sources", []):
                    st.markdown(f"**{src['source']}** — Confidence: `{src['confidence']}`")
                with st.expander("Retrieval Trace"):
                    st.json(data.get("retrieval_trace", {}))

with tab_sources:
    st.subheader("Indexed Documents")
    resp = api_get("/sources")
    if resp and resp.ok:
        for src in resp.json():
            with st.expander(f"{src['source']} ({src['department']})"):
                st.json(src)

with tab_connectors:
    st.subheader("Plug & Play Connectors")
    resp = api_get("/connectors")
    if resp and resp.ok:
        st.json(resp.json())
    with st.form("add_document"):
        doc_text = st.text_area("Quick-add document", "Policy text here...")
        if st.form_submit_button("Index Document"):
            resp = api_post("/documents", {
                "connector_name": "runtime_docs",
                "document_id": "runtime_001",
                "source": "runtime_doc.txt",
                "text": doc_text,
                "metadata": {"allowed_roles": [role, "Admin"], "department": "general"},
            })
            if resp and resp.ok:
                st.success("Indexed!")

with tab_audit:
    st.subheader("Audit Logs")
    resp = api_get("/audit?limit=50")
    if resp and resp.ok:
        for entry in reversed(resp.json()):
            st.markdown(f"`{entry['timestamp']}` **{entry['action']}** — {entry['user_id']} ({entry['role']}) → {entry['result']}")

with tab_eval:
    st.subheader("Live RAGAS Evaluation")
    if st.button("Run Evaluation"):
        with st.spinner("Running live RAGAS on sample queries..."):
            resp = api_post("/evaluate", {})
            if resp and resp.ok:
                data = resp.json()
                st.success(f"Method: **{data.get('evaluation_method', 'live')}**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("**Retrieval**")
                    st.json(data["retrieval_metrics"])
                with col2:
                    st.markdown("**Generation (RAGAS)**")
                    st.json(data["generation_metrics"])
                with col3:
                    st.markdown("**Security**")
                    st.json(data["security_metrics"])

with tab_config:
    st.subheader("Platform Configuration")
    resp = api_get("/config")
    if resp and resp.ok:
        st.json(resp.json())

with tab_obs:
    st.subheader("Observability")
    resp = api_get("/observability")
    if resp and resp.ok:
        obs = resp.json()
        st.json(obs)
        if obs.get("phoenix_server_running"):
            st.link_button("Open Phoenix UI", obs["phoenix_ui"])
            st.success("Phoenix is running — traces are being collected.")
        else:
            st.warning("Phoenix UI is not running. Start it in a new terminal:")
            st.code("cd enterprise-rag\n.\\venv\\Scripts\\phoenix serve", language="powershell")
            st.caption("Or use Docker: docker-compose up phoenix")
        if not obs.get("langfuse_enabled"):
            st.caption("Langfuse: set LANGFUSE_PUBLIC_KEY + LANGFUSE_SECRET_KEY in .env, then docker-compose up langfuse")
