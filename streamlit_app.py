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
    df_subjects_cleaned['Credits_4EC'] = pd.to_numeric(df_subjects_cleaned['Credits_4EC'], errors='coerce')
    df_subjects_cleaned['Credits_6ECA'] = pd.to_numeric(df_subjects_cleaned['Credits_6ECA'], errors='coerce')
    return df_subjects_cleaned

# Define timetable structure
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
TIME_SLOTS = ["10:45-11:45", "11:45-12:45", "1:30-2:30", "2:30-3:30", "3:45-4:45", "4:45-5:45"]

# Generate timetable based on constraints
def generate_timetable(subjects, credits):
    timetable = pd.DataFrame(index=TIME_SLOTS, columns=DAYS)
    subject_list = subjects.dropna().tolist()
    credit_list = credits.dropna().astype(int).tolist()
    weighted_subjects = sum([[subj] * cr for subj, cr in zip(subject_list, credit_list)], [])
    np.random.shuffle(weighted_subjects)
    idx = 0
    for day in DAYS:
        for slot in TIME_SLOTS:
            if idx < len(weighted_subjects):
                timetable.at[slot, day] = weighted_subjects[idx]
                idx += 1
    return timetable

# Streamlit UI
st.title("Automated Timetable Generator")
df_subjects = load_data()
semester = st.selectbox("Select Semester", ["4th Semester", "6th Semester"])

if semester == "4th Semester":
    timetable = generate_timetable(df_subjects["Subject_4EC"], df_subjects["Credits_4EC"])
elif semester == "6th Semester":
    timetable = generate_timetable(df_subjects["Subject_6ECA"], df_subjects["Credits_6ECA"])

st.write("### Generated Timetable")
st.dataframe(timetable)
