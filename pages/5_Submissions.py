import streamlit as st
import pandas as pd
import plotly.express as px
from utils import load_data, page_config, show_logo, show_top_logo

page_config("Kayfa Students — Submissions", "📝")
show_logo()
show_top_logo()

master = load_data()

st.title("📝 Submissions & Procrastination Analysis")
st.markdown("##### Effort Tracking, Late Behavior & Time Management")

total_sub = master["total_submissions"].sum()
avg_late_rate = master["late_rate"].mean() * 100
avg_time = master["avg_time_spent"].mean()
avg_sub = master["total_submissions"].mean()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Submissions", f"{total_sub:,.0f}")
col2.metric("Avg Late Rate", f"{avg_late_rate:.1f}%")
col3.metric("Avg Time Spent", f"{avg_time:.0f} min")
col4.metric("Avg Submissions", f"{avg_sub:.1f}")
col5.metric("Students", len(master))

st.divider()

col_a, col_b = st.columns(2)

with col_a:
    late_bins = pd.cut(master["late_rate"], bins=[-0.01, 0.0, 0.25, 0.5, 0.75, 1.0],
                       labels=["0%", "1-25%", "26-50%", "51-75%", "76-100%"])
    late_dist = late_bins.value_counts().reset_index()
    late_dist.columns = ["Late Rate", "Count"]
    fig = px.bar(
        late_dist, x="Late Rate", y="Count", color="Count",
        color_continuous_scale="RdYlGn_r", title="Late Submission Rate Distribution",
        labels={"Late Rate": "Late %", "Count": "Students"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    chronic = (master["late_rate"] >= 0.5).sum()
    st.caption(f"{avg_late_rate:.1f}% average late rate. {chronic} students ({chronic/len(master)*100:.0f}%) are late ≥50% of the time.")

with col_b:
    fig = px.histogram(
        master, x="avg_time_spent", nbins=35, color_discrete_sequence=["#14b8a6"],
        title="Avg Time Spent on Assignments", labels={"avg_time_spent": "Minutes"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    med_time = master["avg_time_spent"].median()
    st.caption(f"Median time spent is {med_time:.0f} minutes. The distribution is right-skewed.")

st.divider()

col_c, col_d = st.columns(2)

with col_c:
    fig = px.histogram(
        master, x="total_submissions", nbins=20, color_discrete_sequence=["#f59e0b"],
        title="Total Submissions per Student",
        labels={"total_submissions": "Submissions"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Most students have {int(master['total_submissions'].median())} submissions. Submission count reflects course assessment load.")

with col_d:
    fig = px.scatter(
        master, x="late_rate", y="avg_concept_score",
        trendline="ols", color_discrete_sequence=["#ef4444"], opacity=0.5,
        title="Late Rate vs Concept Score",
        labels={"late_rate": "Late Rate", "avg_concept_score": "Avg Concept Score"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Clear downward trend: the more a student procrastinates, the lower their concept scores.")

st.divider()

col_e, col_f = st.columns(2)

with col_e:
    fig = px.scatter(
        master, x="avg_time_spent", y="avg_concept_score",
        trendline="ols", color_discrete_sequence=["#6366f1"], opacity=0.5,
        title="Avg Time Spent vs Concept Score",
        labels={"avg_time_spent": "Avg Time Spent (min)", "avg_concept_score": "Avg Concept Score"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Diminishing returns on time spent — quality of study time matters more than quantity.")

with col_f:
    fig = px.scatter(
        master, x="total_submissions", y="avg_concept_score",
        color="category", hover_data=["student_id"],
        title="Submissions vs Concept Score",
        labels={"total_submissions": "Total Submissions", "avg_concept_score": "Avg Concept Score"},
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("More submissions generally correlate with higher scores, though the relationship varies by category.")
