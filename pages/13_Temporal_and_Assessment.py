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

att_raw = load_attendance()
eng_raw = load_engagement()
grades = load_grades()

# ── Filter to the specific 6-month term: Dec 2025 → May 2026 ──
TERM_START = pd.Timestamp("2025-12-01")
TERM_END = pd.Timestamp("2026-05-31 23:59:59")

att = att_raw[(att_raw["session_datetime"] >= TERM_START) & (att_raw["session_datetime"] <= TERM_END)].copy()
eng = eng_raw[(eng_raw["event_datetime"] >= TERM_START) & (eng_raw["event_datetime"] <= TERM_END)].copy()

# Month labels for the 6-month term
MONTH_LABELS = {12: "Dec 2025", 1: "Jan 2026", 2: "Feb 2026", 3: "Mar 2026", 4: "Apr 2026", 5: "May 2026"}

# ═══════════════════════════════════════════════════════════════════
# SECTION 1 — Attendance & Engagement Over the 6-Month Term
# ═══════════════════════════════════════════════════════════════════

st.title("📉 Temporal Trends & Assessment Analysis")
st.markdown("##### Tracking cohort-wide participation and score volatility across the Dec 2025 → May 2026 term")
st.divider()

st.header("Q1: Attendance & Engagement Over the 6-Month Term")
st.markdown("_Dec 2025 → May 2026 · Is there a window where the whole cohort dips at once?_")

# ── Monthly aggregation (cleaner than weekly for 6 months) ──
att["month"] = att["session_datetime"].dt.to_period("M").apply(lambda r: r.start_time)
att_monthly = (
    att.groupby("month")
    .apply(lambda g: pd.Series({
        "attended": (g["status"] == "attended").sum(),
        "total": len(g),
        "rate": (g["status"] == "attended").mean() * 100,
        "unique_students": g["student_id"].nunique(),
    }))
    .reset_index()
    .sort_values("month")
)
att_monthly["month_label"] = att_monthly["month"].dt.strftime("%b %Y")

eng["month"] = eng["event_datetime"].dt.to_period("M").apply(lambda r: r.start_time)
eng_monthly = (
    eng.groupby("month")
    .agg(total_events=("event_id", "count"), unique_students=("student_id", "nunique"))
    .reset_index()
    .sort_values("month")
)
eng_monthly["events_per_student"] = eng_monthly["total_events"] / eng_monthly["unique_students"]
eng_monthly["month_label"] = eng_monthly["month"].dt.strftime("%b %Y")

# ── Also compute weekly for detailed chart ──
att["week"] = att["session_datetime"].dt.to_period("W").apply(lambda r: r.start_time)
att_weekly = (
    att.groupby("week")
    .apply(lambda g: pd.Series({
        "rate": (g["status"] == "attended").mean() * 100,
        "unique_students": g["student_id"].nunique(),
    }))
    .reset_index()
    .sort_values("week")
)
att_weekly["rolling_mean"] = att_weekly["rate"].rolling(4, min_periods=2, center=True).mean()
att_weekly["rolling_std"] = att_weekly["rate"].rolling(4, min_periods=2, center=True).std()
att_weekly["is_dip"] = att_weekly["rate"] < (att_weekly["rolling_mean"] - att_weekly["rolling_std"])
dip_weeks = att_weekly[att_weekly["is_dip"]]

eng["week"] = eng["event_datetime"].dt.to_period("W").apply(lambda r: r.start_time)
eng_weekly = (
    eng.groupby("week")
    .agg(total_events=("event_id", "count"), unique_students=("student_id", "nunique"))
    .reset_index()
    .sort_values("week")
)
eng_weekly["events_per_student"] = eng_weekly["total_events"] / eng_weekly["unique_students"]

# ── KPI metrics ──
overall_att_rate = (att["status"] == "attended").mean() * 100
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("Term Attendance Rate", f"{overall_att_rate:.1f}%")
col_m2.metric("Total Events (6 mo)", f"{len(eng):,}")
col_m3.metric("Attendance Dip Weeks", f"{len(dip_weeks)}")
lowest_month = att_monthly.loc[att_monthly["rate"].idxmin()]
col_m4.metric("Weakest Month", lowest_month["month_label"], f"{lowest_month['rate']:.1f}%")

