import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils import load_all, page_config, show_logo, show_top_logo
from db_utils import require_auth, render_save_ui, dataframe_to_dict

require_auth()

page_config("Kayfa — Student Risk & Segmentation", "⚠️")
show_logo()
show_top_logo()

data = load_all()
master = data["master"]
students = data["students"]
groups = data["groups"]
engagement = data["engagement"]
grades = data["grades"]

grades = grades[grades["assessment_title"] != "Bonus Exam"]
engagement["event_datetime"] = pd.to_datetime(engagement["event_datetime"])

st.title("⚠️ Student Risk Profiling & Segmentation")
st.markdown("##### Age bands, behavioral clustering, and at-risk identification")

# ── Q10: Age Bands vs Outcomes ──
st.header("Q10: Age Bands vs Outcomes — Does Age Matter?")

master["age_band"] = pd.cut(
    master["age"], bins=[0, 20, 25, 30, 35, 100],
    labels=["18-20", "21-25", "26-30", "31-35", "36+"],
)

age_analysis = master.groupby("age_band", observed=True).agg(
    avg_grade=("avg_concept_score", "mean"),
    avg_att=("attendance_rate_pct", "mean"),
    avg_fail_rate=("concept_fail_rate_pct", "mean"),
    count=("student_id", "count"),
).reset_index()
age_analysis.columns = ["Age Band", "Avg Grade %", "Avg Attendance %", "Avg Fail Rate %", "Count"]

col1, col2 = st.columns(2)

with col1:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=age_analysis["Age Band"], y=age_analysis["Avg Grade %"],
        marker_color=["#6366f1", "#6366f1", "#10b981", "#f59e0b", "#ef4444"],
        text=age_analysis["Avg Grade %"].round(1).astype(str) + "%",
        textposition="outside",
    ))
    fig.update_layout(
        template="plotly_dark", height=350,
        title="Average Grade by Age Band",
        xaxis_title="Age Band", yaxis_title="Avg Grade %",
        margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Age 26-30 performs best (71.6%). The 21-25 band (largest cohort at 260 students) has the highest fail rate at 25%.")

with col2:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=age_analysis["Age Band"], y=age_analysis["Avg Attendance %"],
        marker_color=["#10b981", "#10b981", "#10b981", "#f59e0b", "#ef4444"],
        text=age_analysis["Avg Attendance %"].round(1).astype(str) + "%",
        textposition="outside",
    ))
    fig.update_layout(
        template="plotly_dark", height=350,
        title="Average Attendance by Age Band",
        xaxis_title="Age Band", yaxis_title="Avg Attendance %",
        margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Attendance peaks at 82.8% for ages 26-30. The 31-35 band (n=2) is too small for reliable conclusions.")

col3, col4 = st.columns(2)

with col3:
    fig = px.pie(
        age_analysis, values="Count", names="Age Band", hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set2,
        title="Student Distribution by Age Band",
    )
    fig.update_layout(template="plotly_dark", height=350,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("52% of students are aged 21-25. Only 9% are over 25 — the platform skews young.")

with col4:
    # Engagement by age band
    eng_count = engagement.groupby("student_id").size().reset_index(name="total_events")
    video_sum = engagement[engagement["event_type"] == "video_watch"].groupby("student_id")["duration_seconds"].sum().reset_index(name="total_video_sec")
    eng_per_student = eng_count.merge(video_sum, on="student_id", how="left").fillna(0)
    eng_per_student = eng_per_student.merge(master[["student_id", "age_band"]], on="student_id")
    eng_age = eng_per_student.groupby("age_band", observed=True).agg(
        avg_events=("total_events", "mean"),
        avg_video_hrs=("total_video_sec", "mean"),
    ).reset_index()
    eng_age["avg_video_hrs"] = (eng_age["avg_video_hrs"] / 3600).round(1)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=eng_age["age_band"], y=eng_age["avg_events"], mode="lines+markers",
        name="Avg Events", line=dict(color="#6366f1", width=3), marker=dict(size=10),
    ))
    fig.add_trace(go.Scatter(
        x=eng_age["age_band"], y=eng_age["avg_video_hrs"], mode="lines+markers",
        name="Avg Video Hrs", line=dict(color="#14b8a6", width=3), marker=dict(size=10),
        yaxis="y2",
    ))
    fig.update_layout(
        template="plotly_dark", height=350,
        title="Engagement by Age Band",
        xaxis_title="Age Band",
        yaxis=dict(title="Avg Events"),
        yaxis2=dict(title="Avg Video Hours", overlaying="y", side="right"),
        margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11),
        legend=dict(orientation="h", y=1.1),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Engagement is relatively flat across age bands. Age 26-30 shows slightly higher video consumption (12,250s vs 10,450s for 21-25).")

