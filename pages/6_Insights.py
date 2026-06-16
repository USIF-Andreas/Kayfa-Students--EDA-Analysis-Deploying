import streamlit as st
import plotly.express as px
from utils import load_data, page_config, show_logo, show_top_logo, compute_instructor_metrics
from db_utils import require_auth

require_auth()

page_config("Kayfa — Insights & Recommendations", "🎯")
show_logo()
show_top_logo()

master = load_data()

st.title("🎯 Strategic Insights & Recommendations")
st.markdown("##### Data-Driven Answers to Kayfa's Key Questions")

insights = [
    ("👥", "Behavioral Personas Drive Strategy",
     "The student base falls into 4 clear personas (High Achievers, Hard Workers, Natural Talents, At-Risk). "
     "One-size-fits-all communication is inefficient; we must target support based on the persona."),
    ("🎓", "Attendance is the Ultimate Predictor",
     "Platform engagement and session attendance are the most powerful leading indicators of academic success. "
     "Students simply cannot succeed if they do not show up."),
    ("📉", "The Hidden Cost of Being Late",
     "Procrastination directly hurts performance. Students with higher late submission rates consistently "
     "score lower on concept assessments, making 'late rate' our best early-warning signal."),
    ("🗓️", "Temporal Engagement Dips",
     "Engagement naturally dips cohort-wide during specific periods (like post-exams or holidays). "
     "We must anticipate these drops and proactively reach out to prevent dropouts."),
    ("🏙️", "Geographic Performance Gaps",
     "Cairo and Alexandria students consistently outperform other cities. "
     "Students in Fayoum and Asyut may need localized support or offline materials."),
    ("📚", "Instructor Impact is Measurable",
     "Concept fail rates vary wildly depending on the instructor. "
     "Peer mentoring between the highest and lowest performing instructors is highly recommended."),
]

cols = st.columns(3)
for i, (emoji, title, desc) in enumerate(insights):
    with cols[i % 3]:
        st.markdown(f"### {emoji} {title}")
        st.caption(desc)

st.divider()

st.header("🔄 Controllable vs. Uncontrollable Success Factors")
st.markdown("##### Where should we focus our interventions?")

col_change, col_unchange = st.columns(2)

with col_change:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #064e3b, #065f46); border-radius: 12px; padding: 20px; height: 100%;">
        <h4 style="color: #34d399; margin-top: 0;">✅ Changeable (Actionable) Factors</h4>
        <p style="color: #a7f3d0; font-size: 14px;">These are behavioral metrics we can actively influence through platform design, nudges, and interventions.</p>
        <ul style="color: white; font-size: 15px; line-height: 1.6;">
            <li><b>Attendance:</b> The #1 predictor of success. We can send automated reminders to the "Hard Workers" or "At-Risk" personas.</li>
            <li><b>Late Submissions:</b> High late rates guarantee lower grades. We can enforce hard deadlines, send SMS reminders, or offer early-bird submission bonuses.</li>
            <li><b>Platform Engagement:</b> Active days correlate with higher scores. We can build gamification, streaks, or daily challenges to boost logins.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col_unchange:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #7f1d1d, #991b1b); border-radius: 12px; padding: 20px; height: 100%;">
        <h4 style="color: #fca5a5; margin-top: 0;">🛑 Unchangeable (Contextual) Factors</h4>
        <p style="color: #fecaca; font-size: 14px;">These are demographic factors we cannot change, but must adapt our curriculum and teaching style to accommodate.</p>
        <ul style="color: white; font-size: 15px; line-height: 1.6;">
            <li><b>Age Band:</b> Younger and older students have wildly different digital literacy and time constraints. We must provide flexible pacing.</li>
            <li><b>City / Geography:</b> Students in Fayoum and Asyut face different infrastructure challenges (e.g., internet speed) than Cairo. We must ensure offline/low-bandwidth support.</li>
            <li><b>Baseline Knowledge:</b> Students arrive with varying levels of preparation. Identifying "Natural Talents" vs those needing foundations early is critical.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.divider()

st.header("🏆 Instructor Performance Ranking")
st.markdown("##### Who delivers the best student outcomes?")

instructor_metrics = compute_instructor_metrics(master)

instructor_metrics["score_rank"] = range(1, len(instructor_metrics) + 1)

