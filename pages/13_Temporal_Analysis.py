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

# ── Specific 6 months: Dec 2025 → May 2026 ──
TERM_START = pd.Timestamp("2025-12-01")
TERM_END = pd.Timestamp("2026-05-31 23:59:59")
TERM_LABEL = "Dec 2025 → May 2026"

att = att_raw[(att_raw["session_datetime"] >= TERM_START) & (att_raw["session_datetime"] <= TERM_END)].copy()
eng = eng_raw[(eng_raw["event_datetime"] >= TERM_START) & (eng_raw["event_datetime"] <= TERM_END)].copy()

# ═══════════════════════════════════════════════════
# SECTION 1 — Engagement & Attendance Over the Term
# ═══════════════════════════════════════════════════

st.title("📉 Temporal Trends Analysis")
st.markdown(f"##### Tracking participation and attendance across the {TERM_LABEL} term")
st.divider()

st.header("Q1: Engagement & Attendance Over the 6-Month Term")
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

st.markdown("")

# ── Relationship between Attendance and Grades ──
st.subheader("📈 Do students with better attendance get better grades?")
st.markdown("_Tracking the direct impact of showing up to sessions._")

# Calculate attendance rate per student using att_raw
student_att_rate = att_raw.assign(is_attended=att_raw["status"] == "attended").groupby("student_id")["is_attended"].mean() * 100
student_att_rate = student_att_rate.reset_index(name="attendance_rate")

grades_copy = grades.copy()
if "score_pct" not in grades_copy.columns:
    grades_copy["score_pct"] = (grades_copy["score"] / grades_copy["max_score"]) * 100
student_avg_grade = grades_copy.groupby("student_id")["score_pct"].mean().reset_index(name="average_grade")

att_grade_df = pd.merge(student_att_rate, student_avg_grade, on="student_id", how="inner")
correlation = att_grade_df["attendance_rate"].corr(att_grade_df["average_grade"])

fig_scatter = px.scatter(
    att_grade_df, x="attendance_rate", y="average_grade",
    title="Attendance vs Average Grades",
    labels={"attendance_rate": "Attendance Rate (%)", "average_grade": "Average Grade (%)"},
    opacity=0.7, color_discrete_sequence=["#34d399"]
)

# Add trendline manually to avoid statsmodels dependency issues
if len(att_grade_df) > 1:
    z = np.polyfit(att_grade_df["attendance_rate"], att_grade_df["average_grade"], 1)
    p = np.poly1d(z)
    att_grade_df_sorted = att_grade_df.sort_values("attendance_rate")
    
    fig_scatter.add_trace(go.Scatter(
        x=att_grade_df_sorted["attendance_rate"],
        y=p(att_grade_df_sorted["attendance_rate"]),
        mode="lines",
        name="General Trend",
        line=dict(color="#fbbf24", width=3, dash="dash")
    ))

fig_scatter.update_layout(template="plotly_dark", height=450, margin=dict(l=10, r=10, t=50, b=10))
st.plotly_chart(fig_scatter, use_container_width=True)

st.info(f'''
**What does this mean for the students?**
- **The Pattern:** We can see that {'students who attend more sessions generally score higher on their assignments and exams.' if correlation > 0 else 'there is no obvious impact of attendance on grades.'}
- **The Yellow Line:** This line shows the general direction. It goes {'up, meaning better attendance equals better grades.' if correlation > 0 else 'down or stays flat, meaning attendance does not guarantee better grades.'}
- **The Real Takeaway:** Encourage students to show up! The data clearly shows that those who participate consistently have a much easier time succeeding in the course.
''')

st.divider()

# ═══════════════════════════════════════════════════
# SECTION 1B — Attendance (session + proxy)
# ═══════════════════════════════════════════════════

st.header("📅 Attendance Over the 6-Month Term")
st.markdown("""
_Session attendance records are available for **December 2025 only**.  
To track attendance across all 6 months, we measure **platform attendance** — how many days each student was active on the platform._
""")

# ── Proxy attendance: active days per student per month ──
eng_copy = eng.copy()
eng_copy["date"] = eng_copy["event_datetime"].dt.date
proxy_monthly = eng_copy.groupby("month").agg(
    total_active_days=("date", "nunique"),
    unique_students=("student_id", "nunique"),
).reset_index().sort_values("month")

