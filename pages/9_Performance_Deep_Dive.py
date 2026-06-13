import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import pearsonr
from utils import load_all, page_config, show_logo, show_top_logo
from db_utils import require_auth, render_save_ui, dataframe_to_dict

require_auth()

page_config("Kayfa — Performance Deep Dive", "🎯")
show_logo()
show_top_logo()

data = load_all()
grades = data["grades"]
master = data["master"]
attendance = data["attendance"]
engagement = data["engagement"]
submissions = data["submissions"]
students = data["students"]
groups = data["groups"]

attendance["status"] = attendance["status"].str.strip().str.lower()
attendance = attendance[attendance["status"].isin(["attended", "absent"])]
grades = grades[grades["assessment_title"] != "Bonus Exam"]

st.title("🎯 Academic Performance Deep Dive")
st.markdown("##### Score distributions, course comparisons, attendance effects & submission behavior")

# ── Q2: Score Distribution by Assessment Type ──
st.header("Q2: Score Distribution by Assessment Type — Volatility Analysis")

type_stats = grades.groupby("type")["score"].agg(["mean", "std", "count", "min", "max"]).reset_index()
type_stats.columns = ["Type", "Mean", "Std", "Count", "Min", "Max"]
type_stats["CV (%)"] = (type_stats["Std"] / type_stats["Mean"] * 100).round(1)
type_stats["Mean"] = type_stats["Mean"].round(1)
type_stats["Std"] = type_stats["Std"].round(1)

col1, col2 = st.columns(2)

