# %% [markdown]
# # ፁ Kayfa Student Education Data — Professional EDA
# **Full Exploratory Data Analysis with Plotly**
# 
# ---

# %% — Install & Import
import pandas as pd
import numpy as np
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

pd.set_option('display.max_columns', 20)
pd.set_option('display.max_rows', 100)

BASE = '.'

# %% [markdown]
# ## 1. Load All Datasets


students = pd.read_csv(f'{BASE}/students.csv')
courses = pd.read_csv(f'{BASE}/courses.csv')
groups = pd.read_csv(f'{BASE}/groups.csv')
submissions = pd.read_csv(f'{BASE}/assignment_submissions.csv')
concepts = pd.read_csv(f'{BASE}/concepts_performance.csv')
engagement = pd.read_csv(f'{BASE}/engagement_events.csv')
attendance = pd.read_excel(f'{BASE}/attendance.xlsx')
with open(f'{BASE}/grades.json', 'r') as f:
    grades_raw = json.load(f)

print("✅ All files loaded successfully!")
print(f"  students:    {students.shape}")
print(f"  courses:     {courses.shape}")
print(f"  groups:      {groups.shape}")
print(f"  submissions: {submissions.shape}")
print(f"  concepts:    {concepts.shape}")
print(f"  engagement:  {engagement.shape}")
print(f"  attendance:  {attendance.shape}")
print(f"  grades:      {len(grades_raw)} entries")

# %% [markdown]
# ## 2. Data Overview & Info

# %%
print("="*60)
print("STUDENTS")
print("="*60)
students.info()
print("\n", students.describe())
print("\n", students.head())

# %%
print("="*60)
print("COURSES")
print("="*60)
print(courses.to_string())

# %%
print("="*60)
print("GROUPS")
print("="*60)
print(groups.to_string())

# %%
print("="*60)
print("SUBMISSIONS (sample)")
print("="*60)
submissions.info()
print("\n", submissions.head(10))

# %%
print("="*60)
print("ENGAGEMENT EVENTS (sample)")
print("="*60)
engagement.info()
print("\n", engagement.head(10))

# %%
print("="*60)
print("ATTENDANCE (sample)")
print("="*60)
attendance.info()
print("\n", attendance.head(10))

# %% [markdown]
# ## 3. Data Quality Audit

# %% [markdown]
# ### 3.1 Missing Values

# %%
def missing_report(df, name):
    m = df.isnull().sum()
    m = m[m > 0]
    if len(m) == 0:
        print(f"  {name}: No missing values ✅")
    else:
        pct = (m / len(df) * 100).round(2)
        report = pd.DataFrame({'missing': m, 'pct': pct})
        print(f"\n  {name}:")
        print(report.to_string())

print("፤ MISSING VALUES REPORT")
print("-"*40)
missing_report(students, 'students')
missing_report(submissions, 'submissions')
missing_report(concepts, 'concepts')
missing_report(engagement, 'engagement')
missing_report(attendance, 'attendance')

# %% [markdown]
# ### 3.2 Students — Quality Issues

# %%
# Blank/whitespace names
blank_names = students[students['full_name'].isna() | (students['full_name'].str.strip() == '')]
print(f"ፃ Blank/missing names: {len(blank_names)}")
print(blank_names[['student_id','full_name','email']].to_string())

# %%
# Invalid ages
invalid_ages = students[(students['age'] < 15) | (students['age'] > 50)]
print(f"\nፃ Invalid ages (outside 15-50): {len(invalid_ages)}")
print(invalid_ages[['student_id','full_name','age']].to_string())

# %%
# Gender inconsistencies
print(f"\nፃ Gender value counts (should be only Male/Female):")
print(students['gender'].value_counts())

# %%
# Invalid emails
import re
email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
bad_emails = students[~students['email'].apply(lambda x: bool(email_pattern.match(str(x))))]
print(f"\nፃ Invalid emails: {len(bad_emails)}")
print(bad_emails[['student_id','full_name','email']].to_string())

# %%
# Duplicate student IDs
dup_ids = students[students['student_id'].duplicated(keep=False)]
print(f"\nፃ Duplicate student_ids: {len(dup_ids)}")
print(dup_ids[['student_id','full_name','age','group_id']].to_string())

