import streamlit as st

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


st.set_page_config(page_title="Sign Up - Support Escalation AI", layout="wide")
inject_theme()
hide_sidebar()
auth_service.bootstrap_session()

if auth_service.is_authenticated() and auth_service.restore_session():
    st.switch_page("pages/3_Chat.py")

st.markdown("<div style='height:4vh'></div>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align:center; margin-bottom: 1.5rem;'>Create your account</h2>", unsafe_allow_html=True)

_, center, _ = st.columns([1, 1.8, 1])
with center:
    with st.container(border=True):
        with st.form("signup_form"):
            full_name = st.text_input("Full name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password", help="At least 8 characters.")
            confirm = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button("Sign Up", use_container_width=True, type="primary")

        if submitted:
            if password != confirm:
                st.error("Passwords do not match.")
            else:
                result = auth_service.sign_up(email.strip(), password, full_name.strip())
                if result.success:
                    st.success(result.message)
                    if auth_service.is_authenticated():
                        st.rerun()
                else:
                    st.error(result.message)

    st.write("")
    with st.container(border=True):
        st.markdown("<div style='text-align:center; font-size:0.9rem;'>Already have an account?</div>", unsafe_allow_html=True)
        st.write("")
        if st.button("Sign in", use_container_width=True):
            st.switch_page("pages/1_Login.py")

