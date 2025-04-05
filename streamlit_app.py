import streamlit as st
import pandas as pd
import random
from collections import defaultdict

# Load subject and faculty data from uploaded file
@st.cache_data
def load_data(uploaded_file):
    df = pd.read_excel(uploaded_file, sheet_name='Sheet1', header=None)
    
    # Extract data for each semester
    sem2_start = 2  # Row index where sem2 data starts
    sem4_start = 2   # Row index where sem4 data starts
    sem6_start = 2   # Row index where sem6 data starts
    
    sem2_cols = [0, 1, 2, 3]  # Columns for sem2 (Subject, Lecture, Lab, Prof)
    sem4_cols = [6, 7, 8, 9]  # Columns for sem4
    sem6_cols = [12, 13, 14, 15]  # Columns for sem6
    
    semesters = {
        '2': df.iloc[sem2_start:, sem2_cols].dropna(how='all'),
        '4': df.iloc[sem4_start:, sem4_cols].dropna(how='all'),
        '6': df.iloc[sem6_start:, sem6_cols].dropna(how='all')
    }
    
    # Clean and rename columns for each semester
    for sem in semesters:
        semesters[sem].columns = ['Subject', 'Lecture', 'Lab', 'Prof']
        semesters[sem] = semesters[sem][semesters[sem]['Subject'].notna()]
        semesters[sem]['Lecture'] = semesters[sem]['Lecture'].fillna(0).astype(int)
        semesters[sem]['Lab'] = semesters[sem]['Lab'].fillna(0).astype(int)
        semesters[sem]['Prof'] = semesters[sem]['Prof'].fillna('')
    
    return semesters

# Define timetable structure
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
TIME_SLOTS = ["10:45-11:45", "11:45-12:45", "12:45-1:30 (BREAK)", 
              "1:30-2:30", "2:30-3:30", "3:30-3:45 (BREAK)", 
              "3:45-4:45", "4:45-5:45"]

