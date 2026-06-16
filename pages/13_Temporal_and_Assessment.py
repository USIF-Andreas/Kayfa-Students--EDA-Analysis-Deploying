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

# ── Specific 6 months: Dec 2025 → May 2026 ──
TERM_START = pd.Timestamp("2025-12-01")
TERM_END = pd.Timestamp("2026-05-31 23:59:59")
TERM_LABEL = "Dec 2025 → May 2026"

att = att_raw[(att_raw["session_datetime"] >= TERM_START) & (att_raw["session_datetime"] <= TERM_END)].copy()
eng = eng_raw[(eng_raw["event_datetime"] >= TERM_START) & (eng_raw["event_datetime"] <= TERM_END)].copy()

# ═══════════════════════════════════════════════════
# SECTION 1 — Engagement & Attendance Over the Term
# ═══════════════════════════════════════════════════

st.title("📉 Temporal Trends & Assessment Analysis")
st.markdown(f"##### Tracking participation and scores across the {TERM_LABEL} term")
st.divider()

st.header("Q9: Engagement & Attendance Over the 6-Month Term")
st.markdown(f"_{TERM_LABEL} · Is there a window where the whole cohort dips at once?_")

# ── NOTE: Attendance data only covers December 2025 ──
# ── Engagement data covers all 6 months — used as primary participation metric ──

# ── Monthly engagement aggregation (full 6 months) ──
eng["month"] = eng["event_datetime"].dt.to_period("M").apply(lambda r: r.start_time)
eng_monthly = (
    eng.groupby("month")
    .agg(total_events=("event_id", "count"), unique_students=("student_id", "nunique"))
    .reset_index().sort_values("month")
)
eng_monthly["events_per_student"] = eng_monthly["total_events"] / eng_monthly["unique_students"]
eng_monthly["month_label"] = eng_monthly["month"].dt.strftime("%b %Y")

# ── Weekly engagement for detail chart ──
eng["week"] = eng["event_datetime"].dt.to_period("W").apply(lambda r: r.start_time)
eng_weekly = (
    eng.groupby("week")
    .agg(total_events=("event_id", "count"), unique_students=("student_id", "nunique"))
    .reset_index().sort_values("week")
)
eng_weekly["events_per_student"] = eng_weekly["total_events"] / eng_weekly["unique_students"]
eng_weekly["rolling_mean"] = eng_weekly["events_per_student"].rolling(4, min_periods=2, center=True).mean()
eng_weekly["rolling_std"] = eng_weekly["events_per_student"].rolling(4, min_periods=2, center=True).std()
eng_weekly["is_dip"] = eng_weekly["events_per_student"] < (eng_weekly["rolling_mean"] - eng_weekly["rolling_std"])
dip_weeks = eng_weekly[eng_weekly["is_dip"]]

# ── Attendance (December only) ──
att["month"] = att["session_datetime"].dt.to_period("M").apply(lambda r: r.start_time)
att["is_attended"] = (att["status"] == "attended").astype(int)
overall_att_rate = (att["status"] == "attended").mean() * 100 if len(att) > 0 else 0

# ── Detect weakest engagement month ──
weakest_eng = eng_monthly.loc[eng_monthly["events_per_student"].idxmin()]
avg_eng = eng_monthly["events_per_student"].mean()

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

# ── CHART 2: Weekly engagement detail ──
st.subheader("📈 Weekly Engagement Detail (with Dip Detection)")

fig2 = go.Figure()
fig2.add_trace(go.Scatter(
    x=eng_weekly["week"], y=eng_weekly["events_per_student"],
    name="Weekly Engagement", mode="lines",
    line=dict(color="#6366f1", width=2),
    fill="tozeroy", fillcolor="rgba(99,102,241,0.15)",
    hovertemplate="Week of %{x|%b %d, %Y}<br>Events/Student: %{y:.1f}<extra></extra>",
))
fig2.add_trace(go.Scatter(
    x=eng_weekly["week"], y=eng_weekly["rolling_mean"],
    name="4-Week Trend", mode="lines",
    line=dict(color="#fbbf24", width=2, dash="dash"),
))
if not dip_weeks.empty:
    fig2.add_trace(go.Scatter(
        x=dip_weeks["week"], y=dip_weeks["events_per_student"],
        name="⚠ Dip Detected", mode="markers",
        marker=dict(size=14, color="#ef4444", symbol="diamond", line=dict(width=2, color="white")),
        hovertemplate="⚠ DIP: %{x|%b %d}<br>Events/Student: %{y:.1f}<extra></extra>",
    ))

for m_start in pd.date_range(TERM_START, TERM_END, freq="MS"):
    fig2.add_vline(x=m_start, line_dash="dot", line_color="rgba(255,255,255,0.15)")
    fig2.add_annotation(x=m_start + pd.Timedelta(days=15), y=eng_weekly["events_per_student"].max() * 1.05,
                        text=m_start.strftime("%b"), showarrow=False,
                        font=dict(size=11, color="#94a3b8"))

