import streamlit as st
import pandas as pd
import random

# Define Timetable Parameters
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
TIME_SLOTS = ["9-10 AM", "10-11 AM", "11-12 PM", "1-2 PM", "2-3 PM", "3-4 PM"]
SEMESTERS = ["2nd Semester", "4th Semester", "6th Semester"]

st.title("📅 Timetable Generator")

# Sidebar for Inputs
st.sidebar.header("📌 Input Subjects & Faculty")

faculty_data = []
num_faculty = st.sidebar.number_input("Number of Faculty", min_value=1, max_value=20, value=3)

for i in range(num_faculty):
    with st.sidebar.expander(f"Faculty {i+1}"):
        name = st.text_input(f"Faculty Name {i+1}", key=f"fac{i}")
        subjects = st.text_area(f"Subjects (comma-separated) {i+1}", key=f"subj{i}")
        weekly_hours = st.number_input(f"Weekly Hours {i+1}", min_value=1, max_value=10, value=3, key=f"hrs{i}")
        
        if name and subjects:
            faculty_data.append({
                "name": name,
                "subjects": [s.strip() for s in subjects.split(",")],
                "weekly_hours": weekly_hours
            })

# Generate Timetable Button
if st.button("Generate Timetable"):
    if not faculty_data:
        st.warning("Please enter at least one faculty with subjects.")
    else:
        st.success("Generating Timetable...")

        # Create timetable structure
        timetable = {semester: {day: {slot: "" for slot in TIME_SLOTS} for day in DAYS} for semester in SEMESTERS}

        # Faculty Schedule Dictionary
        faculty_schedule = {faculty["name"]: [] for faculty in faculty_data}

        for semester in SEMESTERS:
            remaining_hours = {faculty["name"]: faculty["weekly_hours"] for faculty in faculty_data}
            
            for faculty in faculty_data:
                assigned_hours = 0
                available_slots = [(day, slot) for day in DAYS for slot in TIME_SLOTS]
                random.shuffle(available_slots)  # Shuffle to distribute lectures randomly
                
                while assigned_hours < faculty["weekly_hours"] and available_slots:
                    day, slot = available_slots.pop()
                    
                    # Check if the slot is free
                    if not timetable[semester][day][slot]:
                        subject = random.choice(faculty["subjects"])
                        timetable[semester][day][slot] = f"{subject} ({faculty['name']})"
                        faculty_schedule[faculty["name"]].append((semester, day, slot))
                        assigned_hours += 1
                        remaining_hours[faculty["name"]] -= 1

        # Display Timetable
        for semester in SEMESTERS:
            st.subheader(f"📘 {semester} Timetable")
            df = pd.DataFrame.from_dict(timetable[semester], orient="index")
            st.dataframe(df)

        # Allow CSV Download
        def convert_df(df):
            return df.to_csv(index=True).encode('utf-8')

        st.download_button(
            label="Download Timetable as CSV",
            data=convert_df(df),
            file_name="timetable.csv",
            mime="text/csv",
        )
