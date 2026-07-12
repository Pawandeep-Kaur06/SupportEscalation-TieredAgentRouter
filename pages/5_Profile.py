import streamlit as st

from auth import auth_service
from components.badges import admin_badge
from components.layout import inject_theme
from components.sidebar import render_sidebar
from database import db_service

st.set_page_config(page_title="Profile - Support Escalation AI", layout="wide")
inject_theme()
auth_service.bootstrap_session()
auth_service.require_auth()

user = auth_service.current_user()
render_sidebar(active_page="profile")

st.markdown("<h2 style='letter-spacing: -0.015em; margin-bottom: 1.5rem;'>Profile</h2>", unsafe_allow_html=True)

conversations = db_service.list_conversations(user["id"])
initial = (user["email"] or "?")[0].upper()

# -----------------------------
# Identity card
# -----------------------------
with st.container(border=True):
    id_col, badge_col = st.columns([5, 1])
    with id_col:
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:1.25rem; padding: 0.5rem 0;">
                <div class="se-avatar-lg">{initial}</div>
                <div>
                    <div style="font-size:1.2rem; font-weight:700; color:var(--text-primary);">{user['email']}</div>
                    <div style="color:var(--text-secondary); font-size:0.85rem; margin-top: 0.2rem;">Account Member</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with badge_col:
        if user["role"] == "admin":
            st.markdown(
                f'<div style="text-align:right; padding-top:1.1rem;">{admin_badge()}</div>',
                unsafe_allow_html=True,
            )

# -----------------------------
# Metric grid
# -----------------------------
st.write("")
m1, m2 = st.columns(2)
m1.metric("Role", user["role"].capitalize())
m2.metric("Total Conversations", len(conversations))

st.write("")

# -----------------------------
# Conversation timeline
# -----------------------------
with st.container(border=True):
    st.markdown("##### Your Conversations")
    st.write("")

    if conversations:
        rows = ""
        for convo in conversations:
            title = convo.get("title", "Untitled")
            date_str = (convo.get("updated_at") or "")[:16].replace("T", " ")
            rows += f"""
            <div class="se-convo-row">
                <span class="se-convo-title">📄 {title}</span>
                <span class="se-convo-date">{date_str}</span>
            </div>
            """
        st.markdown(rows, unsafe_allow_html=True)
    else:
        st.info("You haven't started a conversation yet.")
