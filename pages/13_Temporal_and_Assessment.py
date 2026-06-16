import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from utils import page_config, show_logo, show_top_logo
from db_utils import require_auth, render_save_ui, dataframe_to_dict

require_auth()

page_config("Kayfa — Temporal & Assessment Analysis", "📉")
show_logo()
show_top_logo()

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Load raw CSV files ──
@st.cache_data
def load_attendance():
    return pd.read_csv(os.path.join(BASE, "clean_attendance.csv"), parse_dates=["session_datetime"])

@st.cache_data
def load_engagement():
    return pd.read_csv(os.path.join(BASE, "clean_engagement.csv"), parse_dates=["event_datetime"])

@st.cache_data
def load_grades():
    return pd.read_csv(os.path.join(BASE, "clean_grades.csv"), parse_dates=["date"])

att = load_attendance()
eng = load_engagement()
grades = load_grades()

# ═══════════════════════════════════════════════════════════════════
# SECTION 1 — Attendance & Engagement Over the 6-Month Term
# ═══════════════════════════════════════════════════════════════════

st.title("📉 Temporal Trends & Assessment Analysis")
st.markdown("##### Tracking cohort-wide participation and score volatility over the full term")
st.divider()

st.header("Q1: Attendance & Engagement Over the 6-Month Term")
st.markdown("_Is there a window where the whole cohort dips at once?_")

# ── Attendance: weekly attendance rate ──
att["week"] = att["session_datetime"].dt.to_period("W").apply(lambda r: r.start_time)
att_weekly = (
    att.groupby("week")
    .apply(lambda g: pd.Series({
        "attended": (g["status"] == "attended").sum(),
        "total": len(g),
        "rate": (g["status"] == "attended").mean() * 100,
        "unique_students": g["student_id"].nunique(),
    }))
    .reset_index()
)

# ── Engagement: weekly event count per student ──
eng["week"] = eng["event_datetime"].dt.to_period("W").apply(lambda r: r.start_time)
eng_weekly = (
    eng.groupby("week")
    .agg(
        total_events=("event_id", "count"),
        unique_students=("student_id", "nunique"),
    )
    .reset_index()
)
eng_weekly["events_per_student"] = eng_weekly["total_events"] / eng_weekly["unique_students"]

# ── Merge & Align ──
merged = pd.merge(att_weekly, eng_weekly, on="week", how="outer", suffixes=("_att", "_eng"))
merged = merged.sort_values("week")

# ── Detect cohort-wide dip ──
# A "dip" = attendance rate drops > 1 std below the rolling mean
att_weekly_sorted = att_weekly.sort_values("week")
att_weekly_sorted["rolling_mean"] = att_weekly_sorted["rate"].rolling(4, min_periods=2, center=True).mean()
att_weekly_sorted["rolling_std"] = att_weekly_sorted["rate"].rolling(4, min_periods=2, center=True).std()
att_weekly_sorted["is_dip"] = att_weekly_sorted["rate"] < (att_weekly_sorted["rolling_mean"] - att_weekly_sorted["rolling_std"])

dip_weeks = att_weekly_sorted[att_weekly_sorted["is_dip"]]

# ── Also detect engagement dip ──
eng_weekly_sorted = eng_weekly.sort_values("week")
eng_weekly_sorted["rolling_mean"] = eng_weekly_sorted["events_per_student"].rolling(4, min_periods=2, center=True).mean()
eng_weekly_sorted["rolling_std"] = eng_weekly_sorted["events_per_student"].rolling(4, min_periods=2, center=True).std()
eng_weekly_sorted["is_dip"] = eng_weekly_sorted["events_per_student"] < (eng_weekly_sorted["rolling_mean"] - eng_weekly_sorted["rolling_std"])

eng_dip_weeks = eng_weekly_sorted[eng_weekly_sorted["is_dip"]]

