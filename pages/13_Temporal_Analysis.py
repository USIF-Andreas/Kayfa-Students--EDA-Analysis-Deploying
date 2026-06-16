import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from utils import page_config, show_logo, show_top_logo, load_attendance, load_engagement, load_grades
from db_utils import require_auth, render_save_ui, dataframe_to_dict

require_auth()
page_config("Kayfa — Temporal Analysis", "📉")
show_logo()
show_top_logo()

att_raw = load_attendance()
eng_raw = load_engagement()
grades = load_grades() # Needed for the scatter plot only

TERM_START = pd.Timestamp("2025-12-01")
TERM_END = pd.Timestamp("2026-05-31 23:59:59")
TERM_LABEL = "Dec 2025 → May 2026"

@st.cache_data
def process_temporal_data(att_raw, eng_raw):
    att = att_raw[(att_raw["session_datetime"] >= TERM_START) & (att_raw["session_datetime"] <= TERM_END)].copy()
    eng = eng_raw[(eng_raw["event_datetime"] >= TERM_START) & (eng_raw["event_datetime"] <= TERM_END)].copy()

    # Fast month and week extraction
    eng["month"] = eng["event_datetime"].dt.to_period("M").dt.to_timestamp()
    eng["week"] = eng["event_datetime"].dt.to_period("W").dt.to_timestamp()
    
    eng_monthly = eng.groupby("month").agg(total_events=("event_id", "count"), unique_students=("student_id", "nunique")).reset_index().sort_values("month")
    eng_monthly["events_per_student"] = eng_monthly["total_events"] / eng_monthly["unique_students"]
    eng_monthly["month_label"] = eng_monthly["month"].dt.strftime("%b %Y")

    eng_weekly = eng.groupby("week").agg(total_events=("event_id", "count"), unique_students=("student_id", "nunique")).reset_index().sort_values("week")
    eng_weekly["events_per_student"] = eng_weekly["total_events"] / eng_weekly["unique_students"]
    eng_weekly["rolling_mean"] = eng_weekly["events_per_student"].rolling(4, min_periods=2, center=True).mean()
    eng_weekly["rolling_std"] = eng_weekly["events_per_student"].rolling(4, min_periods=2, center=True).std()
    eng_weekly["is_dip"] = eng_weekly["events_per_student"] < (eng_weekly["rolling_mean"] - eng_weekly["rolling_std"])

    att["month"] = att["session_datetime"].dt.to_period("M").dt.to_timestamp()
    att["is_attended"] = (att["status"] == "attended").astype(int)
    overall_att_rate = att["is_attended"].mean() * 100 if len(att) > 0 else 0

    return eng, att, eng_monthly, eng_weekly, overall_att_rate

eng, att, eng_monthly, eng_weekly, overall_att_rate = process_temporal_data(att_raw, eng_raw)

dip_weeks = eng_weekly[eng_weekly["is_dip"]]
weakest_eng = eng_monthly.loc[eng_monthly["events_per_student"].idxmin()]
avg_eng = eng_monthly["events_per_student"].mean()

# ═══════════════════════════════════════════════════
# SECTION 1 — Engagement & Attendance Over the Term
# ═══════════════════════════════════════════════════

st.title("📉 Temporal Trends Analysis")
st.markdown(f"##### Tracking participation and attendance across the {TERM_LABEL} term")
st.divider()

st.header("Q1: Engagement & Attendance Over the 6-Month Term")
st.markdown(f"_{TERM_LABEL} · Is there a window where the whole cohort dips at once?_")

# KPIs
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("Dec Attendance Rate", f"{overall_att_rate:.1f}%")
col_m2.metric("Total Events (6 mo)", f"{len(eng):,}")
col_m3.metric("Engagement Dip Weeks", f"{len(dip_weeks)}")
col_m4.metric("Weakest Month", weakest_eng["month_label"], f"{weakest_eng['events_per_student']:.1f} events/student")

st.markdown("")

# ── CHART 1: Monthly engagement bars (all 6 months) ──
st.subheader("📊 Monthly Engagement — Events per Student")
st.markdown("_How active were students each month? (logins, video watches, quiz attempts, forum posts, downloads)_")

bar_colors = ["#10b981" if v >= avg_eng else "#ef4444" for v in eng_monthly["events_per_student"]]

fig1 = go.Figure()
fig1.add_trace(go.Bar(
    x=eng_monthly["month_label"], y=eng_monthly["events_per_student"],
    marker_color=bar_colors,
    text=[f"{v:.1f}" for v in eng_monthly["events_per_student"]],
    textposition="outside", textfont=dict(size=14, color="white"),
    hovertemplate="%{x}<br>Events/Student: %{y:.1f}<br>Total Events: %{customdata[0]:,}<br>Active Students: %{customdata[1]}<extra></extra>",
    customdata=list(zip(eng_monthly["total_events"], eng_monthly["unique_students"])),
))

