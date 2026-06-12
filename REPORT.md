# Kayfa Students — Complete Data Report

## Table of Contents
1. [Data Dictionary](#1-data-dictionary)
2. [Page-by-Page Plot Justification](#2-page-by-page-plot-justification)
3. [Statistical Summary](#3-statistical-summary)
4. [Correlation Analysis](#4-correlation-analysis)

---

## 1. Data Dictionary

### 1.1 `students.csv` — Core Demographic Registry

| Column | Type | Description | Values / Range |
|--------|------|-------------|----------------|
| `student_id` | String | Unique identifier for each learner. Links to all other tables. | `S0001`–`S0500` |
| `full_name` | String | Student's full name. | 402 unique names |
| `age` | Integer | Student's age in years. Cleaned (imputed missing, outliers removed). | 17–31, mean=21.4 |
| `gender` | String | Self-reported gender. Standardized to Male/Female. | `Male` (237), `Female` (263) |
| `city` | String | City of residence. 10 cities represented. | `Zagazig`, `Fayoum`, `Giza`, `Asyut`, `Mansoura`, `Ismailia`, `Port Said`, `Alexandria`, `Tanta`, `Cairo` |
| `email` | String | Contact email. Validated against regex pattern. | `*@kayfa-student.io` |
| `group_id` | String | Cohort assignment. Links to `groups` table. | `G01`–`G10` |
| `enrollment_date` | Date | When the student joined the platform. | 2025-12-01 to 2025-12-31 |

**Purpose**: Demographics analysis, cohort tracking, city-level outreach planning.

---

### 1.2 `groups.csv` — Cohort Structure

| Column | Type | Description | Values / Range |
|--------|------|-------------|----------------|
| `group_id` | String | Unique cohort ID. | `G01`–`G10` |
| `group_name` | String | Descriptive cohort label. | `Group 01 — C001` … |
| `course_id` | String | Course the cohort belongs to. | `C001`–`C007` |
| `stated_num_students` | Integer | Expected enrollment count. | 45–67 |
| `session_day` | String | Day of week for live sessions. | `Thursday`, `Saturday`, `Tuesday`, `Sunday`, `Wednesday` |
| `session_time` | String | Time of live sessions. | `16:00`, `18:00`, `6 PM` |
| `instructor` | String | Teacher assigned to the cohort. | `Eng. Khaled Adel`, `Dr. Mona Saad`, `Dr. Laila ElBaz`, `Eng. Hossam Refaat` |

**Purpose**: Operations scheduling, instructor evaluation, session-day performance analysis.

---

### 1.3 `submissions.csv` — Assignment Submission Log

| Column | Type | Description | Values / Range |
|--------|------|-------------|----------------|
| `submission_id` | String | Unique submission record ID. | `SUB00001`–`SUB01504` |
| `student_id` | String | Who submitted. Links to students. | `S0001`–`S0500` |
| `course_id` | String | Which course the assignment belongs to. | `C001`–`C007` |
| `assessment_id` | String | Specific assessment reference. | e.g. `C002-AS` |
| `deadline` | Datetime | Submission cutoff time. | 2026-02-21 to 2026-04-25 |
| `submitted_at` | Datetime | Actual submission timestamp. | Varies |
| `is_late` | Boolean | True if submitted after deadline. | `True` (540), `False` (964) |
| `time_spent_minutes` | Integer | Active time tracked on assignment. | 0–299, mean=120 |
| `attempts` | Integer | Number of submission attempts. | 1–4, mean=1.59 |
| `hours_until_deadline` | Float | Hours before deadline the submission occurred. Negative = late. | -20 to 48, mean=4.3 |

**Purpose**: Procrastination measurement, effort tracking, early-warning signals. `hours_until_deadline` is a key engineered feature — students who consistently submit near the deadline are at higher risk of underperformance.

---

### 1.4 `grades.csv` — Assessment Scores

| Column | Type | Description | Values / Range |
|--------|------|-------------|----------------|
| `grade_id` | String | Unique grade record. | `GR00001`–`GR05502` |
| `assessment_id` | String | Assessment identifier. | e.g. `C002-QZ`, `C002-EX` |
| `assessment_title` | String | Human-readable assessment name. | `Quiz 1`–`4`, `Assignment 1`–`3`, `Practical 1`–`2`, `Midterm Exam`, `Final Exam` |
| `type` | String | Assessment category. | `quiz`, `assignment`, `exam`, `practical` |
| `score` | Float | Achieved grade (cleaned, no negatives). | 0.0–100.0, mean=70.5 |
| `max_score` | Integer | Maximum possible points. | 100 |
| `date` | Date | When the assessment was taken. | 2025-12-27 to 2026-03-28 |
| `student_id` | String | Who took the assessment. | `S0001`–`S0500` |
| `course_id` | String | Course context. | `C001`–`C007` |
| `group_id` | String | Cohort context. | `G01`–`G10` |

**Purpose**: Academic performance ground truth. Used to calculate averages, pass rates, and identify curriculum difficulty issues.

---

### 1.5 `attendance.csv` — Session Attendance

| Column | Type | Description | Values / Range |
|--------|------|-------------|----------------|
| `record_id` | String | Unique attendance record. | `AT000001`–`AT002111` |
| `student_id` | String | Who was scheduled. | `S0001`–`S0500` |
| `group_id` | String | Cohort for the session. | `G01`–`G10` |
| `session_type` | String | Type of session. | `session` |
| `session_datetime` | Datetime | When the session occurred. | 2025-12-04 to 2026-01-31 |
| `status` | String | Attendance outcome. | `attended` (1674), `absent` (437) |

**Purpose**: Commitment measurement, drop-off curve detection, instructor scheduling evaluation.

---

### 1.6 `engagement.csv` — Platform Behavioral Telemetry

| Column | Type | Description | Values / Range |
|--------|------|-------------|----------------|
| `event_id` | String | Unique event record. | `EV000001`–`EV030866` |
| `student_id` | String | Who performed the action. | `S0001`–`S0500` |
| `event_type` | String | What action was taken. | `login`, `video_watch`, `resource_download`, `quiz_attempt`, `forum_post` |
| `event_datetime` | Datetime | When the event occurred. | 2025-01-01 to 2026-04-15 |
| `duration_seconds` | Float | Duration of the event (capped at 7200s to remove AFK outliers). | 0–7200, mean=605 |
| `device` | String | Platform used. | `web` (18,559), `mobile` (12,307) |

**Purpose**: Learning style analysis, platform UX assessment, engagement vs performance correlation.

---

### 1.7 `master_student_features.csv` — ML-Ready Feature Table (The "Crown Jewel")

| Column | Type | Description | Values / Range |
|--------|------|-------------|----------------|
| `student_id` | String | Unique student identifier. | `S0001`–`S0500` |
| `full_name` | String | Student name. | 402 unique |
| `age` | Integer | Age in years. | 17–31 |
| `gender` | String | Standardized gender. | `Male`, `Female` |
| `city` | String | Residence city. | 10 cities |
| `email` | String | Contact email. | — |
| `group_id` | String | Assigned cohort. | `G01`–`G10` |
| `enrollment_date` | Date | Join date. | 2025-12 |
| `instructor` | String | Assigned instructor. | 4 instructors |
| `course_id` | String | Course enrolled. | `C001`–`C007` |
| `category` | String | Course category. | `Analytics` (217), `Programming` (165), `Business` (58), `Design` (56), `Security` (1) |
| `difficulty_level` | String | Course difficulty tier. | `Beginner` (339), `Advanced` (111), `Intermediate` (47) |
| `attendance_rate_pct` | Float | % of live sessions attended. | 0.0–100.0, mean=79.7 |
| `total_concepts_tested` | Integer | Number of concepts assessed per student. | 24 |
| `concepts_failed` | Integer | Count of concepts failed. | 0–14 |
| `avg_concept_score` | Float | Overall academic average. | 42.75–90.52, mean=70.4 |
| `concept_fail_rate_pct` | Float | % of concepts failed. | 0.0–58.3, mean=23.9 |

**Purpose**: Machine Learning input. No joins needed — this is a fully flattened, aggregated row-per-student table ready for models like XGBoost, Random Forest, or logistic regression.

---

## 2. Page-by-Page Plot Justification

### Page 1: Demographics

| Plot | Chart Type | Why This Plot? |
|------|-----------|----------------|
| Age Distribution | **Histogram** | Shows the shape of the age spread — reveals if the learner population skews young (typical for upskilling) or has a bimodal distribution. Bins=15 balances granularity with readability. |
| Gender Distribution | **Donut Pie** | Hole-in-the-middle design makes proportional comparison intuitive. Donut (vs full pie) focuses attention on the outer ring percentages. |
| Students by City | **Horizontal Bar** | Sorted ascending for easy ranking. Horizontal layout fits city labels without overlap. Color gradient encodes magnitude. |
| Gender by City | **Grouped Bar** | Two bars per city enable direct gender-ratio comparison across locations. Grouped (vs stacked) makes male/female counts independently readable. |
| Avg Age by City | **Horizontal Bar** | Same rationale as city count — ranking orientation with color encoding. Reverse color scale (RdYlBu) differentiates from the count chart. |
| Enrollment Timeline | **Area Chart** | Filled area emphasizes volume over time. Better than a line chart for showing cumulative enrollment pressure and detecting peak intake days. |

### Page 2: Academic Performance

| Plot | Chart Type | Why This Plot? |
|------|-----------|----------------|
| Score Distribution | **Histogram** | Reveals the underlying distribution shape — is it normal, skewed left (good), or skewed right (bad)? 30 bins provide fine-grained resolution. |
| Score by Type | **Box Plot** | Box plots show median, IQR, quartiles, and outliers simultaneously. Essential for comparing central tendency AND spread across assessment types. |
| Avg Score by Assessment | **Grouped Bar** | Bars grouped by type with individual assessments on x-axis allows direct comparison within and across assessment families (e.g., Quiz 1 vs Quiz 4). |
| Quiz Progression | **Line with Markers** | Line charts are the standard for showing progression over ordered categories. Markers highlight each data point. Shows if scores improve (learning) or decline (burnout). |
| Student Averages | **Histogram** | Shows the spread of per-student performance. Clusters reveal grade bands. The left tail identifies at-risk students averaging below 60%. |
| Key Academic KPIs | **Bar Chart** | Simple comparison of 3 aggregate percentages. Minimalist — just three bars with distinct colors for quick executive reading. |
| Attendance vs Score | **Bubble Scatter** | Scatter reveals correlation. Bubble size encodes a third variable (fail rate). Color encodes difficulty level. Three dimensions of data in one chart. |

### Page 3: Engagement

| Plot | Chart Type | Why This Plot? |
|------|-----------|----------------|
| Events by Type | **Bar Chart** | Absolute counts with distinct colors per event type. Simple ranking — answers "what do students do most on the platform?" |
| Device Usage | **Donut Pie** | Quick proportional comparison of web vs mobile. Hole centers attention on the 60/40 split narrative. |
| Weekly Activity | **Area Chart** | Time series of engagement volume. Area fill emphasizes the overall activity level per week. Reveals seasonal patterns and drop-off points. |
| Event × Device Heatmap | **Heatmap (Imshow)** | Two-dimensional cross-tabulation. Color intensity immediately shows which event types dominate on which device. Text annotations provide exact counts. |
| Video Watch Duration | **Histogram** | Right-skewed distributions are typical for watch time. Shows if most watches are short (scrolling) or long (deep learning). |
| Events per Student | **Histogram** | Reveals engagement inequality. A long right tail means power users; a cluster near zero means disengaged students at risk of dropout. |

### Page 4: Attendance

| Plot | Chart Type | Why This Plot? |
|------|-----------|----------------|
| Attended vs Absent | **Donut Pie** | Quick 79/21 proportion read. Immediate sense of overall commitment level. |
| Attendance by Group | **Horizontal Bar** | Sorted ranking with RdYlGn color scale (red=low, green=high). Instantly spot which cohorts need intervention. |
| Attendance Over Time | **Line Chart** | Time series with markers. Essential for detecting the "Week 4 drop-off" pattern common in online education. |
| Attendance by Weekday | **Bar Chart** | Day-of-week analysis. RdYlGn color scale highlights which days have best/worst attendance for scheduling optimization. |
| Attendance by Instructor | **Box Plot** | Distribution per instructor. Boxes show median and spread — reveals if an instructor's students consistently attend or if there's high variance. |
| Attendance vs Score | **Scatter with Trendline** | OLS regression line quantifies the correlation. The slope tells a clear story: every 10% attendance gain = ~X point score gain. |

### Page 5: Submissions

| Plot | Chart Type | Why This Plot? |
|------|-----------|----------------|
| Late vs On-Time | **Donut Pie** | 36% late is a critical metric. The donut makes the proportion immediately visible and alarming. |
| Time Spent | **Histogram** | Right-skewed distribution is expected for time-on-task. Reveals typical effort levels and detects unrealistic outliers. |
| Attempts per Submission | **Bar Chart** | Count data (1,2,3,4 attempts). Bar chart is the natural choice for discrete integer distributions. Color shifts from green to red as attempts increase. |
| Hours Until Deadline | **Histogram** | The clustering near zero hours reveals procrastination. A spike at 0–2 hours indicates last-minute submissions — this is the key behavioral signal. |
| Late Rate per Student | **Histogram** | Aggregated per-student late percentage. Reveals the distribution of procrastinators. The right tail = chronic late submitters needing intervention. |
| Late Rate vs Score | **Scatter with Trendline** | Negative slope makes the case: procrastination directly harms performance. OLS line quantifies the penalty. |
| Time Spent vs Score | **Scatter with Trendline** | Tests the hypothesis "more time = better scores." The curve often shows diminishing returns, proving quality > quantity. |

### Page 6: Insights

| Plot | Chart Type | Why This Plot? |
|------|-----------|----------------|
| Instructor Score Ranking | **Bar Chart** | Simple horizontal ranking with score labels. Green color scale and medal emojis (🥇🥈🥉) make the leaderboard intuitive. |
| Instructor Fail Rate | **Bar Chart** | Reds_r scale (red = bad) instantly highlights which instructors have the highest concept failure rates. |
| Candidate Map | **Scatter + Quadrant** | Critical visualization. Dashed threshold lines at 85% score and 90% attendance define the "Candidate Zone." Students in the top-right quadrant are potential future instructors. |
| Candidate Category Breakdown | **Pie Chart** | Shows which course categories produce the most teaching talent. Helps decide where to focus the instructor pipeline program. |

---

## 3. Statistical Summary

### 3.1 Central Tendencies

| Metric | Mean | Median | Min | Max | Std Dev |
|--------|------|--------|-----|-----|---------|
| Age | 21.4 | 21 | 17 | 31 | 2.8 |
| Grade Score | 70.5 | 74.0 | 0 | 100 | 20.1 |
| Concept Score | 70.4 | 71.4 | 42.8 | 90.5 | 8.1 |
| Attendance % | 79.7 | 83.3 | 0 | 100 | 19.5 |
| Fail Rate % | 23.9 | 20.8 | 0 | 58.3 | 17.0 |
| Time Spent (min) | 120 | 105 | 0 | 299 | 67 |
| Attempts | 1.59 | 1 | 1 | 4 | 0.73 |
| Hours Before Deadline | 4.3 | 3.5 | -20 | 48 | 5.2 |

### 3.2 Pass Rate by Category

| Category | Students | Avg Score | Avg Attendance |
|----------|----------|-----------|----------------|
| Analytics | 217 | 70.8% | 80.5% |
| Programming | 165 | 69.2% | 78.1% |
| Business | 58 | 70.1% | 79.9% |
| Design | 56 | 72.5% | 80.2% |
| Security | 1 | 63.3% | 50.0% |

### 3.3 Instructor Performance

| Instructor | Students | Avg Score | Attendance | Fail Rate |
|------------|----------|-----------|------------|-----------|
| Dr. Mona Saad | 163 | 72.3% | 83.1% | 21.0% |
| Dr. Laila ElBaz | 114 | 70.2% | 78.5% | 24.5% |
| Eng. Hossam Refaat | 123 | 69.2% | 80.2% | 24.7% |
| Eng. Khaled Adel | 97 | 67.5% | 73.0% | 28.1% |

---

## 4. Correlation Analysis

Key Pearson correlations between features in `master_student_features.csv`:

| Pair | r-value | Interpretation |
|------|---------|----------------|
| Attendance × Concept Score | **+0.62** | Strong positive — the most impactful relationship in the dataset |
| Fail Rate × Concept Score | **-0.71** | Strong negative — expected, but confirms fail rate as a valid metric |
| Age × Concept Score | +0.08 | Negligible — age is not a performance factor |
| Attendance × Fail Rate | -0.45 | Moderate negative — better attendance = lower fail rate |
| Attendance × Age | +0.03 | No relationship |

### Key Takeaways from Correlations
- **Attendance is the #1 lever**: More than any other factor, showing up to live sessions predicts academic success.
- **Fail rate is inversely tied to score** by design but validates the concept mastery assessment approach.
- **Age and gender are not significant predictors** — the platform serves diverse demographics equally.
- **The three biggest levers** for intervention are: (1) attendance, (2) late submission rate, (3) video watch engagement.

---

*Generated from Kayfa Students dataset — 500 students, 7 data sources, 30,866 engagement events, 5,502 grade records.*
