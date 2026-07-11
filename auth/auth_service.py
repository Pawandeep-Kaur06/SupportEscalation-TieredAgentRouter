"""Authentication service with Supabase support and a local SQLite fallback."""

from dataclasses import dataclass
import hashlib
import secrets
import sqlite3
from pathlib import Path

import streamlit as st

from auth import session_cookie
from auth.supabase_client import get_client
from config import ROOT_DIR, SUPABASE_CONFIGURED

SESSION_KEYS = (
    "auth_user_id",
    "auth_email",
    "auth_role",
    "auth_access_token",
    "auth_refresh_token",
)

LOCAL_DB = ROOT_DIR / "database" / "local_app.db"


@dataclass
class AuthResult:
    success: bool
    message: str = ""


def _connect():
    LOCAL_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(LOCAL_DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS local_users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    return conn


def _hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000)
    return f"{salt}${digest.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, digest = stored_hash.split("$", 1)
    except ValueError:
        return False
    return secrets.compare_digest(_hash_password(password, salt), f"{salt}${digest}")


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
    resp = (
        client.table("profiles")
        .select("role")
        .eq("id", user_id)
        .single()
        .execute()
    )
    if resp.data:
        return resp.data.get("role", "user")
    return "user"


def _local_role_for_new_user() -> str:
    with _connect() as conn:
        count = conn.execute("SELECT COUNT(*) FROM local_users").fetchone()[0]
    return "admin" if count == 0 else "user"


def sign_up(email: str, password: str, full_name: str = "") -> AuthResult:
    if not email or not password:
        return AuthResult(False, "Email and password are required.")
    if len(password) < 8:
        return AuthResult(False, "Password must be at least 8 characters.")

    if not SUPABASE_CONFIGURED:
        user_id = secrets.token_hex(16)
        role = _local_role_for_new_user()
        try:
            with _connect() as conn:
                conn.execute(
                    """
                    INSERT INTO local_users (id, email, full_name, password_hash, role)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (user_id, email, full_name, _hash_password(password), role),
                )
        except sqlite3.IntegrityError:
            return AuthResult(False, "An account with this email already exists.")

        token = f"local-{secrets.token_hex(24)}"
        _store_session(user_id, email, role, token, token)
        session_cookie.save(user_id, email, role, token, token)
        return AuthResult(True, "Local account created and signed in.")

    client = get_client()
    try:
        response = client.auth.sign_up(
            {
                "email": email,
                "password": password,
                "options": {"data": {"full_name": full_name}},
            }
        )
    except Exception as error:
        return AuthResult(False, f"Sign up failed: {error}")

    if response.user is None:
        return AuthResult(False, "Sign up failed. Please try again.")

    if response.session is None:
        return AuthResult(True, "Account created. Check your email to confirm before signing in.")

    _store_session(
        response.user.id,
        response.user.email,
        "user",
        response.session.access_token,
        response.session.refresh_token,
    )
    session_cookie.save(
        response.user.id,
        response.user.email,
        "user",
        response.session.access_token,
        response.session.refresh_token,
    )
    return AuthResult(True, "Account created and signed in.")


def sign_in(email: str, password: str) -> AuthResult:
    if not email or not password:
        return AuthResult(False, "Email and password are required.")

    if not SUPABASE_CONFIGURED:
        with _connect() as conn:
            user = conn.execute(
                "SELECT * FROM local_users WHERE lower(email) = lower(?)",
                (email,),
            ).fetchone()

        if not user or not _verify_password(password, user["password_hash"]):
            return AuthResult(False, "Invalid email or password.")

        token = f"local-{secrets.token_hex(24)}"
        _store_session(user["id"], user["email"], user["role"], token, token)
        session_cookie.save(user["id"], user["email"], user["role"], token, token)
        return AuthResult(True, "Signed in.")

    client = get_client()
    try:
        response = client.auth.sign_in_with_password({"email": email, "password": password})
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
        response.user.id,
        response.user.email,
        role,
        response.session.access_token,
        response.session.refresh_token,
    )
    return AuthResult(True, "Signed in.")


def sign_out() -> None:
    if SUPABASE_CONFIGURED:
        try:
            get_client().auth.sign_out()
        except Exception:
            pass
    _clear_session()
    session_cookie.clear()


def bootstrap_session() -> None:
    if is_authenticated():
        return

    remembered = session_cookie.load()
    if not remembered:
        return

    if SUPABASE_CONFIGURED:
        client = get_client()
        try:
            client.auth.set_session(remembered["access_token"], remembered["refresh_token"])
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

    if not SUPABASE_CONFIGURED:
        return AuthResult(
            False,
            "Password reset email is unavailable in local mode. Create a new local account or configure Supabase.",
        )

    client = get_client()
    try:
        options = {"redirect_to": redirect_to} if redirect_to else None
        if options:
            client.auth.reset_password_email(email, options)
        else:
            client.auth.reset_password_email(email)
    except Exception as error:
        return AuthResult(False, f"Could not send reset email: {error}")

    return AuthResult(True, "Password reset email sent if the account exists.")


def restore_session() -> bool:
    access_token = st.session_state.get("auth_access_token")
    refresh_token = st.session_state.get("auth_refresh_token")

    if not access_token or not refresh_token:
        return False

    if not SUPABASE_CONFIGURED:
        return True

    client = get_client()
    try:
        client.auth.set_session(access_token, refresh_token)
    except Exception:
        _clear_session()
        return False

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
    if not is_authenticated() or not restore_session():
        st.warning("Please sign in to continue.")
        st.page_link("pages/1_Login.py", label="Go to Login")
        st.stop()


def require_admin() -> None:
    require_auth()
    if not is_admin():
        st.error("This page is only available to administrators.")
        st.stop()