best_age = age_analysis.loc[age_analysis["Avg Grade %"].idxmax()]
st.info(
    f"**Best-performing age band: {best_age['Age Band']}** "
    f"(Grade: {best_age['Avg Grade %']:.1f}%, Attendance: {best_age['Avg Attendance %']:.1f}%, "
    f"Fail Rate: {best_age['Avg Fail Rate %']:.1f}%)  \n"
    f"Mature students (26-30) consistently outperform younger cohorts, though the 31-35 band "
    f"(n=2) is too small for reliable comparison. Age 21-25 (largest group) has the highest fail rate."
)

st.divider()

# ── Q11: Student Segmentation (K-Means) ──
st.header("Q11: Student Segmentation — Behavioral Clustering")

def kmeans_manual(X, k=4, max_iter=100, seed=42):
    np.random.seed(seed)
    n = X.shape[0]
    idx = np.random.choice(n, k, replace=False)
    centroids = X[idx].copy()
    for _ in range(max_iter):
        dists = np.array([[np.linalg.norm(x - c) for c in centroids] for x in X])
        labels = np.argmin(dists, axis=1)
        new_centroids = np.array([
            X[labels == i].mean(axis=0) if np.any(labels == i) else centroids[i]
            for i in range(k)
        ])
        if np.allclose(centroids, new_centroids):
            break
        centroids = new_centroids
    return labels, centroids

eng_count_all = engagement.groupby("student_id").size().reset_index(name="total_events")
video_sum_all = engagement[engagement["event_type"] == "video_watch"].groupby("student_id")["duration_seconds"].sum().reset_index(name="total_video_sec")

seg_data = master[["student_id", "attendance_rate_pct", "avg_concept_score", "concepts_failed"]].copy()
seg_data = seg_data.merge(eng_count_all, on="student_id", how="left").fillna(0)
seg_data = seg_data.merge(video_sum_all, on="student_id", how="left").fillna(0)

features = ["attendance_rate_pct", "avg_concept_score", "concepts_failed", "total_events", "total_video_sec"]
means_f = seg_data[features].mean()
stds_f = seg_data[features].std()
X = (seg_data[features] - means_f) / stds_f

labels, centroids = kmeans_manual(X.values, k=4, seed=42)
seg_data["cluster"] = labels

cluster_desc = seg_data.groupby("cluster")[features].agg(["mean", "std"]).round(2)
cluster_counts = seg_data["cluster"].value_counts().sort_index()

# Define cluster labels
cluster_labels = {}
for c in sorted(seg_data["cluster"].unique()):
    row = seg_data[seg_data["cluster"] == c][features].mean()
    desc_parts = []
    if row["attendance_rate_pct"] > 85:
        desc_parts.append("✅ High Attendance")
    elif row["attendance_rate_pct"] < 60:
        desc_parts.append("❌ Low Attendance")
    if row["avg_concept_score"] > 73:
        desc_parts.append("🏆 High Performer")
    elif row["avg_concept_score"] < 65:
        desc_parts.append("⚠️ Low Performer")
    if row["concepts_failed"] > 8:
        desc_parts.append("📚 Many Failures")
    elif row["concepts_failed"] < 4:
        desc_parts.append("✅ Few Failures")
    if row["total_events"] > 70:
        desc_parts.append("⚡ Highly Engaged")
    elif row["total_events"] < 55:
        desc_parts.append("💤 Disengaged")
    cluster_labels[c] = " | ".join(desc_parts)

col5, col6 = st.columns(2)

