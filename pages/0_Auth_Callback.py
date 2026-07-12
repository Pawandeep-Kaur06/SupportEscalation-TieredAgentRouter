import streamlit as st

from auth import auth_service
from components.layout import inject_theme


def _query_params() -> dict:
    params = {}
    for key, value in st.query_params.items():
        params[key] = value[0] if isinstance(value, list) else value
    return params


st.set_page_config(page_title="Email Confirmation - Support Escalation AI", layout="centered")
inject_theme()

st.markdown("<div style='height:8vh'></div>", unsafe_allow_html=True)
st.markdown(
    "<h2 style='text-align:center;'>Email confirmation</h2>",
    unsafe_allow_html=True,
)

_, center, _ = st.columns([1, 1.2, 1])
with center:
    st.markdown('<div class="se-card">', unsafe_allow_html=True)
    params = _query_params()
    callback_key = "|".join(f"{key}={value}" for key, value in sorted(params.items()))

    if st.session_state.get("auth_callback_key") == callback_key:
        st.success(st.session_state["auth_callback_message"])
    else:
        with st.spinner("Confirming your email..."):
            result = auth_service.complete_auth_callback(params)
        st.session_state["auth_callback_key"] = callback_key
        st.session_state["auth_callback_message"] = result.message
        st.session_state["auth_callback_success"] = result.success

        if result.success:
            st.success(result.message)
        else:
            st.error(result.message)

    if auth_service.is_authenticated():
        if st.button("Continue to chat", use_container_width=True, type="primary"):
            st.switch_page("pages/3_Chat.py")
    else:
        if st.button("Go to sign in", use_container_width=True, type="primary"):
            st.switch_page("pages/1_Login.py")

    st.markdown("</div>", unsafe_allow_html=True)
