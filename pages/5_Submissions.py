import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import load_all, page_config, show_logo, show_top_logo, compute_late_by_student

page_config("Kayfa Students — Submissions", "📝")
show_logo()
show_top_logo()

data = load_all()
submissions = data["submissions"]
master = data["master"]
groups = data["groups"]

submissions["deadline"] = pd.to_datetime(submissions["deadline"])
submissions["submitted_at"] = pd.to_datetime(submissions["submitted_at"])

st.title("📝 Submissions & Procrastination Analysis")
st.markdown("##### Effort Tracking, Late Behavior & Time Management")

total_sub = len(submissions)
late_count = submissions["is_late"].sum()
late_pct = late_count / total_sub * 100
avg_time = submissions["time_spent_minutes"].mean()
avg_attempts = submissions["attempts"].mean()
avg_hours = submissions["hours_until_deadline"].dropna().mean()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Submissions", f"{total_sub:,}")
col2.metric("Late Submissions", f"{late_count:,}")
col3.metric("Late %", f"{late_pct:.1f}%")
col4.metric("Avg Time Spent", f"{avg_time:.0f} min")
col5.metric("Avg Hours Before", f"{avg_hours:.1f}h")

st.divider()

col_a, col_b = st.columns(2)

with col_a:
    late_counts = submissions["is_late"].value_counts().reset_index()
    late_counts.columns = ["is_late", "count"]
    late_counts["label"] = late_counts["is_late"].map({True: "Late", False: "On Time"})
    fig = px.pie(
        late_counts, values="count", names="label", color="label",
        color_discrete_map={"Late": "#ef4444", "On Time": "#10b981"}, hole=0.5,
        title="Late vs On-Time Submissions",
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"{late_pct:.1f}% of submissions are late — nearly 1 in {round(100/late_pct) if late_pct > 0 else 100}. This is a significant procrastination signal worth addressing through deadline nudges.")

with col_b:
    valid_time = submissions[
        (submissions["time_spent_minutes"] > 0) & (submissions["time_spent_minutes"] < 300)
    ]
    fig = px.histogram(
        valid_time, x="time_spent_minutes", nbins=35, color_discrete_sequence=["#14b8a6"],
        title="Time Spent on Assignments", labels={"time_spent_minutes": "Minutes"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    med_time = valid_time["time_spent_minutes"].median()
    st.caption(f"Median time spent is {med_time:.0f} minutes. The distribution is right-skewed — most students spend under 2 hours, with a tail of very thorough submissions.")

st.divider()

col_c, col_d = st.columns(2)

with col_c:
    att_counts = submissions["attempts"].value_counts().sort_index().reset_index()
    att_counts.columns = ["attempts", "count"]
    fig = px.bar(
        att_counts, x="attempts", y="count", color="attempts",
        color_discrete_sequence=["#10b981", "#f59e0b", "#ef4444", "#8b5cf6"],
        title="Number of Attempts per Submission",
        labels={"attempts": "Attempts", "count": "Submissions"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    one_att = att_counts[att_counts["attempts"] == 1]["count"].values[0]
    st.caption(f"{one_att:,} submissions ({one_att/len(submissions)*100:.0f}%) are first-attempt. Multiple attempts (>2) may indicate struggling with the material or perfectionism.")

with col_d:
    fig = px.histogram(
        submissions, x="hours_until_deadline", nbins=30, color_discrete_sequence=["#8b5cf6"],
        title="Hours Until Deadline Distribution",
        labels={"hours_until_deadline": "Hours Before Deadline"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    last_min = (submissions["hours_until_deadline"] < 2).sum()
    st.caption(f"Many submissions cluster near the deadline — {last_min} ({last_min/len(submissions)*100:.0f}%) submitted within 2 hours. This last-minute pattern is a classic procrastination indicator.")

st.divider()

late_by_student = compute_late_by_student(submissions)
fig = px.histogram(
    late_by_student, x="late_pct", nbins=25, color_discrete_sequence=["#ef4444"],
    title="Late Submission Rate per Student",
    labels={"late_pct": "Late %"},
)
fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
st.plotly_chart(fig, use_container_width=True)
chronic = (late_by_student["late_pct"] >= 50).sum()
st.caption(f"{chronic} students ({chronic/len(late_by_student)*100:.0f}%) are late ≥50% of the time. These chronic procrastinators should be flagged for early academic intervention.")

st.divider()

sub_with_master = submissions.merge(
    master[["student_id", "avg_concept_score", "attendance_rate_pct"]], on="student_id", how="left"
)

col_e, col_f = st.columns(2)

with col_e:
    late_by_concept = sub_with_master.groupby("student_id").agg(
        late_pct=("is_late", "mean"),
        avg_concept_score=("avg_concept_score", "first"),
    ).reset_index()
    late_by_concept["late_pct"] *= 100
    fig = px.scatter(
        late_by_concept, x="late_pct", y="avg_concept_score",
        trendline="ols", color_discrete_sequence=["#ef4444"], opacity=0.5,
        title="Late Rate vs Concept Score",
        labels={"late_pct": "Late Submission %", "avg_concept_score": "Avg Concept Score"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Clear downward trend: the more a student procrastinates, the lower their concept scores. Late submission rate is a reliable early-warning signal for academic risk.")

with col_f:
    time_vs_score = sub_with_master.groupby("student_id").agg(
        avg_time=("time_spent_minutes", "mean"),
        avg_concept_score=("avg_concept_score", "first"),
    ).reset_index()
    fig = px.scatter(
        time_vs_score, x="avg_time", y="avg_concept_score",
        trendline="ols", color_discrete_sequence=["#6366f1"], opacity=0.5,
        title="Avg Time Spent vs Concept Score",
        labels={"avg_time": "Avg Time Spent (min)", "avg_concept_score": "Avg Concept Score"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Diminishing returns on time spent — very high time investment doesn't guarantee proportionally higher scores. Quality of study time matters more than quantity.")
