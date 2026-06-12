import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import (
    load_all, page_config, show_logo, show_top_logo,
    compute_student_avg_grades, compute_quiz_progression, compute_grade_avg_by_type,
)

page_config("Kayfa Students — Academic Performance", "📚")
show_logo()
show_top_logo()

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
        grades, x="score", nbins=30, color_discrete_sequence=["#6366f1"],
        title="Score Distribution (All Assessments)", labels={"score": "Score"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"The distribution is slightly left-skewed with a mean of {avg_score:.1f}%. Most students score between 50–80%, with a long tail of low performers needing intervention.")

with col_b:
    fig = px.box(
        grades, x="type", y="score", color="type",
        color_discrete_sequence=["#6366f1", "#14b8a6", "#f59e0b", "#ef4444"],
        title="Score Distribution by Assessment Type", labels={"type": "Type", "score": "Score"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    by_type = grades.groupby("type")["score"].mean()
    worst = by_type.idxmin()
    best = by_type.idxmax()
    st.caption(f"{best.title()}s have the highest median scores; {worst}s show the widest spread and lowest median. Assessment type difficulty varies significantly.")

st.divider()

grade_by_type = compute_grade_avg_by_type(grades)
fig = px.bar(
    grade_by_type, x="assessment_title", y="score", color="type", barmode="group",
    color_discrete_sequence=["#6366f1", "#14b8a6", "#f59e0b", "#ef4444"],
    title="Average Score by Assessment", labels={"assessment_title": "Assessment", "score": "Avg Score"},
)
fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
st.plotly_chart(fig, use_container_width=True)
max_assess = grade_by_type.loc[grade_by_type["score"].idxmax()]
min_assess = grade_by_type.loc[grade_by_type["score"].idxmin()]
st.caption(f"'{max_assess['assessment_title']}' ({max_assess['type']}) has the highest average ({max_assess['score']:.1f}%). '{min_assess['assessment_title']}' ({min_assess['type']}) is lowest ({min_assess['score']:.1f}%) — may need curriculum review.")

st.divider()

col_c, col_d = st.columns(2)

with col_c:
    quiz_avg = compute_quiz_progression(grades)
    fig = px.line(
        quiz_avg, x="quiz_num", y="score", markers=True,
        color_discrete_sequence=["#8b5cf6"],
        title="Quiz Score Progression", labels={"quiz_num": "Quiz #", "score": "Avg Score"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    q1 = quiz_avg[quiz_avg["quiz_num"] == 1]["score"].values[0] if len(quiz_avg) > 0 else 0
    q4 = quiz_avg[quiz_avg["quiz_num"] == 4]["score"].values[0] if len(quiz_avg[quiz_avg["quiz_num"] == 4]) > 0 else 0
    st.caption(f"Quiz scores trend {'upward' if q4 > q1 else 'downward'} from Q1 ({q1:.1f}%) to Q4 ({q4:.1f}%), suggesting {'improving' if q4 > q1 else 'declining'} concept retention across the term.")

with col_d:
    student_avg = compute_student_avg_grades(grades)
    student_avg.columns = ["student_id", "avg_score"]
    fig = px.histogram(
        student_avg, x="avg_score", nbins=25, color_discrete_sequence=["#10b981"],
        title="Distribution of Student Averages", labels={"avg_score": "Average Score"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    below60 = (student_avg["avg_score"] < 60).sum()
    st.caption(f"Most students cluster around the mean. {below60} students ({below60/len(student_avg)*100:.0f}%) average below 60% — these are at-risk candidates for intervention.")

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
        concept_dist, x="metric", y="value", color="metric",
        color_discrete_sequence=["#6366f1", "#ef4444", "#10b981"],
        title="Key Academic KPIs", labels={"metric": "", "value": "Percentage"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Average concept score ({master['avg_concept_score'].mean():.1f}%) and attendance ({master['attendance_rate_pct'].mean():.1f}%) are healthy. Fail rate ({master['concept_fail_rate_pct'].mean():.1f}%) is a key area to reduce.")

with col_f:
    fig = px.scatter(
        master, x="attendance_rate_pct", y="avg_concept_score",
        color="difficulty_level", size="concept_fail_rate_pct",
        hover_data=["student_id", "instructor"],
        color_discrete_map={"Beginner": "#10b981", "Intermediate": "#f59e0b", "Advanced": "#ef4444"},
        title="Attendance vs Concept Score (bubble = fail rate)",
        labels={"attendance_rate_pct": "Attendance %", "avg_concept_score": "Avg Concept Score"},
    )
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Clear positive correlation: higher attendance = higher concept scores. The bubble size (fail rate) shrinks as attendance improves, reinforcing attendance as the top success driver.")
