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


st.set_page_config(page_title="Sign In - Support Escalation AI", layout="wide")
inject_theme()
hide_sidebar()
auth_service.bootstrap_session()

if auth_service.is_authenticated() and auth_service.restore_session():
    st.switch_page("pages/3_Chat.py")

st.markdown("<div style='height:4vh'></div>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align:center; margin-bottom: 1.5rem;'>Sign In</h2>", unsafe_allow_html=True)

_, center, _ = st.columns([1, 1.8, 1])
with center:
    with st.container(border=True):
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")

        if submitted:
            result = auth_service.sign_in(email.strip(), password)
            if result.success:
                st.success(result.message)
                st.rerun()
            else:
                st.error(result.message)

        st.write("")
        with st.expander("Forgot your password?"):
            reset_email = st.text_input("Email for password reset", key="reset_email")
            if st.button("Send reset link", use_container_width=True):
                result = auth_service.request_password_reset(reset_email.strip())
                (st.success if result.success else st.error)(result.message)

    st.write("")
    with st.container(border=True):
        st.markdown("<div style='text-align:center; font-size:0.9rem;'>Don't have an account?</div>", unsafe_allow_html=True)
        st.write("")
        if st.button("Create one", use_container_width=True):
            st.switch_page("pages/2_Signup.py")

