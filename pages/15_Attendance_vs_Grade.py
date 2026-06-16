import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils import load_data, page_config, show_logo, show_top_logo
from db_utils import require_auth, render_save_ui, dataframe_to_dict

require_auth()
page_config("Kayfa — Attendance vs Grade", "📈")
show_logo()
show_top_logo()

master = load_data()

st.title("📈 Attendance vs Grade")
st.markdown("##### How does showing up impact student success?")
st.divider()

col1, col2 = st.columns(2)

with col1:
    fig = px.scatter(
        master, x="attendance_rate_pct", y="avg_concept_score",
        opacity=0.5, color_discrete_sequence=["#10b981"],
        title="Impact of Attendance on Concept Scores",
        labels={"attendance_rate_pct": "Attendance (%)", "avg_concept_score": "Concept Score (%)"},
    )
    
    # Non-technical trendline
    if len(master) > 1:
        z = np.polyfit(master["attendance_rate_pct"].fillna(0), master["avg_concept_score"].fillna(0), 1)
        p = np.poly1d(z)
        master_sorted = master.sort_values("attendance_rate_pct")
        fig.add_trace(go.Scatter(
            x=master_sorted["attendance_rate_pct"],
            y=p(master_sorted["attendance_rate_pct"]),
            mode="lines",
            name="General Trend",
            line=dict(color="#fbbf24", width=3, dash="dash")
        ))
        
    fig.update_layout(template="plotly_dark", height=350,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    master["att_bucket"] = pd.cut(
        master["attendance_rate_pct"],
        bins=[-1, 40, 60, 80, 90, 100],
        labels=["0-40%", "40-60%", "60-80%", "80-90%", "90-100%"],
    )
    bucket_trend = master.groupby("att_bucket", observed=True)["avg_concept_score"].mean().reset_index()
    bucket_trend.columns = ["Attendance Band", "Avg Score"]
    
    fig = px.bar(
        bucket_trend, x="Attendance Band", y="Avg Score", color="Avg Score",
        color_continuous_scale="Viridis", text="Avg Score",
        title="Average Score by Attendance Group",
    )
    fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
    fig.update_layout(template="plotly_dark", height=350,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("💡 Professional Insights")
st.info("""
**The Power of Showing Up:**  
The charts clearly demonstrate a strong positive pattern: students who maintain higher attendance rates consistently achieve better concept scores. The bar chart explicitly shows how scores jump as students move into higher attendance brackets.

**Recommendation:**  
Attendance is a major leading indicator of success. Proactively reaching out to students who fall below the 80% attendance mark could catch them before their grades suffer. Emphasizing the direct link between attendance and grades during onboarding may also boost participation.
""")
