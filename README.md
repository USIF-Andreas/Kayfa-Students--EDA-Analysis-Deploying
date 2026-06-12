# Kayfa Students — EDA Analysis & Interactive Dashboard

A comprehensive **Streamlit + Plotly** dashboard for analyzing student performance, engagement, attendance, and behavioral patterns across Kayfa's educational platform. Built with a multi-page architecture, cached data pipelines, and professional visualizations.

---

## Dashboard Overview

The dashboard transforms **7 raw datasets** (student registry, grades, attendance, engagement events, submissions, groups, and a master feature table) into **6 interactive pages** with 30+ Plotly charts, KPI metric cards, and data-driven insights.

### Architecture

```
kayfa-students--eda-analysis-deploying/
├── Home.py                     # Executive Dashboard (entry point)
├── utils.py                    # Shared data loader, cached computations, logo
├── requirements.txt            # Python dependencies
├── pages/
│   ├── 1_Demographics.py       # Student demographics
│   ├── 2_Academic_Performance.py  # Grades & concept mastery
│   ├── 3_Engagement.py         # Platform behavior & device usage
│   ├── 4_Attendance.py         # Session attendance patterns
│   ├── 5_Submissions.py        # Procrastination & effort analysis
│   └── 6_Insights.py           # Recommendations, teacher ranking, verdict
└── data/
    ├── clean_students.csv
    ├── clean_groups.csv
    ├── clean_submissions.csv
    ├── clean_grades.csv
    ├── clean_attendance.csv
    ├── clean_engagement.csv
    └── master_student_features.csv
```

**Total: ~1,800 lines of Python**, 7 CSV data sources, zero external services.

---

## Pages & Features

### 1. Executive Dashboard (`Home.py`)

High-level KPIs and cross-sectional overview:
- **4 KPI cards**: Total Students, Avg Attendance, Avg Concept Score, Avg Fail Rate
- Score by Category (Analytics, Programming, Business, Design)
- Score by Difficulty Level (Beginner, Intermediate, Advanced)
- Instructor ranking by score and attendance
- Assessment type performance with standard deviation
- Engagement event distribution (donut chart)

### 2. Demographics (`pages/1_Demographics.py`)

Student population analysis:
- Age distribution histogram
- Gender distribution (donut chart)
- City enrollment ranking
- Gender breakdown by city (grouped bars)
- Average age by city
- Enrollment timeline (area chart)

### 3. Academic Performance (`pages/2_Academic_Performance.py`)

Deep dive into grades and assessments:
- Overall score distribution
- Box plots by assessment type (quiz, assignment, exam, practical)
- Per-assessment average scores
- Quiz score progression (Quiz 1 → Quiz 4)
- Student average distribution
- Attendance vs concept score (bubble scatter)

### 4. Engagement (`pages/3_Engagement.py`)

Platform behavioral telemetry:
- Event type breakdown (login, video_watch, resource_download, quiz_attempt, forum_post)
- Device usage split (web vs mobile)
- Weekly activity trend (area chart)
- Event type × Device heatmap
- Video watch duration histogram
- Events per student distribution
- **Interactive filter**: Select/deselect event types

### 5. Attendance (`pages/4_Attendance.py`)

Commitment tracking:
- Pie chart: attended vs absent
- Attendance rate by group
- Daily attendance trend (line chart)
- Attendance by day of week
- Attendance distribution by instructor (box plot)
- Scatter: Attendance vs Concept Score (with OLS trendline)

### 6. Insights & Recommendations (`pages/6_Insights.py`)

Strategic analysis layer:
- **Instructor leaderboard** (🥇🥈🥉 ranked with metrics)
- **Student-to-Teacher candidates**: students with ≥85% score, ≥90% attendance, ≤5% fail rate
- Candidate identification scatter plot (with Candidate Zone quadrant)
- Candidate breakdown by category
- 6 actionable recommendations
- **Verdict: "Is Kayfa Worth It?"** — data-driven answer with KPI cards

---

## Data Sources & Report

### Dataset Overview

