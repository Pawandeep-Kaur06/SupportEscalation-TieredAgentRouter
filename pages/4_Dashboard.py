import pandas as pd
import plotly.express as px
import streamlit as st

from auth import auth_service
from components.charts import BRAND_PALETTE, apply_chart_theme
from components.layout import inject_theme
from components.sidebar import render_sidebar
from database import db_service

st.set_page_config(page_title="Dashboard - Support Escalation AI", layout="wide")
inject_theme()
auth_service.bootstrap_session()
auth_service.require_admin()

render_sidebar(active_page="dashboard")

st.markdown(
    """
    <h2 style="margin-bottom:0.1rem; letter-spacing: -0.015em;">Admin Dashboard</h2>
    <p style="color:var(--text-secondary); margin-top:0; font-size: 0.95rem; margin-bottom: 1.5rem;">
        Live metrics across every user's support queries.
    </p>
    """,
    unsafe_allow_html=True,
)

metrics = db_service.get_metrics()
total_users = db_service.count_users()

# -----------------------------
# Top-line metrics
# -----------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Users", total_users)
c2.metric("Total Queries", metrics["total_queries"])
c3.metric("Avg. Retrieval Confidence", f"{metrics['average_confidence']:.2f}")
c4.metric("Avg. Response Time", f"{metrics['average_response_ms']:.0f} ms")

st.write("")
c5, c6, c7 = st.columns(3)
total = max(metrics["total_queries"], 1)
tier1_rate = metrics["tier1_resolved"] / total * 100
tier2_rate = metrics["escalated"] / total * 100
c5.metric("Tier 1 Resolution Rate", f"{tier1_rate:.1f}%")
c6.metric("Tier 2 Escalation Rate", f"{tier2_rate:.1f}%")
c7.metric("Unresolved", metrics["unresolved"])

st.write("")

# -----------------------------
# Charts
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("##### Queries by Category")
        if metrics["categories"]:
            cat_df = pd.DataFrame(
                {"Category": list(metrics["categories"].keys()), "Count": list(metrics["categories"].values())}
            )
            fig = px.bar(cat_df, x="Category", y="Count", color="Category", color_discrete_sequence=BRAND_PALETTE)
            fig.update_layout(showlegend=False)
            apply_chart_theme(fig)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No queries logged yet.")

with col2:
    with st.container(border=True):
        st.markdown("##### Resolution Breakdown")
        breakdown = {
            "Tier 1 Resolved": metrics["tier1_resolved"],
            "Tier 2 Resolved": metrics["tier2_resolved"],
            "Unresolved": metrics["unresolved"],
        }
        if sum(breakdown.values()) > 0:
            fig = px.pie(
                names=list(breakdown.keys()),
                values=list(breakdown.values()),
                hole=0.55,
                color_discrete_sequence=[BRAND_PALETTE[2], BRAND_PALETTE[1], BRAND_PALETTE[5]],
            )
            theme = st.session_state.get("theme", "dark")
            slice_text_color = "#000000" if theme == "light" else "#e6edf2"
            fig.update_traces(textfont_color=slice_text_color)
            apply_chart_theme(fig)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No queries logged yet.")

# -----------------------------
# Trend over time
# -----------------------------
with st.container(border=True):
    st.markdown("##### Query Volume Trend")
    logs = db_service.list_recent_logs(limit=2000)
    if logs:
        df = pd.DataFrame(logs)
        df["created_at"] = pd.to_datetime(df["created_at"])
        df["date"] = df["created_at"].dt.date
        trend = df.groupby("date").size().reset_index(name="queries")
        fig = px.line(trend, x="date", y="queries", markers=True, color_discrete_sequence=[BRAND_PALETTE[0]])
        apply_chart_theme(fig, height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No queries logged yet.")

# -----------------------------
# Recent escalations
# -----------------------------
with st.container(border=True):
    st.markdown("##### Recent Escalations")
    if metrics["recent_escalations"]:
        esc_df = pd.DataFrame(metrics["recent_escalations"])[
            ["created_at", "query", "category", "specialist", "status"]
        ]
        esc_df.columns = ["Created At", "Query", "Category", "Specialist", "Status"]
        st.markdown(
            f'<div class="table-container">{esc_df.to_html(index=False, classes="dashboard-table")}</div>',
            unsafe_allow_html=True
        )
    else:
        st.info("No escalations yet.")

# -----------------------------
# Full log table
# -----------------------------
with st.expander("All Recent Requests"):
    if logs:
        full_df = pd.DataFrame(logs)[
            ["created_at", "query", "category", "tier_used", "specialist", "status", "retrieval_confidence"]
        ]
        full_df.columns = ["Created At", "Query", "Category", "Tier Used", "Specialist", "Status", "Confidence"]
        st.markdown(
            f'<div class="table-container">{full_df.to_html(index=False, classes="dashboard-table")}</div>',
            unsafe_allow_html=True
        )
    else:
        st.info("No logs available.")

