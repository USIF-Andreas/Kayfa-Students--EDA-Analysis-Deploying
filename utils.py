import pandas as pd
import streamlit as st
import os

BASE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE, "master_student_features (1).csv")

@st.cache_data
def load_data():
    return pd.read_csv(CSV_PATH)

@st.cache_data
def load_attendance():
    return pd.read_csv(os.path.join(BASE, "clean_attendance (1).csv"), parse_dates=["session_datetime"])

@st.cache_data
def load_engagement():
    return pd.read_csv(os.path.join(BASE, "clean_engagement.csv"), parse_dates=["event_datetime"])

@st.cache_data
def load_grades():
    return pd.read_csv(os.path.join(BASE, "clean_grades.csv"), parse_dates=["date"])

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