st.markdown("")

# ── CHART 1: Monthly attendance bar + engagement line (separated, clear) ──
st.subheader("📊 Monthly Attendance Rate & Engagement Events")

fig1 = make_subplots(specs=[[{"secondary_y": True}]])

# Attendance as colored bars — green for above avg, orange/red for below
avg_rate = att_monthly["rate"].mean()
bar_colors = ["#10b981" if r >= avg_rate else "#ef4444" for r in att_monthly["rate"]]

fig1.add_trace(
    go.Bar(
        x=att_monthly["month_label"], y=att_monthly["rate"],
        name="Attendance Rate %",
        marker_color=bar_colors,
        text=[f"{r:.1f}%" for r in att_monthly["rate"]],
        textposition="outside", textfont=dict(size=13, color="white"),
        opacity=0.85,
    ),
    secondary_y=False,
)

# Avg line
fig1.add_hline(
    y=avg_rate, line_dash="dot", line_color="#fbbf24", line_width=2,
    annotation_text=f"Avg: {avg_rate:.1f}%", annotation_position="top left",
    annotation_font_color="#fbbf24", secondary_y=False,
)

# Engagement as line on secondary axis
fig1.add_trace(
    go.Scatter(
        x=eng_monthly["month_label"], y=eng_monthly["events_per_student"],
        name="Engagement / Student",
        mode="lines+markers+text",
        line=dict(color="#6366f1", width=3),
        marker=dict(size=10, color="#6366f1", line=dict(width=2, color="white")),
        text=[f"{v:.1f}" for v in eng_monthly["events_per_student"]],
        textposition="top center", textfont=dict(size=11, color="#a5b4fc"),
    ),
    secondary_y=True,
)

fig1.update_layout(
    template="plotly_dark", height=420,
    title=dict(text="Attendance vs Engagement — Month by Month (Dec 2025 → May 2026)", font=dict(size=16)),
    legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center", font=dict(size=12)),
    margin=dict(l=10, r=10, t=60, b=10), font=dict(size=12),
    bargap=0.35,
)
fig1.update_yaxes(title_text="Attendance Rate %", range=[0, 110], secondary_y=False)
fig1.update_yaxes(title_text="Events per Student", secondary_y=True)
fig1.update_xaxes(title_text="")

st.plotly_chart(fig1, use_container_width=True)
st.caption("🟢 Green bars = above average attendance · 🔴 Red bars = below average · 🟣 Purple line = engagement per student")

st.markdown("")

# ── CHART 2: Weekly detail (area chart, easier to read) ──
st.subheader("📈 Weekly Attendance Detail (with Dip Detection)")

fig2 = go.Figure()

# Area fill for attendance
fig2.add_trace(go.Scatter(
    x=att_weekly["week"], y=att_weekly["rate"],
    name="Weekly Attendance %", mode="lines",
    line=dict(color="#6366f1", width=2),
    fill="tozeroy", fillcolor="rgba(99,102,241,0.15)",
    hovertemplate="Week of %{x|%b %d, %Y}<br>Attendance: %{y:.1f}%<extra></extra>",
))

# Rolling average
fig2.add_trace(go.Scatter(
    x=att_weekly["week"], y=att_weekly["rolling_mean"],
    name="4-Week Trend", mode="lines",
    line=dict(color="#fbbf24", width=2, dash="dash"),
))

# Dip markers
if not dip_weeks.empty:
    fig2.add_trace(go.Scatter(
        x=dip_weeks["week"], y=dip_weeks["rate"],
        name="⚠ Dip Detected", mode="markers",
        marker=dict(size=14, color="#ef4444", symbol="diamond", line=dict(width=2, color="white")),
        hovertemplate="⚠ DIP: %{x|%b %d}<br>Rate: %{y:.1f}%<extra></extra>",
    ))

# Month separator annotations
for m_start in pd.date_range(TERM_START, TERM_END, freq="MS"):
    fig2.add_vline(x=m_start, line_dash="dot", line_color="rgba(255,255,255,0.15)", line_width=1)
    fig2.add_annotation(x=m_start + pd.Timedelta(days=15), y=103,
                        text=m_start.strftime("%b"), showarrow=False,
                        font=dict(size=11, color="#94a3b8"))

