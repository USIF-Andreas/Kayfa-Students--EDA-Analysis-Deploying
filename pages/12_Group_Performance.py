import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils import load_all, page_config, show_logo, show_top_logo
from db_utils import require_auth, render_save_ui, dataframe_to_dict

require_auth()

page_config("Kayfa — Group Performance Trends", "📊")
show_logo()
show_top_logo()

data = load_all()
grades = data["grades"]
groups = data["groups"]
students = data["students"]

grades = grades[grades["assessment_title"] != "Bonus Exam"]

st.title("📊 Group Performance Trends Across the Term")
st.markdown("##### Tracking each group's average grade across successive assessments")

# ── Q15: Group Grade Trends ──
st.header("Q15: Which Groups Are Trending Up vs Down?")

grades_sorted = grades.copy()
grades_sorted["date"] = pd.to_datetime(grades_sorted["date"])
grades_sorted = grades_sorted.sort_values(["group_id", "date"])
grades_sorted["assessment_order"] = grades_sorted.groupby("group_id").cumcount()

group_progression = grades_sorted.groupby(["group_id", "assessment_order"])["score"].mean().reset_index()
group_progression = group_progression.merge(
    groups[["group_id", "group_name", "course_id", "instructor"]], on="group_id"
)

# Compute group trend slope
def get_group_trend(grp):
    if len(grp) < 2:
        return 0, "insufficient data", 0
    slope = np.polyfit(grp["assessment_order"], grp["score"], 1)[0]
    if slope > 0.02:
        direction = "improving"
    elif slope < -0.02:
        direction = "declining"
    else:
        direction = "stable"
    return slope, direction, grp["score"].mean()

trend_results = []
for gid, grp in group_progression.groupby(["group_id", "group_name", "course_id", "instructor"]):
    slope, direction, avg = get_group_trend(grp)
    trend_results.append({
        "group_id": gid[0], "group_name": gid[1], "course_id": gid[2],
        "instructor": gid[3], "slope": slope, "direction": direction,
        "avg_grade": avg, "assessments": len(grp),
    })
trends = pd.DataFrame(trend_results).sort_values("slope", ascending=False)

# Color map
dir_colors = {"improving": "#10b981", "stable": "#6366f1", "declining": "#ef4444"}

col1, col2 = st.columns([2, 1])

