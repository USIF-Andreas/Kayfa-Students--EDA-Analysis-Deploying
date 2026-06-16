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

col1, col2 = st.columns(2)

with col1:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=age_analysis["Age Band"], y=age_analysis["Avg Grade %"],
        marker_color=["#6366f1", "#6366f1", "#10b981", "#f59e0b", "#ef4444"],
        text=age_analysis["Avg Grade %"].round(1).astype(str) + "%",
        textposition="outside",
    ))
    fig.update_layout(
        template="plotly_dark", height=350,
        title="Average Grade by Age Band",
        xaxis_title="Age Band", yaxis_title="Avg Grade %",
        margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11),
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=age_analysis["Age Band"], y=age_analysis["Avg Attendance %"],
        marker_color=["#10b981", "#10b981", "#10b981", "#f59e0b", "#ef4444"],
        text=age_analysis["Avg Attendance %"].round(1).astype(str) + "%",
        textposition="outside",
    ))
    fig.update_layout(
        template="plotly_dark", height=350,
        title="Average Attendance by Age Band",
        xaxis_title="Age Band", yaxis_title="Avg Attendance %",
        margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11),
    )
    st.plotly_chart(fig, use_container_width=True)

col3, col4 = st.columns(2)

with col3:
    fig = px.pie(
        age_analysis, values="Count", names="Age Band", hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set2,
        title="Student Distribution by Age Band",
    )
    fig.update_layout(template="plotly_dark", height=350,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

with col4:
    eng_age = master.groupby("age_band", observed=True).agg(
        avg_events=("total_events", "mean"),
        avg_video_hrs=("total_video_seconds", "mean"),
    ).reset_index()
    eng_age["avg_video_hrs"] = (eng_age["avg_video_hrs"] / 3600).round(1)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=eng_age["age_band"], y=eng_age["avg_events"], mode="lines+markers",
        name="Avg Events", line=dict(color="#6366f1", width=3), marker=dict(size=10),
    ))
    fig.add_trace(go.Scatter(
        x=eng_age["age_band"], y=eng_age["avg_video_hrs"], mode="lines+markers",
        name="Avg Video Hrs", line=dict(color="#14b8a6", width=3), marker=dict(size=10),
        yaxis="y2",
    ))
    fig.update_layout(
        template="plotly_dark", height=350,
        title="Engagement by Age Band",
        xaxis_title="Age Band",
        yaxis=dict(title="Avg Events"),
        yaxis2=dict(title="Avg Video Hours", overlaying="y", side="right"),
        margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11),
        legend=dict(orientation="h", y=1.1),
    )
    st.plotly_chart(fig, use_container_width=True)

best_age = age_analysis.loc[age_analysis["Avg Grade %"].idxmax()]
st.info(
    f"**Best-performing age band: {best_age['Age Band']}** "
    f"(Grade: {best_age['Avg Grade %']:.1f}%, Attendance: {best_age['Avg Attendance %']:.1f}%, "
    f"Fail Rate: {best_age['Avg Fail Rate %']:.1f}%)"
)

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
    display_df = risk[["full_name", "group_id", "risk_score", "attendance_rate_pct", "avg_concept_score", "concepts_failed"]].copy()
    display_df["attendance_rate_pct"] = display_df["attendance_rate_pct"].round(0).astype(str) + "%"
    display_df["avg_concept_score"] = display_df["avg_concept_score"].round(1).astype(str) + "%"
    display_df["risk_score"] = display_df["risk_score"].round(1)
    
    st.dataframe(
        display_df.head(50),
        use_container_width=True,
        hide_index=True
    )

st.divider()

# ── Summary ──
st.header("📋 Key Takeaways")
st.markdown("""
| Question | Finding |
|---|---|
| **Q10 — Age Bands** | Best-performing age band: **{best_band}** |
| **Q14 — At-Risk Top 10** | **#{worst_name}** (risk={worst_risk:.1f}): {worst_att}% att, {worst_grade}% grade, {worst_fail} failures |
""".format(best_band=best_age['Age Band'],
           worst_name=top10.iloc[0]['full_name'],
           worst_risk=top10.iloc[0]['risk_score'],
           worst_att=top10.iloc[0]['attendance_rate_pct'],
           worst_grade=top10.iloc[0]['avg_concept_score'],
           worst_fail=int(top10.iloc[0]['concepts_failed'])))

render_save_ui("student_profiling", "Student profiling data",
               dataframe_to_dict(risk.head(10)))