# ── KPI metrics ──
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
overall_att_rate = (att["status"] == "attended").mean() * 100
col_m1.metric("Avg Attendance Rate", f"{overall_att_rate:.1f}%")
col_m2.metric("Total Engagement Events", f"{len(eng):,}")
col_m3.metric("Attendance Dip Weeks", f"{len(dip_weeks)}")
col_m4.metric("Engagement Dip Weeks", f"{len(eng_dip_weeks)}")

st.markdown("")

# ── Dual-axis time series chart ──
fig = make_subplots(specs=[[{"secondary_y": True}]])

# Attendance line
fig.add_trace(
    go.Scatter(
        x=att_weekly_sorted["week"], y=att_weekly_sorted["rate"],
        name="Attendance Rate %", mode="lines+markers",
        line=dict(color="#6366f1", width=3),
        marker=dict(size=6),
        hovertemplate="Week: %{x|%b %d}<br>Attendance: %{y:.1f}%<extra></extra>",
    ),
    secondary_y=False,
)

# Rolling mean
fig.add_trace(
    go.Scatter(
        x=att_weekly_sorted["week"], y=att_weekly_sorted["rolling_mean"],
        name="Attendance Trend (4-wk avg)", mode="lines",
        line=dict(color="#6366f1", width=1.5, dash="dash"),
        opacity=0.5,
    ),
    secondary_y=False,
)

# Engagement events per student
fig.add_trace(
    go.Scatter(
        x=eng_weekly_sorted["week"], y=eng_weekly_sorted["events_per_student"],
        name="Engagement / Student", mode="lines+markers",
        line=dict(color="#14b8a6", width=3),
        marker=dict(size=6),
        hovertemplate="Week: %{x|%b %d}<br>Events/Student: %{y:.1f}<extra></extra>",
    ),
    secondary_y=True,
)

# Highlight dip weeks with red markers
if not dip_weeks.empty:
    fig.add_trace(
        go.Scatter(
            x=dip_weeks["week"], y=dip_weeks["rate"],
            name="⚠ Attendance Dip", mode="markers",
            marker=dict(size=14, color="#ef4444", symbol="diamond", line=dict(width=2, color="white")),
            hovertemplate="DIP WEEK: %{x|%b %d}<br>Rate: %{y:.1f}%<extra></extra>",
        ),
        secondary_y=False,
    )

if not eng_dip_weeks.empty:
    fig.add_trace(
        go.Scatter(
            x=eng_dip_weeks["week"], y=eng_dip_weeks["events_per_student"],
            name="⚠ Engagement Dip", mode="markers",
            marker=dict(size=14, color="#f59e0b", symbol="diamond", line=dict(width=2, color="white")),
            hovertemplate="DIP WEEK: %{x|%b %d}<br>Events/Student: %{y:.1f}<extra></extra>",
        ),
        secondary_y=True,
    )

fig.update_layout(
    template="plotly_dark", height=480,
    title="Attendance Rate & Engagement Over the 6-Month Term",
    legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
    margin=dict(l=0, r=0, t=50, b=0), font=dict(size=12),
    hovermode="x unified",
)
fig.update_xaxes(title_text="Week", tickformat="%b %d, %Y")
fig.update_yaxes(title_text="Attendance Rate %", secondary_y=False, range=[0, 105])
fig.update_yaxes(title_text="Engagement Events / Student", secondary_y=True)

st.plotly_chart(fig, use_container_width=True)

