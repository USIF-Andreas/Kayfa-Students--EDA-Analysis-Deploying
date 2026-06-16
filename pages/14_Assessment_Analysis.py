import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
from utils import page_config, show_logo, show_top_logo
from db_utils import require_auth, render_save_ui, dataframe_to_dict

require_auth()
page_config("Kayfa — Assessment Analysis", "📊")
show_logo()
show_top_logo()

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@st.cache_data
def load_grades():
    return pd.read_csv(os.path.join(BASE, "clean_grades.csv"), parse_dates=["date"])

grades = load_grades()

st.title("📊 Assessment Analysis")
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

if not type_stats.empty:
    most_unpredictable = type_stats.sort_values("spread", ascending=False).iloc[0]["type"]
    most_consistent = type_stats.sort_values("spread").iloc[0]["type"]
else:
    most_unpredictable = "None"
    most_consistent = "None"

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
    color = color_map.get(t, "#ffffff")
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
            <p style="font-size: 28px; margin: 0;">{emoji_map.get(t, '📈')}</p>
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
render_save_ui("assessment_data", "Assessment data", dataframe_to_dict(type_stats))