# %%
# Invalid group references
valid_groups = set(groups['group_id'].unique())
invalid_grp = students[~students['group_id'].isin(valid_groups)]
print(f"\nፃ Invalid group references: {len(invalid_grp)}")
print(invalid_grp[['student_id','group_id']].to_string())

# %% [markdown]
# ### 3.3 Grades — Quality Issues

# %%
grades_flat = []
for entry in grades_raw:
    for g in entry['grades']:
        row = {**g, 'student_id': entry['student_id'], 'course_id': entry['course_id'], 'group_id': entry['group_id']}
        grades_flat.append(row)
grades = pd.DataFrame(grades_flat)

print(f"Grades flattened: {grades.shape}")
print(f"\nፃ Null scores: {grades['score'].isna().sum()}")
print(grades[grades['score'].isna()][['student_id','assessment_title','score']].to_string())

neg = grades[grades['score'] < 0]
print(f"\nፃ Negative scores: {len(neg)}")
print(neg[['student_id','assessment_title','score','max_score']].to_string())

over = grades[grades['score'] > grades['max_score']]
print(f"\nፃ Score > max_score: {len(over)}")
print(over[['student_id','assessment_title','score','max_score']].to_string())

wrong_max = grades[grades['max_score'] != 100]
print(f"\nፃ Wrong max_score (!=100): {len(wrong_max)}")
print(wrong_max[['student_id','assessment_title','score','max_score']].to_string())

# Flat-line check
student_std = grades.groupby('student_id')['score'].std()
flat = student_std[student_std == 0]
print(f"\nፃ Students with zero score variance (flat-line): {list(flat.index)}")

# %% [markdown]
# ### 3.4 Submissions — Quality Issues

# %%
neg_time = submissions[submissions['time_spent_minutes'] < 0]
print(f"ፃ Negative time_spent: {len(neg_time)}")
print(neg_time[['submission_id','time_spent_minutes']].to_string())

miss_sub = submissions[submissions['submitted_at'].isna()]
print(f"\nፃ Missing submitted_at: {len(miss_sub)}")
print(miss_sub[['submission_id','student_id','deadline']].to_string())

# %% [markdown]
# ### 3.5 Engagement — Quality Issues

# %%
neg_dur = engagement[engagement['duration_seconds'] < 0]
print(f"ፃ Negative duration: {len(neg_dur)}")
print(neg_dur[['event_id','duration_seconds']].to_string())

extreme = engagement[engagement['duration_seconds'] > 7200]
print(f"\nፃ Extreme duration (>2hrs): {len(extreme)}")
print(extreme[['event_id','student_id','duration_seconds']].head(10).to_string())

# %% [markdown]
# ## 4. Students EDA — Visualizations

# %%
# Clean students for analysis (remove duplicates at end)
students_clean = students.drop_duplicates(subset='student_id', keep='first').copy()
students_clean['gender_clean'] = students_clean['gender'].str.strip().str.lower()
students_clean['gender_clean'] = students_clean['gender_clean'].map(
    {'male':'Male','female':'Female','m':'Male','f':'Female','fem':'Female'}
).fillna(students_clean['gender'])

# %%
# Age Distribution
valid_students = students_clean[(students_clean['age'] >= 15) & (students_clean['age'] <= 50)]
fig = px.histogram(valid_students, x='age', nbins=20, color_discrete_sequence=['#6366f1'],
                   title='ፁ Age Distribution of Students (Valid Ages Only)')
fig.update_layout(template='plotly_dark', xaxis_title='Age', yaxis_title='Count',
                  bargap=0.1, font=dict(family='Inter'))
fig.show()

# %%
# City Distribution
city_counts = students_clean['city'].value_counts().reset_index()
city_counts.columns = ['city','count']
fig = px.bar(city_counts, x='count', y='city', orientation='h', color='count',
             color_continuous_scale='Viridis', title='ፇ Students by City')
fig.update_layout(template='plotly_dark', yaxis={'categoryorder':'total ascending'},
                  showlegend=False, font=dict(family='Inter'))
fig.show()

# %%
# Gender Distribution (Raw vs Cleaned)
fig = make_subplots(rows=1, cols=2, specs=[[{"type":"pie"},{"type":"pie"}]],
                    subplot_titles=["Raw Gender Values","Cleaned Gender"])
