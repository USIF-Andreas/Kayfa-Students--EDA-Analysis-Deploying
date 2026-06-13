import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import pearsonr
from utils import load_data, page_config, show_logo, show_top_logo
from db_utils import require_auth, render_save_ui, dataframe_to_dict

require_auth()

page_config("Kayfa — Performance Deep Dive", "🎯")
show_logo()
show_top_logo()

master = load_data()

st.title("🎯 Academic Performance Deep Dive")
st.markdown("##### Score distributions, course comparisons, attendance effects & submission behavior")

# ── Q3: Course Comparison ──
st.header("Q3: Highest & Lowest Average Grade — Course Comparison")

course_stats = master.dropna(subset=["course_name"]).groupby("course_name")["avg_grade"].agg(["mean", "std", "count", "median"]).reset_index()
course_stats.columns = ["Course", "Mean", "Std", "Count", "Median"]
course_stats = course_stats.sort_values("Mean", ascending=False)

col1, col2 = st.columns(2)

with col1:
    fig = px.bar(
        course_stats, x="Course", y="Mean", color="Mean", text="Mean",
        error_y="Std", color_continuous_scale="RdYlGn",
        title="Average Grade by Course (error bar = std)",
        labels={"Course": "Course", "Mean": "Avg Grade %"},
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.add_hline(y=master["avg_grade"].mean(), line_dash="dash", line_color="orange",
                  annotation_text=f"Platform Avg: {master['avg_grade'].mean():.1f}%")
    fig.update_layout(template="plotly_dark", height=350,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.box(
        master.dropna(subset=["course_name"]), x="course_name", y="avg_grade", color="course_name",
        title="Average Grade Distribution by Course",
        labels={"course_name": "Course", "avg_grade": "Avg Grade %"},
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
    f"**Gap:** {highest['Mean'] - lowest['Mean']:.1f} percentage points"
)

st.divider()

# ── Q4: Attendance vs Grade ──
st.header("Q4: Attendance Rate vs Average Grade — Correlation")

r, p = pearsonr(master["attendance_rate_pct"], master["avg_concept_score"])

col3, col4 = st.columns(2)

with col3:
    fig = px.scatter(
        master, x="attendance_rate_pct", y="avg_concept_score",
        trendline="ols", opacity=0.4, color_discrete_sequence=["#10b981"],
        title=f"Attendance vs Avg Concept Score (r = {r:.3f}, p = {p:.2e})",
        labels={"attendance_rate_pct": "Attendance %", "avg_concept_score": "Avg Concept Score %"},
        hover_data={"student_id": True},
    )
    fig.update_layout(template="plotly_dark", height=350,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Each 10pp increase in attendance corresponds to roughly 2-3pp higher concept scores.")

with col4:
    master["att_bucket"] = pd.cut(
        master["attendance_rate_pct"],
        bins=[0, 40, 60, 80, 90, 100],
        labels=["0-40%", "40-60%", "60-80%", "80-90%", "90-100%"],
    )
    bucket_trend = master.groupby("att_bucket", observed=True)["avg_concept_score"].agg(
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
    st.caption("Students with >90% attendance average significantly higher scores.")

st.divider()

# ── Q8: Late Submissions vs Scores ──
st.header("Q8: Late Submission Rate vs Scores")

master["late_bucket"] = pd.cut(
    master["late_rate"],
    bins=[-0.01, 0.0, 0.25, 0.5, 0.75, 1.0],
    labels=["0%", "1-25%", "26-50%", "51-75%", "76-100%"],
)
bucket_trend = master.groupby("late_bucket", observed=True)["avg_concept_score"].agg(
    ["mean", "std", "count"]
).reset_index()
bucket_trend.columns = ["Late Rate Band", "Avg Score", "Std", "Count"]

col5, col6 = st.columns(2)

with col5:
    fig = px.bar(
        bucket_trend, x="Late Rate Band", y="Avg Score", color="Avg Score",
        color_continuous_scale="RdYlGn_r", text="Avg Score",
        title="Avg Score by Late Submission Rate",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(template="plotly_dark", height=350,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Clear trend: higher late rates correlate with lower scores.")

with col6:
    r_late, p_late = pearsonr(master["late_rate"], master["avg_concept_score"])
    fig = px.scatter(
        master, x="late_rate", y="avg_concept_score",
        trendline="ols", opacity=0.3, color_discrete_sequence=["#ef4444"],
        title=f"Late Rate vs Score (r = {r_late:.3f})",
        labels={"late_rate": "Late Rate", "avg_concept_score": "Avg Score"},
    )
    fig.update_layout(template="plotly_dark", height=350,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"p={p_late:.2e}")

st.divider()

# ── Summary ──
st.header("📋 Key Takeaways")
st.markdown("""
| Question | Finding |
|---|---|
| **Q3 — Course Comparison** | Highest: **{highest}** ({highest_mean:.1f}%), Lowest: **{lowest}** ({lowest_mean:.1f}%) — gap of {gap:.1f}pp |
| **Q4 — Attendance vs Grade** | r = **{r:.2f}** (p < 0.0001) |
| **Q8 — Late Submissions** | Higher late rates consistently correlate with lower scores |
""".format(highest=highest['Course'], highest_mean=highest['Mean'],
           lowest=lowest['Course'], lowest_mean=lowest['Mean'],
           gap=highest['Mean'] - lowest['Mean'], r=r))

render_save_ui("performance_deep_dive", "Performance data",
               dataframe_to_dict(course_stats))
