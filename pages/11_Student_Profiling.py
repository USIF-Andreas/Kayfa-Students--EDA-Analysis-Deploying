import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils import load_data, page_config, show_logo, show_top_logo
from db_utils import require_auth, render_save_ui, dataframe_to_dict

require_auth()

page_config("Kayfa — Student Risk & Segmentation", "⚠️")
show_logo()
show_top_logo()

master = load_data()

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
    avg_fail_rate=("concept_fail_pct", "mean"),
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

with col4:
    eng_age = master.groupby("age_band", observed=True).agg(
        avg_events=("total_events", "mean"),
        avg_video_hrs=("total_video_seconds", "mean"),
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

best_age = age_analysis.loc[age_analysis["Avg Grade %"].idxmax()]
st.info(
    f"**Best-performing age band: {best_age['Age Band']}** "
    f"(Grade: {best_age['Avg Grade %']:.1f}%, Attendance: {best_age['Avg Attendance %']:.1f}%, "
    f"Fail Rate: {best_age['Avg Fail Rate %']:.1f}%)"
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

seg_data = master[["student_id", "attendance_rate_pct", "avg_concept_score", "concepts_failed",
                   "total_events", "total_video_seconds"]].copy()

features = ["attendance_rate_pct", "avg_concept_score", "concepts_failed", "total_events", "total_video_seconds"]
means_f = seg_data[features].mean()
stds_f = seg_data[features].std()
X = (seg_data[features] - means_f) / stds_f

labels, centroids = kmeans_manual(X.values, k=4, seed=42)
seg_data["cluster"] = labels

cluster_counts = seg_data["cluster"].value_counts().sort_index()

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

st.subheader("Cluster Profiles")
cluster_desc = seg_data.groupby("cluster")[features].agg(["mean", "std"]).round(2)
for c in sorted(cluster_counts.index):
    row = cluster_desc.loc[c]
    with st.container(border=True):
        st.markdown(
            f"### {'🟦' if c==0 else '🟥' if c==1 else '🟧' if c==2 else '🟩'} "
            f"Cluster {c} — {cluster_labels[c]}  \n"
            f"**{int(cluster_counts[c])} students** ({int(cluster_counts[c])/len(seg_data)*100:.0f}% of population)  \n"
            f"Attendance: {row[('attendance_rate_pct', 'mean')]:.1f}% | "
            f"Grade: {row[('avg_concept_score', 'mean')]:.1f}% | "
            f"Failures: {row[('concepts_failed', 'mean')]:.1f} | "
            f"Events: {row[('total_events', 'mean')]:.0f} | "
            f"Video: {row[('total_video_seconds', 'mean')]:.0f}s"
        )

st.divider()

# ── Q14: At-Risk Ranking ──
st.header("Q14: At-Risk Ranking — Top 10 Students to Contact First")

risk = master[["student_id", "full_name", "group_id", "concepts_failed", "attendance_rate_pct",
               "avg_concept_score", "late_rate", "total_events"]].copy()

risk["z_low_att"] = (100 - risk["attendance_rate_pct"]) / risk["attendance_rate_pct"].std()
risk["z_low_grade"] = (100 - risk["avg_concept_score"]) / risk["avg_concept_score"].std()
risk["z_failed"] = risk["concepts_failed"] / risk["concepts_failed"].std()
risk["z_late"] = risk["late_rate"] / risk["late_rate"].std()

risk["risk_score"] = risk["z_low_att"] + risk["z_low_grade"] + risk["z_failed"] + risk["z_late"]
risk = risk.sort_values("risk_score", ascending=False)

top10 = risk.head(10)

risk_colors = ["#ef4444", "#ef4444", "#f97316", "#f97316", "#f97316",
               "#f59e0b", "#f59e0b", "#f59e0b", "#eab308", "#eab308"]

for i, (_, row) in enumerate(top10.iterrows()):
    color = risk_colors[i] if i < len(risk_colors) else "#eab308"
    with st.container(border=True):
        r1, r2, r3 = st.columns([2, 3, 1])
        r1.markdown(f"**#{i+1}** — {row['full_name']}  \n{row['student_id']}  \n*Group {row['group_id']}*")
        r2.markdown(
            f"Attendance: **{row['attendance_rate_pct']:.0f}%** | "
            f"Score: **{row['avg_concept_score']:.1f}%** | "
            f"Failed: **{int(row['concepts_failed'])}** concepts | "
            f"Late Rate: **{row['late_rate']*100:.0f}%**"
        )
        r3.markdown(f"### **{row['risk_score']:.1f}**")
        r3.caption("Risk Score")

st.divider()

# ── Summary ──
st.header("📋 Key Takeaways")
st.markdown("""
| Question | Finding |
|---|---|
| **Q10 — Age Bands** | Best-performing age band: **{best_band}** |
| **Q11 — Segmentation** | **4 clusters** identified with distinct behavioral profiles |
| **Q14 — At-Risk Top 10** | **#{worst_name}** (risk={worst_risk:.1f}): {worst_att}% att, {worst_grade}% grade, {worst_fail} failures |
""".format(best_band=best_age['Age Band'],
           worst_name=top10.iloc[0]['full_name'],
           worst_risk=top10.iloc[0]['risk_score'],
           worst_att=top10.iloc[0]['attendance_rate_pct'],
           worst_grade=top10.iloc[0]['avg_concept_score'],
           worst_fail=int(top10.iloc[0]['concepts_failed'])))

render_save_ui("student_profiling", "Student profiling data",
               dataframe_to_dict(risk.head(10)))
