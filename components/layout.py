from pathlib import Path

import streamlit as st

_STYLES_DIR = Path(__file__).resolve().parent.parent / "styles"


def inject_theme():
    # Retrieve theme from query parameters (survives refresh) or session state (survives navigation)
    theme = st.query_params.get("theme", None)
    
    if theme:
        st.session_state["theme"] = theme
    else:
        theme = st.session_state.get("theme", "dark")
        st.query_params["theme"] = theme
        
    css_file = "theme_light.css" if theme == "light" else "theme_dark.css"
    css = (_STYLES_DIR / css_file).read_text(encoding="utf-8")
    st.html(f"<style>{css}</style>")



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
