import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from utils import load_data, page_config, show_logo, show_top_logo
from db_utils import require_auth, render_save_ui, dataframe_to_dict

require_auth()
page_config("Kayfa — Student Personas", "👥")
show_logo()
show_top_logo()

master = load_data()

st.title("👥 Student Personas & Segmentation")
st.markdown("##### Categorizing students to tailor support and communication")
st.divider()

def assign_personas(df):
    seg_data = df[["student_id", "attendance_rate_pct", "avg_concept_score", "concepts_failed", "total_events"]].copy()
    
    # Simple rule-based personas (easier to explain than K-means and very business-friendly)
    personas = []
    for _, row in seg_data.iterrows():
        att = row["attendance_rate_pct"]
        score = row["avg_concept_score"]
        if att >= 80 and score >= 75:
            personas.append("🌟 The High Achievers")
        elif att >= 80 and score < 75:
            personas.append("🛠️ The Hard Workers")
        elif att < 80 and score >= 75:
            personas.append("⚡ The Natural Talents")
        else:
            personas.append("⚠️ The At-Risk")
            
    seg_data["Persona"] = personas
    return seg_data

seg_data = assign_personas(master)
persona_counts = seg_data["Persona"].value_counts().reset_index()
persona_counts.columns = ["Persona", "Count"]

col1, col2 = st.columns(2)

with col1:
    fig = px.pie(
        persona_counts, values="Count", names="Persona", hole=0.4,
        color="Persona",
        color_discrete_map={
            "🌟 The High Achievers": "#10b981",
            "🛠️ The Hard Workers": "#f59e0b",
            "⚡ The Natural Talents": "#3b82f6",
            "⚠️ The At-Risk": "#ef4444"
        },
        title="Student Population by Persona"
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Averages per persona
    persona_stats = seg_data.groupby("Persona", observed=True).agg(
        avg_score=("avg_concept_score", "mean"),
        avg_att=("attendance_rate_pct", "mean")
    ).reset_index()
    
    fig2 = px.bar(
        persona_stats, x="Persona", y=["avg_score", "avg_att"], barmode="group",
        title="Average Grade & Attendance by Persona",
        labels={"value": "Percentage (%)", "variable": "Metric", "Persona": ""},
        color_discrete_sequence=["#6366f1", "#14b8a6"]
    )
    fig2.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11), legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

st.subheader("💡 Professional Insights & Solutions")

st.markdown("""
By categorizing our students into behavioral personas, we can move away from a 'one-size-fits-all' approach and deliver targeted support.

<div style="background: linear-gradient(135deg, #064e3b, #065f46); border-radius: 12px; padding: 20px; margin-bottom: 12px;">
    <h4 style="color: #34d399; margin-top: 0;">🌟 The High Achievers</h4>
    <p style="color: #a7f3d0; margin-bottom: 8px;">These students have high attendance and excellent grades. They are fully engaged and mastering the material.</p>
    <b>Solution:</b> Offer advanced modules, peer-mentoring opportunities, or career networking to keep them challenged.
</div>

<div style="background: linear-gradient(135deg, #78350f, #92400e); border-radius: 12px; padding: 20px; margin-bottom: 12px;">
    <h4 style="color: #fbbf24; margin-top: 0;">🛠️ The Hard Workers</h4>
    <p style="color: #fde68a; margin-bottom: 8px;">They attend almost every session but struggle to get high grades. They have the right attitude but might lack foundational knowledge.</p>
    <b>Solution:</b> Provide extra tutoring, clearer rubrics, and supplementary materials. Their effort is there; they just need academic guidance.
</div>

<div style="background: linear-gradient(135deg, #1e3a8a, #1e40af); border-radius: 12px; padding: 20px; margin-bottom: 12px;">
    <h4 style="color: #93c5fd; margin-top: 0;">⚡ The Natural Talents</h4>
    <p style="color: #bfdbfe; margin-bottom: 8px;">They get good grades despite poor attendance. They might find the material too easy or have conflicting schedules.</p>
    <b>Solution:</b> Reach out to ensure they feel connected. If the course is too easy, fast-track them. If they have scheduling conflicts, ensure asynchronous materials are top-notch.
</div>

<div style="background: linear-gradient(135deg, #7f1d1d, #991b1b); border-radius: 12px; padding: 20px; margin-bottom: 12px;">
    <h4 style="color: #fca5a5; margin-top: 0;">⚠️ The At-Risk</h4>
    <p style="color: #fecaca; margin-bottom: 8px;">Low attendance and low grades. These students are at a high risk of dropping out.</p>
    <b>Solution:</b> Immediate 1-on-1 intervention by student success advisors. Identify root causes (personal, technical, or academic) and create a recovery plan.
</div>
""", unsafe_allow_html=True)

render_save_ui("student_personas", "Student Personas data", dataframe_to_dict(seg_data))
