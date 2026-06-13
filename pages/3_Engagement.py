import streamlit as st
import pandas as pd
import plotly.express as px
from utils import load_data, page_config, show_logo, show_top_logo
from db_utils import require_auth

require_auth()

page_config("Kayfa Students — Engagement", "⚡")
show_logo()
show_top_logo()

master = load_data()

st.title("⚡ Engagement & Behavioral Analytics")
st.markdown("##### Platform Interaction & Learning Activity Summary")

total_events = master["total_events"].sum()
total_video_sec = master["total_video_seconds"].sum()
avg_events = master["total_events"].mean()
avg_video_hrs = master["total_video_seconds"].mean() / 3600
avg_time = master["avg_time_spent"].mean()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Events", f"{total_events:,.0f}")
col2.metric("Total Video Time", f"{total_video_sec/3600:.0f}h")
col3.metric("Avg Events/Student", f"{avg_events:.0f}")
col4.metric("Avg Time Spent", f"{avg_time:.0f} min")

st.divider()

col_a, col_b = st.columns(2)

with col_a:
    fig = px.histogram(
        master, x="total_events", nbins=30, color_discrete_sequence=["#6366f1"],
        title="Total Events per Student", labels={"total_events": "Events"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    low_events = (master["total_events"] < 50).sum()
    st.caption(f"Most students generate 50-100 events. {low_events} students ({low_events/len(master)*100:.0f}%) have fewer than 50 — likely disengaged.")

with col_b:
    fig = px.histogram(
        master, x="total_video_seconds", nbins=30, color_discrete_sequence=["#14b8a6"],
        title="Total Video Watch Time per Student", labels={"total_video_seconds": "Seconds"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    median_vid = master["total_video_seconds"].median()
    st.caption(f"Median video watch time is {median_vid:.0f}s. The distribution is right-skewed — most watches are moderate, with a tail of heavy viewers.")

st.divider()

col_c, col_d = st.columns(2)

with col_c:
    fig = px.histogram(
        master, x="avg_time_spent", nbins=30, color_discrete_sequence=["#f59e0b"],
        title="Avg Time Spent on Assignments", labels={"avg_time_spent": "Minutes"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    med_time = master["avg_time_spent"].median()
    st.caption(f"Median time spent is {med_time:.0f} minutes. The distribution varies widely across students.")

with col_d:
    fig = px.scatter(
        master, x="total_events", y="avg_concept_score",
        color="category", hover_data=["student_id", "course_name"],
        title="Events vs Concept Score",
        labels={"total_events": "Total Events", "avg_concept_score": "Avg Concept Score"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Positive trend: more engagement events generally correlate with higher concept scores.")

st.divider()

col_e, col_f = st.columns(2)

with col_e:
    fig = px.scatter(
        master, x="total_video_seconds", y="avg_concept_score",
        color="difficulty_level", hover_data=["student_id"],
        title="Video Watch Time vs Concept Score",
        labels={"total_video_seconds": "Video Watch (seconds)", "avg_concept_score": "Avg Concept Score"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Video consumption correlates positively with scores — students who watch more content perform better.")

with col_f:
    fig = px.scatter(
        master, x="avg_time_spent", y="avg_concept_score",
        color="category", hover_data=["student_id"],
        title="Time Spent vs Concept Score",
        labels={"avg_time_spent": "Avg Time (min)", "avg_concept_score": "Avg Concept Score"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Diminishing returns on time spent — very high time investment doesn't guarantee proportionally higher scores.")