# ── Dip analysis callout ──
if not dip_weeks.empty:
    # Find the strongest dip
    worst_dip = dip_weeks.loc[dip_weeks["rate"].idxmin()]
    dip_date = worst_dip["week"]
    dip_rate = worst_dip["rate"]
    dip_month = dip_date.strftime("%B %Y")

    # Check if engagement also dips in the same window
    concurrent_eng_dip = eng_dip_weeks[
        (eng_dip_weeks["week"] >= dip_date - pd.Timedelta(weeks=1)) &
        (eng_dip_weeks["week"] <= dip_date + pd.Timedelta(weeks=1))
    ]

    col_insight1, col_insight2 = st.columns([2, 1])
    with col_insight1:
        st.error(f"""
        **🔍 Cohort-Wide Dip Detected — Week of {dip_date.strftime('%b %d, %Y')}**

        Attendance dropped to **{dip_rate:.1f}%** — significantly below the rolling trend.
        {"Engagement also dipped simultaneously, confirming a cohort-wide disengagement event." if not concurrent_eng_dip.empty else "Engagement remained stable, suggesting the dip is attendance-specific (not a motivation issue)."}
        """)
    with col_insight2:
        st.info(f"""
        **🗓 All Dip Weeks ({len(dip_weeks)}):**

        {chr(10).join([f"• {w.strftime('%b %d, %Y')} — {r:.1f}%" for w, r in zip(dip_weeks['week'], dip_weeks['rate'])])}
        """)

    st.markdown("---")

    st.subheader("🧐 What Could Explain the Cohort-Wide Dip?")

    # Determine the month/season for contextual guessing
    dip_month_num = dip_date.month
    explanations = []
    if dip_month_num in [1]:
        explanations = [
            ("🎄 Post-Holiday Re-entry", "The dip falls right after winter/New Year holidays. Students often struggle to re-engage after an extended break."),
            ("📝 Semester Start Adjustment", "Early-term scheduling confusion or registration delays cause lower attendance in the opening weeks."),
            ("🤒 Seasonal Illness", "Winter flu season commonly reduces attendance across entire cohorts."),
        ]
    elif dip_month_num in [3, 4]:
        explanations = [
            ("🌙 Ramadan / Religious Holidays", "Fasting month or Eid holidays significantly alter daily routines, reducing both attendance and engagement."),
            ("📊 Mid-Term Exam Prep", "Students may skip regular sessions to self-study for upcoming midterms."),
            ("🏖 Spring Break", "A scheduled or informal break period where students disengage."),
        ]
    elif dip_month_num in [5, 6]:
        explanations = [
            ("📝 Final Exam Period", "Students shift focus from class attendance to exam preparation, causing session absences."),
            ("😓 End-of-Term Fatigue", "Burnout accumulates over 6 months — motivation and attendance naturally decline near the term end."),
            ("🎓 Early Completion", "Some students may have already met requirements and stop attending."),
        ]
    elif dip_month_num in [12]:
        explanations = [
            ("🎄 Holiday Season", "December holidays (Christmas/New Year) lead to travel and reduced campus engagement."),
            ("📅 Term-Start Lag", "If the term begins in December, early weeks see lower attendance as students settle in."),
            ("🤒 Winter Illness Wave", "Cold/flu season causes absenteeism spikes."),
        ]
    else:
        explanations = [
            ("📅 Scheduled Break", "The dip aligns with what appears to be a planned institutional break or holiday."),
            ("🏥 External Event", "A campus or community event (illness wave, infrastructure issue) may have affected the entire cohort."),
            ("📊 Assessment Window", "Heavy assessment deadlines sometimes cause students to skip sessions to prepare."),
        ]

    cols = st.columns(len(explanations))
    for i, (title, desc) in enumerate(explanations):
        with cols[i]:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1e1b4b, #312e81); border-radius: 12px; padding: 20px; height: 200px;">
                <h4 style="color: #a5b4fc; margin-bottom: 8px;">{title}</h4>
                <p style="color: #c7d2fe; font-size: 14px; line-height: 1.5;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)
else:
    st.success("✅ No significant cohort-wide attendance dips were detected — the cohort maintained consistent participation throughout the term.")

st.markdown("")

# ── Heatmap: per-group weekly attendance ──
st.subheader("Weekly Attendance Heatmap by Group")

att_group_week = (
    att.groupby(["group_id", "week"])
    .apply(lambda g: (g["status"] == "attended").mean() * 100)
    .reset_index(name="rate")
)
att_group_week["week_label"] = att_group_week["week"].dt.strftime("%b %d")

pivot = att_group_week.pivot(index="group_id", columns="week_label", values="rate")
# Sort columns chronologically
week_order = att_group_week.drop_duplicates("week").sort_values("week")["week_label"].tolist()
pivot = pivot.reindex(columns=week_order)

