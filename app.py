import streamlit as st
import sys

print("DEBUG: Running with Python executable:", sys.executable)

from auth import auth_service

from components.layout import inject_theme



def hide_sidebar():
    st.html(
        """
        <style>
            [data-testid="stSidebar"], 
            [data-testid="collapsedControl"] {
                display: none !important;
            }
            [data-testid="stAppViewContainer"] {
                padding-left: 0px !important;
            }
        </style>
        """
    )



st.set_page_config(
    page_title="Support Escalation AI",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_theme()
hide_sidebar()
auth_service.bootstrap_session()





if auth_service.is_authenticated() and auth_service.restore_session():
    st.switch_page("pages/3_Chat.py")

st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Fuzzy+Bubbles:wght@400;700&display=swap" rel="stylesheet">
    
    <div style="text-align:center; padding: 3rem 0 1.5rem 0;">
        <span style="font-size:3rem;">💬</span>
        <h1 style="font-family: 'Fuzzy Bubbles', sans-serif; font-weight: 700; margin-top: 1rem; font-size: 2.5rem; letter-spacing: -0.02em;">Support Escalation AI</h1>
        <p style="color:#8b949e; font-size:1.05rem; max-width: 500px; margin: 0.5rem auto 0 auto;">
            AI-powered IT support with RAG retrieval, tiered agent routing,
            and specialist escalation.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


_, col2, _ = st.columns([1, 1.8, 1])
with col2:
    with st.container(border=True):
        st.markdown("<h3 style='margin-top:0;'>Get Started</h3>", unsafe_allow_html=True)
        st.write("Sign in to your account or create a new one to start chatting with the support agent.")
        st.write("")

        b1, b2 = st.columns(2)
        with b1:
            if st.button("Sign In", use_container_width=True, type="primary"):
                st.switch_page("pages/1_Login.py")
        with b2:
            if st.button("Sign Up", use_container_width=True):
                st.switch_page("pages/2_Signup.py")

