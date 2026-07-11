from pathlib import Path

import streamlit as st

_STYLES_DIR = Path(__file__).resolve().parent.parent / "styles"


def inject_theme():
    theme = st.session_state.get("theme", "dark")
    css_file = "theme_light.css" if theme == "light" else "theme_dark.css"
    css = (_STYLES_DIR / css_file).read_text()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
