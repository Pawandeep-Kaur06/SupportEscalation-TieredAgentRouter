"""Shared ChatGPT-style sidebar, rendered from every authenticated page."""

from datetime import datetime, timezone

import streamlit as st

from auth import auth_service
from database import db_service


def _group_label(updated_at_iso: str) -> str:
    try:
        dt = datetime.fromisoformat(updated_at_iso.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return "Older"

    now = datetime.now(timezone.utc)
    delta_days = (now.date() - dt.date()).days

    if delta_days <= 0:
        return "Today"
    if delta_days == 1:
        return "Yesterday"
    return "Older"


def render_sidebar(active_page: str = "chat"):
    user = auth_service.current_user()

    with st.sidebar:
        st.markdown("### Support Escalation AI")

        if st.button("+ New Chat", use_container_width=True, type="primary"):
            convo = db_service.create_conversation(user["id"], "New Chat")
            st.session_state["active_conversation_id"] = convo["id"]
            st.session_state["chat_messages"] = []
            st.switch_page("pages/3_Chat.py")

        conversations = db_service.list_conversations(user["id"])
        groups: dict[str, list] = {"Today": [], "Yesterday": [], "Older": []}
        for convo in conversations:
            groups[_group_label(convo.get("updated_at", ""))].append(convo)

        for label in ("Today", "Yesterday", "Older"):
            items = groups[label]
            if not items:
                continue
            st.markdown(f'<div class="se-sidebar-title">{label}</div>', unsafe_allow_html=True)
            for convo in items:
                is_active = st.session_state.get("active_conversation_id") == convo["id"]
                if st.button(
                    ("* " if is_active else "") + (convo.get("title") or "New Chat"),
                    key=f"convo_{convo['id']}",
                    use_container_width=True,
                ):
                    st.session_state["active_conversation_id"] = convo["id"]
                    st.session_state["chat_messages"] = None
                    st.switch_page("pages/3_Chat.py")

        st.markdown('<div class="se-sidebar-title">Menu</div>', unsafe_allow_html=True)

        if st.button("Chat", use_container_width=True, disabled=(active_page == "chat")):
            st.switch_page("pages/3_Chat.py")

        if auth_service.is_admin():
            if st.button("Admin Dashboard", use_container_width=True, disabled=(active_page == "dashboard")):
                st.switch_page("pages/4_Dashboard.py")

        if st.button("Profile", use_container_width=True, disabled=(active_page == "profile")):
            st.switch_page("pages/5_Profile.py")

        if st.button("Settings", use_container_width=True, disabled=(active_page == "settings")):
            st.switch_page("pages/6_Settings.py")

        st.divider()
        st.caption(user["email"] or "")
        if st.button("Logout", use_container_width=True):
            auth_service.sign_out()
            st.switch_page("app.py")
