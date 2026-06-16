import streamlit as st
import pandas as pd
import plotly.express as px
from utils import load_data, page_config, show_logo, show_top_logo
from db_utils import require_auth, render_save_ui, dataframe_to_dict

require_auth()
page_config("Kayfa — Course Comparison", "🎯")
show_logo()
show_top_logo()

master = load_data()

st.title("🎯 Course Comparison")
st.markdown("##### Comparing average performance across different courses")
st.divider()

st.header("Highest & Lowest Average Grade")

course_stats = master.dropna(subset=["course_name"]).groupby("course_name")["avg_grade"].agg(["mean", "std", "count", "median"]).reset_index()
course_stats.columns = ["Course", "Mean", "Std", "Count", "Median"]
course_stats = course_stats.sort_values("Mean", ascending=False)

col1, col2 = st.columns(2)

with col1:
    fig = px.bar(
        course_stats, x="Course", y="Mean", color="Mean", text="Mean",
        color_continuous_scale="RdYlGn",
        title="Average Grade by Course",
        labels={"Course": "Course", "Mean": "Avg Grade %"},
    )
    fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
    fig.add_hline(y=master["avg_grade"].mean(), line_dash="dash", line_color="orange",
                  annotation_text=f"Platform Avg: {master['avg_grade'].mean():.0f}%")
    fig.update_layout(template="plotly_dark", height=350,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.box(
        master.dropna(subset=["course_name"]), x="course_name", y="avg_grade", color="course_name",
        title="Grade Spread by Course",
        labels={"course_name": "Course", "avg_grade": "Avg Grade %"},
    )
    fig.update_layout(template="plotly_dark", height=350,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11),
                      showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

highest = course_stats.iloc[0]
lowest = course_stats.iloc[-1]

st.subheader("💡 Professional Insights")
st.info(f"""
**Performance Gap:**  
The data reveals a noticeable difference in performance between courses. **{highest['Course']}** stands out as the highest-performing course with an average grade of **{highest['Mean']:.0f}%**. In contrast, **{lowest['Course']}** has the lowest average at **{lowest['Mean']:.0f}%**.

**Recommendation:**  
We recommend analyzing the structure and delivery of **{highest['Course']}** to identify successful teaching patterns that can be applied to **{lowest['Course']}**. Additionally, gathering student feedback on **{lowest['Course']}** could highlight specific areas where students are struggling.
""")

render_save_ui("course_comparison", "Course data", dataframe_to_dict(course_stats))