fig2.update_layout(
    template="plotly_dark", height=380,
    title=dict(text=f"Weekly Engagement — {TERM_LABEL}", font=dict(size=15)),
    legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
    margin=dict(l=10, r=10, t=50, b=10),
    xaxis=dict(tickformat="%b %d", title=""),
    yaxis=dict(title="Events per Student"),
)
st.plotly_chart(fig2, use_container_width=True)

# ── Dip callout ──
if not dip_weeks.empty:
    worst = dip_weeks.loc[dip_weeks["events_per_student"].idxmin()]
    st.error(f"""
    **🔍 Cohort-Wide Dip — Week of {worst['week'].strftime('%b %d, %Y')}**
    
    Engagement dropped to **{worst['events_per_student']:.1f} events/student**, well below the trend.
    """)

    st.subheader("🧐 What Could Explain It?")
    m = worst["week"].month
    if m in [12, 1, 2]:
        exps = [("🎄 Holiday Season", "Winter holidays and New Year reduce student activity."),
                ("🤒 Winter Illness", "Flu season hits engagement across the board."),
                ("📝 Early Assessments", "First quizzes cause stress and less platform use.")]
    elif m in [3, 4]:
        exps = [("🌙 Ramadan", "Fasting alters daily routines, reducing online activity."),
                ("📊 Midterm Prep", "Students focus on studying rather than platform activities."),
                ("🏖 Spring Break", "Scheduled break lowers participation across the board.")]
    else:
        exps = [("📝 Finals Period", "Students shift focus to exam prep."),
                ("😓 End-of-Term Fatigue", "6 months of work causes burnout."),
                ("🎓 Early Finishers", "Some students already met requirements.")]

    cols = st.columns(3)
    for i, (title, desc) in enumerate(exps):
        with cols[i]:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1e1b4b, #312e81); border-radius: 12px; padding: 20px; min-height: 140px;">
                <h4 style="color: #a5b4fc; margin-bottom: 8px;">{title}</h4>
                <p style="color: #c7d2fe; font-size: 14px;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)
else:
    st.success("✅ No significant dips detected — consistent engagement throughout the term.")

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

# ═══════════════════════════════════════════════════
# SECTION 2 — Score Distribution (plain language)
# ═══════════════════════════════════════════════════

st.header("Q2: How Do Students Score on Each Assessment Type?")
st.markdown("_Quizzes, Assignments, Practicals, and Exams — where do students struggle most?_")

grades["score_pct"] = (grades["score"] / grades["max_score"]) * 100
color_map = {"quiz": "#6366f1", "assignment": "#14b8a6", "practical": "#f59e0b", "exam": "#ef4444"}

# Simple stats in plain language
type_stats = grades.groupby("type")["score_pct"].agg(
    avg_score="mean", lowest="min", highest="max", total="count",
    median_score="median"
).reset_index()
type_stats["spread"] = type_stats["highest"] - type_stats["lowest"]
type_stats = type_stats.sort_values("avg_score", ascending=False)

most_unpredictable = type_stats.sort_values("spread", ascending=False).iloc[0]["type"]
most_consistent = type_stats.sort_values("spread").iloc[0]["type"]

# KPIs — plain language
col_k1, col_k2, col_k3, col_k4 = st.columns(4)
col_k1.metric("Total Scores Recorded", f"{len(grades):,}")
col_k2.metric("Assessment Types", "4")
col_k3.metric("Widest Score Range", most_unpredictable.title(), "Most unpredictable")
col_k4.metric("Tightest Score Range", most_consistent.title(), "Most consistent")

st.markdown("")

# ── Type cards: plain English summary ──
st.subheader("📋 How Each Type Performs")

type_cols = st.columns(4)
type_order_display = ["quiz", "assignment", "practical", "exam"]
emoji_map = {"quiz": "📝", "assignment": "📄", "practical": "🔧", "exam": "🎓"}

for i, t in enumerate(type_order_display):
    row = type_stats[type_stats["type"] == t]
    if len(row) == 0:
        continue
    row = row.iloc[0]
    color = color_map[t]
    avg = row["avg_score"]
    med = row["median_score"]
    lo = row["lowest"]
    hi = row["highest"]
    n = int(row["total"])

    if avg >= 75:
        verdict = "Students do well here overall"
        v_color = "#34d399"
    elif avg >= 55:
        verdict = "Moderate — room for improvement"
        v_color = "#fbbf24"
    else:
        verdict = "Students struggle here"
        v_color = "#f87171"

    with type_cols[i]:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0f172a, #1e293b); border: 1px solid {color}44; border-radius: 14px; padding: 20px; text-align: center;">
            <p style="font-size: 28px; margin: 0;">{emoji_map[t]}</p>
            <h3 style="color: {color}; margin: 4px 0; text-transform: capitalize;">{t}</h3>
            <p style="font-size: 36px; font-weight: 800; color: white; margin: 8px 0;">{avg:.0f}%</p>
            <p style="color: #94a3b8; font-size: 13px; margin: 2px 0;">Average score</p>
            <hr style="border-color: {color}33; margin: 12px 0;">
            <p style="color: #cbd5e1; font-size: 13px; margin: 4px 0;">📊 Typical student gets <b>{med:.0f}%</b></p>
            <p style="color: #cbd5e1; font-size: 13px; margin: 4px 0;">📉 Lowest: <b>{lo:.0f}%</b> · Highest: <b>{hi:.0f}%</b></p>
            <p style="color: #cbd5e1; font-size: 13px; margin: 4px 0;">📁 {n} scores recorded</p>
            <hr style="border-color: {color}33; margin: 12px 0;">
            <p style="color: {v_color}; font-weight: 700; font-size: 13px; margin: 0;">{verdict}</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("")