raw_g = students_clean['gender'].value_counts()
fig.add_trace(go.Pie(labels=raw_g.index, values=raw_g.values, hole=0.4,
                     marker_colors=px.colors.qualitative.Set3), row=1, col=1)
clean_g = students_clean['gender_clean'].value_counts()
fig.add_trace(go.Pie(labels=clean_g.index, values=clean_g.values, hole=0.4,
                     marker_colors=['#6366f1','#f472b6']), row=1, col=2)
fig.update_layout(template='plotly_dark', title='ፐ Gender Distribution — Raw vs Cleaned',
                  font=dict(family='Inter'))
fig.show()

# %%
# Students per Group (Actual vs Stated)
grp_actual = students_clean['group_id'].value_counts().reset_index()
grp_actual.columns = ['group_id','actual']
grp_actual = grp_actual[grp_actual['group_id'].isin(valid_groups)]
grp_stated = groups[~groups['group_id'].isin(['G99'])].drop_duplicates('group_id')[['group_id','stated_num_students']]
grp_compare = grp_actual.merge(grp_stated, on='group_id', how='left').sort_values('group_id')

fig = go.Figure()
fig.add_trace(go.Bar(x=grp_compare['group_id'], y=grp_compare['actual'], name='Actual', marker_color='#6366f1'))
# FIX: Hex color #8b5cf680 is invalid in Plotly; using a standard 6-char hex code instead.
fig.add_trace(go.Bar(x=grp_compare['group_id'], y=grp_compare['stated_num_students'], name='Stated', marker_color='#8b5cf6'))
fig.update_layout(template='plotly_dark', barmode='group', title='፤ Actual vs Stated Students per Group',
                  xaxis_title='Group', yaxis_title='Students', font=dict(family='Inter'))
fig.show()

# %%
# Enrollment Timeline
students_clean['enrollment_date'] = pd.to_datetime(students_clean['enrollment_date'])
enroll_ts = students_clean.groupby('enrollment_date').size().reset_index(name='count')
fig = px.bar(enroll_ts, x='enrollment_date', y='count', color_discrete_sequence=['#14b8a6'],
             title='፥ Enrollment Timeline')
fig.update_layout(template='plotly_dark', xaxis_title='Date', yaxis_title='Enrollments',
                  font=dict(family='Inter'))
fig.show()

# %% [markdown]
# ## 5. Grades EDA

# %%
# Clean grades
grades_clean = grades.dropna(subset=['score']).copy()
grades_clean = grades_clean[(grades_clean['score'] >= 0) & (grades_clean['score'] <= grades_clean['max_score'])]

# Average score by assessment type
avg_by_type = grades_clean.groupby('type')['score'].agg(['mean','std','count']).reset_index()
fig = px.bar(avg_by_type, x='type', y='mean', error_y='std', color='type',
             color_discrete_sequence=['#6366f1','#f59e0b','#14b8a6','#f43f5e'],
             title='ፘ Average Score by Assessment Type')
fig.update_layout(template='plotly_dark', xaxis_title='Type', yaxis_title='Average Score',
                  font=dict(family='Inter'))
fig.show()

# %%
# Score Distribution by Type
fig = px.box(grades_clean, x='type', y='score', color='type',
             color_discrete_sequence=['#6366f1','#f59e0b','#14b8a6','#f43f5e'],
             title='ፒ Score Distribution by Assessment Type')
fig.update_layout(template='plotly_dark', font=dict(family='Inter'))
fig.show()

# %%
# Quiz progression (Quiz 1-4)
quizzes = grades_clean[grades_clean['type'] == 'quiz'].copy()
quizzes['quiz_num'] = quizzes['assessment_title'].str.extract(r'(\d+)').astype(int)
quiz_avg = quizzes.groupby('quiz_num')['score'].mean().reset_index()
fig = px.line(quiz_avg, x='quiz_num', y='score', markers=True, color_discrete_sequence=['#8b5cf6'],
              title='ፘ Average Quiz Score Progression')
fig.update_layout(template='plotly_dark', xaxis_title='Quiz Number', yaxis_title='Avg Score',
                  font=dict(family='Inter'))
fig.show()

# %%
# Score distribution per course
course_map = dict(zip(courses['course_id'], courses['course_name']))
grades_clean['course_name'] = grades_clean['course_id'].map(course_map)
fig = px.violin(grades_clean, x='course_name', y='score', color='course_name', box=True,
                title='፣ Score Distribution by Course')