with col1:
    fig = go.Figure()
    for _, row in trends.iterrows():
        gdata = group_progression[group_progression["group_id"] == row["group_id"]]
        color = dir_colors.get(row["direction"], "#6366f1")
        line_width = 3 if row["direction"] != "stable" else 1.5
        opacity = 1.0 if row["direction"] != "stable" else 0.4
        fig.add_trace(go.Scatter(
            x=gdata["assessment_order"], y=gdata["score"],
            mode="lines+markers", name=row["group_name"],
            line=dict(color=color, width=line_width),
            marker=dict(size=6),
            opacity=opacity,
        ))
    fig.update_layout(
        template="plotly_dark", height=500,
        title="Group Grade Trajectories Across Assessments",
        xaxis_title="Assessment Order", yaxis_title="Avg Score %",
        margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Most groups show flat trajectories (slope ≈ 0). No group is significantly improving. G10 shows decline but is a single-student group.")

with col2:
    st.subheader("Trend Summary")
    for _, row in trends.iterrows():
        emoji = {"improving": "📈", "stable": "➡️", "declining": "📉"}.get(row["direction"], "➡️")
        color = dir_colors.get(row["direction"], "#6366f1")
        st.markdown(
            f"{emoji} **{row['group_name']}**  \n"
            f"<span style='color:{color}'>**{row['direction'].upper()}**</span> "
            f"(slope={row['slope']:.2f})  \n"
            f"Avg: {row['avg_grade']:.1f}% | {row['course_id']} | {row['instructor']}",
            unsafe_allow_html=True,
        )
        if row["direction"] != "stable":
            st.markdown("---")

st.divider()

# Visualize improving vs declining separately
st.subheader("Improving vs Declining Groups — Detail View")

improving = trends[trends["direction"] == "improving"]
declining = trends[trends["direction"] == "declining"]

col3, col4 = st.columns(2)

with col3:
    if len(improving) > 0:
        st.success(f"**Improving Groups ({len(improving)})**")
        for _, row in improving.iterrows():
            st.markdown(f"📈 **{row['group_name']}** — slope={row['slope']:.3f}, avg grade={row['avg_grade']:.1f}%")
            gdata = group_progression[group_progression["group_id"] == row["group_id"]]
            fig = px.line(
                gdata, x="assessment_order", y="score", markers=True,
                title=f"{row['group_name']} — Upward Trend",
                labels={"assessment_order": "Assessment #", "score": "Score %"},
                color_discrete_sequence=["#10b981"],
            )
            fig.update_layout(template="plotly_dark", height=250,
                              margin=dict(l=0, r=0, t=30, b=0), font=dict(size=10))
            st.plotly_chart(fig, use_container_width=True)
            st.caption(f"Slope={row['slope']:.3f} — a small positive trend.")
    else:
        st.info("No groups show a significant upward trend.")

with col4:
    if len(declining) > 0:
        st.error(f"**Declining Groups ({len(declining)})**")
        for _, row in declining.iterrows():
            st.markdown(f"📉 **{row['group_name']}** — slope={row['slope']:.3f}, avg grade={row['avg_grade']:.1f}%")
            gdata = group_progression[group_progression["group_id"] == row["group_id"]]
            fig = px.line(
                gdata, x="assessment_order", y="score", markers=True,
                title=f"{row['group_name']} — Downward Trend",
                labels={"assessment_order": "Assessment #", "score": "Score %"},
                color_discrete_sequence=["#ef4444"],
            )
            fig.update_layout(template="plotly_dark", height=250,
                              margin=dict(l=0, r=0, t=30, b=0), font=dict(size=10))
            st.plotly_chart(fig, use_container_width=True)
            st.caption(f"Slope={row['slope']:.3f} — a declining trajectory worth monitoring.")
    else:
        st.info("No groups show a significant downward trend (beyond G10 which has only 1 student).")

st.divider()

# Assessment-level detail
st.subheader("Assessment-by-Assessment: Average Score per Group")
pivot_table = grades_sorted.groupby(["group_id", "assessment_title"])["score"].mean().reset_index()
pivot_table = pivot_table.merge(groups[["group_id", "group_name"]], on="group_id")
pivot_pivot = pivot_table.pivot(index="group_name", columns="assessment_title", values="score").round(1)

fig = px.imshow(
    pivot_pivot, text_auto=True, color_continuous_scale="RdYlGn",
    title="Group × Assessment Heatmap (Avg Score %)",
    labels={"x": "Assessment", "y": "Group", "color": "Score %"},
    aspect="auto",
)
fig.update_layout(template="plotly_dark", height=500,
                  margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
st.plotly_chart(fig, use_container_width=True)
st.caption("C005 assessments (dark red/orange) are consistently low across all groups taking them. G10 has too few data points for reliable tracking.")

st.divider()

# ── Summary ──
st.header("📋 Key Takeaways")
st.markdown("""
| Question | Finding |
|---|---|
| **Q15 — Group Trends** | Most groups are **stable** (slope ≈ 0). No groups are significantly improving. Only **G10** shows decline but is a single-student group. |
| **Implication** | Grades are consistent across the term — curriculum difficulty is uniform, no interventions are shifting trajectories |
| **Recommendation** | Introduce targeted interventions for declining/stable-low groups; pilot new teaching methods in G07 (C005) which has the lowest overall performance |
""")

render_save_ui("group_performance", "Group performance data",
               dataframe_to_dict(trends))
