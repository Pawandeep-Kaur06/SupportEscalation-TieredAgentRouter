"""HTML chat bubble rendering for user and AI messages."""

import html

import streamlit as st

from components.badges import status_badge, tier_badge


def _to_html_paragraphs(text: str) -> str:
    escaped = html.escape(text or "")
    return escaped.replace("\n", "<br>")


def render_user_message(content: str) -> None:
    st.markdown(
        f"""<div class="se-chat-row se-chat-row-user">
            <div class="se-avatar se-avatar-user">You</div>
            <div class="se-bubble se-bubble-user">{_to_html_paragraphs(content)}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def render_ai_message(
    content: str,
    tier_used: str = "",
    specialist: str = "",
    status: str = "",
) -> None:
    badges_html = ""
    if tier_used:
        badges_html = (
            f'<div class="se-bubble-badges">{tier_badge(tier_used, specialist)} '
            f"{status_badge(status)}</div>"
        )

    st.markdown(
        f"""<div class="se-chat-row">
            <div class="se-avatar se-avatar-ai">AI</div>
            <div class="se-bubble se-bubble-ai">
                {_to_html_paragraphs(content)}
                {badges_html}
            </div>
        </div>""",
        unsafe_allow_html=True,
    )