fig2.update_layout(
    template="plotly_dark", height=380,
    title=dict(text="Weekly Attendance Rate — Dec 2025 to May 2026", font=dict(size=15)),
    legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
    margin=dict(l=10, r=10, t=50, b=10), font=dict(size=12),
    xaxis=dict(tickformat="%b %d", title=""),
    yaxis=dict(title="Attendance %", range=[0, 110]),
)
st.plotly_chart(fig2, use_container_width=True)

# ── Dip analysis callout ──
if not dip_weeks.empty:
    worst_dip = dip_weeks.loc[dip_weeks["rate"].idxmin()]
    dip_date = worst_dip["week"]
    dip_rate = worst_dip["rate"]

    col_i1, col_i2 = st.columns([2, 1])
    with col_i1:
        st.error(f"""
        **🔍 Cohort-Wide Dip Detected — Week of {dip_date.strftime('%b %d, %Y')}**

        Attendance dropped to **{dip_rate:.1f}%** — significantly below the 4-week rolling trend.
        This indicates a cohort-wide disengagement event during this window.
        """)
    with col_i2:
        st.info(f"""
        **🗓 All Dip Weeks ({len(dip_weeks)}):**

        {chr(10).join([f"• {w.strftime('%b %d')} — {r:.1f}%" for w, r in zip(dip_weeks['week'], dip_weeks['rate'])])}
        """)

    st.markdown("---")
    st.subheader("🧐 What Could Explain the Cohort-Wide Dip?")

    dip_month_num = dip_date.month
    if dip_month_num in [12, 1]:
        explanations = [
            ("🎄 Holiday Season / Post-Holiday", "Winter holidays and New Year cause travel and slow re-engagement."),
            ("🤒 Seasonal Illness", "Winter flu season commonly reduces attendance across entire cohorts."),
            ("📅 Term-Start Lag", "Early weeks of a new term see lower attendance as students settle in."),
        ]
    elif dip_month_num in [2]:
        explanations = [
            ("📝 Early Assessments", "First assignments/quizzes may cause stress-related absences."),
            ("😓 Adjustment Period", "Students still adapting to the course pace and workload."),
            ("🏥 Illness Wave", "Late-winter illness patterns can affect attendance broadly."),
        ]
    elif dip_month_num in [3, 4]:
        explanations = [
            ("🌙 Ramadan / Religious Holidays", "Fasting month significantly alters daily routines and attendance."),
            ("📊 Mid-Term Exam Prep", "Students skip sessions to self-study for upcoming midterms."),
            ("🏖 Spring Break", "A scheduled or informal break period where students disengage."),
        ]
    else:
        explanations = [
            ("📝 Final Exam Period", "Students shift focus to exam prep, skipping regular sessions."),
            ("😓 End-of-Term Fatigue", "6 months of coursework leads to burnout and motivation decline."),
            ("🎓 Early Completion", "Some students already met requirements and stop attending."),
        ]

    cols = st.columns(len(explanations))
    for i, (title, desc) in enumerate(explanations):
        with cols[i]:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1e1b4b, #312e81); border-radius: 12px; padding: 20px; min-height: 160px;">
                <h4 style="color: #a5b4fc; margin-bottom: 8px;">{title}</h4>
                <p style="color: #c7d2fe; font-size: 14px; line-height: 1.5;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)
else:
    st.success("✅ No significant cohort-wide attendance dips detected — participation was consistent throughout the 6-month term.")

st.markdown("")

# ── Heatmap: per-group monthly attendance ──
st.subheader("Monthly Attendance Heatmap by Group")

att_group_month = (
    att.groupby(["group_id", "month"])
    .apply(lambda g: (g["status"] == "attended").mean() * 100)
    .reset_index(name="rate")
)
att_group_month["month_label"] = att_group_month["month"].dt.strftime("%b %Y")

pivot = att_group_month.pivot(index="group_id", columns="month_label", values="rate")
month_order = att_group_month.drop_duplicates("month").sort_values("month")["month_label"].tolist()
pivot = pivot.reindex(columns=month_order)

