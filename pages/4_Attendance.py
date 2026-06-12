import streamlit as st
import pandas as pd
import plotly.express as px
from utils import load_all, page_config

page_config("Kayfa Students — Attendance", "📅")

data = load_all()
attendance = data["attendance"]
master = data["master"]
groups = data["groups"]
students = data["students"]

attendance["session_datetime"] = pd.to_datetime(attendance["session_datetime"])

st.title("📅 Attendance Analysis")
st.markdown("##### Commitment Tracking & Drop-Off Patterns")

total_records = len(attendance)
attended = (attendance["status"] == "attended").sum()
absent = (attendance["status"] == "absent").sum()
att_rate = attended / total_records * 100

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Records", f"{total_records:,}")
col2.metric("Attended", f"{attended:,}")
col3.metric("Absent", f"{absent:,}")
col4.metric("Attendance Rate", f"{att_rate:.1f}%")

st.divider()

col_a, col_b = st.columns(2)

with col_a:
    status_counts = attendance["status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]
    fig = px.pie(
        status_counts,
        values="count",
        names="status",
        color="status",
        color_discrete_map={"attended": "#10b981", "absent": "#ef4444"},
        hole=0.5,
        title="Attendance vs Absence",
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    attendance_merged = attendance.merge(groups[["group_id", "group_name"]], on="group_id", how="left")
    att_by_group = (
        attendance_merged.groupby("group_name")["status"]
        .apply(lambda x: (x == "attended").mean() * 100)
        .reset_index(name="att_rate")
        .sort_values("att_rate")
    )
    fig = px.bar(
        att_by_group,
        x="att_rate",
        y="group_name",
        orientation="h",
        color="att_rate",
        color_continuous_scale="RdYlGn",
        title="Attendance Rate by Group",
        labels={"att_rate": "Attendance %", "group_name": ""},
    )
    fig.update_layout(template="plotly_dark", yaxis={"categoryorder": "total ascending"},
                      height=400, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

attendance["date"] = attendance["session_datetime"].dt.date
att_over_time = attendance.groupby("date")["status"].apply(lambda x: (x == "attended").mean() * 100).reset_index(name="att_rate")
fig = px.line(
    att_over_time,
    x="date",
    y="att_rate",
    markers=True,
    title="Attendance Rate Over Time",
    labels={"date": "Session Date", "att_rate": "Attendance %"},
)
fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
st.plotly_chart(fig, use_container_width=True)

st.divider()

col_c, col_d = st.columns(2)

with col_c:
    attendance["weekday"] = attendance["session_datetime"].dt.day_name()
    att_by_day = (
        attendance.groupby("weekday")["status"]
        .apply(lambda x: (x == "attended").mean() * 100)
        .reset_index(name="att_rate")
    )
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    att_by_day["weekday"] = pd.Categorical(att_by_day["weekday"], categories=day_order, ordered=True)
    att_by_day = att_by_day.sort_values("weekday")
    fig = px.bar(
        att_by_day,
        x="weekday",
        y="att_rate",
        color="att_rate",
        color_continuous_scale="RdYlGn",
        title="Attendance Rate by Day of Week",
        labels={"weekday": "", "att_rate": "Attendance %"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

with col_d:
    fig = px.box(
        master,
        x="instructor",
        y="attendance_rate_pct",
        color="instructor",
        color_discrete_sequence=["#6366f1", "#14b8a6", "#f59e0b", "#ef4444"],
        title="Attendance Distribution by Instructor",
        labels={"instructor": "", "attendance_rate_pct": "Attendance %"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

fig = px.scatter(
    master,
    x="attendance_rate_pct",
    y="avg_concept_score",
    color="difficulty_level",
    color_discrete_map={"Beginner": "#10b981", "Intermediate": "#f59e0b", "Advanced": "#ef4444"},
    hover_data=["student_id", "instructor"],
    title="Attendance vs Concept Score (colored by difficulty)",
    labels={"attendance_rate_pct": "Attendance %", "avg_concept_score": "Avg Concept Score"},
    trendline="ols",
)
fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
st.plotly_chart(fig, use_container_width=True)