fig_heat = px.imshow(
    pivot.values,
    labels=dict(x="Week", y="Group", color="Attendance %"),
    x=pivot.columns.tolist(),
    y=pivot.index.tolist(),
    color_continuous_scale="RdYlGn",
    aspect="auto",
    title="Attendance Rate by Group × Week (darker red = lower attendance)",
)
fig_heat.update_layout(
    template="plotly_dark", height=400,
    margin=dict(l=0, r=0, t=50, b=0), font=dict(size=11),
    xaxis=dict(tickangle=45),
)
st.plotly_chart(fig_heat, use_container_width=True)
st.caption("This heatmap reveals whether dips are isolated to specific groups or affect the entire cohort simultaneously. A vertical red stripe indicates a cohort-wide event.")

st.divider()

# ═══════════════════════════════════════════════════════════════════
# SECTION 2 — Score Distribution by Assessment Type
# ═══════════════════════════════════════════════════════════════════

st.header("Q2: Score Distribution by Assessment Type")
st.markdown("_Where is performance most volatile?_")

# Normalize scores to percentage
grades["score_pct"] = (grades["score"] / grades["max_score"]) * 100

# ── KPI Metrics ──
type_stats = grades.groupby("type")["score_pct"].agg(["mean", "std", "count"]).reset_index()
type_stats.columns = ["Type", "Mean", "Std", "Count"]
type_stats = type_stats.sort_values("Std", ascending=False)

# Compute CoV (Coefficient of Variation) as the volatility measure
type_stats["CoV"] = (type_stats["Std"] / type_stats["Mean"]) * 100

most_volatile = type_stats.iloc[0]["Type"]
least_volatile = type_stats.iloc[-1]["Type"]

col_k1, col_k2, col_k3, col_k4 = st.columns(4)
col_k1.metric("Total Assessments", f"{len(grades):,}")
col_k2.metric("Assessment Types", f"{grades['type'].nunique()}")
col_k3.metric("Most Volatile", f"{most_volatile.title()}", f"σ = {type_stats.iloc[0]['Std']:.1f}")
col_k4.metric("Most Consistent", f"{least_volatile.title()}", f"σ = {type_stats.iloc[-1]['Std']:.1f}")

st.markdown("")

# ── Violin + Box plot ──
col_v1, col_v2 = st.columns([3, 2])

with col_v1:
    type_order = type_stats.sort_values("Mean")["Type"].tolist()
    color_map = {
        "quiz": "#6366f1",
        "assignment": "#14b8a6",
        "practical": "#f59e0b",
        "exam": "#ef4444",
    }

    fig_violin = px.violin(
        grades, x="type", y="score_pct", color="type",
        box=True, points="outliers",
        color_discrete_map=color_map,
        category_orders={"type": type_order},
        title="Score Distribution by Assessment Type (Violin + Box)",
        labels={"type": "Assessment Type", "score_pct": "Score %"},
    )
    fig_violin.update_layout(
        template="plotly_dark", height=480,
        margin=dict(l=0, r=0, t=50, b=0), font=dict(size=12),
        showlegend=False,
    )
    st.plotly_chart(fig_violin, use_container_width=True)

