import pandas as pd
import streamlit as st
import os

BASE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE, "master_student_features (1).csv")

@st.cache_data
def load_data():
    return pd.read_csv(CSV_PATH)

def load_all():
    return {"master": load_data()}

LOGO_PATH = os.path.join(BASE, "logo.png")

def show_logo():
    st.sidebar.image(LOGO_PATH, width="stretch")
    st.sidebar.divider()

def show_top_logo():
    cols = st.columns([6, 1])
    with cols[1]:
        st.image(LOGO_PATH, width=120)
    st.divider()

def page_config(title, icon):
    st.set_page_config(page_title=title, page_icon=icon, layout="wide")

@st.cache_data
def compute_instructor_metrics(df):
    return df.groupby("instructor").agg(
        avg_score=("avg_concept_score", "mean"),
        avg_attendance=("attendance_rate_pct", "mean"),
        fail_rate=("concept_fail_pct", "mean"),
        student_count=("student_id", "count"),
    ).reset_index().sort_values("avg_score", ascending=False)