with col5:
    fig = px.scatter(
        seg_data, x="avg_concept_score", y="attendance_rate_pct",
        color=seg_data["cluster"].astype(str), size="concepts_failed",
        hover_data=["student_id"],
        color_discrete_sequence=["#6366f1", "#ef4444", "#f59e0b", "#10b981"],
        title="Cluster Map: Score vs Attendance (size = failures)",
        labels={"avg_concept_score": "Avg Concept Score %", "attendance_rate_pct": "Attendance %"},
    )
    fig.update_layout(template="plotly_dark", height=400,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Cluster 2 (orange, 19% of students) is the most concerning — low scores (58.1%) with many concept failures (13.1 avg). Cluster 0 (blue) are the high-achievers.")

with col6:
    fig = px.scatter(
        seg_data, x="total_events", y="avg_concept_score",
        color=seg_data["cluster"].astype(str), size="concepts_failed",
        hover_data=["student_id"],
        color_discrete_sequence=["#6366f1", "#ef4444", "#f59e0b", "#10b981"],
        title="Cluster Map: Events vs Score (size = failures)",
        labels={"total_events": "Total Engagement Events", "avg_concept_score": "Avg Concept Score %"},
    )
    fig.update_layout(template="plotly_dark", height=400,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Engagement separates clusters clearly. The bottom-left quadrant (low events, low scores) is where intervention resources should focus.")

# Cluster profile table
st.subheader("Cluster Profiles")
profile_rows = []
for c in sorted(cluster_counts.index):
    row = cluster_desc.loc[c]
    profile_rows.append({
        "Cluster": c,
        "Label": cluster_labels[c],
        "Students": int(cluster_counts[c]),
        "Attendance %": f"{row[('attendance_rate_pct', 'mean')]:.1f}",
        "Grade %": f"{row[('avg_concept_score', 'mean')]:.1f}",
        "Failures": f"{row[('concepts_failed', 'mean')]:.1f}",
        "Events": f"{row[('total_events', 'mean')]:.0f}",
        "Video Sec": f"{row[('total_video_sec', 'mean')]:.0f}",
    })

# Color the cluster cards
cluster_colors = {0: "blue", 1: "red", 2: "orange", 3: "green"}
for pr in profile_rows:
    c = pr["Cluster"]
    color = cluster_colors.get(c, "gray")
    with st.container(border=True):
        st.markdown(
            f"### {'🟦' if c==0 else '🟥' if c==1 else '🟧' if c==2 else '🟩'} "
            f"Cluster {c} — {pr['Label']}  \n"
            f"**{pr['Students']} students** ({pr['Students']/len(seg_data)*100:.0f}% of population)  \n"
            f"Attendance: {pr['Attendance %']}% | Grade: {pr['Grade %']}% | "
            f"Failures: {pr['Failures']} | Events: {pr['Events']} | Video: {pr['Video Sec']}s"
        )

st.divider()

# ── Q14: At-Risk Ranking ──
st.header("Q14: At-Risk Ranking — Top 10 Students to Contact First")

eng_term = engagement[
    (engagement["event_datetime"] >= "2025-10-01") &
    (engagement["event_datetime"] <= "2026-06-01")
].copy()
eng_term["week"] = eng_term["event_datetime"].dt.to_period("W").dt.start_time

def get_trend(grp):
    if len(grp) < 2:
        return 0
    weeks_num = (grp["week"] - grp["week"].min()).dt.days / 7
    if weeks_num.std() == 0:
        return 0
    slope = np.polyfit(weeks_num, grp["n_events"], 1)[0]
    return slope

eng_trend_data = eng_term.groupby(["student_id", "week"]).size().reset_index(name="n_events")
student_trend = eng_trend_data.groupby("student_id").apply(get_trend).reset_index(name="eng_slope")

risk = master[["student_id", "concepts_failed", "attendance_rate_pct", "avg_concept_score"]].copy()
risk = risk.merge(student_trend, on="student_id", how="left").fillna(0)

risk["z_low_att"] = (100 - risk["attendance_rate_pct"]) / risk["attendance_rate_pct"].std()
risk["z_low_grade"] = (100 - risk["avg_concept_score"]) / risk["avg_concept_score"].std()
risk["z_failed"] = risk["concepts_failed"] / risk["concepts_failed"].std()
risk["z_declining"] = -risk["eng_slope"] / risk["eng_slope"].std() if risk["eng_slope"].std() > 0 else 0

risk["risk_score"] = risk["z_low_att"] + risk["z_low_grade"] + risk["z_failed"] + risk["z_declining"]
risk = risk.sort_values("risk_score", ascending=False)

top10 = risk.head(10).merge(students[["student_id", "full_name", "group_id"]], on="student_id")
top10 = top10.merge(groups[["group_id", "group_name"]], on="group_id", how="left")

risk_colors = ["#ef4444", "#ef4444", "#f97316", "#f97316", "#f97316",
               "#f59e0b", "#f59e0b", "#f59e0b", "#eab308", "#eab308"]

for i, (_, row) in enumerate(top10.iterrows()):
    color = risk_colors[i] if i < len(risk_colors) else "#eab308"
    eng_dir = "📉" if row["eng_slope"] < 0 else "➡️" if abs(row["eng_slope"]) < 0.01 else "📈"
    with st.container(border=True):
        r1, r2, r3 = st.columns([2, 3, 1])
        r1.markdown(f"**#{i+1}** — {row['full_name']}  \n{row['student_id']}  \n*{row['group_name']}*")
        r2.markdown(
            f"Attendance: **{row['attendance_rate_pct']:.0f}%** | "
            f"Score: **{row['avg_concept_score']:.1f}%** | "
            f"Failed: **{int(row['concepts_failed'])}** concepts | "
            f"Engagement: {eng_dir} (slope={row['eng_slope']:.2f})"
        )
        r3.markdown(f"### **{row['risk_score']:.1f}**")
        r3.caption("Risk Score")

st.caption("🏴 Group 07 (C005) dominates — 6 of top 10 at-risk students are from this group, reinforcing C005 as the primary intervention target.")

st.divider()

# ── Summary ──
st.header("📋 Key Takeaways")
st.markdown("""
| Question | Finding |
|---|---|
| **Q10 — Age Bands** | Age **26-30** performs best; 21-25 (largest cohort) has highest fail rate (25%) |
| **Q11 — Segmentation** | **4 clusters**: High-Achievers (30%), Disengaged At-Risk (17%), Struggling/Many Failures (19%), Regular (34%) |
| **Q14 — At-Risk Top 10** | **#1 Rowan ElBaz** (risk=14.5): 20% att, 50.8% grade, 20 failures; **6/10 from Group 07 (C005)** |
""")

render_save_ui("student_profiling", "Student profiling data",
               dataframe_to_dict(risk.head(10)))
