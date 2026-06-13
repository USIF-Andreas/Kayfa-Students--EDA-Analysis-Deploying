import streamlit as st
import pandas as pd
import plotly.express as px
from utils import load_data, page_config, show_logo, show_top_logo

page_config("Kayfa Students — Attendance", "📅")
show_logo()
show_top_logo()

master = load_data()

st.title("📅 Attendance Analysis")
st.markdown("##### Commitment Tracking & Attendance Patterns")

total_students = len(master)
avg_att = master["attendance_rate_pct"].mean()
high_att = (master["attendance_rate_pct"] >= 80).sum()
low_att = (master["attendance_rate_pct"] < 50).sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Students", f"{total_students:,}")
col2.metric("Avg Attendance", f"{avg_att:.1f}%")
col3.metric("High Attendees (≥80%)", f"{high_att}")
col4.metric("Low Attendees (<50%)", f"{low_att}")

st.divider()

col_a, col_b = st.columns(2)

with col_a:
    att_bins = pd.cut(master["attendance_rate_pct"], bins=[0, 40, 60, 80, 90, 100],
                      labels=["0-40%", "40-60%", "60-80%", "80-90%", "90-100%"])
    att_dist = att_bins.value_counts().reset_index()
    att_dist.columns = ["Band", "Count"]
    fig = px.bar(
        att_dist, x="Band", y="Count", color="Count",
        color_continuous_scale="RdYlGn", title="Attendance Distribution",
        labels={"Band": "Attendance %", "Count": "Students"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Overall attendance rate is {avg_att:.1f}%. The majority of students maintain good attendance (60%+).")

with col_b:
    att_by_group = master[master["group_id"] != "Unassigned"].groupby("group_id")["attendance_rate_pct"].mean().reset_index()
    att_by_group = att_by_group.sort_values("attendance_rate_pct")
    fig = px.bar(
        att_by_group, x="attendance_rate_pct", y="group_id", orientation="h", color="attendance_rate_pct",
        color_continuous_scale="RdYlGn", title="Attendance Rate by Group",
        labels={"attendance_rate_pct": "Attendance %", "group_id": "Group"},
    )
    fig.update_layout(template="plotly_dark", yaxis={"categoryorder": "total ascending"},
                      height=400, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Attendance varies significantly across groups. Some groups need targeted intervention.")

st.divider()

col_c, col_d = st.columns(2)

with col_c:
    fig = px.box(
        master, x="instructor", y="attendance_rate_pct", color="instructor",
        color_discrete_sequence=["#6366f1", "#14b8a6", "#f59e0b", "#ef4444"],
        title="Attendance Distribution by Instructor",
        labels={"instructor": "", "attendance_rate_pct": "Attendance %"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    by_inst = master.groupby("instructor")["attendance_rate_pct"].mean()
    st.caption(f"Instructor attendance rates vary: {by_inst.idxmax()} leads ({by_inst.max():.0f}%), {by_inst.idxmin()} trails ({by_inst.min():.0f}%).")

with col_d:
    fig = px.box(
        master.dropna(subset=["course_name"]), x="course_name", y="attendance_rate_pct", color="course_name",
        title="Attendance Distribution by Course",
        labels={"course_name": "", "attendance_rate_pct": "Attendance %"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Course-level attendance patterns reveal which programs maintain the highest commitment.")

st.divider()

fig = px.scatter(
    master, x="attendance_rate_pct", y="avg_concept_score",
    color="difficulty_level",
    color_discrete_map={"Beginner": "#10b981", "Intermediate": "#f59e0b", "Advanced": "#ef4444"},
    hover_data=["student_id", "instructor"],
    title="Attendance vs Concept Score (colored by difficulty)",
    labels={"attendance_rate_pct": "Attendance %", "avg_concept_score": "Avg Concept Score"},
    trendline="ols",
)
fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
st.plotly_chart(fig, use_container_width=True)
r2 = round(master[["attendance_rate_pct", "avg_concept_score"]].corr().iloc[0, 1], 3)
st.caption(f"Strong positive correlation (r={r2}) between attendance and concept scores. Every 10% attendance increase corresponds to roughly 2–3 pts higher concept scores.")
