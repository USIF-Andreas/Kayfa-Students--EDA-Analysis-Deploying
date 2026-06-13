import pandas as pd
import numpy as np
from scipy.stats import pearsonr
import warnings
warnings.filterwarnings("ignore")

BASE = "."
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)
pd.set_option("display.width", 200)
pd.set_option("display.float_format", lambda x: "%.2f" % x)

master = pd.read_csv(f"{BASE}/master_student_features.csv")
groups = pd.read_csv(f"{BASE}/clean_groups.csv")
students = pd.read_csv(f"{BASE}/clean_students.csv")
grades = pd.read_csv(f"{BASE}/clean_grades.csv")
attendance = pd.read_csv(f"{BASE}/clean_attendance.csv")
engagement = pd.read_csv(f"{BASE}/clean_engagement.csv")
submissions = pd.read_csv(f"{BASE}/clean_submissions.csv")

# ── Clean data ──
attendance["status"] = attendance["status"].str.strip().str.lower()
attendance = attendance[attendance["status"].isin(["attended", "absent"])]
grades = grades[grades["assessment_title"] != "Bonus Exam"]

# ── Helper: merge student groups ──
student_with_group = students.merge(groups[["group_id", "group_name"]], on="group_id", how="left")

print("=" * 100)
print("Q1: ATTENDANCE RATE PER GROUP — Groups below platform average")
print("=" * 100)

att_by_student = attendance.groupby("student_id")["status"].apply(lambda x: (x == "attended").mean() * 100).reset_index(name="att_rate")
att_by_student = att_by_student.merge(students[["student_id", "group_id"]], on="student_id")
att_by_group = att_by_student.groupby("group_id")["att_rate"].agg(["mean", "std", "count"]).reset_index()
att_by_group.columns = ["group_id", "avg_att_rate", "std_att_rate", "n_students"]
att_by_group = att_by_group.merge(groups[["group_id", "group_name", "course_id", "instructor"]], on="group_id")
platform_avg_att = att_by_student["att_rate"].mean()
print(f"Platform-wide average attendance rate: {platform_avg_att:.2f}%")
print()
att_by_group = att_by_group.sort_values("avg_att_rate", ascending=False)
print(att_by_group[["group_name", "course_id", "instructor", "avg_att_rate", "n_students"]].to_string(index=False))
print()
print("--- Groups BELOW platform average ---")
below = att_by_group[att_by_group["avg_att_rate"] < platform_avg_att]
print(below[["group_name", "course_id", "instructor", "avg_att_rate"]].to_string(index=False))

print()
print("=" * 100)
print("Q2: SCORE DISTRIBUTION BY ASSESSMENT TYPE — Volatility")
print("=" * 100)

type_stats = grades.groupby("type")["score"].agg(["mean", "std", "count", "min", "max"]).reset_index()
type_stats.columns = ["type", "mean", "std", "count", "min", "max"]
type_stats["cv"] = type_stats["std"] / type_stats["mean"] * 100  # coefficient of variation
print(type_stats.to_string(index=False))
print()
most_volatile = type_stats.sort_values("cv", ascending=False).iloc[0]
print(f"Most volatile: {most_volatile['type']} (CV = {most_volatile['cv']:.1f}%, std = {most_volatile['std']:.2f})")

print()
print("=" * 100)
print("Q3: COURSE WITH HIGHEST / LOWEST AVERAGE GRADE & SPREAD")
print("=" * 100)

course_grades = grades.groupby("course_id")["score"].agg(["mean", "std", "count", "median"]).reset_index()
course_grades.columns = ["course_id", "mean", "std", "count", "median"]
course_grades = course_grades.sort_values("mean", ascending=False)
print(course_grades.to_string(index=False))
highest = course_grades.iloc[0]
lowest = course_grades.iloc[-1]
print(f"\nHighest: {highest['course_id']} (mean={highest['mean']:.2f}, std={highest['std']:.2f})")
print(f"Lowest:  {lowest['course_id']} (mean={lowest['mean']:.2f}, std={lowest['std']:.2f})")
print(f"Spread ratio (std highest / std lowest): {highest['std'] / lowest['std']:.2f}")

print()
print("=" * 100)
print("Q4: ATTENDANCE vs AVERAGE GRADE — Correlation")
print("=" * 100)