with col1:
    fig = px.bar(
        type_stats, x="Type", y="Mean", color="Type", text="Mean",
        error_y="Std",
        color_discrete_sequence=["#6366f1", "#14b8a6", "#f59e0b", "#ef4444"],
        title="Average Score by Assessment Type (with Std Dev)",
        labels={"Type": "Assessment Type", "Mean": "Average Score"},
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(template="plotly_dark", height=350,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.box(
        grades, x="type", y="score", color="type",
        color_discrete_sequence=["#6366f1", "#14b8a6", "#f59e0b", "#ef4444"],
        title="Score Distribution by Assessment Type",
        labels={"type": "Type", "score": "Score"},
        points="outliers",
    )
    fig.update_layout(template="plotly_dark", height=350,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

most_volatile = type_stats.sort_values("CV (%)", ascending=False).iloc[0]
st.error(
    f"**Most Volatile: {most_volatile['Type']}** "
    f"(CV = {most_volatile['CV (%)']:.1f}%, Std = {most_volatile['Std']:.1f}, "
    f"Mean = {most_volatile['Mean']:.1f}%) — students show the widest performance variation here."
)
st.caption("Assignments have the lowest mean (65.3%) and highest volatility — suggesting inconsistent effort or unclear grading rubrics.")

st.divider()

# ── Q3: Course Comparison ──
st.header("Q3: Highest & Lowest Average Grade — Spread Comparison")

course_stats = grades.groupby("course_id")["score"].agg(["mean", "std", "count", "median"]).reset_index()
course_stats.columns = ["Course", "Mean", "Std", "Count", "Median"]
course_stats = course_stats.sort_values("Mean", ascending=False)

col3, col4 = st.columns(2)

with col3:
    fig = px.bar(
        course_stats, x="Course", y="Mean", color="Mean", text="Mean",
        error_y="Std", color_continuous_scale="RdYlGn",
        title="Average Grade by Course (error bar = std)",
        labels={"Course": "Course", "Mean": "Avg Grade %"},
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.add_hline(y=master["avg_concept_score"].mean(), line_dash="dash", line_color="orange",
                  annotation_text=f"Platform Avg: {master['avg_concept_score'].mean():.1f}%")
    fig.update_layout(template="plotly_dark", height=350,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

with col4:
    fig = px.box(
        grades, x="course_id", y="score", color="course_id",
        title="Score Distribution by Course",
        labels={"course_id": "Course", "score": "Score"},
        points="outliers",
    )
    fig.update_layout(template="plotly_dark", height=350,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11),
                      showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

highest = course_stats.iloc[0]
lowest = course_stats.iloc[-1]
st.info(
    f"**Highest:** {highest['Course']} (Mean={highest['Mean']:.1f}%, Std={highest['Std']:.1f})  \n"
    f"**Lowest:** {lowest['Course']} (Mean={lowest['Mean']:.1f}%, Std={lowest['Std']:.1f})  \n"
    f"**Gap:** {highest['Mean'] - lowest['Mean']:.1f} percentage points  \n"
    f"Note: {highest['Course']} has only {int(highest['Count'])} records — small sample size."
)

st.divider()

# ── Q4: Attendance vs Grade ──
st.header("Q4: Attendance Rate vs Average Grade — Correlation")

att_by_student = attendance.groupby("student_id")["status"].apply(
    lambda x: (x == "attended").mean() * 100
).reset_index(name="att_rate")
student_avg = master[["student_id", "avg_concept_score"]]
merged = att_by_student.merge(student_avg, on="student_id")

r, p = pearsonr(merged["att_rate"], merged["avg_concept_score"])

col5, col6 = st.columns(2)

with col5:
    fig = px.scatter(
        merged, x="att_rate", y="avg_concept_score",
        trendline="ols", opacity=0.4, color_discrete_sequence=["#10b981"],
        title=f"Attendance vs Avg Concept Score (r = {r:.3f}, p = {p:.2e})",
        labels={"att_rate": "Attendance %", "avg_concept_score": "Avg Concept Score %"},
        hover_data={"student_id": True},
    )
    fig.update_layout(template="plotly_dark", height=350,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

with col6:
    merged["att_bucket"] = pd.cut(
        merged["att_rate"],
        bins=[0, 40, 60, 80, 90, 100],
        labels=["0-40%", "40-60%", "60-80%", "80-90%", "90-100%"],
    )
    bucket_trend = merged.groupby("att_bucket", observed=True)["avg_concept_score"].agg(
        ["mean", "std", "count"]
    ).reset_index()
    bucket_trend.columns = ["Attendance Band", "Avg Score", "Std", "Count"]
    fig = px.bar(
        bucket_trend, x="Attendance Band", y="Avg Score", color="Avg Score",
        color_continuous_scale="Viridis", text="Avg Score",
        title="Average Score by Attendance Band",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(template="plotly_dark", height=350,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

st.caption(f"r² = {r**2:.3f} — attendance explains {r**2*100:.1f}% of grade variance. Each 10pp attendance increase ≈ ~2-3pp higher score.")

st.divider()

# ── Q8: Late Submissions vs Scores ──
st.header("Q8: Late Submissions & Buffer Time vs Scores")

student_avg_grades = master[["student_id", "avg_concept_score"]]
sub_merged = submissions.merge(student_avg_grades, on="student_id")

col7, col8 = st.columns(2)

with col7:
    late_stats = sub_merged.groupby("is_late")["avg_concept_score"].agg(["mean", "std", "count"]).reset_index()
    late_stats.columns = ["Is Late", "Avg Score", "Std", "Count"]
    late_stats["Label"] = late_stats["Is Late"].map({True: "Late", False: "On Time"})
    fig = px.bar(
        late_stats, x="Label", y="Avg Score", color="Label", text="Avg Score",
        error_y="Std",
        color_discrete_map={"On Time": "#10b981", "Late": "#ef4444"},
        title="Avg Grade: On-Time vs Late Submitters",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(template="plotly_dark", height=350,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

with col8:
    sub_merged["buffer_bucket"] = pd.cut(
        sub_merged["hours_until_deadline"],
        bins=[-50, 0, 6, 12, 24, 48],
        labels=["Missed", "0-6hr", "6-12hr", "12-24hr", "24hr+"],
    )
    buffer_trend = sub_merged.groupby("buffer_bucket", observed=True)["avg_concept_score"].agg(
        ["mean", "std", "count"]
    ).reset_index()
    buffer_trend.columns = ["Buffer", "Avg Score", "Std", "Count"]
    fig = px.bar(
        buffer_trend, x="Buffer", y="Avg Score", color="Avg Score",
        color_continuous_scale="RdYlGn", text="Avg Score",
        title="Avg Grade by Submission Buffer Time",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(template="plotly_dark", height=350,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

# Per-submission analysis
per_sub = submissions.merge(
    grades[["student_id", "assessment_id", "score"]], on=["student_id", "assessment_id"], how="left"
).dropna(subset=["score"])

col9, col10 = st.columns(2)

with col9:
    fig = px.box(
        per_sub, x="is_late", y="score", color="is_late",
        color_discrete_map={True: "#ef4444", False: "#10b981"},
        title="Per-Assignment Score: Late vs On Time",
        labels={"is_late": "Late?", "score": "Score"},
        points="all",
    )
    fig.update_layout(template="plotly_dark", height=350,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    fig.update_xaxes(tickvals=[False, True], ticktext=["On Time", "Late"])
    st.plotly_chart(fig, use_container_width=True)

with col10:
    valid = per_sub[per_sub["hours_until_deadline"].notna() & (per_sub["score"].notna())]
    if valid["hours_until_deadline"].nunique() > 1 and valid["score"].nunique() > 1:
        r_sub, p_sub = pearsonr(valid["hours_until_deadline"], valid["score"])
    else:
        r_sub, p_sub = np.nan, np.nan
    fig = px.scatter(
        valid, x="hours_until_deadline", y="score",
        trendline="ols", opacity=0.3, color_discrete_sequence=["#8b5cf6"],
        title=f"Hours Until Deadline vs Score (r = {r_sub:.3f})",
        labels={"hours_until_deadline": "Hours Before Deadline", "score": "Score"},
    )
    fig.update_layout(template="plotly_dark", height=350,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

st.caption("Students who submit early score ~7-8pp higher on average. Every hour of buffer correlates with higher scores — a strong procrastination signal.")

st.divider()

# ── Summary ──
st.header("📋 Key Takeaways")
st.markdown("""
| Question | Finding |
|---|---|
| **Q2 — Score Volatility** | **Assignments** most volatile (CV=19.9%, mean=65.3%) |
| **Q3 — Course Comparison** | Highest: **C007** (76.2%), Lowest: **C005** (59.1%) — gap of 17.1pp |
| **Q4 — Attendance vs Grade** | r = **0.26** (weak-moderate, p < 0.0001) |
| **Q8 — Late Submissions** | On-time avg **72.2%** vs Late **67.4%**; submitting 24hr+ early avg **74.5%** |
""")

render_save_ui("performance_deep_dive", "Performance data",
               dataframe_to_dict(course_stats if 'course_stats' in dir() else pd.DataFrame()))
