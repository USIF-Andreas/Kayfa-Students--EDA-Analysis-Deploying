import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils import load_data, page_config, show_logo, show_top_logo
from db_utils import require_auth, render_save_ui, dataframe_to_dict

require_auth()

page_config("Kayfa — Group Performance Trends", "📊")
show_logo()
show_top_logo()

master = load_data()

st.title("📊 Group Performance Overview")
st.markdown("##### Tracking each group's average scores and performance patterns")

# ── Q15: Group Performance ──
st.header("Q15: Which Groups Are Performing Best vs Worst?")

group_stats = master[master["group_id"] != "Unassigned"].groupby("group_id").agg(
    avg_grade=("avg_grade", "mean"),
    avg_concept=("avg_concept_score", "mean"),
    avg_attendance=("attendance_rate_pct", "mean"),
    avg_fail=("concept_fail_pct", "mean"),
    avg_late=("late_rate", "mean"),
    count=("student_id", "count"),
).reset_index()
group_stats = group_stats.sort_values("avg_concept", ascending=False)

col1, col2 = st.columns([2, 1])

with col1:
    fig = go.Figure()
    for _, row in group_stats.iterrows():
        fig.add_trace(go.Bar(
            name=row["group_id"],
            y=[row["avg_concept"]],
            x=[row["group_id"]],
            text=f"{row['avg_concept']:.1f}%",
            textposition="outside",
        ))
    fig.update_layout(
        template="plotly_dark", height=400,
        title="Average Concept Score by Group",
        xaxis_title="Group", yaxis_title="Avg Concept Score %",
        margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Groups sorted by average concept score. Performance varies across cohorts.")

with col2:
    st.subheader("Group Summary")
    for _, row in group_stats.iterrows():
        emoji = "📈" if row["avg_concept"] > master["avg_concept_score"].mean() else "📉"
        st.markdown(
            f"{emoji} **{row['group_id']}** ({int(row['count'])} students)  \n"
            f"Score: {row['avg_concept']:.1f}% | Att: {row['avg_attendance']:.0f}%  \n"
            f"Fail: {row['avg_fail']:.1f}% | Late: {row['avg_late']*100:.0f}%"
        )
        st.markdown("---")

st.divider()

# Performance comparison across metrics
st.subheader("Multi-Metric Group Comparison")

metrics = ["avg_grade", "avg_concept", "avg_attendance"]
metric_labels = ["Avg Grade %", "Avg Concept Score %", "Avg Attendance %"]

fig = go.Figure()
for metric in metrics:
    fig.add_trace(go.Bar(
        name=metric_labels[metrics.index(metric)],
        x=group_stats["group_id"],
        y=group_stats[metric],
    ))
fig.update_layout(
    template="plotly_dark", height=400,
    barmode="group",
    title="Group Comparison: Grade, Concept Score & Attendance",
    xaxis_title="Group", yaxis_title="Percentage",
    margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11),
)
st.plotly_chart(fig, use_container_width=True)
st.caption("Side-by-side comparison of key metrics across groups. Some groups consistently underperform.")

st.divider()

# Course-level group performance
st.subheader("Performance by Course")

course_group = master.dropna(subset=["course_name"]).groupby(["course_name", "group_id"])["avg_concept_score"].mean().reset_index()
pivot_data = course_group.pivot(index="group_id", columns="course_name", values="avg_concept_score").round(1)

fig = px.imshow(
    pivot_data, text_auto=True, color_continuous_scale="RdYlGn",
    title="Group × Course Heatmap (Avg Concept Score %)",
    labels={"x": "Course", "y": "Group", "color": "Score %"},
    aspect="auto",
)
fig.update_layout(template="plotly_dark", height=400,
                  margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
st.plotly_chart(fig, use_container_width=True)
st.caption("Heatmap showing group performance across courses. Darker green = better performance.")

st.divider()

# ── Summary ──
st.header("📋 Key Takeaways")
st.markdown("""
| Question | Finding |
|---|---|
| **Q15 — Group Performance** | Best group: **{best_group}** ({best_score:.1f}%), Worst: **{worst_group}** ({worst_score:.1f}%) |
| **Implication** | Performance varies significantly across groups — investigate teaching methods and cohort composition |
| **Recommendation** | Introduce targeted interventions for low-performing groups; replicate successful practices from top groups |
""".format(
    best_group=group_stats.iloc[0]["group_id"],
    best_score=group_stats.iloc[0]["avg_concept"],
    worst_group=group_stats.iloc[-1]["group_id"],
    worst_score=group_stats.iloc[-1]["avg_concept"],
))

render_save_ui("group_performance", "Group performance data",
               dataframe_to_dict(group_stats))