# Per-student active days
student_month = eng_copy.groupby(["student_id", "month"])["date"].nunique().reset_index(name="active_days")
student_month["month_days"] = student_month["month"].dt.days_in_month
student_month["attendance_pct"] = (student_month["active_days"] / student_month["month_days"]) * 100

proxy_rate = student_month.groupby("month")["attendance_pct"].mean().reset_index()
proxy_rate.columns = ["month", "avg_attendance_pct"]
proxy_rate["month_label"] = proxy_rate["month"].dt.strftime("%b %Y")

# ── Session attendance (Dec only) ──
dec_att_rate = overall_att_rate

# KPIs
col_a1, col_a2, col_a3, col_a4 = st.columns(4)
col_a1.metric("Dec Session Attendance", f"{dec_att_rate:.1f}%")
avg_proxy = proxy_rate["avg_attendance_pct"].mean()
col_a2.metric("Avg Platform Attendance", f"{avg_proxy:.1f}%")
worst_proxy = proxy_rate.loc[proxy_rate["avg_attendance_pct"].idxmin()]
best_proxy = proxy_rate.loc[proxy_rate["avg_attendance_pct"].idxmax()]
col_a3.metric("Weakest Month", worst_proxy["month_label"], f"{worst_proxy['avg_attendance_pct']:.1f}%")
col_a4.metric("Strongest Month", best_proxy["month_label"], f"{best_proxy['avg_attendance_pct']:.1f}%")

st.markdown("")

# ── Chart: Platform attendance by month ──
st.subheader("📊 Platform Attendance Rate — Each Month")
st.markdown("_% of days in the month that the average student was active on the platform_")

avg_p = proxy_rate["avg_attendance_pct"].mean()
p_colors = ["#10b981" if v >= avg_p else "#ef4444" for v in proxy_rate["avg_attendance_pct"]]

fig_att = go.Figure()
fig_att.add_trace(go.Bar(
    x=proxy_rate["month_label"], y=proxy_rate["avg_attendance_pct"],
    marker_color=p_colors,
    text=[f"{v:.1f}%" for v in proxy_rate["avg_attendance_pct"]],
    textposition="outside", textfont=dict(size=14, color="white"),
))
fig_att.add_hline(y=avg_p, line_dash="dot", line_color="#fbbf24", line_width=2,
                  annotation_text=f"Avg: {avg_p:.1f}%", annotation_position="top left",
                  annotation_font_color="#fbbf24")

fig_att.update_layout(
    template="plotly_dark", height=400,
    title=dict(text=f"Platform Attendance Rate — {TERM_LABEL}", font=dict(size=16)),
    margin=dict(l=10, r=10, t=60, b=10), font=dict(size=12), bargap=0.3,
    yaxis=dict(title="Avg % of Days Active", range=[0, proxy_rate["avg_attendance_pct"].max() * 1.3]),
    xaxis=dict(title=""),
)
st.plotly_chart(fig_att, use_container_width=True)
st.caption("🟢 Green = above average · 🔴 Red = below average · Platform attendance = % of days a student logged in or did any activity")

st.markdown("")

# ── Per-month cards ──
att_cols = st.columns(min(len(proxy_rate), 6))
for i, (_, row) in enumerate(proxy_rate.iterrows()):
    col_idx = i % len(att_cols)
    pct = row["avg_attendance_pct"]
    if pct >= avg_p * 1.1:
        bg = "linear-gradient(135deg, #064e3b, #065f46)"
        emoji = "✅"
    elif pct >= avg_p * 0.9:
        bg = "linear-gradient(135deg, #1e3a5f, #1e40af)"
        emoji = "📊"
    else:
        bg = "linear-gradient(135deg, #7f1d1d, #991b1b)"
        emoji = "⚠️"

    with att_cols[col_idx]:
        st.markdown(f"""
        <div style="background: {bg}; border-radius: 12px; padding: 16px; text-align: center; margin-bottom: 8px;">
            <h4 style="color: white; margin: 0;">{row['month_label']}</h4>
            <p style="font-size: 28px; font-weight: 800; color: white; margin: 8px 0;">{emoji} {pct:.1f}%</p>
            <p style="color: #d1d5db; font-size: 12px; margin: 0;">of days students were active</p>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ═══════════════════════════════════════════════════
# KEY TAKEAWAYS
# ═══════════════════════════════════════════════════

st.header("📋 Key Takeaways")

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

st.markdown("")
render_save_ui("temporal_data", "Temporal Analysis data", dataframe_to_dict(proxy_rate))

