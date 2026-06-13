import streamlit as st
import pandas as pd
import plotly.express as px
from utils import load_data, page_config, show_logo, show_top_logo
from db_utils import require_auth

require_auth()

page_config("Kayfa Students — Demographics", "👥")
show_logo()
show_top_logo()

master = load_data()

st.title("👥 Demographics Analysis")
st.markdown("##### Understanding the Student Population")

total = len(master)
cities = master["city"].nunique()
age_mean = master["age"].mean()
age_min, age_max = master["age"].min(), master["age"].max()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Students", total)
col2.metric("Cities", cities)
col3.metric("Avg Age", f"{age_mean:.1f}")
col4.metric("Age Range", f"{age_min} – {age_max}")

st.divider()

col_a, col_b = st.columns(2)

with col_a:
    fig = px.histogram(
        master, x="age", nbins=15, color_discrete_sequence=["#6366f1"],
        title="Age Distribution",
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    top_age = master["age"].value_counts().idxmax()
    st.caption(f"Most students are {top_age} years old. The cohort skews young (18–24), typical for online upskilling programs.")

with col_b:
    gender_counts = master["gender"].value_counts().reset_index()
    gender_counts.columns = ["gender", "count"]
    fig = px.pie(
        gender_counts, values="count", names="gender", color="gender",
        color_discrete_map={"Male": "#6366f1", "Female": "#f472b6"}, hole=0.5,
        title="Gender Distribution",
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    f_pct = master["gender"].value_counts(normalize=True).get("Female", 0) * 100
    m_pct = master["gender"].value_counts(normalize=True).get("Male", 0) * 100
    st.caption(f"Female students make up {f_pct:.0f}% of the population ({m_pct:.0f}% Male). Near-balanced representation across the platform.")

st.divider()

city_counts = master["city"].value_counts().reset_index()
city_counts.columns = ["city", "count"]
fig = px.bar(
    city_counts, x="count", y="city", orientation="h", color="count",
    color_continuous_scale="Viridis", title="Students by City",
    labels={"count": "Students", "city": ""},
)
fig.update_layout(template="plotly_dark", yaxis={"categoryorder": "total ascending"},
                  height=450, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
st.plotly_chart(fig, use_container_width=True)
city_max = city_counts.iloc[0]["city"]
city_min = city_counts.iloc[-1]["city"]
st.caption(f"Zagazig leads enrollment with {city_counts.iloc[0]['count']} students, while Cairo has the fewest ({city_counts.iloc[-1]['count']}). Geographic outreach varies significantly.")

st.divider()

col_c, col_d = st.columns(2)

with col_c:
    gender_city = master.groupby(["city", "gender"]).size().reset_index(name="count")
    fig = px.bar(
        gender_city, x="city", y="count", color="gender", barmode="group",
        color_discrete_map={"Male": "#6366f1", "Female": "#f472b6"},
        title="Gender Breakdown by City",
    )
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Gender ratios are fairly consistent across cities. No city shows extreme imbalance beyond the overall 53:47 female-to-male split.")

with col_d:
    age_city = master.groupby("city")["age"].mean().reset_index().sort_values("age")
    fig = px.bar(
        age_city, x="age", y="city", orientation="h", color="age",
        color_continuous_scale="RdYlBu_r", title="Average Age by City",
        labels={"age": "Avg Age", "city": ""},
    )
    fig.update_layout(template="plotly_dark", yaxis={"categoryorder": "total ascending"},
                      height=400, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Mean age spans {age_city['age'].min():.1f} to {age_city['age'].max():.1f} across cities — a narrow band suggesting similar learner demographics nationwide.")

st.divider()

master["enrollment_date"] = pd.to_datetime(master["enrollment_date"])
enroll_ts = master.groupby("enrollment_date").size().reset_index(name="count")
fig = px.area(
    enroll_ts, x="enrollment_date", y="count",
    title="Enrollment Timeline",
    labels={"enrollment_date": "Date", "count": "Enrollments"},
)
fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
st.plotly_chart(fig, use_container_width=True)
st.caption(f"Enrollments span {enroll_ts['enrollment_date'].min().date()} to {enroll_ts['enrollment_date'].max().date()}. Peak enrollment days may correlate with marketing campaigns or term start dates.")