# ── Box plot (simple, no violin) ──
st.subheader("📊 Score Spread — Where Are Results Most Unpredictable?")
st.markdown("_The wider the box, the more scores jump around. A narrow box means students score similarly._")

fig_box = px.box(
    grades, x="type", y="score_pct", color="type",
    color_discrete_map=color_map,
    category_orders={"type": type_order_display},
    title="Score Range by Assessment Type",
    labels={"type": "Assessment Type", "score_pct": "Score %"},
)
fig_box.update_layout(
    template="plotly_dark", height=450,
    margin=dict(l=0, r=0, t=50, b=0), font=dict(size=12),
    showlegend=False,
)
st.plotly_chart(fig_box, use_container_width=True)

# Plain explanation
st.markdown(f"""
<div style="background: linear-gradient(135deg, #1e1b4b, #312e81); border-radius: 12px; padding: 20px; margin-top: 8px;">
    <h4 style="color: #fbbf24; margin-bottom: 8px;">🔍 How to Read This Chart</h4>
    <ul style="color: #c7d2fe; font-size: 14px; line-height: 2;">
        <li>The <b>box</b> shows where most students scored (middle 50%)</li>
        <li>The <b>line inside the box</b> is the typical (median) score</li>
        <li>The <b>dots outside</b> are unusually high or low scores</li>
        <li>A <b>tall box = unpredictable</b> results (students score very differently)</li>
        <li>A <b>short box = consistent</b> results (students score similarly)</li>
    </ul>
    <p style="color: #a5b4fc; font-size: 14px; margin-top: 12px;">
        👉 <b>{most_unpredictable.title()}</b> has the widest range — students' scores vary the most here.
        This could mean the difficulty is inconsistent, or students need more preparation.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("")

# ── Score trend over time ──
st.subheader("📈 How Scores Change Over the Term")
st.markdown("_Are students improving month by month, or declining?_")

grades["g_month"] = grades["date"].dt.to_period("M").apply(lambda r: r.start_time)
monthly_type = grades.groupby(["g_month", "type"])["score_pct"].mean().reset_index()
monthly_type.columns = ["month", "type", "avg_score"]

fig_trend = px.line(
    monthly_type, x="month", y="avg_score", color="type",
    color_discrete_map=color_map, markers=True,
    title="Average Score by Month & Assessment Type",
    labels={"month": "Month", "avg_score": "Average Score %", "type": "Type"},
)
fig_trend.update_layout(
    template="plotly_dark", height=380,
    margin=dict(l=0, r=0, t=50, b=0), font=dict(size=12),
    legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
    hovermode="x unified",
)
st.plotly_chart(fig_trend, use_container_width=True)
st.caption("If lines go up → students are improving. If lines go down → the material is getting harder or students are losing momentum.")

st.divider()

# ═══════════════════════════════════════════════════
# KEY TAKEAWAYS
# ═══════════════════════════════════════════════════

st.header("📋 Key Takeaways")
col_t1, col_t2 = st.columns(2)

with col_t1:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #064e3b, #065f46); border-radius: 12px; padding: 20px;">
        <h4 style="color: #34d399; margin-bottom: 10px;">📅 Attendance Trends ({TERM_LABEL})</h4>
        <ul style="color: #a7f3d0; font-size: 14px; line-height: 1.8;">
            <li>Attendance and engagement generally rise and fall together</li>
            <li>Dip weeks often align with holidays, exam seasons, or Ramadan</li>
            <li>The heatmap shows whether dips hit all groups or just some</li>
            <li>Reaching out to students during dip windows can prevent dropouts</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col_t2:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e1b4b, #312e81); border-radius: 12px; padding: 20px;">
        <h4 style="color: #a5b4fc; margin-bottom: 10px;">📊 Assessment Scores</h4>
        <ul style="color: #c7d2fe; font-size: 14px; line-height: 1.8;">
            <li><b>{most_unpredictable.title()}</b> scores vary the most — students need more support here</li>
            <li><b>{most_consistent.title()}</b> scores are the most consistent across students</li>
            <li>Wide score ranges suggest unclear expectations or uneven difficulty</li>
            <li>Clearer rubrics and practice materials can help reduce gaps</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.markdown("")
render_save_ui("temporal_assessment", "Temporal & Assessment data", dataframe_to_dict(type_stats))
