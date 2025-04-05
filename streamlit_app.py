import streamlit as st
import pandas as pd
import random
from collections import defaultdict

# Load subject and faculty data from uploaded file
@st.cache_data
def load_data(uploaded_file):
    df = pd.read_excel(uploaded_file, sheet_name='Sheet1', header=None)
    
    # Extract data for each semester (adjust column indices as needed)
    semesters = {
        '2': df.iloc[2:, [0, 1, 2, 3]].dropna(how='all'),  # Columns for sem2
        '4': df.iloc[2:, [6, 7, 8, 9]].dropna(how='all'),  # Columns for sem4
        '6': df.iloc[2:, [12, 13, 14, 15]].dropna(how='all')  # Columns for sem6
    }
    
    # Clean and prepare data for each semester
    for sem in semesters:
        semesters[sem].columns = ['Subject', 'Lecture', 'Lab', 'Prof']
        semesters[sem] = semesters[sem][semesters[sem]['Subject'].notna()]
        semesters[sem]['Lecture'] = semesters[sem]['Lecture'].fillna(0).astype(int)
        semesters[sem]['Lab'] = semesters[sem]['Lab'].fillna(0).astype(int)
        semesters[sem]['Prof'] = semesters[sem]['Prof'].fillna('')
    
    return semesters

# Define timetable structure
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
TIME_SLOTS = ["10:45-11:45", "11:45-12:45", "12:45-1:30", 
              "1:30-2:30", "2:30-3:30", "3:30-3:45", 
              "3:45-4:45", "4:45-5:45"]

def generate_timetable(semester_data, semester_name):
    # Initialize timetable dataframe
    timetable = pd.DataFrame("", index=TIME_SLOTS, columns=DAYS)
    
    # Add header information
    header = pd.DataFrame({
        'A': ["GOVERNMENT ENGINEERING COLLEGE, BHAVNAGAR", 
              "ELECTRONICS & COMMUNICATION DEPARTMENT",
              "",
              f"{semester_name} TIME TABLE",
              "",
              "Period No.", "Time"] + TIME_SLOTS + ["", ""],
        'B': [""]*7 + ["1"] + [""]*(len(TIME_SLOTS)-1) + ["", "H.O.D."],
        'Monday': [""]*7 + DAYS[0:1] + [""]*(len(TIME_SLOTS)-1) + ["", ""],
        # ... other days similarly
    })
    
    # Initialize faculty tracking
    faculty_hours = defaultdict(int)
    faculty_schedule = defaultdict(set)  # (day, time_slot) -> faculty
    
    def is_faculty_available(professor, day, time_slot):
        return professor not in faculty_schedule.get((day, time_slot), set())
    
    def assign_lecture(subject, professor, day, time_slot):
        timetable.at[time_slot, day] = f"{subject}-{professor}"
        faculty_schedule[(day, time_slot)].add(professor)
        faculty_hours[professor] += 1
    
    def assign_lab(subject, professor, day, time_slot1, time_slot2):
        # Format for batches: B1-SUB-PROF, B2-SUB-PROF, etc.
        timetable.at[time_slot1, day] = f"B1-{subject}-{professor}\nB2-{subject}-{professor}"
        timetable.at[time_slot2, day] = f"B1-{subject}-{professor}\nB2-{subject}-{professor}"
        faculty_schedule[(day, time_slot1)].add(professor)
        faculty_schedule[(day, time_slot2)].add(professor)
        faculty_hours[professor] += 2  # Labs count as 2 hours
    
    # Process each subject
    for _, row in semester_data.iterrows():
        subject = row['Subject']
        lecture_count = row['Lecture']
        lab_count = row['Lab']
        professors = [p.strip() for p in str(row['Prof']).split(',') if p.strip()]
        
        if not professors:
            continue
        
        # Assign lectures
        for _ in range(lecture_count):
            assigned = False
            while not assigned:
                day = random.choice(DAYS)
                time_slot = random.choice([ts for ts in TIME_SLOTS if "BREAK" not in ts])
                prof = random.choice(professors)
                
                if (timetable.at[time_slot, day] == "" and 
                    is_faculty_available(prof, day, time_slot) and 
                    faculty_hours[prof] < 18):
                    
                    assign_lecture(subject, prof, day, time_slot)
                    assigned = True
        
        # Assign labs (2 consecutive slots)
        if lab_count > 0:
            for _ in range(lab_count):
                assigned = False
                while not assigned:
                    day = random.choice(DAYS)
                    # Find consecutive slots
                    for i in range(len(TIME_SLOTS)-1):
                        time_slot1 = TIME_SLOTS[i]
                        time_slot2 = TIME_SLOTS[i+1]
                        
                        if ("BREAK" not in time_slot1 and "BREAK" not in time_slot2 and
                            timetable.at[time_slot1, day] == "" and 
                            timetable.at[time_slot2, day] == ""):
                            
                            prof = random.choice(professors)
                            if (is_faculty_available(prof, day, time_slot1) and 
                                is_faculty_available(prof, day, time_slot2) and 
                                faculty_hours[prof] < 16):
                                
                                assign_lab(subject, prof, day, time_slot1, time_slot2)
                                assigned = True
                                break
    
    return timetable

# Streamlit UI
st.title("Automated Timetable Generator")

# File uploader
uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])

if uploaded_file:
    semesters_data = load_data(uploaded_file)
    submit_button = st.button("Generate All Timetables")
    
    if submit_button:
        # Generate and display timetables for all semesters
        for sem, name in [('2', '2nd Semester'), ('4', '4th Semester'), ('6', '6th Semester')]:
            st.write(f"### {name} Timetable")
            timetable = generate_timetable(semesters_data[sem], name)
            
            # Display with the reference layout style
            display_df = pd.DataFrame(index=TIME_SLOTS, columns=DAYS)
            for day in DAYS:
                for time_slot in TIME_SLOTS:
                    display_df.at[time_slot, day] = timetable.at[time_slot, day]
            
            st.dataframe(display_df.style.set_properties(**{
                'white-space': 'pre-wrap',
                'text-align': 'center'
            }))
        
        # Show faculty workload summary
        st.write("### Faculty Workload Summary")
        # (Workload calculation would go here)
