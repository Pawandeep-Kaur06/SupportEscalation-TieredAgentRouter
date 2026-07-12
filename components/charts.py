"""Applies the dark/light brand theme to Plotly figures consistently
across the dashboard: transparent backgrounds so charts blend into the
page, the brand color sequence, and margins wide enough that axis
labels don't clip against column edges."""

BRAND_PALETTE = ["#6366f1", "#fb7185", "#10b981", "#f59e0b", "#4f46e5", "#8b949e"]


def apply_chart_theme(fig, height: int = 340):
    import streamlit as st
    theme = st.session_state.get("theme", "dark")
    if theme == "light":
        paper_bg = "rgba(0,0,0,0)"
        plot_bg = "rgba(0,0,0,0)"
        font_color = "#000000"
        grid_color = "rgba(0, 0, 0, 0.15)"
        axis_line_color = "#000000"
        axis_font_color = "#000000"
        show_axis_line = True
    else:
        paper_bg = "rgba(0,0,0,0)"
        plot_bg = "rgba(0,0,0,0)"
        font_color = "#8b949e"
        grid_color = "rgba(139,148,158,0.15)"
        axis_line_color = "rgba(139,148,158,0.15)"
        axis_font_color = "#8b949e"
        show_axis_line = False

    fig.update_layout(
        paper_bgcolor=paper_bg,
        plot_bgcolor=plot_bg,
        font=dict(color=font_color, family="Inter, sans-serif"),
        height=height,
        margin=dict(l=48, r=24, t=24, b=48),
        legend=dict(bgcolor=paper_bg, font=dict(color=font_color)),
        colorway=BRAND_PALETTE,
    )
    fig.update_xaxes(
        showline=show_axis_line,
        linecolor=axis_line_color,
        gridcolor=grid_color,
        zerolinecolor=grid_color,
        tickfont=dict(color=axis_font_color),
        title=dict(font=dict(color=axis_font_color))
    )
    fig.update_yaxes(
        showline=show_axis_line,
        linecolor=axis_line_color,
        gridcolor=grid_color,
        zerolinecolor=grid_color,
        tickfont=dict(color=axis_font_color),
        title=dict(font=dict(color=axis_font_color))
    )
    return fig