def generate_timetables(semesters_data):
    # Initialize timetables for all semesters and batches
    timetables = {
        sem: {
            'B1': pd.DataFrame("", index=TIME_SLOTS, columns=DAYS),
            'B2': pd.DataFrame("", index=TIME_SLOTS, columns=DAYS)
        } for sem in semesters_data
    }
    
    # Initialize faculty tracking
    faculty_hours = defaultdict(int)
    faculty_schedule = defaultdict(set)  # (day, time_slot) -> faculty
    
    # Insert BREAK slots
    for sem in timetables:
        for batch in ['B1', 'B2']:
            for day in DAYS:
                timetables[sem][batch].at["12:45-1:30 (BREAK)", day] = "BREAK"
                timetables[sem][batch].at["3:30-3:45 (BREAK)", day] = "BREAK"
    
    def is_faculty_available(professor, day, time_slot):
        # Check if faculty is already scheduled at this time across all semesters
        for sem in timetables:
            for batch in ['B1', 'B2']:
                if professor in faculty_schedule.get((sem, batch, day, time_slot), set()):
                    return False
        return True
    
    def assign_lecture(sem, subject, professor, lecture_count):
        assigned = 0
        while assigned < lecture_count:
            for day in random.sample(DAYS, len(DAYS)):
                for time_slot in random.sample(TIME_SLOTS, len(TIME_SLOTS)):
                    if "BREAK" in time_slot:
                        continue
                    # Check if faculty is available and not overworked
                    if (is_faculty_available(professor, day, time_slot) and faculty_hours[professor] < 18):  # 18 hours max (with buffer)
                        # Assign to both batches at same time (since lectures are common)
                        for batch in ['B1', 'B2']:
                            if timetables[sem][batch].at[time_slot, day] == "":
                                timetables[sem][batch].at[time_slot, day] = f"{subject} ({professor})"
                                faculty_schedule[(sem, batch, day, time_slot)].add(professor)
                                faculty_hours[professor] += 1
                        assigned += 1
                        break
                if assigned >= lecture_count:
                    break
    
    def assign_lab(sem, subject, professor):
        # Labs are 2 hours and need to be assigned to both batches at different times
        lab_assigned_b1 = False
        lab_assigned_b2 = False
        
        while not (lab_assigned_b1 and lab_assigned_b2):
            for day in random.sample(DAYS, len(DAYS)):
                # Find consecutive slots for lab
                for i in range(len(TIME_SLOTS)-1):
                    time_slot1 = TIME_SLOTS[i]
                    time_slot2 = TIME_SLOTS[i+1]
                    
                    if "BREAK" in time_slot1 or "BREAK" in time_slot2:
                        continue
                    
                    # Assign to B1 first
                    if not lab_assigned_b1:
                        if (timetables[sem]['B1'].at[time_slot1, day] == "" and 
                            timetables[sem]['B1'].at[time_slot2, day] == "" and 
                            is_faculty_available(professor, day, time_slot1) and 
                            is_faculty_available(professor, day, time_slot2) and 
                            faculty_hours[professor] < 16):  # Labs count as 2 hours
                            
                            timetables[sem]['B1'].at[time_slot1, day] = f"{subject} ({professor}) [LAB]"
                            timetables[sem]['B1'].at[time_slot2, day] = f"{subject} ({professor}) [LAB]"
                            faculty_schedule[(sem, 'B1', day, time_slot1)].add(professor)
                            faculty_schedule[(sem, 'B1', day, time_slot2)].add(professor)
                            faculty_hours[professor] += 2
                            lab_assigned_b1 = True
                    
                    # Assign to B2 at a different time
                    if not lab_assigned_b2:
                        # Find a different time slot for B2
                        for j in range(len(TIME_SLOTS)-1):
                            time_slot1_b2 = TIME_SLOTS[j]
                            time_slot2_b2 = TIME_SLOTS[j+1]
                            
                            if "BREAK" in time_slot1_b2 or "BREAK" in time_slot2_b2:
                                continue
                            
                            if (timetables[sem]['B2'].at[time_slot1_b2, day] == "" and 
                                timetables[sem]['B2'].at[time_slot2_b2, day] == "" and 
                                is_faculty_available(professor, day, time_slot1_b2) and 
                                is_faculty_available(professor, day, time_slot2_b2) and 
                                faculty_hours[professor] < 16):
                                
                                timetables[sem]['B2'].at[time_slot1_b2, day] = f"{subject} ({professor}) [LAB]"
                                timetables[sem]['B2'].at[time_slot2_b2, day] = f"{subject} ({professor}) [LAB]"
                                faculty_schedule[(sem, 'B2', day, time_slot1_b2)].add(professor)
                                faculty_schedule[(sem, 'B2', day, time_slot2_b2)].add(professor)
                                faculty_hours[professor] += 2
                                lab_assigned_b2 = True
                                break
                    
                    if lab_assigned_b1 and lab_assigned_b2:
                        break
                if lab_assigned_b1 and lab_assigned_b2:
                    break
    
    # Process each semester
    for sem, data in semesters_data.items():
        for _, row in data.iterrows():
            subject = row['Subject']
            lecture_count = row['Lecture']
            lab_count = row['Lab']
            professors = [p.strip() for p in str(row['Prof']).split(',') if p.strip()]
            
            if not professors:
                continue
            
            # Distribute lectures among professors
            lectures_per_prof = lecture_count // len(professors)
            remaining_lectures = lecture_count % len(professors)
            
            for i, prof in enumerate(professors):
                count = lectures_per_prof + (1 if i < remaining_lectures else 0)
                if count > 0:
                    assign_lecture(sem, subject, prof, count)
            
            # Assign labs (each lab is 2 hours for each batch)
            if lab_count > 0:
                labs_per_prof = lab_count // len(professors)
                remaining_labs = lab_count % len(professors)
                
                for i, prof in enumerate(professors):
                    count = labs_per_prof + (1 if i < remaining_labs else 0)
                    for _ in range(count):
                        assign_lab(sem, subject, prof)
    
    return timetables

# Streamlit UI
st.title("Automated Timetable Generator")

# Sample file download link
sample_file_path = "Subject Prof. credits.xlsx"
with open(sample_file_path, "rb") as file:
    sample_bytes = file.read()

st.download_button(
    label="Download Sample Excel File",
    data=sample_bytes,
    file_name="Subject_Prof_credits.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# File uploader
uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])

if uploaded_file:
    semesters_data = load_data(uploaded_file)
    semester = st.selectbox("Select Semester", ["2nd Semester", "4th Semester", "6th Semester"])
    batch = st.selectbox("Select Batch", ["B1", "B2"])
    submit_button = st.button("Generate Timetable")
    
    if submit_button:
        timetables = generate_timetables(semesters_data)
        sem_key = semester[0]  # Extract '2', '4', or '6' from semester name
        
        st.write(f"### {semester} Timetable - Batch {batch}")
        st.dataframe(timetables[sem_key][batch])
        
        # Show faculty workload
        st.write("### Faculty Workload Summary")
        faculty_workload = defaultdict(int)
        for sem in timetables:
            for batch in ['B1', 'B2']:
                for day in DAYS:
                    for time_slot in TIME_SLOTS:
                        cell = timetables[sem][batch].at[time_slot, day]
                        if "(" in cell and ")" in cell:
                            prof = cell.split('(')[1].split(')')[0]
                            if "[LAB]" in cell:
                                faculty_workload[prof] += 2
                            else:
                                faculty_workload[prof] += 1
        
        workload_df = pd.DataFrame.from_dict(faculty_workload, orient='index', columns=['Hours'])
        st.dataframe(workload_df.sort_values(by='Hours', ascending=False))
