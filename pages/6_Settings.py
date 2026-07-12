import streamlit as st

from auth import auth_service
from components.layout import inject_theme
from components.sidebar import render_sidebar
from database import db_service
from services import export_service

st.set_page_config(page_title="Settings - Support Escalation AI", layout="wide")
inject_theme()
auth_service.bootstrap_session()
auth_service.require_auth()

user = auth_service.current_user()
render_sidebar(active_page="settings")

st.markdown("<h2 style='letter-spacing: -0.015em; margin-bottom: 1.5rem;'>Settings</h2>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown("<h4 style='margin-top:0;'>Appearance</h4>", unsafe_allow_html=True)
    current_theme = st.session_state.get("theme", "dark")
    theme_choice = st.radio(
        "Theme",
        ["Dark", "Light"],
        index=0 if current_theme == "dark" else 1,
        horizontal=True,
    )
    new_theme = theme_choice.lower()
    if new_theme != current_theme:
        st.session_state["theme"] = new_theme
        st.query_params["theme"] = new_theme
        st.rerun()
    st.caption("Theme preference is saved in your browser URL to survive refreshes.")


with st.container(border=True):
    st.markdown("<h4 style='margin-top:0;'>Manage Conversations</h4>", unsafe_allow_html=True)
    st.write("")

    conversations = db_service.list_conversations(user["id"])
    if conversations:
        for convo in conversations:
            c1, c2, c3 = st.columns([4, 1, 1])
            c1.write(f"**{convo.get('title', 'Untitled')}**")

            with c2.popover("Rename"):
                new_title = st.text_input(
                    "New title", value=convo.get("title", ""), key=f"rename_{convo['id']}"
                )
                if st.button("Save", key=f"save_{convo['id']}"):
                    db_service.rename_conversation(convo["id"], new_title.strip() or "Untitled")
                    st.rerun()

            if c3.button("Delete", key=f"delete_{convo['id']}"):
                db_service.delete_conversation(convo["id"])
                if st.session_state.get("active_conversation_id") == convo["id"]:
                    st.session_state["active_conversation_id"] = None
                    st.session_state["chat_messages"] = None
                st.rerun()
    else:
        st.info("No conversations yet.")

with st.container(border=True):
    st.markdown("<h4 style='margin-top:0;'>Export a Conversation</h4>", unsafe_allow_html=True)
    st.write("")

    if conversations:
        options = {c["title"] or "Untitled": c["id"] for c in conversations}
        selected_title = st.selectbox("Conversation", list(options.keys()))
        selected_id = options[selected_title]
        messages = db_service.list_messages(selected_id)
        safe_name = selected_title.replace(" ", "_").replace("/", "-")

        export_format = st.radio("Format", ["JSON", "Plain text", "PDF"], horizontal=True)

        if export_format == "JSON":
            st.download_button(
                "Download JSON",
                data=export_service.to_json(messages),
                file_name=f"{safe_name}.json",
                mime="application/json",
                use_container_width=True
            )
        elif export_format == "Plain text":
            st.download_button(
                "Download Text",
                data=export_service.to_text(messages),
                file_name=f"{safe_name}.txt",
                mime="text/plain",
                use_container_width=True
            )
        else:
            pdf_bytes = export_service.to_pdf(messages, title=selected_title)
            st.download_button(
                "Download PDF",
                data=pdf_bytes,
                file_name=f"{safe_name}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    else:
        st.info("No conversations to export yet.")

with st.container(border=True):
    st.markdown("<h4 style='margin-top:0; color:var(--red);'>Danger Zone</h4>", unsafe_allow_html=True)
    st.write("This permanently deletes all of your conversations and messages. This cannot be undone.")
    confirm = st.checkbox("I understand this cannot be undone")
    if st.button("Clear all conversations", type="primary", disabled=not confirm, use_container_width=True):
        for convo in conversations:
            db_service.delete_conversation(convo["id"])
        st.session_state["active_conversation_id"] = None
        st.session_state["chat_messages"] = None
        st.success("All conversations cleared.")
        st.rerun()