fig.update_layout(template='plotly_dark', showlegend=False, xaxis_tickangle=-30,
                  font=dict(family='Inter'))
fig.show()

# %%
# Overall score per student
student_avg = grades_clean.groupby('student_id')['score'].mean().reset_index()
student_avg.columns = ['student_id','avg_score']
fig = px.histogram(student_avg, x='avg_score', nbins=30, color_discrete_sequence=['#6366f1'],
                   title='ፁ Distribution of Student Average Scores')
fig.update_layout(template='plotly_dark', xaxis_title='Average Score', yaxis_title='Students',
                  font=dict(family='Inter'))
fig.show()

# %% [markdown]
# ## 6. Assignment Submissions EDA

# %%
submissions['deadline'] = pd.to_datetime(submissions['deadline'])
submissions['submitted_at'] = pd.to_datetime(submissions['submitted_at'])

# Late vs On-time
late_counts = submissions['is_late'].value_counts().reset_index()
late_counts.columns = ['is_late','count']
late_counts['label'] = late_counts['is_late'].map({True:'Late', False:'On Time'})
fig = px.pie(late_counts, values='count', names='label', color='label',
             color_discrete_map={'Late':'#f43f5e','On Time':'#10b981'}, hole=0.5,
             title='፠ Late vs On-Time Submissions')
fig.update_layout(template='plotly_dark', font=dict(family='Inter'))
fig.show()

# %%
# Time spent distribution
valid_time = submissions[(submissions['time_spent_minutes'] > 0) & (submissions['time_spent_minutes'] < 300)]
fig = px.histogram(valid_time, x='time_spent_minutes', nbins=40, color_discrete_sequence=['#14b8a6'],
                   title='⏱ Time Spent on Assignments (minutes)')
fig.update_layout(template='plotly_dark', xaxis_title='Minutes', yaxis_title='Count',
                  font=dict(family='Inter'))
fig.show()

# %%
# Attempts distribution
att_counts = submissions['attempts'].value_counts().sort_index().reset_index()
att_counts.columns = ['attempts','count']
fig = px.bar(att_counts, x='attempts', y='count', color='attempts',
             color_discrete_sequence=['#10b981','#f59e0b','#f43f5e'],
             title='ፔ Number of Attempts per Submission')
fig.update_layout(template='plotly_dark', xaxis_title='Attempts', yaxis_title='Count',
                  font=dict(family='Inter'))
fig.show()

# %%
# Late submissions by course
sub_course = submissions.copy()
sub_course['course_name'] = sub_course['course_id'].map(course_map)
late_by_course = sub_course.groupby('course_name')['is_late'].mean().reset_index()
late_by_course.columns = ['course_name','late_pct']
late_by_course['late_pct'] = (late_by_course['late_pct'] * 100).round(1)
fig = px.bar(late_by_course.sort_values('late_pct'), x='late_pct', y='course_name', orientation='h',
             color='late_pct', color_continuous_scale='Reds',
             title='ፃ Late Submission Rate by Course (%)')
fig.update_layout(template='plotly_dark', xaxis_title='Late %', font=dict(family='Inter'))
fig.show()

# %% [markdown]
# ## 7. Concepts Performance EDA

# %%
# Pass/Fail overall
pf = concepts['mastery_status'].value_counts().reset_index()
pf.columns = ['status','count']
fig = px.pie(pf, values='count', names='status', color='status',
             color_discrete_map={'passed':'#10b981','failed':'#f43f5e'}, hole=0.5,
             title='✅ Overall Concept Mastery: Pass vs Fail')
fig.update_layout(template='plotly_dark', font=dict(family='Inter'))
fig.show()

# %%
# Fail rate by concept
concept_fail = concepts.groupby('concept_name')['mastery_status'].apply(
    lambda x: (x == 'failed').mean() * 100).reset_index()
concept_fail.columns = ['concept','fail_rate']
concept_fail = concept_fail.sort_values('fail_rate', ascending=False).head(15)
fig = px.bar(concept_fail, x='fail_rate', y='concept', orientation='h',
             color='fail_rate', color_continuous_scale='RdYlGn_r',
             title='ፃ Top 15 Hardest Concepts (Fail Rate %)')
