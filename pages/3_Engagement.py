import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import (
    load_all, page_config, show_logo, show_top_logo,
    compute_weekly_engagement, compute_student_engagement_count,
)

if "engagement_events" not in st.session_state:
    st.session_state.engagement_events = None

page_config("Kayfa Students — Engagement", "⚡")
show_logo()
show_top_logo()

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

event_options = sorted(engagement["event_type"].unique())
if st.session_state.engagement_events is None:
    st.session_state.engagement_events = event_options

selected_events = st.multiselect(
    "Filter Event Types",
    options=event_options,
    default=event_options,
    key="engagement_events",
)

filtered = engagement[engagement["event_type"].isin(selected_events)]

col_a, col_b = st.columns(2)

with col_a:
    evt_counts = filtered["event_type"].value_counts().reset_index()
    evt_counts.columns = ["event_type", "count"]
    fig = px.bar(
        evt_counts, x="event_type", y="count", color="event_type",
        color_discrete_map={
            "login": "#6366f1", "video_watch": "#14b8a6",
            "resource_download": "#f59e0b", "quiz_attempt": "#8b5cf6",
            "forum_post": "#f43f5e",
        },
        title="Events by Type", labels={"event_type": "", "count": "Count"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    top_evt = evt_counts.iloc[0]
    st.caption(f"Logins dominate ({top_evt['count']:,} events — {top_evt['count']/len(engagement)*100:.0f}% of all activity). Forum posts are the rarest, suggesting low peer interaction.")

with col_b:
    dev_counts = filtered["device"].value_counts().reset_index()
    dev_counts.columns = ["device", "count"]
    fig = px.pie(
        dev_counts, values="count", names="device", color="device",
        color_discrete_map={"web": "#6366f1", "mobile": "#14b8a6"}, hole=0.5,
        title="Device Usage",
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    web_pct = dev_counts[dev_counts["device"] == "web"]["count"].values[0] / len(filtered) * 100
    st.caption(f"Web is preferred ({web_pct:.0f}% of events). With {100-web_pct:.0f}% on mobile, the platform should ensure feature parity and smooth experience on both devices.")

st.divider()

weekly = compute_weekly_engagement(engagement)
fig = px.area(
    weekly, x="week", y="events",
    title="Engagement Activity Over Time (Weekly)",
    labels={"week": "Week", "events": "Events"},
)
fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
st.plotly_chart(fig, use_container_width=True)
peak_week = weekly.loc[weekly["events"].idxmax()]
st.caption(f"Activity peaked around {peak_week['week'].date()} ({peak_week['events']:,.0f} events). Engagement may drop in later weeks — a pattern to monitor for course completion strategies.")

st.divider()

col_c, col_d = st.columns(2)

with col_c:
    cross = pd.crosstab(engagement["event_type"], engagement["device"])
    fig = px.imshow(
        cross, text_auto=True, color_continuous_scale="Viridis",
        title="Event Type × Device Heatmap",
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Mobile usage is proportionally higher for logins and quiz attempts. Video watching skews heavily toward web, possibly due to streaming quality on mobile.")

with col_d:
    videos = engagement[
        (engagement["event_type"] == "video_watch")
        & (engagement["duration_seconds"] > 0)
        & (engagement["duration_seconds"] < 3600)
    ]
    fig = px.histogram(
        videos, x="duration_seconds", nbins=40, color_discrete_sequence=["#14b8a6"],
        title="Video Watch Duration", labels={"duration_seconds": "Duration (seconds)"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    median_vid = videos["duration_seconds"].median()
    st.caption(f"Median video watch time is {median_vid:.0f}s. The distribution is right-skewed — most watches are short, with a long tail of longer sessions.")

st.divider()

events_per_student = compute_student_engagement_count(engagement)
fig = px.histogram(
    events_per_student, x="total_events", nbins=25, color_discrete_sequence=["#f59e0b"],
    title="Events per Student Distribution",
    labels={"total_events": "Total Events"},
)
fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
st.plotly_chart(fig, use_container_width=True)
low_events = (events_per_student["total_events"] < 20).sum()
st.caption(f"Most students generate 20–80 events. {low_events} students ({low_events/len(events_per_student)*100:.0f}%) have fewer than 20 events — likely disengaged and at risk of dropping out.")
