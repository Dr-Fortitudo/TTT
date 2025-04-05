import streamlit as st
import pandas as pd
import numpy as np
from collections import defaultdict

# Constants
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
TIME_SLOTS = ["10:45-11:45", "11:45-12:45", "12:45-1:30", 
             "1:30-2:30", "2:30-3:30", "3:30-3:45", 
             "3:45-4:45", "4:45-5:45"]
MAX_DAILY_CLASSES = 4  # Maximum classes per day per semester

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

def distribute_classes_evenly(semester_data):
    """Ensure even distribution of classes across days"""
    total_classes = semester_data['Lecture'].sum() + semester_data['Lab'].sum()
    target_per_day = min(MAX_DAILY_CLASSES, int(np.ceil(total_classes / len(DAYS))))
    
    day_distribution = {day: 0 for day in DAYS}
    for _, row in semester_data.iterrows():
        lectures = row['Lecture']
        labs = row['Lab']
        
        # Distribute lectures
        for _ in range(lectures):
            day = min(day_distribution, key=day_distribution.get)
            day_distribution[day] += 1
        
        # Distribute labs (count as 2 classes)
        for _ in range(labs):
            day1 = min(day_distribution, key=day_distribution.get)
            day_distribution[day1] += 1
            day2 = min(day_distribution, key=day_distribution.get)
            day_distribution[day2] += 1
    
    return day_distribution

def generate_timetable(semester_data, semester_name):
    timetable = pd.DataFrame("", index=TIME_SLOTS, columns=DAYS)
    faculty_schedule = defaultdict(set)
    day_distribution = distribute_classes_evenly(semester_data)
    
    # Assign BREAK periods
    for day in DAYS:
        timetable.at["12:45-1:30", day] = "BREAK"
        timetable.at["3:30-3:45", day] = "BREAK"
    
    # Process subjects in random order to prevent bias
    subjects = semester_data.sample(frac=1).iterrows()
    
    for _, row in subjects:
        subject = row['Subject']
        lectures = row['Lecture']
        labs = row['Lab']
        professors = [p.strip() for p in str(row['Prof']).split(',') if p.strip()]
        
        if not professors:
            continue
        
        # Assign lectures
        for _ in range(lectures):
            assigned = False
            for day in sorted(DAYS, key=lambda d: day_distribution[d]):
                if day_distribution[day] <= 0:
                    continue
                
                for time_slot in TIME_SLOTS:
                    if "BREAK" in time_slot or timetable.at[time_slot, day] != "":
                        continue
                    
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
            for day in sorted(DAYS, key=lambda d: day_distribution[d]):
                if day_distribution[day] <= 1:  # Need 2 consecutive slots
                    continue
                
                for i in range(len(TIME_SLOTS)-1):
                    time_slot1 = TIME_SLOTS[i]
                    time_slot2 = TIME_SLOTS[i+1]
                    
                    if ("BREAK" in time_slot1 or "BREAK" in time_slot2 or
                        timetable.at[time_slot1, day] != "" or 
                        timetable.at[time_slot2, day] != ""):
                        continue
                    
                    for prof in professors:
                        if (prof not in faculty_schedule[(day, time_slot1)] and
                            prof not in faculty_schedule[(day, time_slot2)]):
                            
                            timetable.at[time_slot1, day] = f"B1-{subject}-{prof}\nB2-{subject}-{prof}"
                            timetable.at[time_slot2, day] = f"B1-{subject}-{prof}\nB2-{subject}-{prof}"
                            faculty_schedule[(day, time_slot1)].add(prof)
                            faculty_schedule[(day, time_slot2)].add(prof)
                            day_distribution[day] -= 2
                            assigned = True
                            break
                    if assigned:
                        break
                if assigned:
                    break
    
    return timetable

# Streamlit UI
st.title("Academic Timetable Generator")

uploaded_file = st.file_uploader("Upload Excel file with subject data", type=["xlsx"])

if uploaded_file:
    semesters_data = load_data(uploaded_file)
    
    # Verify equal distribution
    total_classes = {
        '2': semesters_data['2']['Lecture'].sum() + semesters_data['2']['Lab'].sum() * 2,
        '4': semesters_data['4']['Lecture'].sum() + semesters_data['4']['Lab'].sum() * 2,
        '6': semesters_data['6']['Lecture'].sum() + semesters_data['6']['Lab'].sum() * 2
    }
    
    if submit_button := st.button("Generate Timetables"):
        for sem, name in [('2', '2nd Semester'), ('4', '4th Semester'), ('6', '6th Semester')]:
            st.write(f"### {name} Timetable")
            timetable = generate_timetable(semesters_data[sem], name)
            
            # Format display
            display_df = pd.DataFrame(index=TIME_SLOTS, columns=DAYS)
            for day in DAYS:
                for time_slot in TIME_SLOTS:
                    display_df.at[time_slot, day] = timetable.at[time_slot, day]
            
            st.dataframe(
                display_df.style.set_properties(**{
                    'white-space': 'pre-wrap',
                    'text-align': 'center',
                    'min-width': '150px'
                }),
                height=600
            )