fig_heat = px.imshow(
    pivot.values,
    labels=dict(x="Month", y="Group", color="Attendance %"),
    x=pivot.columns.tolist(), y=pivot.index.tolist(),
    color_continuous_scale="RdYlGn", aspect="auto",
    title="Attendance Rate by Group × Month (red = low, green = high)",
)
fig_heat.update_layout(
    template="plotly_dark", height=350,
    margin=dict(l=0, r=0, t=50, b=0), font=dict(size=12),
)
st.plotly_chart(fig_heat, use_container_width=True)
st.caption("A full red column means ALL groups dipped that month (cohort-wide event). Isolated red cells = group-specific issues.")

st.divider()

# ═══════════════════════════════════════════════════════════════════
# SECTION 2 — Score Distribution by Assessment Type
# ═══════════════════════════════════════════════════════════════════

st.header("Q2: Score Distribution by Assessment Type")
st.markdown("_Where is performance most volatile?_")

grades["score_pct"] = (grades["score"] / grades["max_score"]) * 100

type_stats = grades.groupby("type")["score_pct"].agg(["mean", "std", "count"]).reset_index()
type_stats.columns = ["Type", "Mean", "Std", "Count"]
type_stats = type_stats.sort_values("Std", ascending=False)
type_stats["CoV"] = (type_stats["Std"] / type_stats["Mean"]) * 100

most_volatile = type_stats.iloc[0]["Type"]
least_volatile = type_stats.iloc[-1]["Type"]

col_k1, col_k2, col_k3, col_k4 = st.columns(4)
col_k1.metric("Total Assessments", f"{len(grades):,}")
col_k2.metric("Assessment Types", f"{grades['type'].nunique()}")
col_k3.metric("Most Volatile", f"{most_volatile.title()}", f"σ = {type_stats.iloc[0]['Std']:.1f}")
col_k4.metric("Most Consistent", f"{least_volatile.title()}", f"σ = {type_stats.iloc[-1]['Std']:.1f}")

st.markdown("")

col_v1, col_v2 = st.columns([3, 2])

color_map = {"quiz": "#6366f1", "assignment": "#14b8a6", "practical": "#f59e0b", "exam": "#ef4444"}

with col_v1:
    type_order = type_stats.sort_values("Mean")["Type"].tolist()
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

# ── Overlapping histograms ──
st.subheader("Overlapping Score Distributions")

fig_hist = go.Figure()
for t in ["quiz", "assignment", "practical", "exam"]:
    subset = grades[grades["type"] == t]["score_pct"]
    fig_hist.add_trace(go.Histogram(
        x=subset, name=t.title(), opacity=0.6,
        marker_color=color_map.get(t, "#888"), nbinsx=30,
    ))

fig_hist.update_layout(
    template="plotly_dark", height=380, barmode="overlay",
    title="Overlapping Score Distributions by Assessment Type",
    xaxis_title="Score %", yaxis_title="Count",
    legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
    margin=dict(l=0, r=0, t=50, b=0), font=dict(size=12),
)
st.plotly_chart(fig_hist, use_container_width=True)

# ── Score trend over time by type ──
st.subheader("Average Score Trend Over Time by Assessment Type")

grades["g_month"] = grades["date"].dt.to_period("M").apply(lambda r: r.start_time)
monthly_type = grades.groupby(["g_month", "type"])["score_pct"].agg(["mean", "std"]).reset_index()
monthly_type.columns = ["month", "type", "mean_score", "std_score"]

fig_trend = px.line(
    monthly_type, x="month", y="mean_score", color="type",
    color_discrete_map=color_map, markers=True,
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
        <h4 style="color: #34d399; margin-bottom: 10px;">📅 Temporal Trends (Dec 2025 → May 2026)</h4>
        <ul style="color: #a7f3d0; font-size: 14px; line-height: 1.8;">
            <li>Attendance & engagement generally track together over the 6-month term</li>
            <li>Dip weeks often align with holidays, exam seasons, or Ramadan</li>
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

render_save_ui("temporal_assessment", "Temporal & Assessment data", dataframe_to_dict(type_stats))
