import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import load_all, page_config

page_config("Kayfa Students — Engagement", "⚡")

data = load_all()
engagement = data["engagement"]
master = data["master"]

engagement["event_datetime"] = pd.to_datetime(engagement["event_datetime"])

st.title("⚡ Engagement & Behavioral Analytics")
st.markdown("##### Platform Interaction, Learning Styles & Device Usage")

total_events = len(engagement)
total_students = engagement["student_id"].nunique()
avg_duration = engagement["duration_seconds"].dropna().mean()
mobile_pct = (engagement["device"] == "mobile").mean() * 100

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Events", f"{total_events:,}")
col2.metric("Active Students", total_students)
col3.metric("Avg Duration", f"{avg_duration:.0f}s")
col4.metric("Mobile Usage", f"{mobile_pct:.1f}%")

st.divider()

selected_events = st.multiselect(
    "Filter Event Types",
    options=sorted(engagement["event_type"].unique()),
    default=sorted(engagement["event_type"].unique()),
)

filtered = engagement[engagement["event_type"].isin(selected_events)]

col_a, col_b = st.columns(2)

with col_a:
    evt_counts = filtered["event_type"].value_counts().reset_index()
    evt_counts.columns = ["event_type", "count"]
    fig = px.bar(
        evt_counts,
        x="event_type",
        y="count",
        color="event_type",
        color_discrete_map={
            "login": "#6366f1",
            "video_watch": "#14b8a6",
            "resource_download": "#f59e0b",
            "quiz_attempt": "#8b5cf6",
            "forum_post": "#f43f5e",
        },
        title="Events by Type",
        labels={"event_type": "", "count": "Count"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    dev_counts = filtered["device"].value_counts().reset_index()
    dev_counts.columns = ["device", "count"]
    fig = px.pie(
        dev_counts,
        values="count",
        names="device",
        color="device",
        color_discrete_map={"web": "#6366f1", "mobile": "#14b8a6"},
        hole=0.5,
        title="Device Usage",
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

engagement["week"] = engagement["event_datetime"].dt.to_period("W").dt.start_time
weekly = engagement.groupby("week").size().reset_index(name="events")
fig = px.area(
    weekly,
    x="week",
    y="events",
    title="Engagement Activity Over Time (Weekly)",
    labels={"week": "Week", "events": "Events"},
)
fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
st.plotly_chart(fig, use_container_width=True)

st.divider()

col_c, col_d = st.columns(2)

with col_c:
    cross = pd.crosstab(engagement["event_type"], engagement["device"])
    fig = px.imshow(
        cross,
        text_auto=True,
        color_continuous_scale="Viridis",
        title="Event Type × Device Heatmap",
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

with col_d:
    videos = engagement[
        (engagement["event_type"] == "video_watch")
        & (engagement["duration_seconds"] > 0)
        & (engagement["duration_seconds"] < 3600)
    ]
    fig = px.histogram(
        videos,
        x="duration_seconds",
        nbins=40,
        color_discrete_sequence=["#14b8a6"],
        title="Video Watch Duration",
        labels={"duration_seconds": "Duration (seconds)"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

events_per_student = engagement.groupby("student_id").size().reset_index(name="total_events")
fig = px.histogram(
    events_per_student,
    x="total_events",
    nbins=25,
    color_discrete_sequence=["#f59e0b"],
    title="Events per Student Distribution",
    labels={"total_events": "Total Events", "count": "Students"},
)
fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
st.plotly_chart(fig, use_container_width=True)
