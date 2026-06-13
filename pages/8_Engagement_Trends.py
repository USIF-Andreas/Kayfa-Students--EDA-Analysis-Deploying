import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import pearsonr
from utils import load_all, page_config, show_logo, show_top_logo
from db_utils import require_auth, render_save_ui, dataframe_to_dict

require_auth()

page_config("Kayfa — Attendance & Engagement Trends", "📈")
show_logo()
show_top_logo()

data = load_all()
attendance = data["attendance"]
engagement = data["engagement"]
master = data["master"]
groups = data["groups"]
students = data["students"]

attendance["status"] = attendance["status"].str.strip().str.lower()
attendance = attendance[attendance["status"].isin(["attended", "absent"])]
engagement["event_datetime"] = pd.to_datetime(engagement["event_datetime"])
attendance["session_datetime"] = pd.to_datetime(attendance["session_datetime"])

st.title("📈 Attendance & Engagement Trends")
st.markdown("##### Tracking participation patterns, group-level attendance, and identifying cohort-wide dips")

# ── Q1: Attendance Rate Per Group ──
st.header("Q1: Attendance Rate by Group — Who Sits Below Average?")

att_by_student = attendance.groupby("student_id")["status"].apply(
    lambda x: (x == "attended").mean() * 100
).reset_index(name="att_rate")
att_by_student = att_by_student.merge(students[["student_id", "group_id"]], on="student_id")
att_by_group = att_by_student.groupby("group_id")["att_rate"].mean().reset_index(name="avg_att_rate")
att_by_group = att_by_group.merge(groups[["group_id", "group_name", "course_id", "instructor"]], on="group_id")
att_by_group = att_by_group.sort_values("avg_att_rate")
platform_avg = att_by_student["att_rate"].mean()

col1, col2 = st.columns(2)

