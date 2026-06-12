import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import load_all, page_config

page_config("Kayfa Students — Demographics", "👥")

data = load_all()
students = data["students"]
groups = data["groups"]
master = data["master"]

st.title("👥 Demographics Analysis")
st.markdown("##### Understanding the Student Population")

total = len(students)
cities = students["city"].nunique()
age_mean = students["age"].mean()
age_min, age_max = students["age"].min(), students["age"].max()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Students", total)
col2.metric("Cities", cities)
col3.metric("Avg Age", f"{age_mean:.1f}")
col4.metric("Age Range", f"{age_min} – {age_max}")

st.divider()

col_a, col_b = st.columns(2)

with col_a:
    fig = px.histogram(
        students,
        x="age",
        nbins=15,
        color_discrete_sequence=["#6366f1"],
        title="Age Distribution",
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    gender_counts = students["gender"].value_counts().reset_index()
    gender_counts.columns = ["gender", "count"]
    fig = px.pie(
        gender_counts,
        values="count",
        names="gender",
        color="gender",
        color_discrete_map={"Male": "#6366f1", "Female": "#f472b6"},
        hole=0.5,
        title="Gender Distribution",
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

city_counts = students["city"].value_counts().reset_index()
city_counts.columns = ["city", "count"]
fig = px.bar(
    city_counts,
    x="count",
    y="city",
    orientation="h",
    color="count",
    color_continuous_scale="Viridis",
    title="Students by City",
    labels={"count": "Students", "city": ""},
)
fig.update_layout(template="plotly_dark", yaxis={"categoryorder": "total ascending"},
                  height=450, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
st.plotly_chart(fig, use_container_width=True)

st.divider()

col_c, col_d = st.columns(2)

with col_c:
    gender_city = students.groupby(["city", "gender"]).size().reset_index(name="count")
    fig = px.bar(
        gender_city,
        x="city",
        y="count",
        color="gender",
        barmode="group",
        color_discrete_map={"Male": "#6366f1", "Female": "#f472b6"},
        title="Gender Breakdown by City",
    )
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

with col_d:
    age_city = students.groupby("city")["age"].mean().reset_index().sort_values("age")
    fig = px.bar(
        age_city,
        x="age",
        y="city",
        orientation="h",
        color="age",
        color_continuous_scale="RdYlBu_r",
        title="Average Age by City",
        labels={"age": "Avg Age", "city": ""},
    )
    fig.update_layout(template="plotly_dark", yaxis={"categoryorder": "total ascending"},
                      height=400, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

students["enrollment_date"] = pd.to_datetime(students["enrollment_date"])
enroll_ts = students.groupby("enrollment_date").size().reset_index(name="count")
fig = px.area(
    enroll_ts,
    x="enrollment_date",
    y="count",
    title="Enrollment Timeline",
    labels={"enrollment_date": "Date", "count": "Enrollments"},
)
fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
st.plotly_chart(fig, use_container_width=True)