| File | Rows | Columns | Description |
|------|------|---------|-------------|
| `clean_students.csv` | 500 | 8 | Demographics (age, gender, city, group) |
| `clean_groups.csv` | 10 | 7 | Cohort structure (instructor, schedule) |
| `clean_submissions.csv` | 1,504 | 10 | Homework log (time, attempts, lateness) |
| `clean_grades.csv` | 5,502 | 10 | Assessment scores by type |
| `clean_attendance.csv` | 2,111 | 6 | Session attendance ledger |
| `clean_engagement.csv` | 30,866 | 6 | Platform event telemetry |
| `master_student_features.csv` | 500 | 17 | Flattened ML-ready feature table |

### Key Findings

| Metric | Value |
|--------|-------|
| Total Students | 500 |
| Average Age | 21.4 (range 17–31) |
| Gender Split | 53% Female, 47% Male |
| Cities | 10 (Zagazig leads, Cairo lowest) |
| Instructors | 4 (Dr. Mona Saad, Eng. Hossam Refaat, Dr. Laila ElBaz, Eng. Khaled Adel) |
| Overall Avg Score | 70.5% |
| Avg Concept Score | 70.4% |
| Avg Attendance Rate | 79.3% |
| Avg Fail Rate | 23.9% |
| Late Submissions | 35.9% |
| Avg Time on Assignments | 120 min |
| Total Engagement Events | 30,866 |
| Mobile Usage Share | 40% |
| Top Instructor Score | ~78% |
| Student-to-Teacher Candidates | ~20 students |

### Performance by Assessment Type

| Type | Avg Score |
|------|----------|
| Assignment | 65.3% |
| Exam | 72.6% |
| Practical | 72.4% |
| Quiz | 72.3% |

### Engagement Event Mix

| Event | Count | Share |
|-------|-------|-------|
| Login | 11,052 | 35.8% |
| Video Watch | 8,817 | 28.6% |
| Resource Download | 4,439 | 14.4% |
| Quiz Attempt | 4,318 | 14.0% |
| Forum Post | 2,240 | 7.3% |

---

## Technical Implementation

### Stack
- **Frontend**: Streamlit 1.58+ (multi-page app)
- **Visualization**: Plotly Express + Plotly Graph Objects (dark theme)
- **Data**: Pandas 3.x (cached with `@st.cache_data`)
- **Statistics**: Statsmodels (OLS trendlines)

### Performance Optimizations
- **Data caching**: All 7 CSV files cached in memory via `@st.cache_data`
- **Computation caching**: 9 reusable cached functions for expensive groupby/merge operations
- **Session state**: Engagement page filter persists across reruns
- **Lazy loading**: Each page loads only the datasets it needs

### Key Design Decisions
- **Multi-page architecture**: Native Streamlit sidebar navigation
- **Consistent dark theme**: Plotly `template="plotly_dark"` across all charts
- **Contextual insights**: `st.caption()` under every plot with computed statistics
- **Logo branding**: Sidebar + page-top logo via shared `utils.py` functions

---

## How to Run

### Local
```bash
pip install -r requirements.txt
streamlit run Home.py
```

### Deployed (Streamlit Cloud)
1. Push repo to GitHub
2. Connect at [streamlit.io/cloud](https://streamlit.io/cloud)
3. Set entry point: `Home.py`
4. Requirements auto-installed from `requirements.txt`

### Requirements
```
streamlit>=1.28.0
pandas>=2.0.0
plotly>=5.17.0
statsmodels>=0.14.0
numpy>=1.24.0
```

---

## Recommendation Summary

1. **Early Warning System** — Alert when attendance drops below 70% or 2+ late assignments
2. **Instructor Peer Mentoring** — Pair lower-performing instructors with top performers
3. **Mobile Experience Overhaul** — Mobile users show 34% shorter engagement; UX audit needed
4. **Targeted City Interventions** — Fayoum/Asyut underperform — consider local study groups
5. **Student-to-Teacher Pipeline** — ~20 candidates identified for instructor training
6. **Concept Curriculum Review** — Redesign materials for top-5 hardest concepts

---

## Verdict

> **Yes — Kayfa is delivering value.** The data shows a functioning educational platform with a ~70% pass rate, strong instructor talent, and an emerging student-to-teacher pipeline. The core product works. The path to excellence lies in tackling procrastination, closing geographic gaps, and investing in the mobile experience.

---

*Built with Streamlit + Plotly • Kayfa Student Analytics v1.0*