fig.update_layout(template='plotly_dark', yaxis={'categoryorder':'total ascending'},
                  xaxis_title='Fail Rate %', font=dict(family='Inter'))
fig.show()

# %%
# Average score by concept
concept_avg = concepts.groupby('concept_name')['score_pct'].mean().reset_index()
concept_avg = concept_avg.sort_values('score_pct')
fig = px.bar(concept_avg, x='score_pct', y='concept_name', orientation='h',
             color='score_pct', color_continuous_scale='Viridis',
             title='ፁ Average Score by Concept')
fig.update_layout(template='plotly_dark', yaxis={'categoryorder':'total ascending'},
                  xaxis_title='Avg Score %', font=dict(family='Inter'))
fig.show()

# %%
# Performance by assessment type (QZ vs EX vs EXF)
concepts['assess_type'] = concepts['assessment_id'].str.extract(r'-(QZ|EX|EXF)$')
perf_type = concepts.groupby('assess_type')['score_pct'].agg(['mean','median']).reset_index()
fig = px.bar(perf_type, x='assess_type', y='mean', color='assess_type',
             color_discrete_sequence=['#6366f1','#f59e0b','#f43f5e'],
             title='ፘ Concept Scores: Quiz vs Midterm vs Final')
fig.update_layout(template='plotly_dark', xaxis_title='Assessment', yaxis_title='Avg Score %',
                  font=dict(family='Inter'))
fig.show()

# %% [markdown]
# ## 8. Engagement Events EDA

# %%
engagement['event_datetime'] = pd.to_datetime(engagement['event_datetime'])

# Event type distribution
evt_counts = engagement['event_type'].value_counts().reset_index()
evt_counts.columns = ['event_type','count']
fig = px.bar(evt_counts, x='event_type', y='count', color='event_type',
             color_discrete_sequence=['#6366f1','#14b8a6','#f59e0b','#0ea5e9','#f43f5e'],
             title='⚡ Engagement Events by Type')
fig.update_layout(template='plotly_dark', xaxis_title='Event Type', yaxis_title='Count',
                  font=dict(family='Inter'))
fig.show()

# %%
# Device usage
dev_counts = engagement['device'].value_counts().reset_index()
dev_counts.columns = ['device','count']
fig = px.pie(dev_counts, values='count', names='device', color='device',
             color_discrete_map={'web':'#6366f1','mobile':'#14b8a6'}, hole=0.5,
             title='ፓ Device Usage Distribution')
fig.update_layout(template='plotly_dark', font=dict(family='Inter'))
fig.show()

# %%
# Events over time (weekly)
engagement['week'] = engagement['event_datetime'].dt.to_period('W').dt.start_time
weekly = engagement.groupby('week').size().reset_index(name='events')
fig = px.area(weekly, x='week', y='events', color_discrete_sequence=['#8b5cf6'],
              title='፥ Engagement Activity Over Time (Weekly)')
fig.update_layout(template='plotly_dark', xaxis_title='Week', yaxis_title='Events',
                  font=dict(family='Inter'))
fig.show()

# %%
# Event type by device (heatmap)
cross = pd.crosstab(engagement['event_type'], engagement['device'])
fig = px.imshow(cross, text_auto=True, color_continuous_scale='Viridis',
                title='ፏ Event Type × Device Heatmap')
fig.update_layout(template='plotly_dark', font=dict(family='Inter'))
fig.show()

# %%
# Video watch duration distribution
videos = engagement[(engagement['event_type'] == 'video_watch') &
                     (engagement['duration_seconds'] > 0) &
                     (engagement['duration_seconds'] < 3600)]
fig = px.histogram(videos, x='duration_seconds', nbins=50, color_discrete_sequence=['#14b8a6'],
                   title='ፗ Video Watch Duration Distribution (seconds)')
fig.update_layout(template='plotly_dark', xaxis_title='Duration (sec)', yaxis_title='Count',
                  font=dict(family='Inter'))
fig.show()

# %%
# Events per student
events_per_student = engagement.groupby('student_id').size().reset_index(name='total_events')
fig = px.histogram(events_per_student, x='total_events', nbins=30, color_discrete_sequence=['#f59e0b'],
                   title='ፐ Events per Student Distribution')
fig.update_layout(template='plotly_dark', xaxis_title='Total Events', yaxis_title='Students',
                  font=dict(family='Inter'))
fig.show()

