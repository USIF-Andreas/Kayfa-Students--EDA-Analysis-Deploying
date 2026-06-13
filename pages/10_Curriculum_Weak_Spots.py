import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import load_data, page_config, show_logo, show_top_logo
from db_utils import require_auth, render_save_ui, dataframe_to_dict

require_auth()

page_config("Kayfa — Curriculum Weak Spots", "📉")
show_logo()
show_top_logo()

master = load_data()

st.title("📉 Curriculum Weak Spots & Concept Mastery")
st.markdown("##### Identifying concepts and courses with the highest failure rates")

# ── Q6: Highest Failure Rate Concepts ──
st.header("Q6: Highest Failure Rate Areas — The Biggest Weak Spots")

course_fail = master.dropna(subset=["course_name"]).groupby(["course_name", "category"])["concept_fail_pct"].agg(["mean", "std", "count"]).reset_index()
course_fail.columns = ["course_name", "category", "avg_fail_rate", "std", "count"]
course_fail = course_fail.sort_values("avg_fail_rate", ascending=False)

top_n = course_fail.head(10).copy()

col1, col2 = st.columns([2, 1])

with col1:
    colors = ["#ef4444" if r["avg_fail_rate"] >= 30 else "#f59e0b" if r["avg_fail_rate"] >= 15 else "#10b981"
              for _, r in top_n.iterrows()]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=top_n["avg_fail_rate"], y=top_n["course_name"],
        orientation="h", marker_color=colors,
        text=top_n["avg_fail_rate"].round(1).astype(str) + "%",
        textposition="outside",
    ))
    fig.update_layout(
        template="plotly_dark", height=450,
        title="Top Courses by Avg Concept Fail Rate",
        xaxis_title="Fail Rate %", yaxis_title="",
        margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Courses with highest concept fail rates need curriculum redesign attention.")

with col2:
    worst = course_fail.iloc[0]
    st.error(f"**Biggest Weak Spot**")
    st.markdown(f"**Course:** {worst['course_name']}  \n"
                f"**Category:** {worst['category']}  \n"
                f"**Avg Fail Rate:** {worst['avg_fail_rate']:.1f}%  \n"
                f"**Students:** {int(worst['count'])}")

st.subheader("Fail Rate by Course & Category")
heat_data = course_fail.pivot_table(
    index="course_name", columns="category", values="avg_fail_rate", aggfunc="mean"
).round(1)
fig = px.imshow(
    heat_data, text_auto=True, color_continuous_scale="RdYlGn_r",
    title="Average Concept Fail Rate % by Course × Category",
    labels={"x": "Category", "y": "Course", "color": "Fail Rate %"},
)
fig.update_layout(template="plotly_dark", height=350,
                  margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
st.plotly_chart(fig, use_container_width=True)
st.caption("Some courses have alarmingly high fail rates across the board — systemic issues.")

st.divider()

# ── Fail rate distribution ──
st.header("Fail Rate Distribution Across Students")

col3, col4 = st.columns(2)

with col3:
    fig = px.histogram(
        master, x="concept_fail_pct", nbins=25, color_discrete_sequence=["#ef4444"],
        title="Distribution of Student-Level Concept Fail Rates",
        labels={"concept_fail_pct": "Fail Rate %"},
    )
    fig.update_layout(template="plotly_dark", height=350,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    high_fail = (master["concept_fail_pct"] >= 50).sum()
    st.caption(f"{high_fail} students ({high_fail/len(master)*100:.0f}%) have a fail rate ≥50% — these need targeted intervention.")

with col4:
    fig = px.scatter(
        master, x="concept_fail_pct", y="avg_concept_score",
        color="category", hover_data=["student_id", "course_name"],
        title="Fail Rate vs Concept Score",
        labels={"concept_fail_pct": "Fail Rate %", "avg_concept_score": "Avg Concept Score"},
    )
    fig.update_layout(template="plotly_dark", height=350,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Strong negative correlation: students with high fail rates have low overall scores.")

st.divider()

# ── Summary ──
st.header("📋 Key Takeaways")
st.markdown("""
| Question | Finding |
|---|---|
| **Q6 — Worst Course** | **{worst_course}**: {worst_rate:.1f}% avg fail rate |
| **Recommendation** | Redesign curriculum for high-fail-rate courses; provide extra support |
""".format(worst_course=worst['course_name'], worst_rate=worst['avg_fail_rate']))

render_save_ui("curriculum_weak_spots", "Curriculum data",
               dataframe_to_dict(course_fail.head(15)))