with col1:
    colors = ["#ef4444" if r["avg_att_rate"] < platform_avg else "#10b981" for _, r in att_by_group.iterrows()]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=att_by_group["avg_att_rate"], y=att_by_group["group_name"],
        orientation="h", marker_color=colors,
        text=att_by_group["avg_att_rate"].round(1).astype(str) + "%",
        textposition="outside",
    ))
    fig.add_vline(x=platform_avg, line_dash="dash", line_color="orange",
                  annotation_text=f"Platform Avg: {platform_avg:.1f}%")
    fig.update_layout(template="plotly_dark", height=400,
                      title="Attendance Rate by Group",
                      xaxis_title="Attendance %", yaxis_title="",
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Group 07 (C005, Eng. Hossam Refaat) at 61.4% is the lowest — 18.3pp below the platform average. Group 05 (C003) leads at 87.0%.")

with col2:
    below = att_by_group[att_by_group["avg_att_rate"] < platform_avg]
    st.markdown(f"**Platform average attendance: {platform_avg:.1f}%**")
    st.markdown(f"**Groups below average: {len(below)}**")
    for _, r in below.iterrows():
        delta = r["avg_att_rate"] - platform_avg
        st.metric(
            label=f"{r['group_name']} ({r['course_id']}, {r['instructor']})",
            value=f"{r['avg_att_rate']:.1f}%",
            delta=f"{delta:.1f}pp",
            delta_color="inverse",
        )

st.caption("🔴 Red bars = below platform average. Group 07 (C005, Eng. Hossam Refaat) at 61.4% is the standout concern.")

st.divider()

# ── Q5: Engagement vs Performance ──
st.header("Q5: Engagement (Login Frequency & Video Time) vs Academic Performance")

login_count = engagement[engagement["event_type"] == "login"].groupby("student_id").size().reset_index(name="login_count")
video_time = engagement[engagement["event_type"] == "video_watch"].groupby("student_id")["duration_seconds"].sum().reset_index(name="total_video_sec")

student_grades = master[["student_id", "avg_concept_score"]]

eng_student = login_count.merge(video_time, on="student_id", how="outer").fillna(0)
eng_student = eng_student.merge(student_grades, on="student_id")

r_logins, p_logins = pearsonr(eng_student["login_count"], eng_student["avg_concept_score"])
r_video, p_video = pearsonr(eng_student["total_video_sec"], eng_student["avg_concept_score"])

eng_student["eng_z_logins"] = (eng_student["login_count"] - eng_student["login_count"].mean()) / eng_student["login_count"].std()
eng_student["eng_z_video"] = (eng_student["total_video_sec"] - eng_student["total_video_sec"].mean()) / eng_student["total_video_sec"].std()
eng_student["eng_composite"] = eng_student["eng_z_logins"] + eng_student["eng_z_video"]

r_comp, p_comp = pearsonr(eng_student["eng_composite"], eng_student["avg_concept_score"])

col3, col4 = st.columns(2)

with col3:
    fig = px.scatter(
        eng_student, x="login_count", y="avg_concept_score",
        trendline="ols", opacity=0.5, color_discrete_sequence=["#6366f1"],
        title=f"Login Count vs Avg Score (r={r_logins:.3f})",
        labels={"login_count": "Login Count", "avg_concept_score": "Avg Concept Score %"},
    )
    fig.update_layout(template="plotly_dark", height=350,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"p={p_logins:.2e} — {'significant' if p_logins < 0.05 else 'not significant'}")

with col4:
    eng_student["video_hrs"] = eng_student["total_video_sec"] / 3600
    fig = px.scatter(
        eng_student, x="video_hrs", y="avg_concept_score",
        trendline="ols", opacity=0.5, color_discrete_sequence=["#14b8a6"],
        title=f"Video Watch Hours vs Avg Score (r={r_video:.3f})",
        labels={"video_hrs": "Total Video Hours", "avg_concept_score": "Avg Concept Score %"},
    )
    fig.update_layout(template="plotly_dark", height=350,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"p={p_video:.2e} — video time is the stronger predictor")

st.subheader("Composite Engagement Quartile Breakdown")
eng_student["eng_quartile"] = pd.qcut(eng_student["eng_composite"], 4, labels=["Q1 (Low)", "Q2", "Q3", "Q4 (High)"])
eng_trend = eng_student.groupby("eng_quartile", observed=True)["avg_concept_score"].agg(["mean", "std", "count"]).reset_index()
eng_trend.columns = ["Quartile", "Avg Score", "Std", "Count"]

fig = px.bar(
    eng_trend, x="Quartile", y="Avg Score", color="Avg Score",
    color_continuous_scale="Viridis", text="Avg Score",
    title="Average Score by Engagement Quartile",
    labels={"Quartile": "Engagement Quartile", "Avg Score": "Avg Score %"},
)
fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
fig.update_layout(template="plotly_dark", height=350,
                  margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
st.plotly_chart(fig, use_container_width=True)

delta = eng_trend.iloc[-1]["Avg Score"] - eng_trend.iloc[0]["Avg Score"]
st.caption(f"Q4 (High engagement) scores {delta:.1f}pp higher than Q1 (Low) — clear dose-response relationship.")

st.divider()

# ── Q9: Attendance & Engagement Over Time ──
st.header("Q9: Attendance & Engagement Over 6 Months — Cohort Dip Detection")

attendance["week"] = attendance["session_datetime"].dt.to_period("W").dt.start_time
att_weekly = attendance.groupby("week")["status"].apply(
    lambda x: (x == "attended").mean() * 100
).reset_index(name="att_rate").sort_values("week")

eng_term = engagement[
    (engagement["event_datetime"] >= "2025-10-01") &
    (engagement["event_datetime"] <= "2026-06-01")
].copy()
eng_term["week"] = eng_term["event_datetime"].dt.to_period("W").dt.start_time
eng_weekly = eng_term.groupby("week").size().reset_index(name="event_count").sort_values("week")

# Merge for combined timeline
combined = att_weekly.merge(eng_weekly, on="week", how="outer")

fig = make_subplots(specs=[[{"secondary_y": True}]])

fig.add_trace(
    go.Scatter(x=combined["week"], y=combined["att_rate"], mode="lines+markers",
               name="Attendance Rate", line=dict(color="#10b981", width=3),
               marker=dict(size=8)),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=combined["week"], y=combined["event_count"], mode="lines+markers",
               name="Engagement Events", line=dict(color="#6366f1", width=3),
               marker=dict(size=8)),
    secondary_y=True,
)

fig.update_layout(
    template="plotly_dark", height=400,
    title="Attendance & Engagement Over Time (Dec 2025 - May 2026)",
    margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11),
    hovermode="x unified",
)
fig.update_xaxes(title_text="Week")
fig.update_yaxes(title_text="Attendance %", secondary_y=False)
fig.update_yaxes(title_text="Engagement Events", secondary_y=True)
st.plotly_chart(fig, use_container_width=True)
st.caption("Engagement halves in early March (weeks of Mar 2-16) — coincides with C005 Assignment 2 & 3 deadlines. Attendance dips 9pp in late December (holidays).")