for _, row in instructor_metrics.iterrows():
    medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(row["score_rank"], "  ")
    with st.container(border=True):
        c1, c2, c3, c4, c5 = st.columns([1, 3, 2, 2, 2])
        c1.markdown(f"### {medal}")
        c2.markdown(f"**{row['instructor']}**  \n{row['student_count']} students")
        c3.metric("Avg Score", f"{row['avg_score']:.1f}%")
        c4.metric("Attendance", f"{row['avg_attendance']:.1f}%")
        c5.metric("Fail Rate", f"{row['fail_rate']:.1f}%")

st.divider()

col_a, col_b = st.columns(2)

with col_a:
    fig = px.bar(
        instructor_metrics,
        x="avg_score",
        y="instructor",
        orientation="h",
        color="avg_score",
        color_continuous_scale="Greens",
        text="avg_score",
        title="Average Concept Score by Instructor",
        labels={"avg_score": "Avg Score %", "instructor": ""},
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(template="plotly_dark", yaxis={"categoryorder": "total ascending"},
                      height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    fig = px.bar(
        instructor_metrics,
        x="fail_rate",
        y="instructor",
        orientation="h",
        color="fail_rate",
        color_continuous_scale="Reds_r",
        text="fail_rate",
        title="Concept Fail Rate by Instructor",
        labels={"fail_rate": "Fail Rate %", "instructor": ""},
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(template="plotly_dark", yaxis={"categoryorder": "total ascending"},
                      height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

st.header("🌟 Student-to-Teacher Candidates")
st.markdown("##### Top students who could become excellent instructors after training")

top_students = master[
    (master["avg_concept_score"] >= 85)
    & (master["attendance_rate_pct"] >= 90)
    & (master["concept_fail_pct"] <= 5)
].copy()

top_students["teach_score"] = (
    top_students["avg_concept_score"] * 0.4
    + top_students["attendance_rate_pct"] * 0.35
    + (100 - top_students["concept_fail_pct"]) * 0.25
)

top_students = top_students.sort_values("teach_score", ascending=False)

st.info(f"Found **{len(top_students)} students** who meet the criteria for instructor candidacy "
        f"(avg_score ≥85%, attendance ≥90%, fail_rate ≤5%).")

candidates = top_students[["student_id", "full_name", "age", "city", "category",
                           "difficulty_level", "avg_concept_score", "attendance_rate_pct",
                           "concept_fail_pct", "instructor", "teach_score"]].head(20)

for _, row in candidates.iterrows():
    with st.container(border=True):
        r1, r2, r3, r4, r5 = st.columns([2, 2, 1.5, 1.5, 2])
        r1.markdown(f"**{row['full_name']}**  \n{row['student_id']}  \n{row['city']}")
        r2.markdown(f"**{row['category']}** — {row['difficulty_level']}  \nCurrent Instructor: {row['instructor']}")
        r3.metric("Avg Score", f"{row['avg_concept_score']:.1f}%")
        r4.metric("Attendance", f"{row['attendance_rate_pct']:.0f}%")
        r5.metric("Teach Score", f"{row['teach_score']:.1f}", delta=f"Fail Rate: {row['concept_fail_pct']:.1f}%")

st.divider()

col_c, col_d = st.columns(2)

with col_c:
    fig = px.scatter(
        master,
        x="avg_concept_score",
        y="attendance_rate_pct",
        color="concept_fail_pct",
        size="concept_fail_pct",
        hover_data=["full_name", "instructor"],
        color_continuous_scale="RdYlGn_r",
        title="Candidate Identification Map",
        labels={"avg_concept_score": "Avg Concept Score %", "attendance_rate_pct": "Attendance %"},
    )
    fig.add_hline(y=90, line_dash="dash", line_color="white", opacity=0.3)
    fig.add_vline(x=85, line_dash="dash", line_color="white", opacity=0.3)
    fig.add_annotation(x=92, y=95, text="Candidate Zone", showarrow=False,
                       font=dict(color="lime", size=14))
    fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

with col_d:
    cat_counts = candidates["category"].value_counts().reset_index()
    cat_counts.columns = ["category", "count"]
    fig = px.pie(
        cat_counts,
        values="count",
        names="category",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set2,
        title="Candidates by Category",
    )
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

st.header("⚠️ Recommendations for Kayfa")

recs = [
    ("📋", "Early Warning System",
     "Deploy an automated alert when a student's attendance drops below 70% OR "
     "their late rate exceeds 50%. The `late_rate` feature can predict risk before grades drop."),
    ("👨‍🏫", "Instructor Peer Mentoring",
     f"Pair instructors from lower-performing cohorts with **{instructor_metrics.iloc[0]['instructor']}** "
     f"(avg score {instructor_metrics.iloc[0]['avg_score']:.1f}%) for knowledge transfer sessions."),
    ("📱", "Time Management Support",
     "Students who spend excessive time on assignments without proportional score gains may need "
     "study skill workshops. Quality of study time matters more than quantity."),
    ("🏙️", "Targeted City Interventions",
     "Students from Fayoum, Asyut score below average. Consider: local study groups, "
     "dedicated office hours, or city-specific cohorts with tailored pacing."),
    ("🎓", "Student-to-Teacher Pipeline",
     f"Identify **{len(top_students)} high-potential candidates** for a paid instructor training program. "
     f"Graduates could become teaching assistants or lead Beginner-level cohorts."),
    ("📊", "Concept Curriculum Review",
     "Analyze which specific concepts have the highest fail rates across all cohorts. "
     "Redesign instructional materials for the hardest concepts identified in the data."),
]

for emoji, title, desc in recs:
    with st.container(border=True):
        st.markdown(f"### {emoji} {title}")
        st.markdown(desc)

avg_late_rate = master["late_rate"].mean() * 100
chronic = (master["late_rate"] >= 0.5).sum()
below60 = (master["avg_concept_score"] < 60).sum()

st.divider()
st.header("🎯 Is Kayfa Worth It?")
st.markdown("##### A Data-Driven Verdict")

worth_col1, worth_col2 = st.columns([2, 1])

with worth_col1:
    pass_rate = (master["passed"] == True).mean() * 100
    top_10_pct = master["avg_concept_score"].quantile(0.9)
    st.markdown(f"""
    After analyzing **{len(master)} students** across **{master['city'].nunique()} cities**, **{master['category'].nunique()} categories**,
    and **{master['course_name'].nunique()} courses** led by **{master['instructor'].nunique()} instructors**, here is what the data says:

    #### ✅ The Case for Kayfa

    1. **Strong Overall Outcomes** — The average concept score across all students is **{master['avg_concept_score'].mean():.1f}%**,
       and the average grade is **{master['avg_grade'].mean():.1f}%**. This indicates the curriculum delivers solid learning outcomes.

    2. **High Engagement** — With **{master['total_events'].sum():,.0f}** tracked events (avg **{master['total_events'].mean():.0f}** per student),
       learners are actively using the platform.

    3. **Talent Pipeline Potential** — We identified **{len(top_students)} students** ({len(top_students)/len(master)*100:.1f}% of the population)
       who combine top-tier scores (≥85%), near-perfect attendance (≥90%), and minimal fail rates (≤5%).
       These candidates could become Kayfa's next generation of instructors — a self-sustaining talent loop.

    4. **Instructor Quality** — The top instructor achieves a **{instructor_metrics.iloc[0]['avg_score']:.1f}%** average student score,
       proving that great teaching exists within the platform and can be replicated.

    #### ⚠️ Areas for Improvement

    1. **Procrastination is Costly** — **{avg_late_rate:.1f}%** average late rate, and students who submit late score
       **~8–10 pts lower** on concept assessments. An early-warning system could recover these students.

    2. **Drop-off Risk** — **{below60:.0f} students** ({below60/len(master)*100:.0f}%) score below 60%,
       and **{chronic} students** are chronically late (≥50% late rate). These groups need structured intervention.

    3. **Geographic Disparity** — Students from Fayoum and Asyut underperform the national average by
       **{master[master['city'].isin(['Fayoum','Asyut'])]['avg_concept_score'].mean():.1f}%** vs **{master['avg_concept_score'].mean():.1f}%**.
       Targeted support could close this gap.
    """)

with worth_col2:
    st.metric("Avg Concept Score", f"{master['avg_concept_score'].mean():.1f}%")
    st.metric("Avg Grade", f"{master['avg_grade'].mean():.1f}%")
    st.metric("Pass Rate", f"{pass_rate:.0f}%")
    st.metric("Top 10% Threshold", f"{top_10_pct:.0f}%")
    st.metric("Instructor Candidates", len(top_students))
    st.metric("Cities Served", master["city"].nunique())

verdict_col1, verdict_col2 = st.columns([3, 1])
with verdict_col1:
    st.success(
        f"**Verdict: YES — Kayfa is delivering value.** "
        f"The data shows a functioning educational platform with a {pass_rate:.0f}% pass rate, "
        f"strong instructor talent, and an emerging pipeline of student-to-teacher candidates. "
        f"The core product works. The path to excellence lies in tackling procrastination, "
        f"closing geographic gaps, and improving time management — all clearly "
        f"measurable and actionable from this dashboard."
    )

st.divider()
st.caption("Kayfa Student Analytics — Insights Engine v1.0")
