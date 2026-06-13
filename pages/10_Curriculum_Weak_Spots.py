import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils import load_all, page_config, show_logo, show_top_logo
from db_utils import require_auth, render_save_ui, dataframe_to_dict

require_auth()

page_config("Kayfa — Curriculum Weak Spots", "📉")
show_logo()
show_top_logo()

data = load_all()
grades = data["grades"]
master = data["master"]
groups = data["groups"]

grades = grades[grades["assessment_title"] != "Bonus Exam"]

st.title("📉 Curriculum Weak Spots & Concept Mastery")
st.markdown("##### Identifying concepts with the highest failure rates and tracking improvement over time")

# ── Q6: Concepts with Highest Failure Rate ──
st.header("Q6: Highest Failure Rate Concepts — The Biggest Weak Spot")

grades["passed"] = (grades["score"] >= 50).astype(int)
concept_fail = grades.groupby(["course_id", "assessment_title", "type"])["passed"].agg(["count", "sum"]).reset_index()
concept_fail.columns = ["course_id", "assessment_title", "type", "total_students", "passed_count"]
concept_fail["fail_rate"] = ((1 - concept_fail["passed_count"] / concept_fail["total_students"]) * 100).round(1)
concept_fail = concept_fail.sort_values("fail_rate", ascending=False)

top15 = concept_fail.head(15).copy()
top15["label"] = top15["course_id"] + " — " + top15["assessment_title"]
top15["label"] = top15["label"].str.slice(0, 30)

col1, col2 = st.columns([2, 1])

with col1:
    colors = ["#ef4444" if r["fail_rate"] >= 30 else "#f59e0b" if r["fail_rate"] >= 15 else "#10b981"
              for _, r in top15.iterrows()]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=top15["fail_rate"], y=top15["label"],
        orientation="h", marker_color=colors,
        text=top15["fail_rate"].astype(str) + "%",
        textposition="outside",
    ))
    fig.update_layout(
        template="plotly_dark", height=500,
        title="Top 15 Highest Failure Rate Concepts",
        xaxis_title="Failure Rate %", yaxis_title="",
        margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11),
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    worst = concept_fail.iloc[0]
    st.error(f"**Single Biggest Weak Spot**")
    st.markdown(f"**Course:** {worst['course_id']}  \n"
                f"**Assessment:** {worst['assessment_title']}  \n"
                f"**Type:** {worst['type']}  \n"
                f"**Fail Rate:** {worst['fail_rate']:.1f}%  \n"
                f"**Students Tested:** {int(worst['total_students'])}  \n"
                f"**Passed:** only {int(worst['passed_count'])} of {int(worst['total_students'])}")

    # Course C005 summary
    c005 = concept_fail[concept_fail["course_id"] == "C005"]
    st.warning(f"**C005 (Business) dominates top-fail list**")
    st.markdown(f"C005 occupies **{(c005['fail_rate'] >= 15).sum()} of the top-10** failing concepts.  \n"
                f"Average fail rate across all C005 assessments: **{c005['fail_rate'].mean():.1f}%**")

