import streamlit as st
import pandas as pd
from utils import load_data, page_config, show_logo, show_top_logo
from db_utils import authenticate_user, register_user, logout, db_available

page_config("Kayfa Students", "📊")
show_logo()
show_top_logo()

master = load_data()

# ── Login / Logout ──
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔐 Kayfa Student Analytics")
    st.markdown("##### Sign in to access the dashboard")

    if not db_available():
        st.info("⚠️ **MongoDB Atlas unreachable** — using local file storage. Login/register will work.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Login")
        with st.form("login_form"):
            l_user = st.text_input("Username", key="login_user")
            l_pass = st.text_input("Password", type="password", key="login_pass")
            if st.form_submit_button("Login", use_container_width=True):
                ok, msg = authenticate_user(l_user, l_pass)
                if ok:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = l_user
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    with col2:
        st.subheader("Register")
        with st.form("register_form"):
            r_user = st.text_input("Username", key="reg_user")
            r_pass = st.text_input("Password", type="password", key="reg_pass")
            r_confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
            if st.form_submit_button("Register", use_container_width=True):
                if r_pass != r_confirm:
                    st.error("Passwords do not match")
                elif len(r_pass) < 4:
                    st.error("Password must be at least 4 characters")
                else:
                    ok, msg = register_user(r_user, r_pass)
                    if ok:
                        st.success(msg)
                        st.info("You can now log in.")
                    else:
                        st.error(msg)
    st.stop()

# ── Authenticated: show data info ──
st.success(f"✅ Logged in as **{st.session_state['username']}**")
if st.button("Logout"):
    logout()

st.title("📊 Kayfa Student Analytics")
st.markdown("##### Dataset Overview")

total = len(master)
courses = master["course_name"].nunique()
cities = master["city"].nunique()
instructors = master["instructor"].nunique()
pass_count = master["passed"].sum()
fail_count = (~master["passed"]).sum()
avg_grade = master["avg_grade"].mean()
avg_concept = master["avg_concept_score"].mean()
avg_att = master["attendance_rate_pct"].mean()
avg_fail_rate = master["concept_fail_pct"].mean()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Students", total)
col2.metric("Courses", courses)
col3.metric("Cities", cities)
col4.metric("Instructors", instructors)

col5, col6, col7, col8 = st.columns(4)
col5.metric("Passed", pass_count)
col6.metric("Failed", fail_count)
col7.metric("Avg Grade", f"{avg_grade:.1f}%")
col8.metric("Avg Concept Score", f"{avg_concept:.1f}%")

col9, col10, col11, col12 = st.columns(4)
col9.metric("Avg Attendance", f"{avg_att:.1f}%")
col10.metric("Avg Fail Rate", f"{avg_fail_rate:.1f}%")
col11.metric("Total Events", f"{master['total_events'].sum():,.0f}")
col12.metric("Total Submissions", f"{master['total_submissions'].sum():,.0f}")

st.divider()

st.subheader("Column Overview")
col_info = pd.DataFrame({
    "Column": master.columns,
    "Type": master.dtypes.values,
    "Non-Null": master.count().values,
    "Unique": [master[c].nunique() for c in master.columns],
    "Sample": [str(master[c].iloc[0]) for c in master.columns],
})
st.dataframe(col_info, use_container_width=True, hide_index=True)

st.divider()

st.subheader("Data Summary")
st.dataframe(master.describe(), use_container_width=True)

st.divider()

st.subheader("Available Pages")
st.markdown("""
| Page | Description |
|---|---|
| 👥 Demographics | Age, gender, city distribution |
| 📚 Academic Performance | Grades, concept scores, course comparison |
| ⚡ Engagement | Events, video watch time, time spent |
| 📅 Attendance | Attendance rates by group, instructor, course |
| 📝 Submissions | Late rates, time spent, submission patterns |
| 🎯 Insights | Instructor ranking, recommendations, verdict |
| 🔍 Group Integrity | Group sizes, unviable group detection |
| 📈 Engagement Trends | Attendance & engagement correlations |
| 🎯 Performance Deep Dive | Course comparison, attendance vs grade |
| 📉 Curriculum Weak Spots | High-failure concepts and courses |
| ⚠️ Student Risk & Segmentation | Age bands, clustering, at-risk ranking |
| 📊 Group Performance Trends | Group-level performance comparison |
""")
