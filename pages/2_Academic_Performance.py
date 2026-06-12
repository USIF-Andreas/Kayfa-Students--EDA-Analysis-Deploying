import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import load_all, page_config

page_config("Kayfa Students — Academic Performance", "📚")

data = load_all()
grades = data["grades"]
master = data["master"]
groups = data["groups"]

st.title("📚 Academic Performance")
st.markdown("##### Grades, Concept Mastery & Assessment Analysis")

avg_score = grades["score"].mean()
avg_max = grades["max_score"].mean()
total_assessments = grades["assessment_title"].nunique()
total_scores = len(grades)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Overall Avg Score", f"{avg_score:.1f}%")
col2.metric("Avg Max Score", f"{avg_max:.0f}")
col3.metric("Assessment Types", total_assessments)
col4.metric("Total Records", f"{total_scores:,}")

st.divider()

col_a, col_b = st.columns(2)

with col_a:
    fig = px.histogram(
        grades,
        x="score",
        nbins=30,
        color_discrete_sequence=["#6366f1"],
        title="Score Distribution (All Assessments)",
        labels={"score": "Score"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    fig = px.box(
        grades,
        x="type",
        y="score",
        color="type",
        color_discrete_sequence=["#6366f1", "#14b8a6", "#f59e0b", "#ef4444"],
        title="Score Distribution by Assessment Type",
        labels={"type": "Type", "score": "Score"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

grade_by_type = grades.groupby(["type", "assessment_title"])["score"].mean().reset_index()
fig = px.bar(
    grade_by_type,
    x="assessment_title",
    y="score",
    color="type",
    barmode="group",
    color_discrete_sequence=["#6366f1", "#14b8a6", "#f59e0b", "#ef4444"],
    title="Average Score by Assessment",
    labels={"assessment_title": "Assessment", "score": "Avg Score"},
)
fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
st.plotly_chart(fig, use_container_width=True)

st.divider()

col_c, col_d = st.columns(2)

with col_c:
    quiz_data = grades[grades["type"] == "quiz"].copy()
    quiz_data["quiz_num"] = quiz_data["assessment_title"].str.extract(r"(\d+)").astype(int)
    quiz_avg = quiz_data.groupby("quiz_num")["score"].mean().reset_index()
    fig = px.line(
        quiz_avg,
        x="quiz_num",
        y="score",
        markers=True,
        color_discrete_sequence=["#8b5cf6"],
        title="Quiz Score Progression",
        labels={"quiz_num": "Quiz #", "score": "Avg Score"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

with col_d:
    student_avg = grades.groupby("student_id")["score"].mean().reset_index()
    student_avg.columns = ["student_id", "avg_score"]
    fig = px.histogram(
        student_avg,
        x="avg_score",
        nbins=25,
        color_discrete_sequence=["#10b981"],
        title="Distribution of Student Averages",
        labels={"avg_score": "Average Score"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

col_e, col_f = st.columns(2)

with col_e:
    concept_dist = pd.DataFrame({
        "metric": ["Avg Concept Score", "Avg Fail Rate", "Avg Attendance"],
        "value": [
            master["avg_concept_score"].mean(),
            master["concept_fail_rate_pct"].mean(),
            master["attendance_rate_pct"].mean(),
        ],
    })
    fig = px.bar(
        concept_dist,
        x="metric",
        y="value",
        color="metric",
        color_discrete_sequence=["#6366f1", "#ef4444", "#10b981"],
        title="Key Academic KPIs",
        labels={"metric": "", "value": "Percentage"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

with col_f:
    fig = px.scatter(
        master,
        x="attendance_rate_pct",
        y="avg_concept_score",
        color="difficulty_level",
        size="concept_fail_rate_pct",
        hover_data=["student_id", "instructor"],
        color_discrete_map={"Beginner": "#10b981", "Intermediate": "#f59e0b", "Advanced": "#ef4444"},
        title="Attendance vs Concept Score (bubble = fail rate)",
        labels={"attendance_rate_pct": "Attendance %", "avg_concept_score": "Avg Concept Score"},
    )
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
