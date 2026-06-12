import pandas as pd
import streamlit as st

BASE = "."

@st.cache_data
def load_master():
    return pd.read_csv(f"{BASE}/master_student_features.csv")

@st.cache_data
def load_students():
    return pd.read_csv(f"{BASE}/clean_students.csv")

@st.cache_data
def load_groups():
    return pd.read_csv(f"{BASE}/clean_groups.csv")

@st.cache_data
def load_submissions():
    return pd.read_csv(f"{BASE}/clean_submissions.csv")

@st.cache_data
def load_grades():
    return pd.read_csv(f"{BASE}/clean_grades.csv")

@st.cache_data
def load_attendance():
    return pd.read_csv(f"{BASE}/clean_attendance.csv")

@st.cache_data
def load_engagement():
    return pd.read_csv(f"{BASE}/clean_engagement.csv")

@st.cache_data
def load_all():
    return {
        "master": load_master(),
        "students": load_students(),
        "groups": load_groups(),
        "submissions": load_submissions(),
        "grades": load_grades(),
        "attendance": load_attendance(),
        "engagement": load_engagement(),
    }

def style_metric(value, prefix="", suffix="", fmt=".1f"):
    styled = f"{prefix}{value:{fmt}}{suffix}"
    return styled

def page_config(title, icon):
    st.set_page_config(page_title=title, page_icon=icon, layout="wide")