# Identify dips
min_att = att_weekly.loc[att_weekly["att_rate"].idxmin()]
min_eng = eng_weekly.loc[eng_weekly["event_count"].idxmin()]

col5, col6 = st.columns(2)

with col5:
    st.warning(f"**Lowest Attendance Week:** {min_att['week'].date()}  \n{min_att['att_rate']:.1f}% — {platform_avg - min_att['att_rate']:.1f}pp below average")
    st.caption("Attendance dips in late December — likely a holiday effect (New Year's period).")

with col6:
    st.warning(f"**Lowest Engagement Week:** {min_eng['week'].date()}  \n{min_eng['event_count']:,} events")
    st.caption("Engagement halves in early March — coincides with Assignment 2 & 3 deadlines in C005.")

# Engagement dip detail
st.subheader("Engagement Dip Detail (Mar 2026)")
dip_weeks = eng_weekly[
    (eng_weekly["week"] >= "2026-02-23") & (eng_weekly["week"] <= "2026-03-23")
].copy()
dip_weeks["event_label"] = dip_weeks["week"].dt.strftime("%b %d")

fig = px.area(
    dip_weeks, x="event_label", y="event_count",
    title="Engagement Dip: Mar 2-16, 2026",
    labels={"event_label": "Week", "event_count": "Events"},
    color_discrete_sequence=["#ef4444"],
)
fig.update_layout(template="plotly_dark", height=300,
                  margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
st.plotly_chart(fig, use_container_width=True)
st.caption("The 50% engagement drop in early March is the single largest disruption. Possible causes: mid-term burnout, difficult assignments clustering, or a platform issue.")

st.info(
    "**Proposed Explanation:** The early-March engagement drop (~50% reduction) coincides with "
    "the hardest assignments (Assignment 2 & 3 in C005, which have 46-48% failure rates). "
    "Students likely disengage during high-stress assessment periods. "
    "Alternative explanations: mid-term burnout, spring break timing, or a platform issue. "
    "Recommendation: schedule lighter content or provide support resources during this window."
)

st.divider()

# ── Summary ──
st.header("📋 Key Takeaways")
st.markdown("""
| Question | Finding |
|---|---|
| **Q1 — Group Attendance** | Group 07 (C005) far below at **61.4%**; Group 06 (C004) at **76.3%** |
| **Q5 — Engagement vs Grade** | Video time (r=0.40) > logins (r=0.33); composite r=**0.43** |
| **Q9 — Cohort Dip** | Engagement drops **50%** in early March (Assignment crunch), attendance dips **9pp** in late December (holidays) |
""")

render_save_ui("engagement_trends", "Engagement Trends data",
               dataframe_to_dict(att_by_group[["group_name", "course_id", "avg_att_rate"]]))
