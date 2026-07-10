import pandas as pd
import streamlit as st

from graph import graph
from logger import get_logs, get_metrics


st.set_page_config(
    page_title="Support Escalation: Tiered Agent Router",
    layout="wide",
)

st.title("Support Escalation: Tiered Agent Router")

st.write(
    "AI-powered IT support using RAG, LangGraph, Tier-1 and Tier-2 Agents."
)

# -----------------------------
# Sidebar Metrics
# -----------------------------

metrics = get_metrics()

st.sidebar.header("Metrics")

st.sidebar.metric("Total Queries", metrics["total_queries"])
st.sidebar.metric("Tier 1 Resolved", metrics["tier1_resolved"])
st.sidebar.metric("Tier 2 Resolved", metrics["tier2_resolved"])
st.sidebar.metric("Escalated", metrics["escalated"])
st.sidebar.metric("Unresolved", metrics["unresolved"])
st.sidebar.metric("Average Confidence", f"{metrics['average_confidence']:.2f}")

# -----------------------------
# User Query
# -----------------------------

query = st.text_input("Describe your issue")
submit = st.button("Submit")

# -----------------------------
# Invoke Graph
# -----------------------------

if submit:
    if not query.strip():
        st.warning("Please enter a query.")
    else:
        with st.spinner("Thinking..."):
            result = graph.invoke({"query": query})

        st.success("Response Generated")
        st.divider()

        routing = result["routing"]
        tier1 = result["tier1"]
        tier2 = result.get("tier2") or {}
        used_tier2 = bool(tier2)
        specialist = tier2.get("specialist", "")
        final_status = tier2.get("status") if used_tier2 else tier1.get("status")
        final_category = (
            result.get("handoff", {}).get("category")
            if used_tier2
            else tier1.get("category", routing.get("category", "General"))
        )
        route = result.get("log_entry", {}).get("route", [])
        tier_label = (
            f"Tier 2 ({specialist} Specialist)"
            if used_tier2 and specialist
            else ("Tier 2" if used_tier2 else "Tier 1")
        )

        # -----------------------------
        # Support Summary
        # -----------------------------

        st.subheader("Support Summary")

        c1, c2, c3 = st.columns(3)
        c1.metric("Tier Used", tier_label)
        c2.metric("Status", final_status)
        c3.metric("Retrieval Confidence", f"{routing['confidence']:.2f}")

        c4, c5, c6 = st.columns(3)
        c4.metric("Category", final_category)
        c5.metric("Router Decision", routing["tier"])
        c6.metric("Specialist Used", specialist or "Not used")

        st.write("**Routing Path**")
        st.code(" -> ".join(route or ["Router", "Tier1", "END"]))

        # -----------------------------
        # Final Answer
        # -----------------------------

        st.subheader("Answer")
        st.write(result["final_answer"])

        if used_tier2:
            st.subheader("Root Cause")
            st.write(tier2.get("root_cause") or "Not identified.")

            st.subheader("Advanced Diagnostics")
            st.write(
                tier2.get("advanced_diagnostics")
                or "No advanced diagnostics required."
            )

            st.subheader("Next Action")
            st.write(tier2.get("next_action") or "No additional action provided.")

        # -----------------------------
        # Technical Details
        # -----------------------------

        with st.expander("Technical Details"):
            st.write("**Retrieval Confidence:**", routing["confidence"])
            st.write("**Router Decision:**", routing["tier"])
            st.write("**Category:**", final_category)
            st.write("**Status:**", final_status)
            st.write("**Tier 1 Justification:**")
            st.write(tier1.get("justification", ""))

            if used_tier2:
                st.write("**Tier 2 Justification:**")
                st.write(tier2.get("justification", ""))

            st.write("**Knowledge Base Articles Used**")
            for doc in routing["documents"]:
                st.write("-", doc["file"])

            if "log_entry" in result:
                st.write("**Route**")
                st.code(" -> ".join(result["log_entry"].get("route", [])))

# -----------------------------
# Logs
# -----------------------------

st.divider()
st.subheader("Recent Requests")

logs = get_logs()

if logs:
    df = pd.DataFrame(logs[::-1])
    st.dataframe(df, use_container_width=True)
else:
    st.info("No logs available.")
