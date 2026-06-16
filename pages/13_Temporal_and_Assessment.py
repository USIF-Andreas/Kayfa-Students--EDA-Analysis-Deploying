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

# ── Specific 6 months: Jan 2026 → Jun 2026 ──
TERM_START = pd.Timestamp("2026-01-01")
TERM_END = pd.Timestamp("2026-06-30 23:59:59")
TERM_LABEL = "Jan 2026 → Jun 2026"

att = att_raw[(att_raw["session_datetime"] >= TERM_START) & (att_raw["session_datetime"] <= TERM_END)].copy()
eng = eng_raw[(eng_raw["event_datetime"] >= TERM_START) & (eng_raw["event_datetime"] <= TERM_END)].copy()

# ═══════════════════════════════════════════════════
# SECTION 1 — Attendance & Engagement
# ═══════════════════════════════════════════════════

st.title("📉 Temporal Trends & Assessment Analysis")
st.markdown(f"##### Tracking participation and scores across the {TERM_LABEL} term")
st.divider()

st.header("Q1: Attendance & Engagement Over the 6-Month Term")
st.markdown(f"_{TERM_LABEL} · Is there a window where the whole cohort dips at once?_")

# ── Monthly aggregation ──
att["month"] = att["session_datetime"].dt.to_period("M").apply(lambda r: r.start_time)
att_monthly = (
    att.groupby("month")
    .apply(lambda g: pd.Series({
        "attended": (g["status"] == "attended").sum(),
        "total": len(g),
        "rate": (g["status"] == "attended").mean() * 100,
        "unique_students": g["student_id"].nunique(),
    }))
    .reset_index().sort_values("month")
)
att_monthly["month_label"] = att_monthly["month"].dt.strftime("%b %Y")

eng["month"] = eng["event_datetime"].dt.to_period("M").apply(lambda r: r.start_time)
eng_monthly = (
    eng.groupby("month")
    .agg(total_events=("event_id", "count"), unique_students=("student_id", "nunique"))
    .reset_index().sort_values("month")
)
eng_monthly["events_per_student"] = eng_monthly["total_events"] / eng_monthly["unique_students"]
eng_monthly["month_label"] = eng_monthly["month"].dt.strftime("%b %Y")

# Weekly for detail chart
att["week"] = att["session_datetime"].dt.to_period("W").apply(lambda r: r.start_time)
att_weekly = (
    att.groupby("week")
    .apply(lambda g: pd.Series({
        "rate": (g["status"] == "attended").mean() * 100,
        "unique_students": g["student_id"].nunique(),
    }))
    .reset_index().sort_values("week")
)
att_weekly["rolling_mean"] = att_weekly["rate"].rolling(4, min_periods=2, center=True).mean()
att_weekly["rolling_std"] = att_weekly["rate"].rolling(4, min_periods=2, center=True).std()
att_weekly["is_dip"] = att_weekly["rate"] < (att_weekly["rolling_mean"] - att_weekly["rolling_std"])
dip_weeks = att_weekly[att_weekly["is_dip"]]

# KPIs
overall_att_rate = (att["status"] == "attended").mean() * 100 if len(att) > 0 else 0
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("Term Attendance Rate", f"{overall_att_rate:.1f}%")
col_m2.metric("Total Events (6 mo)", f"{len(eng):,}")
col_m3.metric("Weeks With Dips", f"{len(dip_weeks)}")
if len(att_monthly) > 0:
    lowest_month = att_monthly.loc[att_monthly["rate"].idxmin()]
    col_m4.metric("Weakest Month", lowest_month["month_label"], f"{lowest_month['rate']:.1f}%")

st.markdown("")

# ── CHART 1: Monthly attendance bars + engagement line ──
st.subheader("📊 Monthly Attendance & Engagement")

if len(att_monthly) > 0:
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])
    avg_rate = att_monthly["rate"].mean()
    bar_colors = ["#10b981" if r >= avg_rate else "#ef4444" for r in att_monthly["rate"]]

    fig1.add_trace(go.Bar(
        x=att_monthly["month_label"], y=att_monthly["rate"],
        name="Attendance %", marker_color=bar_colors,
        text=[f"{r:.1f}%" for r in att_monthly["rate"]],
        textposition="outside", textfont=dict(size=13, color="white"), opacity=0.85,
    ), secondary_y=False)

    fig1.add_hline(y=avg_rate, line_dash="dot", line_color="#fbbf24", line_width=2,
                   annotation_text=f"Avg: {avg_rate:.1f}%", annotation_position="top left",
                   annotation_font_color="#fbbf24", secondary_y=False)

    if len(eng_monthly) > 0:
        fig1.add_trace(go.Scatter(
            x=eng_monthly["month_label"], y=eng_monthly["events_per_student"],
            name="Engagement / Student", mode="lines+markers+text",
            line=dict(color="#6366f1", width=3),
            marker=dict(size=10, color="#6366f1", line=dict(width=2, color="white")),
            text=[f"{v:.1f}" for v in eng_monthly["events_per_student"]],
            textposition="top center", textfont=dict(size=11, color="#a5b4fc"),
        ), secondary_y=True)

    fig1.update_layout(
        template="plotly_dark", height=420,
        title=dict(text=f"Attendance vs Engagement — Month by Month ({TERM_LABEL})", font=dict(size=16)),
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
        margin=dict(l=10, r=10, t=60, b=10), font=dict(size=12), bargap=0.35,
    )
    fig1.update_yaxes(title_text="Attendance %", range=[0, 110], secondary_y=False)
    fig1.update_yaxes(title_text="Events per Student", secondary_y=True)
    st.plotly_chart(fig1, use_container_width=True)
    st.caption("🟢 Green = above average · 🔴 Red = below average · 🟣 Purple line = engagement per student")

    # ── Per-month attendance breakdown cards ──
    st.markdown("")
    st.subheader("📅 Attendance Breakdown — Each Month")

    month_cols = st.columns(min(len(att_monthly), 6))
    for i, (_, row) in enumerate(att_monthly.iterrows()):
        col_idx = i % len(month_cols)
        rate = row["rate"]
        attended = int(row["attended"])
        total = int(row["total"])
        students = int(row["unique_students"])
        if rate >= 80:
            bg = "linear-gradient(135deg, #064e3b, #065f46)"
            emoji = "✅"
        elif rate >= 60:
            bg = "linear-gradient(135deg, #78350f, #92400e)"
            emoji = "⚠️"
        else:
            bg = "linear-gradient(135deg, #7f1d1d, #991b1b)"
            emoji = "🔴"

        with month_cols[col_idx]:
            st.markdown(f"""
            <div style="background: {bg}; border-radius: 12px; padding: 16px; text-align: center; margin-bottom: 8px;">
                <h3 style="color: white; margin: 0;">{row['month_label']}</h3>
                <p style="font-size: 32px; font-weight: 800; color: white; margin: 8px 0;">{emoji} {rate:.0f}%</p>
                <p style="color: #d1d5db; font-size: 13px; margin: 0;">{attended} of {total} sessions attended</p>
                <p style="color: #9ca3af; font-size: 12px; margin: 2px 0;">{students} active students</p>
            </div>
            """, unsafe_allow_html=True)

