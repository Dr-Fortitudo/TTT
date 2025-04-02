import streamlit as st
import pandas as pd
import numpy as np

# Load the subject and faculty data
@st.cache_data
def load_data():
    file_subjects = "Subject Prof. credits.xlsx"
    df_subjects = pd.read_excel(file_subjects, sheet_name='Sheet1')
    df_subjects_cleaned = df_subjects.iloc[1:, [0, 1, 2, 5, 6, 7]]
    df_subjects_cleaned.columns = ['Subject_4EC', 'Credits_4EC', 'Prof_4EC', 'Subject_6ECA', 'Credits_6ECA', 'Prof_6ECA']
    df_subjects_cleaned.dropna(how="all", inplace=True)
    df_subjects_cleaned.fillna("", inplace=True)  # Ensure no NaN values
    return df_subjects_cleaned

# Define timetable structure
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
TIME_SLOTS = ["10:45-11:45", "11:45-12:45", "12:45-1:30 (BREAK)", "1:30-2:30", "2:30-3:30", "3:30-3:45 (BREAK)", "3:45-4:45", "4:45-5:45"]

# Generate both timetables simultaneously to prevent faculty overlaps
def generate_timetables(subjects_df):
    timetable_4EC = pd.DataFrame("", index=TIME_SLOTS, columns=DAYS)
    timetable_6ECA = pd.DataFrame("", index=TIME_SLOTS, columns=DAYS)
    
    faculty_schedule = {}
    
    # Insert BREAK slots
    for day in DAYS:
        timetable_4EC.at["12:45-1:30 (BREAK)", day] = "BREAK"
        timetable_4EC.at["3:30-3:45 (BREAK)", day] = "BREAK"
        timetable_6ECA.at["12:45-1:30 (BREAK)", day] = "BREAK"
        timetable_6ECA.at["3:30-3:45 (BREAK)", day] = "BREAK"
    
    def assign_lecture(timetable, subject, professor):
        for day in DAYS:
            for slot in TIME_SLOTS:
                if "BREAK" not in slot and timetable.at[slot, day] == "" and (professor not in faculty_schedule.get((day, slot), [])):
                    timetable.at[slot, day] = subject
                    faculty_schedule.setdefault((day, slot), []).append(professor)
                    return
    
    for _, row in subjects_df.iterrows():
        if row['Subject_4EC']:
            for _ in range(int(row['Credits_4EC'])):
                assign_lecture(timetable_4EC, row['Subject_4EC'], row['Prof_4EC'])
        if row['Subject_6ECA']:
            for _ in range(int(row['Credits_6ECA'])):
                assign_lecture(timetable_6ECA, row['Subject_6ECA'], row['Prof_6ECA'])
    
    return timetable_4EC, timetable_6ECA

# Streamlit UI
st.title("Automated Timetable Generator")
df_subjects = load_data()
timetable_4EC, timetable_6ECA = generate_timetables(df_subjects)

semester = st.selectbox("Select Semester", ["4th Semester", "6th Semester"])

if semester == "4th Semester":
    st.write("### 4th Semester Timetable")
    st.dataframe(timetable_4EC)
elif semester == "6th Semester":
    st.write("### 6th Semester Timetable")
    st.dataframe(timetable_6ECA)
