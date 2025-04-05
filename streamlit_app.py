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

def generate_all_timetables(semesters_data):
    # Store timetables and faculty slots
    timetables = {sem: pd.DataFrame("", index=TIME_SLOTS, columns=DAYS) for sem in semesters_data}
    faculty_schedule = defaultdict(set)
    sem_day_class_count = {sem: {day: 0 for day in DAYS} for sem in semesters_data}

    # Assign BREAK periods
    for sem in timetables:
        for day in DAYS:
            timetables[sem].at["12:45-1:30", day] = "BREAK"
            timetables[sem].at["3:30-3:45", day] = "BREAK"

    # Shuffle to reduce bias
    for sem in semesters_data:
        semesters_data[sem] = semesters_data[sem].sample(frac=1).reset_index(drop=True)

    for sem in semesters_data:
        for _, row in semesters_data[sem].iterrows():
            subject = row['Subject']
            lectures = row['Lecture']
            labs = row['Lab']
            professors = [p.strip() for p in str(row['Prof']).split(',') if p.strip()]
            if not professors:
                continue

            # Assign lectures linearly
            for _ in range(lectures):
                assigned = False
                for day in sorted(DAYS, key=lambda d: sem_day_class_count[sem][d]):
                    for time_slot in TIME_SLOTS:
                        if ("BREAK" in time_slot or 
                            timetables[sem].at[time_slot, day] != ""):
                            continue
                        # Check if previous slots in day are filled
                        prev_slots = TIME_SLOTS[:TIME_SLOTS.index(time_slot)]
                        if any(timetables[sem].at[ts, day] == "" for ts in prev_slots if "BREAK" not in ts):
                            continue
                        for prof in professors:
                            if prof not in faculty_schedule[(day, time_slot)]:
                                timetables[sem].at[time_slot, day] = f"{subject}-{prof}"
                                faculty_schedule[(day, time_slot)].add(prof)
                                sem_day_class_count[sem][day] += 1
                                assigned = True
                                break
                        if assigned:
                            break
                    if assigned:
                        break

            # Assign labs (2 consecutive slots)
            for _ in range(labs):
                assigned = False
                for day in sorted(DAYS, key=lambda d: sem_day_class_count[sem][d]):
                    for i in range(len(TIME_SLOTS)-1):
                        ts1 = TIME_SLOTS[i]
                        ts2 = TIME_SLOTS[i+1]
                        if ("BREAK" in ts1 or "BREAK" in ts2 or
                            timetables[sem].at[ts1, day] != "" or 
                            timetables[sem].at[ts2, day] != ""):
                            continue
                        prev_slots = TIME_SLOTS[:i]
                        if any(timetables[sem].at[ts, day] == "" for ts in prev_slots if "BREAK" not in ts):
                            continue
                        for prof in professors:
                            if (prof not in faculty_schedule[(day, ts1)] and
                                prof not in faculty_schedule[(day, ts2)]):
                                entry = f"B1-{subject}-{prof}\nB2-{subject}-{prof}"
                                timetables[sem].at[ts1, day] = entry
                                timetables[sem].at[ts2, day] = entry
                                faculty_schedule[(day, ts1)].add(prof)
                                faculty_schedule[(day, ts2)].add(prof)
                                sem_day_class_count[sem][day] += 2
                                assigned = True
                                break
                        if assigned:
                            break
                    if assigned:
                        break

    return timetables

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
    
      if st.button("Generate Timetables"):
        timetables = generate_all_timetables(semesters_data)
        for sem, name in [('2', '2nd Semester'), ('4', '4th Semester'), ('6', '6th Semester')]:
            st.write(f"### {name} Timetable")

            display_df = timetables[sem].copy()

            st.dataframe(
                display_df.style.set_properties(**{
                    'white-space': 'pre-wrap',
                    'text-align': 'center',
                    'min-width': '120px',
                    'max-width': '150px'
                }),
                height=600
            )

            
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