fig1.add_hline(y=avg_eng, line_dash="dot", line_color="#fbbf24", line_width=2,
               annotation_text=f"Avg: {avg_eng:.1f}", annotation_position="top left",
               annotation_font_color="#fbbf24")

fig1.update_layout(
    template="plotly_dark", height=420,
    title=dict(text=f"Engagement per Student — Month by Month ({TERM_LABEL})", font=dict(size=16)),
    margin=dict(l=10, r=10, t=60, b=10), font=dict(size=12), bargap=0.3,
    yaxis=dict(title="Events per Student"),
    xaxis=dict(title=""),
)
st.plotly_chart(fig1, use_container_width=True)
st.caption("🟢 Green = above average engagement · 🔴 Red = below average · Hover for details")

st.markdown("")

# ── Per-month engagement breakdown cards ──
st.subheader("📅 Engagement Breakdown — Each Month")

month_cols = st.columns(min(len(eng_monthly), 6))
for i, (_, row) in enumerate(eng_monthly.iterrows()):
    col_idx = i % len(month_cols)
    eps = row["events_per_student"]
    total = int(row["total_events"])
    students = int(row["unique_students"])

    if eps >= avg_eng * 1.1:
        bg = "linear-gradient(135deg, #064e3b, #065f46)"
        emoji = "🔥"
        label = "High"
    elif eps >= avg_eng * 0.9:
        bg = "linear-gradient(135deg, #1e3a5f, #1e40af)"
        emoji = "✅"
        label = "Normal"
    else:
        bg = "linear-gradient(135deg, #7f1d1d, #991b1b)"
        emoji = "⚠️"
        label = "Low"

    with month_cols[col_idx]:
        st.markdown(f"""
        <div style="background: {bg}; border-radius: 12px; padding: 16px; text-align: center; margin-bottom: 8px;">
            <h3 style="color: white; margin: 0;">{row['month_label']}</h3>
            <p style="font-size: 28px; font-weight: 800; color: white; margin: 8px 0;">{emoji} {eps:.1f}</p>
            <p style="color: #d1d5db; font-size: 12px; margin: 0;">events per student</p>
            <hr style="border-color: rgba(255,255,255,0.15); margin: 8px 0;">
            <p style="color: #d1d5db; font-size: 13px; margin: 2px 0;">{total:,} total events</p>
            <p style="color: #9ca3af; font-size: 12px; margin: 2px 0;">{students} active students</p>
            <p style="color: #fbbf24; font-size: 12px; font-weight: 600; margin: 4px 0;">{label}</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("")

# ── Engagement heatmap by group ──
st.subheader("Monthly Engagement Heatmap by Group")
st.markdown("_Which groups were most/least active each month?_")

eng_with_group = eng.merge(
    att_raw[["student_id", "group_id"]].drop_duplicates(),
    on="student_id", how="left"
)
eng_with_group = eng_with_group.dropna(subset=["group_id"])
eng_gm = eng_with_group.groupby(["group_id", "month"]).agg(
    total_events=("event_id", "count"),
    unique_students=("student_id", "nunique"),
).reset_index()
eng_gm["events_per_student"] = eng_gm["total_events"] / eng_gm["unique_students"]
eng_gm["month_label"] = eng_gm["month"].dt.strftime("%b %Y")

pivot = eng_gm.pivot(index="group_id", columns="month_label", values="events_per_student")
mo = eng_gm.drop_duplicates("month").sort_values("month")["month_label"].tolist()
pivot = pivot.reindex(columns=mo)

fig_heat = px.imshow(
    pivot.values, labels=dict(x="Month", y="Group", color="Events/Student"),
    x=pivot.columns.tolist(), y=pivot.index.tolist(),
    color_continuous_scale="RdYlGn", aspect="auto",
    title="Engagement per Student by Group × Month (red = low, green = high)",
)
fig_heat.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=50, b=0))
st.plotly_chart(fig_heat, use_container_width=True)
st.caption("A full red column = ALL groups disengaged that month (cohort-wide event). Isolated red cells = group-specific issues.")

st.divider()

st.header("📋 Key Takeaways")

st.markdown(f"""
<div style="background: linear-gradient(135deg, #064e3b, #065f46); border-radius: 12px; padding: 20px;">
    <h4 style="color: #34d399; margin-bottom: 10px;">📅 Engagement Trends ({TERM_LABEL})</h4>
    <ul style="color: #a7f3d0; font-size: 14px; line-height: 1.8;">
        <li>Engagement (events per student) naturally fluctuates throughout the term.</li>
        <li>The heatmap clearly shows whether dips are cohort-wide or isolated to specific groups.</li>
        <li>Monitoring these metrics allows for timely interventions before students drop off completely.</li>
    </ul>
</div>
""", unsafe_allow_html=True)

st.markdown("")
render_save_ui("engagement_data", "Engagement Analysis data", dataframe_to_dict(eng_monthly))

