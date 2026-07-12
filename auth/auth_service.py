"""
Auth service built on Supabase Auth.

Design notes:
- We never touch password hashes ourselves; Supabase Auth owns that.
- After sign_in / sign_up, the Supabase client keeps the user's session
  internally, so subsequent PostgREST calls made through the same
  client are automatically scoped by RLS as that user.
- Streamlit reruns the whole script on every interaction, so we persist
  the minimum needed (user id, email, role, access/refresh tokens) in
  st.session_state and re-hydrate the Supabase client's session from it
  on each rerun.
"""

from dataclasses import dataclass

import streamlit as st

from auth import session_cookie
from auth.supabase_client import get_client
from config import AUTH_CALLBACK_URL

AUTH_UNAVAILABLE_MESSAGE = (
    "Authentication is not configured. Set SUPABASE_URL and SUPABASE_KEY, "
    "then restart the Streamlit app."
)

SESSION_KEYS = (
    "auth_user_id",
    "auth_email",
    "auth_role",
    "auth_access_token",
    "auth_refresh_token",
)


@dataclass
class AuthResult:
    success: bool
    message: str = ""


def _store_session(user_id, email, role, access_token, refresh_token):
    st.session_state["auth_user_id"] = user_id
    st.session_state["auth_email"] = email
    st.session_state["auth_role"] = role
    st.session_state["auth_access_token"] = access_token
    st.session_state["auth_refresh_token"] = refresh_token


def _clear_session():
    for key in SESSION_KEYS:
        st.session_state.pop(key, None)