student_grade_avg = grades.groupby("student_id")["score"].mean().reset_index(name="avg_grade")
merged_att_grade = att_by_student.merge(student_grade_avg, on="student_id")
r, p = pearsonr(merged_att_grade["att_rate"], merged_att_grade["avg_grade"])
print(f"Pearson r = {r:.4f}, p-value = {p:.4e}")
# Bucket
merged_att_grade["att_bucket"] = pd.cut(merged_att_grade["att_rate"], bins=[0, 40, 60, 80, 90, 100], labels=["0-40%", "40-60%", "60-80%", "80-90%", "90-100%"])
trend = merged_att_grade.groupby("att_bucket", observed=True)["avg_grade"].agg(["mean", "std", "count"])
print(trend.to_string())

print()
print("=" * 100)
print("Q5: ENGAGEMENT (logins + video_watch) vs ACADEMIC PERFORMANCE")
print("=" * 100)

login_count = engagement[engagement["event_type"] == "login"].groupby("student_id").size().reset_index(name="login_count")
video_time = engagement[engagement["event_type"] == "video_watch"].groupby("student_id")["duration_seconds"].sum().reset_index(name="total_video_sec")
video_time["total_video_hrs"] = video_time["total_video_sec"] / 3600

eng_student = login_count.merge(video_time, on="student_id", how="outer").fillna(0)
eng_student = eng_student.merge(student_grade_avg, on="student_id")

r_logins, p_logins = pearsonr(eng_student["login_count"], eng_student["avg_grade"])
r_video, p_video = pearsonr(eng_student["total_video_sec"], eng_student["avg_grade"])

print(f"Login count vs Avg Grade: r = {r_logins:.4f}, p = {p_logins:.4e}")
print(f"Video watch time (sec) vs Avg Grade: r = {r_video:.4f}, p = {p_video:.4e}")

# Composite engagement score
eng_student["eng_z_logins"] = (eng_student["login_count"] - eng_student["login_count"].mean()) / eng_student["login_count"].std()
eng_student["eng_z_video"] = (eng_student["total_video_hrs"] - eng_student["total_video_hrs"].mean()) / eng_student["total_video_hrs"].std()
eng_student["eng_composite"] = eng_student["eng_z_logins"] + eng_student["eng_z_video"]

r_comp, p_comp = pearsonr(eng_student["eng_composite"], eng_student["avg_grade"])
print(f"Composite engagement vs Avg Grade: r = {r_comp:.4f}, p = {p_comp:.4e}")

# Quartile
eng_student["eng_quartile"] = pd.qcut(eng_student["eng_composite"], 4, labels=["Q1 (Low)", "Q2", "Q3", "Q4 (High)"])
eng_trend = eng_student.groupby("eng_quartile", observed=True)["avg_grade"].agg(["mean", "std", "count"])
print(eng_trend.to_string())

print()
print("=" * 100)
print("Q6: CONCEPTS WITH HIGHEST FAILURE RATE — Curriculum Weak Spot")
print("=" * 100)

# Master already has per-student concept fail info
# The concept fail rate in master is per student - we need per CONCEPT
# We use grades to identify which specific assessments/concepts have highest fail rates
# A failing score = score < 50 (commonly used threshold)

grades["passed"] = (grades["score"] >= 50).astype(int)
concept_fail = grades.groupby(["course_id", "assessment_title", "type"])["passed"].agg(["count", "sum"]).reset_index()
concept_fail.columns = ["course_id", "assessment_title", "type", "total_students", "passed_count"]
concept_fail["fail_rate"] = (1 - concept_fail["passed_count"] / concept_fail["total_students"]) * 100
concept_fail = concept_fail.sort_values("fail_rate", ascending=False)

print("Top 10 concepts with highest failure rate:")
print(concept_fail.head(10).to_string(index=False))
print()
worst = concept_fail.iloc[0]
print(f"SINGLE BIGGEST CURRICULUM WEAK SPOT:")
print(f"  Course: {worst['course_id']}")
print(f"  Assessment: {worst['assessment_title']} ({worst['type']})")
print(f"  Fail rate: {worst['fail_rate']:.1f}%")
print(f"  Total students tested: {worst['total_students']}")

