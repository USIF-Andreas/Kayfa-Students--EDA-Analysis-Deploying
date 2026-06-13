import streamlit as st
import pandas as pd
import plotly.express as px
from utils import load_data, page_config, show_logo, show_top_logo

page_config("Kayfa Students — Academic Performance", "📚")
show_logo()
show_top_logo()

master = load_data()

st.title("📚 Academic Performance")
st.markdown("##### Grades, Concept Mastery & Assessment Analysis")

avg_grade = master["avg_grade"].mean()
avg_concept = master["avg_concept_score"].mean()
total_courses = master["course_name"].nunique()
pass_rate = (master["passed"] == True).mean() * 100

col1, col2, col3, col4 = st.columns(4)
col1.metric("Overall Avg Grade", f"{avg_grade:.1f}%")
col2.metric("Avg Concept Score", f"{avg_concept:.1f}%")
col3.metric("Courses", total_courses)
col4.metric("Pass Rate", f"{pass_rate:.1f}%")

st.divider()

col_a, col_b = st.columns(2)

with col_a:
    fig = px.histogram(
        master, x="avg_grade", nbins=25, color_discrete_sequence=["#6366f1"],
        title="Average Grade Distribution", labels={"avg_grade": "Avg Grade %"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"The distribution centers around {avg_grade:.1f}%. Most students score between 50–80%, with a tail of low performers needing intervention.")

with col_b:
    fig = px.histogram(
        master, x="avg_concept_score", nbins=25, color_discrete_sequence=["#14b8a6"],
        title="Concept Score Distribution", labels={"avg_concept_score": "Avg Concept Score"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    below60 = (master["avg_concept_score"] < 60).sum()
    st.caption(f"Most students cluster around the mean. {below60} students ({below60/len(master)*100:.0f}%) score below 60% — at-risk candidates for intervention.")

st.divider()

col_c, col_d = st.columns(2)

with col_c:
    course_avg = master.dropna(subset=["course_name"]).groupby("course_name")["avg_concept_score"].agg(["mean", "count"]).reset_index()
    course_avg.columns = ["course", "avg_score", "count"]
    course_avg = course_avg.sort_values("avg_score")
    fig = px.bar(
        course_avg, x="avg_score", y="course", orientation="h", color="avg_score",
        color_continuous_scale="RdYlGn", title="Avg Concept Score by Course",
        labels={"avg_score": "Avg Score %", "course": ""},
    )
    fig.update_layout(template="plotly_dark", yaxis={"categoryorder": "total ascending"},
                      height=400, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Course performance varies. {course_avg.iloc[-1]['course']} leads; {course_avg.iloc[0]['course']} needs attention.")

with col_d:
    diff_avg = master.groupby("difficulty_level")["avg_concept_score"].mean().reset_index()
    fig = px.bar(
        diff_avg, x="difficulty_level", y="avg_concept_score", color="difficulty_level",
        color_discrete_sequence=["#10b981", "#f59e0b", "#ef4444"],
        title="Avg Concept Score by Difficulty Level",
        labels={"difficulty_level": "Level", "avg_concept_score": "Avg Score"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Beginner courses have the highest scores; Advanced the lowest — expected given increasing complexity.")

st.divider()

col_e, col_f = st.columns(2)

with col_e:
    kpi_data = pd.DataFrame({
        "metric": ["Avg Grade", "Avg Concept Score", "Avg Attendance", "Avg Fail Rate"],
        "value": [
            master["avg_grade"].mean(),
            master["avg_concept_score"].mean(),
            master["attendance_rate_pct"].mean(),
            master["concept_fail_pct"].mean(),
        ],
    })
    fig = px.bar(
        kpi_data, x="metric", y="value", color="metric",
        color_discrete_sequence=["#6366f1", "#14b8a6", "#10b981", "#ef4444"],
        title="Key Academic KPIs", labels={"metric": "", "value": "Percentage"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Avg grade ({master['avg_grade'].mean():.1f}%) and concept score ({master['avg_concept_score'].mean():.1f}%) are healthy. Fail rate ({master['concept_fail_pct'].mean():.1f}%) is a key area to reduce.")

with col_f:
    fig = px.scatter(
        master, x="attendance_rate_pct", y="avg_concept_score",
        color="difficulty_level", size="concept_fail_pct",
        hover_data=["student_id", "instructor"],
        color_discrete_map={"Beginner": "#10b981", "Intermediate": "#f59e0b", "Advanced": "#ef4444"},
        title="Attendance vs Concept Score (bubble = fail rate)",
        labels={"attendance_rate_pct": "Attendance %", "avg_concept_score": "Avg Concept Score"},
    )
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Clear positive correlation: higher attendance = higher concept scores. The bubble size (fail rate) shrinks as attendance improves.")
