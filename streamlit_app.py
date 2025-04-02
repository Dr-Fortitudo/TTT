import streamlit as st
import pandas as pd
import random

# Load subject and faculty data from uploaded file
@st.cache_data
def load_data(uploaded_file):
    df_subjects = pd.read_excel(uploaded_file, sheet_name='Sheet1')
    df_subjects_cleaned = df_subjects.iloc[1:, [0, 1, 2, 5, 6, 7]]
    df_subjects_cleaned.columns = ['Subject_4EC', 'Credits_4EC', 'Prof_4EC', 'Subject_6ECA', 'Credits_6ECA', 'Prof_6ECA']
    df_subjects_cleaned.dropna(how="all", inplace=True)
    df_subjects_cleaned.fillna("", inplace=True)  # Ensure no NaN values
    return df_subjects_cleaned

# Define timetable structure
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
TIME_SLOTS = ["10:45-11:45", "11:45-12:45", "12:45-1:30 (BREAK)", "1:30-2:30", "2:30-3:30", "3:30-3:45 (BREAK)", "3:45-4:45", "4:45-5:45"]

# Generate timetables ensuring no faculty overlap
def generate_timetables(subjects_df):
    timetable_4EC = pd.DataFrame("", index=TIME_SLOTS, columns=DAYS)
    timetable_6ECA = pd.DataFrame("", index=TIME_SLOTS, columns=DAYS)
    faculty_schedule = {}
    subject_schedule = {}
    
    # Insert BREAK slots
    for day in DAYS:
        timetable_4EC.at["12:45-1:30 (BREAK)", day] = "BREAK"
        timetable_4EC.at["3:30-3:45 (BREAK)", day] = "BREAK"
        timetable_6ECA.at["12:45-1:30 (BREAK)", day] = "BREAK"
        timetable_6ECA.at["3:30-3:45 (BREAK)", day] = "BREAK"
    
    def assign_lecture(timetable, subject, professor, is_lab=False):
        random.shuffle(DAYS)
        for day in DAYS:
            if subject_schedule.get((day, subject), 0) == 0:
                for i, slot in enumerate(TIME_SLOTS[:-1]):
                    if "BREAK" not in slot and timetable.at[slot, day] == "" and (professor not in faculty_schedule.get((day, slot), [])):
                        if is_lab and "BREAK" not in TIME_SLOTS[i+1]:
                            timetable.at[slot, day] = f"{subject} ({professor}) [LAB]"
                            timetable.at[TIME_SLOTS[i+1], day] = f"{subject} ({professor}) [LAB]"
                            faculty_schedule.setdefault((day, slot), []).append(professor)
                            faculty_schedule.setdefault((day, TIME_SLOTS[i+1]), []).append(professor)
                            subject_schedule[(day, subject)] = 1
                            return
                        elif not is_lab:
                            timetable.at[slot, day] = f"{subject} ({professor})"
                            faculty_schedule.setdefault((day, slot), []).append(professor)
                            subject_schedule[(day, subject)] = 1
                            return
    
    for _, row in subjects_df.iterrows():
        professors_4EC = [p.strip() for p in str(row['Prof_4EC']).split(',')]
        professors_6ECA = [p.strip() for p in str(row['Prof_6ECA']).split(',')]
        
        if row['Subject_4EC']:
            for professor in professors_4EC:
                for _ in range(int(row['Credits_4EC']) // len(professors_4EC)):
                    assign_lecture(timetable_4EC, row['Subject_4EC'], professor)
                assign_lecture(timetable_4EC, row['Subject_4EC'], professor, is_lab=True)
        if row['Subject_6ECA']:
            for professor in professors_6ECA:
                for _ in range(int(row['Credits_6ECA']) // len(professors_6ECA)):
                    assign_lecture(timetable_6ECA, row['Subject_6ECA'], professor)
                assign_lecture(timetable_6ECA, row['Subject_6ECA'], professor, is_lab=True)
    
    return timetable_4EC, timetable_6ECA

# Streamlit UI
st.title("Automated Timetable Generator")

# Sample file download link
sample_file_path = "Subject Prof. credits.xlsx"

with open(sample_file_path, "rb") as file:
    sample_bytes = file.read()

st.download_button(
    label="Download Sample Excel File",
    data=sample_bytes,
    file_name="Subject_Prof_credits.xlsx",  # Ensure it has the correct filename
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"  # MIME type for Excel
)

# File uploader
uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])

if uploaded_file:
    df_subjects = load_data(uploaded_file)
    semester = st.selectbox("Select Semester", ["4th Semester", "6th Semester"], key="semester_selection")
    submit_button = st.button("Generate Timetable")
    
    if submit_button:
        timetable_4EC, timetable_6ECA = generate_timetables(df_subjects)
        
        if semester == "4th Semester":
            st.write("### 4th Semester Timetable")
            st.dataframe(timetable_4EC)
        elif semester == "6th Semester":
            st.write("### 6th Semester Timetable")
            st.dataframe(timetable_6ECA)