with col_v2:
    st.markdown("#### Volatility Ranking")
    st.markdown("_Ranked by standard deviation (σ) — higher = more spread_")
    st.markdown("")

    for _, row in type_stats.iterrows():
        t = row["Type"]
        color = color_map.get(t, "#888")
        bar_width = min(row["Std"] / type_stats["Std"].max() * 100, 100)
        st.markdown(f"""
        <div style="margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: baseline;">
                <span style="font-weight: 700; font-size: 16px; color: {color}; text-transform: capitalize;">{t}</span>
                <span style="font-size: 13px; color: #94a3b8;">μ = {row['Mean']:.1f}%&ensp;|&ensp;σ = {row['Std']:.1f}&ensp;|&ensp;n = {int(row['Count'])}</span>
            </div>
            <div style="background: #1e293b; border-radius: 6px; height: 10px; margin-top: 6px;">
                <div style="background: {color}; width: {bar_width}%; height: 100%; border-radius: 6px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e1b4b, #312e81); border-radius: 12px; padding: 16px; margin-top: 12px;">
        <p style="color: #fbbf24; font-weight: 700; margin-bottom: 4px;">⚡ Most Volatile: {most_volatile.title()}</p>
        <p style="color: #c7d2fe; font-size: 13px; margin: 0;">
            CoV = {type_stats.iloc[0]['CoV']:.1f}% — scores are most unpredictable here.
            Students need more support and clearer rubrics for this assessment type.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("")

# ── Ridgeline / overlapping histograms ──
st.subheader("Overlapping Score Distributions")

fig_hist = go.Figure()
for t in ["quiz", "assignment", "practical", "exam"]:
    subset = grades[grades["type"] == t]["score_pct"]
    fig_hist.add_trace(go.Histogram(
        x=subset, name=t.title(), opacity=0.6,
        marker_color=color_map.get(t, "#888"),
        nbinsx=30,
    ))

fig_hist.update_layout(
    template="plotly_dark", height=380,
    barmode="overlay",
    title="Overlapping Score Distributions by Assessment Type",
    xaxis_title="Score %", yaxis_title="Count",
    legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
    margin=dict(l=0, r=0, t=50, b=0), font=dict(size=12),
)
st.plotly_chart(fig_hist, use_container_width=True)

# ── Score trend over time by type ──
st.subheader("Average Score Trend Over Time by Assessment Type")

grades["month"] = grades["date"].dt.to_period("M").apply(lambda r: r.start_time)
monthly_type = grades.groupby(["month", "type"])["score_pct"].agg(["mean", "std"]).reset_index()
monthly_type.columns = ["month", "type", "mean_score", "std_score"]

fig_trend = px.line(
    monthly_type, x="month", y="mean_score", color="type",
    color_discrete_map=color_map,
    markers=True,
    title="Monthly Average Score by Assessment Type",
    labels={"month": "Month", "mean_score": "Avg Score %", "type": "Type"},
)
fig_trend.update_layout(
    template="plotly_dark", height=380,
    margin=dict(l=0, r=0, t=50, b=0), font=dict(size=12),
    legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
    hovermode="x unified",
)
st.plotly_chart(fig_trend, use_container_width=True)
st.caption("Track how each assessment type's average score evolves over the term. Diverging lines indicate growing difficulty gaps.")

st.divider()

# ═══════════════════════════════════════════════════════════════════
# KEY TAKEAWAYS
# ═══════════════════════════════════════════════════════════════════

st.header("📋 Key Takeaways")

col_t1, col_t2 = st.columns(2)

with col_t1:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #064e3b, #065f46); border-radius: 12px; padding: 20px;">
        <h4 style="color: #34d399; margin-bottom: 10px;">📅 Temporal Trends</h4>
        <ul style="color: #a7f3d0; font-size: 14px; line-height: 1.8;">
            <li>Attendance & engagement generally track together over the 6-month term</li>
            <li>Dip weeks (if any) often align with holidays, exam seasons, or Ramadan</li>
            <li>The heatmap reveals whether dips are group-specific or cohort-wide</li>
            <li>Proactive outreach during identified dip windows can mitigate dropout risk</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col_t2:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e1b4b, #312e81); border-radius: 12px; padding: 20px;">
        <h4 style="color: #a5b4fc; margin-bottom: 10px;">📊 Assessment Volatility</h4>
        <ul style="color: #c7d2fe; font-size: 14px; line-height: 1.8;">
            <li><strong>{most_volatile.title()}</strong> shows the highest score volatility (σ = {type_stats.iloc[0]['Std']:.1f})</li>
            <li><strong>{least_volatile.title()}</strong> is the most consistent (σ = {type_stats.iloc[-1]['Std']:.1f})</li>
            <li>High volatility suggests unclear expectations or inconsistent difficulty</li>
            <li>Consider standardising rubrics for the most volatile type</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.markdown("")

# ── Save UI ──
render_save_ui(
    "temporal_assessment",
    "Temporal & Assessment data",
    dataframe_to_dict(type_stats),
)
