"""
Best-effort "remember me" using a browser cookie.

streamlit-cookies-controller renders a tiny invisible component to read/write
cookies; on the very first script run after a hard refresh the cookie value
may not be available yet (the component hasn't reported back), so callers
should treat a None result as "unknown, try again next rerun" rather than
"definitely logged out". This is a known limitation of browser-cookie
components in Streamlit, not a bug in this file.
"""

import streamlit as st

try:
    from streamlit_cookies_controller import CookieController
    _COOKIES_AVAILABLE = True
except ImportError:
    _COOKIES_AVAILABLE = False

COOKIE_NAME = "se_auth_session"


@st.cache_resource
def _controller():
    return CookieController()


def save(user_id: str, email: str, role: str, access_token: str, refresh_token: str) -> None:
    if not _COOKIES_AVAILABLE:
        return
    try:
        _controller().set(
            COOKIE_NAME,
            {
                "user_id": user_id,
                "email": email,
                "role": role,
                "access_token": access_token,
                "refresh_token": refresh_token,
            },
            max_age=60 * 60 * 24 * 30,  # 30 days
        )
    except Exception:
        pass


def load() -> dict | None:
    if not _COOKIES_AVAILABLE:
        return None
    try:
        return _controller().get(COOKIE_NAME)
    except Exception:
        return None


def clear() -> None:
    if not _COOKIES_AVAILABLE:
        return
    try:
        _controller().remove(COOKIE_NAME)
    except Exception:
        pass
