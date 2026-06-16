import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils import load_data, page_config, show_logo, show_top_logo
from db_utils import require_auth, render_save_ui, dataframe_to_dict

require_auth()

page_config("Kayfa — Student Risk & Segmentation", "⚠️")
show_logo()
show_top_logo()

master = load_data()

st.title("⚠️ Student Risk Profiling & Segmentation")
st.markdown("##### Age bands, behavioral clustering, and at-risk identification")

# ── Q10: Age Bands vs Outcomes ──
st.header("Q10: Age Bands vs Outcomes — Does Age Matter?")

master["age_band"] = pd.cut(
    master["age"], bins=[0, 20, 25, 30, 35, 100],
    labels=["18-20", "21-25", "26-30", "31-35", "36+"],
)

age_analysis = master.groupby("age_band", observed=True).agg(
    avg_grade=("avg_concept_score", "mean"),
    avg_att=("attendance_rate_pct", "mean"),
    avg_fail_rate=("concept_fail_pct", "mean"),
    count=("student_id", "count"),
).reset_index()
age_analysis.columns = ["Age Band", "Avg Grade %", "Avg Attendance %", "Avg Fail Rate %", "Count"]

best_age = age_analysis.loc[age_analysis["Avg Grade %"].idxmax()]

col1, col2 = st.columns(2)

with col1:
    fig1 = px.bar(
        age_analysis, x="Age Band", y=["Avg Grade %", "Avg Attendance %"], barmode="group",
        title="Grade & Attendance by Age Band",
        labels={"value": "Percentage (%)", "variable": "Metric"},
        color_discrete_sequence=["#6366f1", "#10b981"]
    )
    fig1.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11), legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    fig2 = px.pie(
        age_analysis, values="Count", names="Age Band", hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set2,
        title="Student Population by Age Band",
    )
    fig2.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("")
st.subheader("💡 Professional Insights")
st.info(f"""
**Age & Performance Trend:**  
The data shows that the **{best_age['Age Band']}** age band performs the best across the board, with the highest average grades ({best_age['Avg Grade %']:.1f}%) and attendance rates ({best_age['Avg Attendance %']:.1f}%). 

**Recommendation:**  
Younger or older age groups often face different challenges, such as work commitments or adapting to the learning platform. Consider offering flexible learning paths or mentorship programs specifically targeted at the age bands that are falling behind.
""")

st.divider()

# ── Q14: At-Risk Ranking ──
st.header("Q14: At-Risk Ranking — Top Students to Contact First")

risk = master[["student_id", "full_name", "group_id", "concepts_failed", "attendance_rate_pct",
               "avg_concept_score", "late_rate", "total_events"]].copy()

risk["z_low_att"] = (100 - risk["attendance_rate_pct"]) / risk["attendance_rate_pct"].std()
risk["z_low_grade"] = (100 - risk["avg_concept_score"]) / risk["avg_concept_score"].std()
risk["z_failed"] = risk["concepts_failed"] / risk["concepts_failed"].std()
risk["z_late"] = risk["late_rate"] / risk["late_rate"].std()

risk["risk_score"] = risk["z_low_att"] + risk["z_low_grade"] + risk["z_failed"] + risk["z_late"]
risk = risk.sort_values("risk_score", ascending=False)

# Show Top 6 in a 3-column grid to save vertical space
top6 = risk.head(6)

cols_per_row = 3
for i in range(0, len(top6), cols_per_row):
    cols = st.columns(cols_per_row)
    for j in range(cols_per_row):
        if i + j < len(top6):
            row = top6.iloc[i + j]
            with cols[j]:
                with st.container(border=True):
                    st.markdown(f"<h4 style='color: #ef4444; margin-bottom: 0; margin-top: 0;'>#{i+j+1} {row['full_name']}</h4>", unsafe_allow_html=True)
                    st.caption(f"{row['student_id']} | Group {row['group_id']}")
                    st.markdown(f"**Risk Score: {row['risk_score']:.1f}**")
                    st.markdown(f"Att: {row['attendance_rate_pct']:.0f}% | Score: {row['avg_concept_score']:.1f}%")

st.markdown("")
with st.expander("🔍 View Full At-Risk List (Scrollable)"):
    with st.container(height=350):
        for i, (_, r) in enumerate(risk.iloc[6:50].iterrows()):
            st.warning(f"**#{i+7} {r['full_name']}** (Group {r['group_id']}) — **Risk: {r['risk_score']:.1f}** | Att: {r['attendance_rate_pct']:.0f}% | Score: {r['avg_concept_score']:.1f}% | Fails: {int(r['concepts_failed'])}")

st.divider()

# ── Summary ──
st.header("📋 Key Takeaways")
st.markdown("""
| Question | Finding |
|---|---|
| **Q10 — Age Bands** | Best-performing age band: **{best_band}** |
| **Q14 — At-Risk Top** | **#{worst_name}** (risk={worst_risk:.1f}): {worst_att:.0f}% att, {worst_grade:.1f}% grade, {worst_fail} failures |
""".format(best_band=best_age['Age Band'],
           worst_name=top6.iloc[0]['full_name'],
           worst_risk=top6.iloc[0]['risk_score'],
           worst_att=top6.iloc[0]['attendance_rate_pct'],
           worst_grade=top6.iloc[0]['avg_concept_score'],
           worst_fail=int(top6.iloc[0]['concepts_failed'])))

render_save_ui("student_profiling", "Student profiling data",
               dataframe_to_dict(risk.head(10)))