st.markdown("")

# ── CHART 2: Weekly detail ──
st.subheader("📈 Weekly Attendance Detail")

if len(att_weekly) > 0:
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=att_weekly["week"], y=att_weekly["rate"],
        name="Weekly Attendance %", mode="lines",
        line=dict(color="#6366f1", width=2),
        fill="tozeroy", fillcolor="rgba(99,102,241,0.15)",
        hovertemplate="Week of %{x|%b %d, %Y}<br>Attendance: %{y:.1f}%<extra></extra>",
    ))
    fig2.add_trace(go.Scatter(
        x=att_weekly["week"], y=att_weekly["rolling_mean"],
        name="4-Week Trend", mode="lines",
        line=dict(color="#fbbf24", width=2, dash="dash"),
    ))
    if not dip_weeks.empty:
        fig2.add_trace(go.Scatter(
            x=dip_weeks["week"], y=dip_weeks["rate"],
            name="⚠ Dip Detected", mode="markers",
            marker=dict(size=14, color="#ef4444", symbol="diamond", line=dict(width=2, color="white")),
        ))

    for m_start in pd.date_range(TERM_START, TERM_END, freq="MS"):
        fig2.add_vline(x=m_start, line_dash="dot", line_color="rgba(255,255,255,0.15)")
        fig2.add_annotation(x=m_start + pd.Timedelta(days=15), y=103,
                            text=m_start.strftime("%b"), showarrow=False,
                            font=dict(size=11, color="#94a3b8"))

    fig2.update_layout(
        template="plotly_dark", height=380,
        title=dict(text=f"Weekly Attendance — {TERM_LABEL}", font=dict(size=15)),
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis=dict(tickformat="%b %d", title=""), yaxis=dict(title="Attendance %", range=[0, 110]),
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Dip callout ──
if not dip_weeks.empty:
    worst = dip_weeks.loc[dip_weeks["rate"].idxmin()]
    st.error(f"""
    **🔍 Cohort-Wide Dip — Week of {worst['week'].strftime('%b %d, %Y')}**
    
    Attendance dropped to **{worst['rate']:.1f}%**, well below the trend.
    """)

    st.subheader("🧐 What Could Explain It?")
    m = worst["week"].month
    if m in [1, 2]:
        exps = [("🎄 Post-Holiday Lag", "Students slow to return after winter break."),
                ("🤒 Winter Illness", "Flu season hits attendance hard."),
                ("📝 Early Assessments", "First quizzes cause stress-based absences.")]
    elif m in [3, 4]:
        exps = [("🌙 Ramadan", "Fasting alters routines, reducing attendance."),
                ("📊 Midterm Prep", "Students skip class to study for exams."),
                ("🏖 Spring Break", "Scheduled break lowers participation.")]
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
    st.success("✅ No significant dips detected — consistent participation throughout the term.")

st.markdown("")

# ── Heatmap ──
st.subheader("Monthly Attendance Heatmap by Group")
att_gm = (
    att.groupby(["group_id", "month"])
    .apply(lambda g: (g["status"] == "attended").mean() * 100)
    .reset_index(name="rate")
)
att_gm["month_label"] = att_gm["month"].dt.strftime("%b %Y")
pivot = att_gm.pivot(index="group_id", columns="month_label", values="rate")
mo = att_gm.drop_duplicates("month").sort_values("month")["month_label"].tolist()
pivot = pivot.reindex(columns=mo)

fig_heat = px.imshow(
    pivot.values, labels=dict(x="Month", y="Group", color="Attendance %"),
    x=pivot.columns.tolist(), y=pivot.index.tolist(),
    color_continuous_scale="RdYlGn", aspect="auto",
    title="Attendance by Group × Month (red = low, green = high)",
)
fig_heat.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=50, b=0))
st.plotly_chart(fig_heat, use_container_width=True)
st.caption("A full red column = ALL groups dipped that month. Isolated red cells = group-specific issues.")

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