print()
print("=" * 100)
print("Q7: COHORT MASTERY OVER TIME FOR WEAKEST CONCEPT")
print("=" * 100)

# The weakest concept from Q6 is... let me check the actual worst concept
worst_course = worst["course_id"]
worst_title = worst["assessment_title"]

# For concept mastery over time, we look at how scores change across successive assessments of that type
# For the specific weak concept, track all occurrences
concept_over_time = grades[grades["assessment_title"] == worst_title].copy()
concept_over_time["date"] = pd.to_datetime(concept_over_time["date"])
concept_over_time = concept_over_time.sort_values("date")
print(f"Tracking: {worst_title} in {worst_course}")
print(f"  Overall scores: mean={concept_over_time['score'].mean():.2f}, std={concept_over_time['score'].std():.2f}")
print()

# Track by date (per assessment occurrence)
by_date = concept_over_time.groupby("date")["score"].agg(["mean", "std", "count"]).reset_index()
by_date.columns = ["date", "avg_score", "std", "count"]
print("Scores by date:")
print(by_date.to_string(index=False))
print()

# Check for trend
if len(by_date) > 1:
    first_half = by_date.iloc[:len(by_date)//2]["avg_score"].mean()
    second_half = by_date.iloc[len(by_date)//2:]["avg_score"].mean()
    direction = "improving" if second_half > first_half else "declining"
    print(f"First half avg: {first_half:.2f}")
    print(f"Second half avg: {second_half:.2f}")
    print(f"Trend: {direction}")

# Also check if there are multiple assessments building up to this concept
# Look at the course's assessment sequence
print()
print("Full assessment sequence for this course:")
course_seq = grades[grades["course_id"] == worst_course].copy()
course_seq["date"] = pd.to_datetime(course_seq["date"])
course_seq = course_seq.sort_values("date")
seq_by_date = course_seq.groupby(["date", "assessment_title", "type"])["score"].mean().reset_index()
print(seq_by_date.to_string(index=False))

print()
print("=" * 100)
print("Q8: LATE SUBMISSIONS / BUFFER TIME vs SCORES")
print("=" * 100)

sub_merged = submissions.merge(student_grade_avg, on="student_id")

late_stats = sub_merged.groupby("is_late")["avg_grade"].agg(["mean", "std", "count"])
print("Average grade by lateness status:")
print(late_stats.to_string())
print()

sub_merged["buffer_bucket"] = pd.cut(sub_merged["hours_until_deadline"], 
                                      bins=[-50, 0, 6, 12, 24, 48],
                                      labels=["missed deadline", "0-6hr", "6-12hr", "12-24hr", "24hr+"])
buffer_trend = sub_merged.groupby("buffer_bucket", observed=True)["avg_grade"].agg(["mean", "std", "count"])
print("Average grade by submission buffer time:")
print(buffer_trend.to_string())
print()

if sub_merged["hours_until_deadline"].nunique() > 1 and sub_merged["avg_grade"].nunique() > 1:
    r_buffer, p_buffer = pearsonr(sub_merged["hours_until_deadline"], sub_merged["avg_grade"])
    print(f"Correlation hours_until_deadline vs avg_grade: r = {r_buffer:.4f}, p = {p_buffer:.4e}")
else:
    print("Correlation hours_until_deadline vs avg_grade: N/A (insufficient variance)")

# Per-submission score
per_sub = submissions.merge(grades[["student_id", "assessment_id", "score"]], on=["student_id", "assessment_id"], how="left")
per_sub = per_sub.dropna(subset=["score"])
if per_sub["hours_until_deadline"].nunique() > 1 and per_sub["score"].nunique() > 1:
    r_sub, p_sub = pearsonr(per_sub["hours_until_deadline"], per_sub["score"])
    print(f"Correlation hours_until_deadline vs per-assignment score: r = {r_sub:.4f}, p = {p_sub:.4e}")
else:
    print("Correlation hours_until_deadline vs per-assignment score: N/A (insufficient variance)")

late_vs_early = per_sub.groupby("is_late")["score"].agg(["mean", "std", "count"])
print("\nPer-assignment score by lateness:")
print(late_vs_early.to_string())

print()
print("=" * 100)
print("Q9: ATTENDANCE AND ENGAGEMENT OVER TIME — Cohort Dip")
print("=" * 100)

# Attendance: dates only in Dec 2025, so monthly window is limited
att_time = attendance.copy()
att_time["session_datetime"] = pd.to_datetime(att_time["session_datetime"])
att_time["week"] = att_time["session_datetime"].dt.to_period("W").dt.start_time
att_weekly = att_time.groupby("week")["status"].apply(lambda x: (x == "attended").mean() * 100).reset_index(name="att_rate")
att_weekly = att_weekly.sort_values("week")
print("Weekly attendance rate:")
print(att_weekly.to_string(index=False))
print()

# Engagement over time
eng_time = engagement.copy()
eng_time["event_datetime"] = pd.to_datetime(eng_time["event_datetime"])
eng_time["week"] = eng_time["event_datetime"].dt.to_period("W").dt.start_time
eng_weekly = eng_time.groupby("week").size().reset_index(name="event_count")
eng_weekly = eng_weekly.sort_values("week")
print("Weekly engagement events (first 30 rows):")
print(eng_weekly.head(30).to_string(index=False))
print()

# Filter to relevant term (roughly Oct 2025 - May 2026)
eng_term = eng_time[(eng_time["event_datetime"] >= "2025-10-01") & (eng_time["event_datetime"] <= "2026-06-01")]
eng_weekly_term = eng_term.groupby("week").size().reset_index(name="event_count")
eng_weekly_term = eng_weekly_term.sort_values("week")
print("Weekly engagement during term (Oct 2025 - May 2026):")
print(eng_weekly_term.to_string(index=False))
print()

# Find lowest point
min_eng = eng_weekly_term.loc[eng_weekly_term["event_count"].idxmin()]
print(f"Lowest engagement week: {min_eng['week']} ({min_eng['event_count']} events)")

if len(att_weekly) > 1:
    min_att = att_weekly.loc[att_weekly["att_rate"].idxmin()]
    print(f"Lowest attendance week: {min_att['week']} ({min_att['att_rate']:.1f}%)")

print()
print("=" * 100)
print("Q10: AGE BANDS vs OUTCOMES")
print("=" * 100)

master["age_band"] = pd.cut(master["age"], bins=[0, 20, 25, 30, 35, 100], labels=["18-20", "21-25", "26-30", "31-35", "36+"])
age_analysis = master.groupby("age_band", observed=True).agg(
    avg_grade=("avg_concept_score", "mean"),
    avg_att=("attendance_rate_pct", "mean"),
    avg_fail_rate=("concept_fail_rate_pct", "mean"),
    count=("student_id", "count")
).reset_index()
print(age_analysis.to_string(index=False))
print()

# Add engagement per age band
eng_count = engagement.groupby("student_id").size().reset_index(name="total_events")
video_sum = engagement[engagement["event_type"] == "video_watch"].groupby("student_id")["duration_seconds"].sum().reset_index(name="total_video_sec")
eng_per_student = eng_count.merge(video_sum, on="student_id", how="left").fillna(0)
eng_per_student = eng_per_student.merge(master[["student_id", "age_band"]], on="student_id")

eng_age = eng_per_student.groupby("age_band", observed=True).agg(
    avg_events=("total_events", "mean"),
    avg_video_sec=("total_video_sec", "mean")
).reset_index()
print("Engagement by age band:")
print(eng_age.to_string(index=False))

print()
print("=" * 100)
print("Q11: STUDENT SEGMENTATION (attendance, engagement, grade, failed concepts)")
print("=" * 100)

# Manual KMeans since sklearn not available
def kmeans_manual(X, k=4, max_iter=100, seed=42):
    np.random.seed(seed)
    n = X.shape[0]
    idx = np.random.choice(n, k, replace=False)
    centroids = X[idx].copy()
    for _ in range(max_iter):
        dists = np.array([[np.linalg.norm(x - c) for c in centroids] for x in X])
        labels = np.argmin(dists, axis=1)
        new_centroids = np.array([X[labels == i].mean(axis=0) if np.any(labels == i) else centroids[i] for i in range(k)])
        if np.allclose(centroids, new_centroids):
            break
        centroids = new_centroids
    return labels, centroids

seg_data = master[["student_id", "attendance_rate_pct", "avg_concept_score", "concepts_failed"]].copy()
eng_features = eng_per_student[["student_id", "total_events", "total_video_sec"]]
seg_data = seg_data.merge(eng_features, on="student_id", how="left").fillna(0)

features = ["attendance_rate_pct", "avg_concept_score", "concepts_failed", "total_events", "total_video_sec"]
# Standardize manually
means = seg_data[features].mean()
stds = seg_data[features].std()
X = (seg_data[features] - means) / stds

labels, centroids = kmeans_manual(X.values, k=4, seed=42)
seg_data["cluster"] = labels

cluster_desc = seg_data.groupby("cluster")[features].mean().round(2)
cluster_counts = seg_data["cluster"].value_counts().sort_index()
cluster_desc["count"] = cluster_counts
print("Cluster profiles (mean values):")
print(cluster_desc.to_string())
print()

labels_map = {}
for c in sorted(seg_data["cluster"].unique()):
    row = cluster_desc.loc[c]
    desc = []
    if row["attendance_rate_pct"] > 80:
        desc.append("high-attendance")
    elif row["attendance_rate_pct"] < 60:
        desc.append("low-attendance")
    if row["avg_concept_score"] > 80:
        desc.append("high-performer")
    elif row["avg_concept_score"] < 65:
        desc.append("low-performer")
    if row["concepts_failed"] > 8:
        desc.append("many-failures")
    elif row["concepts_failed"] < 3:
        desc.append("few-failures")
    if row["total_events"] > 80:
        desc.append("highly-engaged")
    elif row["total_events"] < 30:
        desc.append("disengaged")
    labels_map[c] = ", ".join(desc)
    print(f"Cluster {c}: {labels_map[c]} (n={int(cluster_counts[c])})")

print()
print("=" * 100)
print("Q12: TRUE GROUP SIZES vs STATED — Discrepancy")
print("=" * 100)

true_sizes = students[students["group_id"] != "Unassigned"].groupby("group_id").size().reset_index(name="true_count")
size_compare = groups.merge(true_sizes, on="group_id", how="left").fillna(0)
size_compare["true_count"] = size_compare["true_count"].astype(int)
size_compare["discrepancy"] = size_compare["true_count"] - size_compare["stated_num_students"]
size_compare["pct_diff"] = (size_compare["discrepancy"] / size_compare["stated_num_students"] * 100).round(1)
print(size_compare[["group_id", "group_name", "stated_num_students", "true_count", "discrepancy", "pct_diff"]].to_string(index=False))
print()
flagged = size_compare[size_compare["discrepancy"].abs() > 0]
print("--- Groups with discrepancies ---")
print(flagged[["group_id", "group_name", "stated_num_students", "true_count", "discrepancy", "pct_diff"]].to_string(index=False))

print()
print("=" * 100)
print("Q13: GROUP TOO SMALL — Closest counterpart & recommendation")
print("=" * 100)

print("All group sizes:")
print(size_compare[["group_id", "group_name", "true_count"]].to_string(index=False))
print()

# G10 has only 1 student - too small to be viable
g10_student = students[students["group_id"] == "G10"]
print(f"G10 (C007): only {len(g10_student)} student(s)")
print()

if len(g10_student) == 1:
    g10_sid = g10_student["student_id"].iloc[0]
    # Find closest student by concept profile
    g10_profile = master[master["student_id"] == g10_sid][["avg_concept_score", "attendance_rate_pct", "concepts_failed", "age"]]
    print(f"G10 student ({g10_sid}) profile:")
    print(g10_profile.to_string(index=False))
    print()
    
    other_students = master[master["group_id"] != "G10"].copy()
    # Compute euclidean distance
    g10_vals = g10_profile.values[0]
    other_students["dist"] = np.sqrt(
        (other_students["avg_concept_score"] - g10_vals[0])**2 +
        (other_students["attendance_rate_pct"] - g10_vals[1])**2 +
        (other_students["concepts_failed"] - g10_vals[2])**2 +
        (other_students["age"] - g10_vals[3])**2
    )
    closest = other_students.sort_values("dist").iloc[0]
    print(f"Closest counterpart: {closest['student_id']} ({closest['full_name']})")
    print(f"  Group: {closest['group_id']}, Course: {closest['course_id']}")
    print(f"  Distance: {closest['dist']:.2f}")
    print(f"  Profile: avg_score={closest['avg_concept_score']:.1f}, att={closest['attendance_rate_pct']:.1f}%, failed={closest['concepts_failed']}, age={closest['age']}")
    print()
    print("Recommendation: Merge G10 (C007, 1 student) into the closest group based on")
    print(f"concept profile match. Closest match is {closest['student_id']} in {closest['group_id']}")
    print(f"({closest['group_name'] if 'group_name' in closest.index else 'N/A'}).")

print()
print("=" * 100)
print("Q14: AT-RISK RANKING — Top 10 students")
print("=" * 100)

# Engagement trend: slope of events over time per student
eng_trend_data = eng_term.groupby(["student_id", "week"]).size().reset_index(name="n_events")
def get_trend(grp):
    if len(grp) < 2:
        return 0
    weeks_num = (grp["week"] - grp["week"].min()).dt.days / 7
    if weeks_num.std() == 0:
        return 0
    slope = np.polyfit(weeks_num, grp["n_events"], 1)[0]
    return slope

student_trend = eng_trend_data.groupby("student_id").apply(get_trend).reset_index(name="eng_slope")

# Key concepts failed
key_concepts_failed = master[["student_id", "concepts_failed", "attendance_rate_pct", "avg_concept_score"]].copy()

risk = key_concepts_failed.merge(student_trend, on="student_id", how="left").fillna(0)

# Normalize and create risk score
risk["z_low_att"] = (100 - risk["attendance_rate_pct"]) / risk["attendance_rate_pct"].std()
risk["z_low_grade"] = (100 - risk["avg_concept_score"]) / risk["avg_concept_score"].std()
risk["z_failed"] = risk["concepts_failed"] / risk["concepts_failed"].std()
risk["z_declining"] = -risk["eng_slope"] / risk["eng_slope"].std() if risk["eng_slope"].std() > 0 else 0

risk["risk_score"] = risk["z_low_att"] + risk["z_low_grade"] + risk["z_failed"] + risk["z_declining"]
risk = risk.sort_values("risk_score", ascending=False)

top10 = risk.head(10).merge(students[["student_id", "full_name", "group_id"]], on="student_id")
top10 = top10.merge(groups[["group_id", "group_name"]], on="group_id", how="left")
print("Top 10 At-Risk Students:")
print(top10[["student_id", "full_name", "group_name", "attendance_rate_pct", "avg_concept_score", 
             "concepts_failed", "eng_slope", "risk_score"]].to_string(index=False))

print()
print("=" * 100)
print("Q15: GROUP AVERAGE GRADE TRENDS ACROSS SUCCESSIVE ASSESSMENTS")
print("=" * 100)

# Track each group's avg grade per assessment (ordered by date)
grades_sorted = grades.copy()
grades_sorted["date"] = pd.to_datetime(grades_sorted["date"])
grades_sorted = grades_sorted.sort_values(["group_id", "date"])
grades_sorted["assessment_order"] = grades_sorted.groupby("group_id").cumcount()

group_progression = grades_sorted.groupby(["group_id", "assessment_order"])["score"].mean().reset_index()
group_progression = group_progression.merge(groups[["group_id", "group_name", "course_id"]], on="group_id")

# Compute trend slope per group
def get_group_trend(grp):
    if len(grp) < 3:
        return 0, "insufficient data"
    slope = np.polyfit(grp["assessment_order"], grp["score"], 1)[0]
    direction = "improving" if slope > 0.1 else ("declining" if slope < -0.1 else "stable")
    return slope, direction

trends = group_progression.groupby(["group_id", "group_name", "course_id"]).apply(
    lambda g: pd.Series(get_group_trend(g), index=["slope", "direction"])
).reset_index()
trends = trends.sort_values("slope", ascending=False)
print("Group grade trends across successive assessments:")
print(trends.to_string(index=False))
print()
print("--- Trending UP ---")
print(trends[trends["direction"] == "improving"][["group_id", "group_name", "course_id", "slope"]].to_string(index=False))
print()
print("--- Trending DOWN ---")
print(trends[trends["direction"] == "declining"][["group_id", "group_name", "course_id", "slope"]].to_string(index=False))