# %% [markdown]
# ## 9. Attendance EDA

# %%
print("Attendance columns:", attendance.columns.tolist())
print(f"Shape: {attendance.shape}")
print(attendance.head())
# Adapt columns based on actual structure
if 'status' in attendance.columns:
    att_counts = attendance['status'].value_counts().reset_index()
    att_counts.columns = ['status','count']
    fig = px.pie(att_counts, values='count', names='status', hole=0.4,
                 color_discrete_sequence=px.colors.qualitative.Set2,
                 title='፤ Attendance Status Distribution')
    fig.update_layout(template='plotly_dark', font=dict(family='Inter'))
    fig.show()

# %% [markdown]
# ## 10. Cross-File Analysis

# %%
# Merge grades avg with engagement count
student_avg = grades_clean.groupby('student_id')['score'].mean().reset_index(name='avg_grade')
events_count = engagement.groupby('student_id').size().reset_index(name='total_events')
merged = student_avg.merge(events_count, on='student_id', how='inner')

fig = px.scatter(merged, x='total_events', y='avg_grade', trendline='ols',
                 color_discrete_sequence=['#8b5cf6'], opacity=0.6,
                 title='ፓ Engagement vs Academic Performance')
fig.update_layout(template='plotly_dark', xaxis_title='Total Engagement Events',
                  yaxis_title='Average Grade', font=dict(family='Inter'))
fig.show()

# %%
# Late submissions impact on grades
late_rate = submissions.groupby('student_id')['is_late'].mean().reset_index(name='late_pct')
merged2 = student_avg.merge(late_rate, on='student_id', how='inner')
fig = px.scatter(merged2, x='late_pct', y='avg_grade', trendline='ols',
                 color_discrete_sequence=['#f43f5e'], opacity=0.6,
                 title='ፓ Late Submission Rate vs Average Grade')
fig.update_layout(template='plotly_dark', xaxis_title='Late Submission Rate',
                  yaxis_title='Average Grade', font=dict(family='Inter'))
fig.show()

# %% [markdown]
# ## 11. Summary Statistics Dashboard

# %%
fig = make_subplots(rows=2, cols=2, subplot_titles=[
    'Score Distribution (All)', 'Events per Student',
    'Time Spent on Assignments', 'Concept Score Distribution'
])
fig.add_trace(go.Histogram(x=grades_clean['score'], marker_color='#6366f1', nbinsx=30, name='Scores'), row=1, col=1)
fig.add_trace(go.Histogram(x=events_per_student['total_events'], marker_color='#14b8a6', nbinsx=25, name='Events'), row=1, col=2)
fig.add_trace(go.Histogram(x=valid_time['time_spent_minutes'], marker_color='#f59e0b', nbinsx=30, name='Time'), row=2, col=1)
fig.add_trace(go.Histogram(x=concepts['score_pct'], marker_color='#f43f5e', nbinsx=30, name='Concepts'), row=2, col=2)
fig.update_layout(template='plotly_dark', height=700, showlegend=False,
                  title='ፁ Summary Distributions Dashboard', font=dict(family='Inter'))
fig.show()

# %% [markdown]
# ## 12. Data Quality Summary
# 
# | Category | Issue | Count |
# |----------|-------|-------|
# | Students | Missing/blank names | 5 |
# | Students | Invalid ages | 4 |
# | Students | Non-standard gender | 5+ |
# | Students | Invalid emails | 4 |
# | Students | Duplicate IDs | 2 |
# | Students | Invalid group refs | 3 |
# | Groups | Duplicate/test rows | 2 |
# | Grades | Negative scores | 1+ |
# | Grades | Score > max | 1+ |
# | Grades | Null scores | 2+ |
# | Grades | Wrong max_score | 1 |
# | Grades | Flat-line scores | 1 |
# | Submissions | Negative time | 1+ |
# | Submissions | Missing timestamps | 1+ |
# | Engagement | Negative duration | 1+ |
# | Engagement | Extreme outliers | 1+ |
# 
# ### ✅ Recommended Next Steps
# 1. Standardize gender values
# 2. Remove duplicate/test rows
# 3. Fix or remove invalid ages, emails, scores
# 4. Investigate flat-line student (S0006)
# 5. Validate is_late flags against timestamps
# 6. Cap extreme engagement durations

print("✅ EDA Complete! All visualizations rendered above.")