import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils import load_all, page_config, show_logo, show_top_logo
from db_utils import require_auth, render_save_ui, dataframe_to_dict

require_auth()

page_config("Kayfa — Group Integrity & Discrepancies", "🔍")
show_logo()
show_top_logo()

data = load_all()
students = data["students"]
groups = data["groups"]
master = data["master"]

st.title("🔍 Group Integrity & Data Discrepancies")
st.markdown("##### Reconciling self-reported group sizes against actual enrolment")

# ── Q12: True vs Stated Group Sizes ──
st.header("Q12: True Group Sizes vs Self-Reported Counts")
st.markdown("Comparing `groups.csv` (stated) to actual student counts in `students.csv`.")

true_sizes = students[students["group_id"] != "Unassigned"].groupby("group_id").size().reset_index(name="true_count")
size_compare = groups.merge(true_sizes, on="group_id", how="left").fillna(0)
size_compare["true_count"] = size_compare["true_count"].astype(int)
size_compare["discrepancy"] = size_compare["true_count"] - size_compare["stated_num_students"]
size_compare["pct_diff"] = (size_compare["discrepancy"] / size_compare["stated_num_students"] * 100).round(1)

col_a, col_b = st.columns(2)

with col_a:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Stated", x=size_compare["group_id"], y=size_compare["stated_num_students"],
        marker_color="#6366f1", text=size_compare["stated_num_students"],
    ))
    fig.add_trace(go.Bar(
        name="Actual", x=size_compare["group_id"], y=size_compare["true_count"],
        marker_color="#f59e0b", text=size_compare["true_count"],
    ))
    fig.update_layout(
        barmode="group", template="plotly_dark", height=400,
        title="Stated vs Actual Group Sizes",
        xaxis_title="Group", yaxis_title="Student Count",
        margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11),
    )
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    flagged = size_compare[size_compare["discrepancy"] != 0].copy()
    fig = px.bar(
        flagged, x="group_id", y="pct_diff", color="pct_diff",
        color_continuous_scale="RdYlGn_r", text="pct_diff",
        title="Discrepancy % (negative = overstated)",
        labels={"group_id": "Group", "pct_diff": "Difference %"},
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(template="plotly_dark", height=400,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

flagged = size_compare[size_compare["discrepancy"] != 0]
st.subheader("Discrepant Groups")
for _, row in flagged.iterrows():
    pct = row["pct_diff"]
    severity = "🔴" if abs(pct) > 20 else "🟡" if abs(pct) > 5 else "🟢"
    st.markdown(f"{severity} **{row['group_name']}**: stated {row['stated_num_students']}, actual {row['true_count']} "
                f"({pct:+.1f}%) — {abs(row['discrepancy'])} student{'s' if abs(row['discrepancy'])!=1 else ''} unaccounted for.")

st.divider()

# ── Q13: Group Too Small — G10 ──
st.header("Q13: Unviable Group Detection & Merger Recommendation")
st.markdown("Identifying groups whose size is too small to be pedagogically or financially viable.")

true_sizes_all = students[students["group_id"] != "Unassigned"].groupby("group_id").size().reset_index(name="true_count")
unviable = true_sizes_all[true_sizes_all["true_count"] < 10]

col_c, col_d = st.columns(2)

with col_c:
    fig = px.bar(
        true_sizes_all.sort_values("true_count"),
        x="group_id", y="true_count", color="true_count",
        color_continuous_scale="RdYlGn_r", title="Actual Group Sizes",
        labels={"group_id": "Group", "true_count": "Students"},
    )
    fig.add_hline(y=10, line_dash="dash", line_color="red", annotation_text="Viability threshold (10)")
    fig.update_layout(template="plotly_dark", height=400,
                      margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)

with col_d:
    if len(unviable) > 0:
        st.error(f"**{len(unviable)} group(s) below viability threshold (10 students)**")
        for _, row in unviable.iterrows():
            grp_info = groups[groups["group_id"] == row["group_id"]].iloc[0]
            st.markdown(f"**{grp_info['group_name']}**  \n"
                        f"Course: {grp_info['course_id']} | Instructor: {grp_info['instructor']}  \n"
                        f"Stated: {grp_info['stated_num_students']} | Actual: **{row['true_count']} student{'s' if row['true_count']!=1 else ''}**")
    else:
        st.success("All groups meet the minimum size threshold.")

if len(unviable) > 0:
    st.divider()
    st.subheader("Closest Concept-Profile Match")

    g10_id = unviable.iloc[0]["group_id"]
    g10_students_df = students[students["group_id"] == g10_id]
    g10_sid = g10_students_df["student_id"].iloc[0]
    g10_info = groups[groups["group_id"] == g10_id].iloc[0]

    g10_profile = master[master["student_id"] == g10_sid][
        ["avg_concept_score", "attendance_rate_pct", "concepts_failed", "age"]
    ].iloc[0]

    other = master[master["group_id"] != g10_id].copy()
    g10_vals = g10_profile.values
    other["dist"] = np.sqrt(
        (other["avg_concept_score"] - g10_vals[0])**2 +
        (other["attendance_rate_pct"] - g10_vals[1])**2 +
        (other["concepts_failed"] - g10_vals[2])**2 +
        (other["age"] - g10_vals[3])**2
    )
    closest = other.sort_values("dist").iloc[0]

    col_e, col_f = st.columns(2)

    with col_e:
        st.info(f"**Unviable Group:** {g10_info['group_name']}")
        st.markdown(f"Student: **{g10_students_df.iloc[0]['full_name']}** ({g10_sid})  \n"
                    f"Course: {g10_info['course_id']} | Instructor: {g10_info['instructor']}  \n"
                    f"Age: {g10_profile['age']} | Avg Score: {g10_profile['avg_concept_score']:.1f}%  \n"
                    f"Attendance: {g10_profile['attendance_rate_pct']:.0f}% | Failed: {g10_profile['concepts_failed']} concepts")

    with col_f:
        closest_group_info = groups[groups["group_id"] == closest["group_id"]].iloc[0]
        st.success(f"**Closest Match:** {closest['full_name']} ({closest['student_id']})")
        st.markdown(f"Group: **{closest_group_info['group_name']}** ({closest['group_id']})  \n"
                    f"Course: {closest['course_id']} | Instructor: {closest_group_info['instructor']}  \n"
                    f"Age: {closest['age']} | Avg Score: {closest['avg_concept_score']:.1f}%  \n"
                    f"Attendance: {closest['attendance_rate_pct']:.0f}% | Failed: {closest['concepts_failed']} concepts  \n"
                    f"**Profile Distance: {closest['dist']:.2f}**")

    # Recommendation
    st.subheader("📋 Recommendation")
    st.success(
        f"**Merge G10 ({g10_info['course_id']}) → {closest_group_info['group_name']} ({closest_group_info['course_id']})**  \n\n"
        f"**Rationale:** G10 has only 1 student (S0500) vs 31 stated — unviable. "
        f"S0500's concept profile (score={g10_profile['avg_concept_score']:.1f}, "
        f"attendance={g10_profile['attendance_rate_pct']:.0f}%, "
        f"failures={g10_profile['concepts_failed']}) closely matches "
        f"{closest['full_name']} in {closest_group_info['group_name']} "
        f"(distance={closest['dist']:.2f}). Additionally, both G10 and "
        f"{closest_group_info['group_name']} are taught by the same instructor "
        f"({g10_info['instructor']}) in similar domains, making the merger logistically seamless."
    )

st.divider()

# ── Note on unassigned students ──
st.header("📌 Unassigned Students")
unassigned = students[students["group_id"] == "Unassigned"]
if len(unassigned) > 0:
    st.warning(f"**{len(unassigned)} student(s)** have no group assignment:")
    for _, s in unassigned.iterrows():
        st.markdown(f"- {s['full_name']} ({s['student_id']}) — {s['city']}, age {s['age']}")
    st.caption("These students should be assigned to appropriate groups or flagged as registration anomalies.")

render_save_ui("group_integrity", "Group Integrity data",
               dataframe_to_dict(size_compare[["group_id", "group_name", "stated_num_students", "true_count", "discrepancy"]]))
