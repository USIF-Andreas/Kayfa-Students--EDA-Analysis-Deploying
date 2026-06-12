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

LOGO_PATH = f"{BASE}/download (14).png"

# ── Logo ───────────────────────────────────────────────────────────────────

def show_logo():
    st.sidebar.image(LOGO_PATH, width="stretch")
    st.sidebar.divider()

def show_top_logo():
    cols = st.columns([6, 1])
    with cols[1]:
        st.image(LOGO_PATH, width=120)
    st.divider()

# ── Page Config ────────────────────────────────────────────────────────────

def page_config(title, icon):
    st.set_page_config(page_title=title, page_icon=icon, layout="wide")

# ── Cached Computations ────────────────────────────────────────────────────

@st.cache_data
def compute_student_avg_grades(grades):
    return grades.groupby("student_id")["score"].mean().reset_index()

@st.cache_data
def compute_quiz_progression(grades):
    quiz = grades[grades["type"] == "quiz"].copy()
    quiz["quiz_num"] = quiz["assessment_title"].str.extract(r"(\d+)").astype(int)
    return quiz.groupby("quiz_num")["score"].mean().reset_index()

@st.cache_data
def compute_weekly_engagement(engagement):
    df = engagement.copy()
    df["week"] = pd.to_datetime(df["event_datetime"]).dt.to_period("W").dt.start_time
    return df.groupby("week").size().reset_index(name="events")

@st.cache_data
def compute_late_by_student(submissions):
    return submissions.groupby("student_id")["is_late"].mean().reset_index(name="late_pct") * 100

@st.cache_data
def compute_student_engagement_count(engagement):
    return engagement.groupby("student_id").size().reset_index(name="total_events")

@st.cache_data
def compute_attendance_by_group(attendance, groups):
    merged = attendance.merge(groups[["group_id", "group_name"]], on="group_id", how="left")
    return (
        merged.groupby("group_name")["status"]
        .apply(lambda x: (x == "attended").mean() * 100)
        .reset_index(name="att_rate")
    )

@st.cache_data
def compute_grade_avg_by_type(grades):
    return grades.groupby(["type", "assessment_title"])["score"].mean().reset_index()

@st.cache_data
def compute_instructor_metrics(master):
    return master.groupby("instructor").agg(
        avg_score=("avg_concept_score", "mean"),
        avg_attendance=("attendance_rate_pct", "mean"),
        fail_rate=("concept_fail_rate_pct", "mean"),
        student_count=("student_id", "count"),
    ).reset_index().sort_values("avg_score", ascending=False)

@st.cache_data
def compute_city_stats(students):
    return students.groupby("city")["age"].mean().reset_index().sort_values("age")
