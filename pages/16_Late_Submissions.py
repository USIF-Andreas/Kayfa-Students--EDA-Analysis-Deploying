import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils import load_data, page_config, show_logo, show_top_logo
from db_utils import require_auth, render_save_ui, dataframe_to_dict

require_auth()
page_config("Kayfa — Late Submissions", "⏰")
show_logo()
show_top_logo()

master = load_data()

st.title("⏰ Late Submissions")
st.markdown("##### The hidden cost of submitting work late")
st.divider()

master["late_bucket"] = pd.cut(
    master["late_rate"],
    bins=[-0.01, 0.0, 0.25, 0.5, 0.75, 1.0],
    labels=["0%", "1-25%", "26-50%", "51-75%", "76-100%"],
)
bucket_trend = master.groupby("late_bucket", observed=True)["avg_concept_score"].mean().reset_index()
bucket_trend.columns = ["Late Rate Band", "Avg Score"]

col1, col2 = st.columns(2)

with col1:
    fig = px.bar(
        bucket_trend, x="Late Rate Band", y="Avg Score", color="Avg Score",
        color_continuous_scale="RdYlGn_r", text="Avg Score",
        title="Average Score by Late Rate Group",
    )
    fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
    fig.update_layout(template="plotly_dark", height=350,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.scatter(
        master, x="late_rate", y="avg_concept_score",
        opacity=0.4, color_discrete_sequence=["#ef4444"],
        title="Impact of Late Rates on Scores",
        labels={"late_rate": "Late Rate", "avg_concept_score": "Average Score (%)"},
    )
    
    # Non-technical trendline
    if len(master) > 1:
        z = np.polyfit(master["late_rate"].fillna(0), master["avg_concept_score"].fillna(0), 1)
        p = np.poly1d(z)
        master_sorted = master.sort_values("late_rate")
        fig.add_trace(go.Scatter(
            x=master_sorted["late_rate"],
            y=p(master_sorted["late_rate"]),
            mode="lines",
            name="General Trend",
            line=dict(color="#fbbf24", width=3, dash="dash")
        ))
        
    fig.update_layout(template="plotly_dark", height=350,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("💡 Professional Insights")
st.info("""
**The Cost of Being Late:**  
There is a visible downward trend indicating that students who frequently submit their work late tend to receive lower scores. The highest performers overwhelmingly submit their assignments on time (0% late rate).

**Recommendation:**  
Frequent late submissions are a strong early warning sign of a struggling student. Creating automated nudges or reminders a few days before deadlines could help reduce the late rate. Instructors might also want to check in with students in the higher late-rate bands to offer time-management support.
""")