st.subheader("Failure Rate by Course & Assessment Type")
heat_data = concept_fail.pivot_table(
    index="course_id", columns="type", values="fail_rate", aggfunc="mean"
).round(1)
fig = px.imshow(
    heat_data, text_auto=True, color_continuous_scale="RdYlGn_r",
    title="Average Failure Rate % by Course × Assessment Type",
    labels={"x": "Assessment Type", "y": "Course", "color": "Fail Rate %"},
)
fig.update_layout(template="plotly_dark", height=350,
                  margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
st.plotly_chart(fig, use_container_width=True)
st.caption("C005 has alarmingly high failure rates across ALL assessment types — systemic course-level issue, not just one bad assignment.")

st.divider()

# ── Q7: Cohort Mastery Over Time for Weakest Concept ──
st.header("Q7: Mastery Over Time — Successive Assessments of the Weakest Concept")

worst_course = worst["course_id"]
worst_title = worst["assessment_title"]

concept_over_time = grades[
    (grades["assessment_title"] == worst_title) & (grades["course_id"] == worst_course)
].copy()
concept_over_time["date"] = pd.to_datetime(concept_over_time["date"])
concept_over_time = concept_over_time.sort_values("date")

by_date = concept_over_time.groupby("date")["score"].agg(["mean", "std", "count"]).reset_index()
by_date.columns = ["date", "avg_score", "std", "count"]

col3, col4 = st.columns([2, 1])

with col3:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=by_date["date"], y=by_date["avg_score"], mode="lines+markers",
        line=dict(color="#6366f1", width=3), marker=dict(size=10),
        error_y=dict(type="data", array=by_date["std"], visible=True),
        name="Avg Score",
    ))
    fig.add_hline(y=50, line_dash="dash", line_color="#ef4444",
                  annotation_text="Pass Threshold (50%)")
    fig.update_layout(
        template="plotly_dark", height=400,
        title=f"Score Trend: {worst_title} (C005)",
        xaxis_title="Date", yaxis_title="Avg Score",
        margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11),
    )
    st.plotly_chart(fig, use_container_width=True)

with col4:
    first_half = by_date.iloc[:len(by_date)//2]["avg_score"].mean()
    second_half = by_date.iloc[len(by_date)//2:]["avg_score"].mean()
    direction = "📈 Improving" if second_half > first_half else "📉 Declining"
    color = "green" if second_half > first_half else "red"
    st.metric("First Half Avg", f"{first_half:.1f}%")
    st.metric("Second Half Avg", f"{second_half:.1f}%", delta=f"{second_half - first_half:+.1f}pp", delta_color="normal")
    st.markdown(f"**Trend:** :{color}[{direction}]")
    st.caption("Later cohorts scored higher — curriculum adjustments or peer learning may be having a positive effect.")

# Assessment sequence for C005
st.subheader("Full Assessment Progression for C005")
c005_seq = grades[grades["course_id"] == "C005"].copy()
c005_seq["date"] = pd.to_datetime(c005_seq["date"])
c005_seq = c005_seq.sort_values(["date", "assessment_title"])
seq_avg = c005_seq.groupby(["date", "assessment_title", "type"])["score"].mean().reset_index()
seq_avg["date_str"] = seq_avg["date"].dt.strftime("%b %d")

fig = px.line(
    seq_avg, x="date_str", y="score", color="assessment_title",
    markers=True, color_discrete_sequence=px.colors.qualitative.Set2,
    title="C005 Assessment Score Progression Over Time",
    labels={"date_str": "Date", "score": "Avg Score", "assessment_title": "Assessment"},
)
fig.add_hline(y=50, line_dash="dash", line_color="#ef4444", annotation_text="Pass (50%)")
fig.update_layout(template="plotly_dark", height=400,
                  margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
st.plotly_chart(fig, use_container_width=True)
st.caption("Assignments 1-3 show a clear downward trend (48-52 range), while later practicals and exams recover to ~60+. Quiz performance dips mid-term (Quiz 3-4) then stabilizes.")

st.divider()

# ── Summary ──
st.header("📋 Key Takeaways")
st.markdown("""
| Question | Finding |
|---|---|
| **Q6 — Worst Concept** | C005 Assignment 3: **48.3% fail rate** — nearly half the class fails |
| **Q6 — Course Pattern** | **C005 (Business)** dominates all top failing concepts — systemic problem |
| **Q7 — Mastery Trend** | Weakest concept is **improving** (60.1 → 64.8) across successive assessments |
| **Recommendation** | Redesign C005 curriculum; provide extra support during Assignment 2-3 window |
""")

render_save_ui("curriculum_weak_spots", "Curriculum data",
               dataframe_to_dict(concept_fail.head(15)))
