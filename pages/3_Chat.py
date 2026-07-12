import time

import streamlit as st

from auth import auth_service
from components.badges import status_badge, tier_badge
from components.layout import inject_theme
from components.sidebar import render_sidebar
from database import db_service
from services import chat_service

st.set_page_config(page_title="Chat - Support Escalation AI", layout="wide")
inject_theme()
st.html(
    """
    <style>
        body,
        .stApp,
        [data-testid="stAppViewContainer"],
        .main {
            background-image: none !important;
            background: var(--bg-primary) !important;
        }
    </style>
    """
)
auth_service.bootstrap_session()
auth_service.require_auth()

user = auth_service.current_user()
render_sidebar(active_page="chat")

# -----------------------------
# Resolve active conversation
# -----------------------------
if not st.session_state.get("active_conversation_id"):
    existing = db_service.list_conversations(user["id"])
    if existing:
        st.session_state["active_conversation_id"] = existing[0]["id"]
    else:
        convo = db_service.create_conversation(user["id"], "New Chat")
        st.session_state["active_conversation_id"] = convo["id"]

conversation_id = st.session_state["active_conversation_id"]

if st.session_state.get("chat_messages") is None:
    st.session_state["chat_messages"] = db_service.list_messages(conversation_id)

# -----------------------------
# Render history or Landing State
# -----------------------------
messages_container = st.container()

with messages_container:
    # Standard chat view title (compact, aligned to top-left)
    st.markdown(
        """
        <h2 style="margin-bottom:0.1rem; letter-spacing: -0.015em;">Support Chat</h2>
        <p style="color:var(--text-secondary); margin-top:0; font-size: 0.95rem; margin-bottom: 1.5rem;">
            Describe your issue below. Tier 1 resolves common requests instantly,
            while complex issues escalate to a specialist automatically.
        """,
        unsafe_allow_html=True,
    )
    
    for message in st.session_state["chat_messages"]:

        role = message.get("role")
        content = message.get("content", "")
        meta = message.get("metadata") or {}

        if role == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(content)
        else:
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(content)
                
                if not meta.get("is_conversational", False):
                    # Badges row
                    tier_used = meta.get("tier_used", "Tier1")
                    status = meta.get("status", "")
                    specialist = meta.get("specialist", "")
                    
                    if tier_used:
                        badges_html = f'<div style="margin-top: 0.5rem; margin-bottom: 0.5rem;">{tier_badge(tier_used, specialist)} {status_badge(status)}</div>'
                        st.markdown(badges_html, unsafe_allow_html=True)

                    # Technical Details in an elegant Popover
                    if meta:
                        with st.popover("⚙️ Details", use_container_width=False):
                            if auth_service.is_admin():
                                st.write("**Retrieval Confidence:**", meta.get("confidence", 0.0))
                                st.write("**Category:**", meta.get("category", ""))
                                st.write("**Response Time:**", f"{meta.get('response_time_ms', 0)} ms")
                                st.write("**Routing Path:**")
                                st.code(" -> ".join(meta.get("route", []) or ["Router", "Tier1", "END"]))
                                
                                tier1 = meta.get("tier1", {}) or {}
                                st.write("**Tier 1 Justification:**", tier1.get("justification", ""))
                                
                                tier2 = meta.get("tier2", {}) or {}
                                if tier2:
                                    st.write("**Tier 2 Justification:**", tier2.get("justification", ""))
                                    st.write("**Root Cause:**", tier2.get("root_cause", "Not identified."))
                                    st.write("**Advanced Diagnostics:**", tier2.get("advanced_diagnostics", "None."))
                                    st.write("**Next Action:**", tier2.get("next_action", ""))
                                    
                                st.write("**Knowledge Base Articles Used:**")
                                for doc in meta.get("documents", []):
                                    st.write("-", doc.get("file", ""))
                            else:
                                st.write("**Status:**", meta.get("status", ""))
                                st.write("**Support Tier:**", meta.get("tier_used", "Tier 1"))
                                tier2 = meta.get("tier2", {}) or {}
                                if tier2:
                                    st.write("**Next Action:**", tier2.get("next_action", ""))



# -----------------------------
# Chat input
# -----------------------------
placeholder_text = "Ask me anything..."

query = st.chat_input(placeholder_text)

if query:
    # Render user message instantly in the UI
    with messages_container:
        with st.chat_message("user", avatar="👤"):
            st.markdown(query)

    # Spinner while computing LangGraph response
    with st.spinner("Analyzing escalation path..."):
        result = chat_service.run_query(user["id"], conversation_id, query)

    # Stream the assistant answer smoothly inside native chat_message
    with messages_container:
        with st.chat_message("assistant", avatar="🤖"):
            final_answer = result.get("final_answer", "")
            
            def answer_generator():
                for word in final_answer.split(" "):
                    yield word + " "
                    time.sleep(0.015)
                    
            st.write_stream(answer_generator)
            
            if not result.get("is_conversational", False):
                # Show details button and badges immediately
                routing = result.get("routing", {})
                tier1 = result.get("tier1", {})
                tier2 = result.get("tier2") or {}
                used_tier2 = bool(tier2)
                tier_used = "Tier2" if used_tier2 else "Tier1"
                specialist = tier2.get("specialist", "")
                status = tier2.get("status") if used_tier2 else tier1.get("status")

                badges_html = f'<div style="margin-top: 0.5rem; margin-bottom: 0.5rem;">{tier_badge(tier_used, specialist)} {status_badge(status)}</div>'
                st.markdown(badges_html, unsafe_allow_html=True)


    # Auto-title the conversation from the first message
    if len(st.session_state["chat_messages"]) == 0:
        title = db_service.generate_title(query)
        db_service.rename_conversation(conversation_id, title)

    # Reload history from DB & trigger final rerun to sync state and update sidebar
    st.session_state["chat_messages"] = db_service.list_messages(conversation_id)
    st.rerun()
