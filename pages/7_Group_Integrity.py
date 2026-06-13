import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils import load_data, page_config, show_logo, show_top_logo
from db_utils import require_auth, render_save_ui, dataframe_to_dict

require_auth()

page_config("Kayfa — Group Integrity & Discrepancies", "🔍")
show_logo()
show_top_logo()

master = load_data()

st.title("🔍 Group Integrity & Data Discrepancies")
st.markdown("##### Analyzing group sizes and student profiles")

# ── Q12: True Group Sizes ──
st.header("Q12: True Group Sizes")
st.markdown("Actual student counts per group from the master dataset.")

true_sizes = master[master["group_id"] != "Unassigned"].groupby("group_id").size().reset_index(name="true_count")
true_sizes = true_sizes.sort_values("true_count")
median_size = true_sizes["true_count"].median()

col_a, col_b = st.columns(2)

with col_a:
    colors = ["#ef4444" if r["true_count"] < 10 else "#f59e0b" if r["true_count"] < 15 else "#10b981"
              for _, r in true_sizes.iterrows()]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=true_sizes["true_count"], y=true_sizes["group_id"],
        orientation="h", marker_color=colors,
        text=true_sizes["true_count"],
        textposition="outside",
    ))
    fig.add_vline(x=10, line_dash="dash", line_color="red", annotation_text="Viability (10)")
    fig.update_layout(
        template="plotly_dark", height=400,
        title="Actual Group Sizes (Red < 10 = unviable)",
        xaxis_title="Student Count", yaxis_title="Group",
        margin=dict(l=0, r=0, t=40, b=0), font=dict(size=11),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Median group size: {median_size:.0f} students. Groups below the red line (<10) may be unviable.")

with col_b:
    unviable = true_sizes[true_sizes["true_count"] < 10]
    if len(unviable) > 0:
        st.error(f"**{len(unviable)} group(s) below viability threshold (10 students)**")
        for _, row in unviable.iterrows():
            grp_students = master[master["group_id"] == row["group_id"]]
            st.markdown(f"**Group {row['group_id']}** — {int(row['true_count'])} student(s)")
            for _, s in grp_students.iterrows():
                st.markdown(f"- {s['full_name']} ({s['student_id']}), {s['course_name']}, {s['instructor']}")
    else:
        st.success("All groups meet the minimum size threshold.")

st.divider()

# ── Q13: Unviable Group Merger ──
st.header("Q13: Unviable Group Detection & Merger Recommendation")
st.markdown("Finding the closest concept-profile match for students in unviable groups.")

unviable_groups = true_sizes[true_sizes["true_count"] < 10]

if len(unviable_groups) > 0:
    gid = unviable_groups.iloc[0]["group_id"]
    gid_students = master[master["group_id"] == gid]
    gid_sid = gid_students["student_id"].iloc[0]

    gid_profile = master[master["student_id"] == gid_sid][
        ["avg_concept_score", "attendance_rate_pct", "concepts_failed", "age"]
    ].iloc[0]

    other = master[master["group_id"] != gid].copy()
    gid_vals = gid_profile.values
    other["dist"] = np.sqrt(
        (other["avg_concept_score"] - gid_vals[0])**2 +
        (other["attendance_rate_pct"] - gid_vals[1])**2 +
        (other["concepts_failed"] - gid_vals[2])**2 +
        (other["age"] - gid_vals[3])**2
    )
    closest = other.sort_values("dist").iloc[0]

    col_c, col_d = st.columns(2)

    with col_c:
        st.info(f"**Unviable Group:** {gid}")
        st.markdown(f"Student: **{gid_students.iloc[0]['full_name']}** ({gid_sid})  \n"
                    f"Course: {gid_students.iloc[0]['course_name']} | Instructor: {gid_students.iloc[0]['instructor']}  \n"
                    f"Age: {gid_profile['age']} | Avg Score: {gid_profile['avg_concept_score']:.1f}%  \n"
                    f"Attendance: {gid_profile['attendance_rate_pct']:.0f}% | Failed: {gid_profile['concepts_failed']} concepts")

    with col_d:
        st.success(f"**Closest Match:** {closest['full_name']} ({closest['student_id']})")
        st.markdown(f"Group: **{closest['group_id']}**  \n"
                    f"Course: {closest['course_name']} | Instructor: {closest['instructor']}  \n"
                    f"Age: {closest['age']} | Avg Score: {closest['avg_concept_score']:.1f}%  \n"
                    f"Attendance: {closest['attendance_rate_pct']:.0f}% | Failed: {closest['concepts_failed']} concepts  \n"
                    f"**Profile Distance: {closest['dist']:.2f}**")

    st.subheader("📋 Recommendation")
    st.success(
        f"**Merge Group {gid} → Group {closest['group_id']}**  \n\n"
        f"**Rationale:** Group {gid} has only {int(unviable_groups.iloc[0]['true_count'])} student(s) — unviable. "
        f"The student's concept profile closely matches {closest['full_name']} in Group {closest['group_id']} "
        f"(distance={closest['dist']:.2f}). Merging would provide a better learning environment."
    )
else:
    st.success("No unviable groups detected — all groups have 10+ students.")

st.divider()

# ── Unassigned students ──
st.header("📌 Unassigned Students")
unassigned = master[master["group_id"] == "Unassigned"]
if len(unassigned) > 0:
    st.warning(f"**{len(unassigned)} student(s)** have no group assignment:")
    for _, s in unassigned.iterrows():
        st.markdown(f"- {s['full_name']} ({s['student_id']}) — {s['city']}, age {s['age']}")
    st.caption("These students should be assigned to appropriate groups or flagged as registration anomalies.")

render_save_ui("group_integrity", "Group Integrity data",
               dataframe_to_dict(true_sizes))
