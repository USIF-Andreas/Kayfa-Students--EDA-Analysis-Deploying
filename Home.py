import streamlit as st
import plotly.express as px
from utils import load_data, page_config, show_logo, show_top_logo

page_config("Kayfa Students — Executive Dashboard", "📊")
show_logo()
show_top_logo()

master = load_data()

st.title("📊 Kayfa Student Analytics")
st.markdown("##### Executive Dashboard — High-Level Overview of Student Performance & Engagement")

total_students = len(master)
avg_attendance = master["attendance_rate_pct"].mean()
avg_concept_score = master["avg_concept_score"].mean()
avg_fail_rate = master["concept_fail_pct"].mean()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Students", f"{total_students}")
col2.metric("Avg Attendance", f"{avg_attendance:.1f}%")
col3.metric("Avg Concept Score", f"{avg_concept_score:.1f}%")
col4.metric("Avg Fail Rate", f"{avg_fail_rate:.1f}%")

st.divider()

col_left, col_right = st.columns(2)

with col_left:
    category_avg = master.groupby("category")["avg_concept_score"].agg(["mean", "count"]).reset_index()
    category_avg.columns = ["category", "avg_score", "count"]
    category_avg["label"] = category_avg["category"] + " (n=" + category_avg["count"].astype(str) + ")"
    fig = px.bar(
        category_avg,
        x="avg_score",
        y="label",
        orientation="h",
        color="avg_score",
        color_continuous_scale="Blues",
        title="Average Concept Score by Category",
    )
    fig.update_layout(template="plotly_dark", yaxis={"categoryorder": "total ascending"},
                      height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    diff_avg = master.groupby("difficulty_level")["avg_concept_score"].agg(["mean", "count"]).reset_index()
    diff_avg.columns = ["difficulty", "avg_score", "count"]
    diff_avg["label"] = diff_avg["difficulty"] + " (n=" + diff_avg["count"].astype(str) + ")"
    fig = px.bar(
        diff_avg,
        x="difficulty",
        y="avg_score",
        color="difficulty",
        color_discrete_sequence=["#10b981", "#f59e0b", "#ef4444"],
        title="Average Score by Difficulty Level",
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

col3, col4 = st.columns(2)

with col3:
    instructor_avg = master.groupby("instructor")["avg_concept_score"].mean().reset_index()
    instructor_avg = instructor_avg.sort_values("avg_concept_score")
    fig = px.bar(
        instructor_avg,
        x="avg_concept_score",
        y="instructor",
        orientation="h",
        color="avg_concept_score",
        color_continuous_scale="Greens",
        title="Average Concept Score by Instructor",
    )
    fig.update_layout(template="plotly_dark", yaxis={"categoryorder": "total ascending"},
                      height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

with col4:
    instructor_att = master.groupby("instructor")["attendance_rate_pct"].mean().reset_index()
    instructor_att = instructor_att.sort_values("attendance_rate_pct")
    fig = px.bar(
        instructor_att,
        x="attendance_rate_pct",
        y="instructor",
        orientation="h",
        color="attendance_rate_pct",
        color_continuous_scale="RdYlGn",
        title="Average Attendance Rate by Instructor",
    )
    fig.update_layout(template="plotly_dark", yaxis={"categoryorder": "total ascending"},
                      height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

col5, col6 = st.columns(2)

with col5:
    passed_counts = master["passed"].value_counts().reset_index()
    passed_counts.columns = ["passed", "count"]
    passed_counts["label"] = passed_counts["passed"].map({True: "Passed", False: "Failed"})
    fig = px.pie(
        passed_counts,
        values="count",
        names="label",
        color="label",
        color_discrete_map={"Passed": "#10b981", "Failed": "#ef4444"},
        hole=0.4,
        title="Overall Pass/Fail Rate",
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

with col6:
    fig = px.histogram(
        master, x="avg_grade", nbins=25, color_discrete_sequence=["#6366f1"],
        title="Average Grade Distribution",
        labels={"avg_grade": "Average Grade %"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

col7, col8 = st.columns(2)

with col7:
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

with col8:
    fig = px.scatter(
        master, x="avg_time_spent", y="avg_concept_score",
        color="category", size="total_submissions",
        hover_data=["student_id", "course_name"],
        title="Time Spent vs Concept Score (bubble = submissions)",
        labels={"avg_time_spent": "Avg Time Spent (min)", "avg_concept_score": "Avg Concept Score"},
    )
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

st.header("🧠 Deep Analysis Pages")
st.markdown("""
| Page | Questions Covered |
|---|---|
| 🔍 Group Integrity | Q12 — True vs stated group sizes · Q13 — Unviable group merger recommendation |
| 📈 Engagement Trends | Q1 — Attendance rate by group · Q5 — Engagement vs performance · Q9 — Cohort dip detection |
| 🎯 Performance Deep Dive | Q2 — Score volatility by type · Q3 — Course comparison · Q4 — Attendance vs grade · Q8 — Late submissions vs scores |
| 📉 Curriculum Weak Spots | Q6 — Highest failure concepts · Q7 — Weakest concept mastery over time |
| ⚠️ Student Risk & Segmentation | Q10 — Age bands vs outcomes · Q11 — K-Means segmentation · Q14 — At-risk ranking |
| 📊 Group Performance Trends | Q15 — Group grade trajectories |
""")