def _fetch_role(client, user_id: str) -> str:
    try:
        resp = (
            client.table("profiles")
            .select("role")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
    except Exception:
        return "user"

    if resp.data:
        return resp.data.get("role") or "user"
    return "user"


def _store_auth_response(response) -> bool:
    if response is None or response.user is None or response.session is None:
        return False

    role = _fetch_role(get_client(), response.user.id)
    _store_session(
        response.user.id,
        response.user.email,
        role,
        response.session.access_token,
        response.session.refresh_token,
    )
    session_cookie.save(
        response.user.id,
        response.user.email,
        role,
        response.session.access_token,
        response.session.refresh_token,
    )
    return True


def sign_up(email: str, password: str, full_name: str = "") -> AuthResult:
    if not email or not password:
        return AuthResult(False, "Email and password are required.")
    if len(password) < 8:
        return AuthResult(False, "Password must be at least 8 characters.")

    try:
        client = get_client()
        response = client.auth.sign_up(
            {
                "email": email,
                "password": password,
                "options": {
                    "data": {"full_name": full_name},
                    "email_redirect_to": AUTH_CALLBACK_URL,
                },
            }
        )
    except Exception as error:
        message = str(error)
        if "rate limit" in message.lower() or "security purposes" in message.lower():
            return AuthResult(
                False,
                "Signup email limit reached. Wait a few minutes, then try again, "
                "or use the verification email that was already sent.",
            )
        return AuthResult(False, f"Sign up failed: {error}")

    if response.user is None:
        return AuthResult(False, "Sign up failed. Please try again.")

    if response.session is None:
        # Email confirmation is enabled on this Supabase project.
        return AuthResult(
            True,
            "Account created. Check your email to confirm before signing in.",
        )

    _store_session(
        response.user.id,
        response.user.email,
        "user",
        response.session.access_token,
        response.session.refresh_token,
    )
    session_cookie.save(
        response.user.id, response.user.email, "user",
        response.session.access_token, response.session.refresh_token,
    )
    return AuthResult(True, "Account created and signed in.")


def sign_in(email: str, password: str) -> AuthResult:
    if not email or not password:
        return AuthResult(False, "Email and password are required.")

    try:
        client = get_client()
        response = client.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
    except RuntimeError as error:
        return AuthResult(False, str(error) or AUTH_UNAVAILABLE_MESSAGE)
    except Exception:
        return AuthResult(False, "Invalid email or password.")

    if response.user is None or response.session is None:
        return AuthResult(False, "Invalid email or password.")

    role = _fetch_role(client, response.user.id)

    _store_session(
        response.user.id,
        response.user.email,
        role,
        response.session.access_token,
        response.session.refresh_token,
    )
    session_cookie.save(
        response.user.id, response.user.email, role,
        response.session.access_token, response.session.refresh_token,
    )
    return AuthResult(True, "Signed in.")


def sign_out() -> None:
    try:
        get_client().auth.sign_out()
    except Exception:
        pass
    _clear_session()
    session_cookie.clear()


def bootstrap_session() -> None:
    """
    Call once near the top of app.py, before any page routing decisions.
    If st.session_state already has a session, this is a no-op. Otherwise
    it tries to restore one from the "remember me" cookie.
    """
    if is_authenticated():
        return

    remembered = session_cookie.load()
    if not remembered:
        return
    if not isinstance(remembered, dict):
        session_cookie.clear()
        return
    if not remembered.get("access_token") or not remembered.get("refresh_token"):
        session_cookie.clear()
        return

    try:
        client = get_client()
        client.auth.set_session(
            remembered["access_token"], remembered["refresh_token"]
        )
    except Exception:
        session_cookie.clear()
        return

    _store_session(
        remembered["user_id"],
        remembered["email"],
        remembered.get("role", "user"),
        remembered["access_token"],
        remembered["refresh_token"],
    )


def request_password_reset(email: str, redirect_to: str | None = None) -> AuthResult:
    if not email:
        return AuthResult(False, "Enter your email first.")

    try:
        client = get_client()
        client.auth.reset_password_email(
            email,
            {"redirect_to": redirect_to or AUTH_CALLBACK_URL},
        )
    except Exception as error:
        return AuthResult(False, f"Could not send reset email: {error}")

    return AuthResult(True, "Password reset email sent if the account exists.")


def complete_auth_callback(params: dict) -> AuthResult:
    error = params.get("error_description") or params.get("error")
    if error:
        return AuthResult(False, str(error).replace("+", " "))

    try:
        client = get_client()
    except Exception as exc:
        return AuthResult(False, str(exc) or AUTH_UNAVAILABLE_MESSAGE)
    code = params.get("code")
    if code:
        try:
            response = client.auth.exchange_code_for_session({"auth_code": code})
        except Exception as exc:
            return AuthResult(False, f"Could not complete email confirmation: {exc}")

        if _store_auth_response(response):
            return AuthResult(True, "Email confirmed. You are signed in.")
        return AuthResult(True, "Email confirmed. Please sign in.")

    token_hash = params.get("token_hash")
    if token_hash:
        verification_type = params.get("type") or "signup"
        try:
            response = client.auth.verify_otp(
                {"token_hash": token_hash, "type": verification_type}
            )
        except Exception as exc:
            return AuthResult(False, f"Could not verify email link: {exc}")

        if _store_auth_response(response):
            return AuthResult(True, "Email confirmed. You are signed in.")
        return AuthResult(True, "Email confirmed. Please sign in.")

    return AuthResult(
        True,
        "Email confirmed. You can sign in now.",
    )


def restore_session() -> bool:
    """
    Re-hydrate the Supabase client's auth session from Streamlit's
    session_state on a rerun. Returns True if a session was restored.
    """
    access_token = st.session_state.get("auth_access_token")
    refresh_token = st.session_state.get("auth_refresh_token")

    if not access_token or not refresh_token:
        return False

    try:
        response = get_client().auth.set_session(access_token, refresh_token)
    except Exception:
        _clear_session()
        return False

    if response.session:
        st.session_state["auth_access_token"] = response.session.access_token
        st.session_state["auth_refresh_token"] = response.session.refresh_token

    return True


def is_authenticated() -> bool:
    return bool(st.session_state.get("auth_user_id"))


def is_admin() -> bool:
    return st.session_state.get("auth_role") == "admin"


def current_user() -> dict:
    return {
        "id": st.session_state.get("auth_user_id"),
        "email": st.session_state.get("auth_email"),
        "role": st.session_state.get("auth_role", "user"),
    }


def require_auth() -> None:
    """Call at the top of any protected page. Stops the page if unauth'd."""
    if not is_authenticated() or not restore_session():
        st.warning("Please sign in to continue.")
        st.page_link("pages/1_Login.py", label="Go to Login")
        st.stop()


def require_admin() -> None:
    require_auth()
    if not is_admin():
        st.error("This page is only available to administrators.")
        st.stop()
