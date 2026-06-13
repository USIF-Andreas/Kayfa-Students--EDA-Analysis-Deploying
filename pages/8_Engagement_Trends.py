import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import pearsonr
from utils import load_data, page_config, show_logo, show_top_logo
from db_utils import require_auth, render_save_ui, dataframe_to_dict

require_auth()

page_config("Kayfa — Attendance & Engagement Trends", "📈")
show_logo()
show_top_logo()

master = load_data()

st.title("📈 Attendance & Engagement Trends")
st.markdown("##### Tracking participation patterns and performance relationships")

# ── Q1: Attendance Rate Per Group ──
st.header("Q1: Attendance Rate by Group — Who Sits Below Average?")

att_by_group = master[master["group_id"] != "Unassigned"].groupby("group_id")["attendance_rate_pct"].agg(["mean", "count"]).reset_index()
att_by_group.columns = ["group_id", "avg_att_rate", "count"]
att_by_group = att_by_group.sort_values("avg_att_rate")
platform_avg = master["attendance_rate_pct"].mean()

col1, col2 = st.columns(2)

with col1:
    colors = ["#ef4444" if r["avg_att_rate"] < platform_avg else "#10b981" for _, r in att_by_group.iterrows()]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=att_by_group["avg_att_rate"], y=att_by_group["group_id"],
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

with col2:
    below = att_by_group[att_by_group["avg_att_rate"] < platform_avg]
    st.markdown(f"**Platform average attendance: {platform_avg:.1f}%**")
    st.markdown(f"**Groups below average: {len(below)}**")
    for _, r in below.iterrows():
        delta = r["avg_att_rate"] - platform_avg
        group_courses = master[master["group_id"] == r["group_id"]]["course_name"].iloc[0] if len(master[master["group_id"] == r["group_id"]]) > 0 else ""
        st.metric(
            label=f"Group {r['group_id']}",
            value=f"{r['avg_att_rate']:.1f}%",
            delta=f"{delta:.1f}pp",
            delta_color="inverse",
        )

st.caption("🔴 Red bars = below platform average.")

st.divider()

# ── Q5: Engagement vs Performance ──
st.header("Q5: Engagement vs Academic Performance")

r_events, p_events = pearsonr(master["total_events"], master["avg_concept_score"])
r_video, p_video = pearsonr(master["total_video_seconds"], master["avg_concept_score"])

col3, col4 = st.columns(2)

with col3:
    fig = px.scatter(
        master, x="total_events", y="avg_concept_score",
        trendline="ols", opacity=0.5, color_discrete_sequence=["#6366f1"],
        title=f"Total Events vs Avg Score (r={r_events:.3f})",
        labels={"total_events": "Total Events", "avg_concept_score": "Avg Concept Score %"},
    )
    fig.update_layout(template="plotly_dark", height=350,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"p={p_events:.2e} — {'significant' if p_events < 0.05 else 'not significant'}")

with col4:
    master["video_hrs"] = master["total_video_seconds"] / 3600
    fig = px.scatter(
        master, x="video_hrs", y="avg_concept_score",
        trendline="ols", opacity=0.5, color_discrete_sequence=["#14b8a6"],
        title=f"Video Watch Hours vs Avg Score (r={r_video:.3f})",
        labels={"video_hrs": "Total Video Hours", "avg_concept_score": "Avg Concept Score %"},
    )
    fig.update_layout(template="plotly_dark", height=350,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"p={p_video:.2e}")

st.subheader("Engagement Quartile Breakdown")
master["eng_z_events"] = (master["total_events"] - master["total_events"].mean()) / master["total_events"].std()
master["eng_z_video"] = (master["total_video_seconds"] - master["total_video_seconds"].mean()) / master["total_video_seconds"].std()
master["eng_composite"] = master["eng_z_events"] + master["eng_z_video"]

master["eng_quartile"] = pd.qcut(master["eng_composite"], 4, labels=["Q1 (Low)", "Q2", "Q3", "Q4 (High)"])
eng_trend = master.groupby("eng_quartile", observed=True)["avg_concept_score"].agg(["mean", "std", "count"]).reset_index()
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

# ── Summary ──
st.header("📋 Key Takeaways")
st.markdown("""
| Question | Finding |
|---|---|
| **Q1 — Group Attendance** | Groups vary significantly in attendance; those below platform avg need intervention |
| **Q5 — Engagement vs Grade** | Events (r={:.3f}) vs Video (r={:.3f}); composite engagement correlates with scores |
""".format(r_events, r_video))

render_save_ui("engagement_trends", "Engagement Trends data",
               dataframe_to_dict(att_by_group))
