import streamlit as st
import pandas as pd
import numpy as np
from collections import defaultdict

# Constants
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
TIME_SLOTS = ["10:45-11:45", "11:45-12:45", "12:45-1:30", 
             "1:30-2:30", "2:30-3:30", "3:30-3:45", 
             "3:45-4:45", "4:45-5:45"]
MAX_DAILY_CLASSES = 6  # Increased to accommodate more classes

@st.cache_data
def load_data(uploaded_file):
    df = pd.read_excel(uploaded_file, sheet_name='Sheet1', header=None)
    
    semesters = {
        '2': df.iloc[2:, [0, 1, 2, 3]].dropna(how='all'),
        '4': df.iloc[2:, [6, 7, 8, 9]].dropna(how='all'),
        '6': df.iloc[2:, [12, 13, 14, 15]].dropna(how='all')
    }
    
    for sem in semesters:
        semesters[sem].columns = ['Subject', 'Lecture', 'Lab', 'Prof']
        semesters[sem] = semesters[sem][semesters[sem]['Subject'].notna()]
        semesters[sem]['Lecture'] = semesters[sem]['Lecture'].fillna(0).astype(int)
        semesters[sem]['Lab'] = semesters[sem]['Lab'].fillna(0).astype(int)
        semesters[sem]['Prof'] = semesters[sem]['Prof'].fillna('')
    
    return semesters

def calculate_class_distribution(semester_data):
    """Calculate balanced class distribution across days"""
    total_lectures = semester_data['Lecture'].sum()
    total_labs = semester_data['Lab'].sum() * 2  # Labs count as 2 slots
    
    # Calculate base classes per day
    base_classes = (total_lectures + total_labs) // len(DAYS)
    remainder = (total_lectures + total_labs) % len(DAYS)
    
    # Distribute remainder across days
    distribution = {day: base_classes for day in DAYS}
    for i in range(remainder):
        distribution[DAYS[i]] += 1
    
    return distribution

def generate_timetable(semester_data, semester_name):
    timetable = pd.DataFrame("", index=TIME_SLOTS, columns=DAYS)
    faculty_schedule = defaultdict(set)
    day_distribution = calculate_class_distribution(semester_data)
    
    # Assign BREAK periods
    for day in DAYS:
        timetable.at["12:45-1:30", day] = "BREAK"
        timetable.at["3:30-3:45", day] = "BREAK"
    
    # Process subjects in order of most classes first
    semester_data = semester_data.sort_values(by=['Lecture', 'Lab'], ascending=False)
    
    for _, row in semester_data.iterrows():
        subject = row['Subject']
        lectures = row['Lecture']
        labs = row['Lab']
        professors = [p.strip() for p in str(row['Prof']).split(',') if p.strip()]
        
        if not professors:
            continue
        
        # Assign lectures in contiguous blocks
        for _ in range(lectures):
            assigned = False
            for day in DAYS:
                if day_distribution[day] <= 0:
                    continue
                
                # Find first available morning slot
                for time_slot in ["10:45-11:45", "11:45-12:45", "1:30-2:30", "2:30-3:30"]:
                    if timetable.at[time_slot, day] == "":
                        for prof in professors:
                            if prof not in faculty_schedule[(day, time_slot)]:
                                timetable.at[time_slot, day] = f"{subject}-{prof}"
                                faculty_schedule[(day, time_slot)].add(prof)
                                day_distribution[day] -= 1
                                assigned = True
                                break
                        if assigned:
                            break
                if assigned:
                    break
            
            if not assigned:
                # If morning slots full, try afternoon
                for day in DAYS:
                    if day_distribution[day] <= 0:
                        continue
                    
                    for time_slot in ["3:45-4:45", "4:45-5:45"]:
                        if timetable.at[time_slot, day] == "":
                            for prof in professors:
                                if prof not in faculty_schedule[(day, time_slot)]:
                                    timetable.at[time_slot, day] = f"{subject}-{prof}"
                                    faculty_schedule[(day, time_slot)].add(prof)
                                    day_distribution[day] -= 1
                                    assigned = True
                                    break
                            if assigned:
                                break
                    if assigned:
                        break
        
        # Assign labs (2 consecutive slots)
        for _ in range(labs):
            assigned = False
            for day in DAYS:
                if day_distribution[day] < 2:  # Need 2 consecutive slots
                    continue
                
                # Try to place labs in morning first
                for time1, time2 in [("10:45-11:45", "11:45-12:45"), 
                                   ("1:30-2:30", "2:30-3:30")]:
                    if (timetable.at[time1, day] == "" and 
                        timetable.at[time2, day] == ""):
                        
                        for prof in professors:
                            if (prof not in faculty_schedule[(day, time1)] and
                                prof not in faculty_schedule[(day, time2)]):
                                
                                timetable.at[time1, day] = f"B1-{subject}-{prof}"
                                timetable.at[time2, day] = f"B2-{subject}-{prof}"
                                faculty_schedule[(day, time1)].add(prof)
                                faculty_schedule[(day, time2)].add(prof)
                                day_distribution[day] -= 2
                                assigned = True
                                break
                        if assigned:
                            break
                if assigned:
                    break
                
                if not assigned:
                    # Try afternoon slots if morning full
                    if (timetable.at["3:45-4:45", day] == "" and 
                        timetable.at["4:45-5:45", day] == ""):
                        
                        for prof in professors:
                            if (prof not in faculty_schedule[(day, "3:45-4:45")] and
                                prof not in faculty_schedule[(day, "4:45-5:45")]):
                                
                                timetable.at["3:45-4:45", day] = f"B1-{subject}-{prof}"
                                timetable.at["4:45-5:45", day] = f"B2-{subject}-{prof}"
                                faculty_schedule[(day, "3:45-4:45")].add(prof)
                                faculty_schedule[(day, "4:45-5:45")].add(prof)
                                day_distribution[day] -= 2
                                assigned = True
                                break
    
    # Fill empty slots with "-" for cleaner display
    for day in DAYS:
        for time_slot in TIME_SLOTS:
            if timetable.at[time_slot, day] == "":
                timetable.at[time_slot, day] = "-"
    
    return timetable

# Streamlit UI
st.title("Academic Timetable Generator")

uploaded_file = st.file_uploader("Upload Excel file with subject data", type=["xlsx"])

if uploaded_file:
    semesters_data = load_data(uploaded_file)
    
    if submit_button := st.button("Generate Timetables"):
        for sem, name in [('2', '2nd Semester'), ('4', '4th Semester'), ('6', '6th Semester')]:
            st.write(f"### {name} Timetable")
            timetable = generate_timetable(semesters_data[sem], name)
            
            # Create styled dataframe
            styled_df = timetable.style.applymap(
                lambda x: "background-color: #f0f2f6" if x in ["BREAK", "-"] else "",
                subset=pd.IndexSlice[:, :]
            )
            
            # Display with better formatting
            st.dataframe(
                styled_df.set_properties(**{
                    'white-space': 'pre',
                    'text-align': 'center',
                    'border': '1px solid #ddd',
                    'font-size': '14px'
                }).format(lambda x: x if x not in ["-"] else ""),
                height=800,
                width=1200
            )
