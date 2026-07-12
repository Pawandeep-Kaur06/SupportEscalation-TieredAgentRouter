"""Turns a list of message rows into JSON / plain-text / PDF exports."""

import json
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def to_json(messages: list[dict]) -> str:
    return json.dumps(messages, indent=2, default=str)


def to_text(messages: list[dict]) -> str:
    lines = []
    for m in messages:
        speaker = "You" if m["role"] == "user" else "Assistant"
        lines.append(f"{speaker}: {m['content']}\n")
    return "\n".join(lines)


def _escape(text: str) -> str:
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def to_pdf(messages: list[dict], title: str = "Conversation") -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "SETitle", parent=styles["Heading1"], spaceAfter=14
    )
    user_style = ParagraphStyle(
        "SEUser",
        parent=styles["BodyText"],
        alignment=TA_LEFT,
        textColor=colors.HexColor("#1f2937"),
        backColor=colors.HexColor("#eef2ff"),
        borderPadding=8,
        spaceAfter=10,
    )
    assistant_style = ParagraphStyle(
        "SEAssistant",
        parent=styles["BodyText"],
        alignment=TA_LEFT,
        textColor=colors.HexColor("#1f2937"),
        backColor=colors.HexColor("#f3f4f6"),
        borderPadding=8,
        spaceAfter=10,
    )
    label_style = ParagraphStyle(
        "SELabel", parent=styles["BodyText"], fontSize=8, textColor=colors.grey, spaceAfter=2
    )

    story = [Paragraph(_escape(title), title_style)]

    for m in messages:
        speaker = "You" if m["role"] == "user" else "Assistant"
        style = user_style if m["role"] == "user" else assistant_style
        story.append(Paragraph(speaker, label_style))
        story.append(Paragraph(_escape(m.get("content", "")), style))
        story.append(Spacer(1, 4))

    doc.build(story)
    return buffer.getvalue()
