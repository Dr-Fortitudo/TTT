import streamlit as st
import pandas as pd

# Constants
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
TIME_SLOTS = ["9-10 AM", "10-11 AM", "11-12 PM", "1-2 PM", "2-3 PM", "3-4 PM"]
SEMESTERS = ["2nd Semester", "4th Semester", "6th Semester"]

# Page Configuration
st.set_page_config(page_title="Timetable Generator", page_icon="📅", layout="wide")

st.title("📅 Systematic Timetable Generator")

st.sidebar.header("📌 Input Faculty & Subjects")

# Collect Faculty Data
faculty_data = []
num_faculty = st.sidebar.number_input("Number of Faculty", min_value=1, max_value=10, value=3)

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

# Button to Generate Timetable
if st.button("Generate Timetable"):
    if not faculty_data:
        st.warning("⚠️ Please enter at least one faculty with subjects.")
    else:
        st.success("✅ Generating Timetable...")

        # Initialize an empty timetable
        timetable = {semester: {day: {slot: "" for slot in TIME_SLOTS} for day in DAYS} for semester in SEMESTERS}

        # Faculty assignment tracking
        faculty_schedule = {faculty["name"]: 0 for faculty in faculty_data}

        # Systematic lecture allocation
        for semester in SEMESTERS:
            faculty_index = 0  # Start assigning from the first faculty
            
            for day in DAYS:
                for slot in TIME_SLOTS:
                    if faculty_index >= len(faculty_data):  # Reset index if all faculties are used
                        faculty_index = 0

                    faculty = faculty_data[faculty_index]
                    if faculty_schedule[faculty["name"]] < faculty["weekly_hours"]:
                        subject = faculty["subjects"][faculty_schedule[faculty["name"]] % len(faculty["subjects"])]
                        timetable[semester][day][slot] = f"{subject} ({faculty['name']})"
                        faculty_schedule[faculty["name"]] += 1

                    faculty_index += 1

        # Display Timetable
        for semester in SEMESTERS:
            st.subheader(f"📘 {semester} Timetable")
            df = pd.DataFrame.from_dict(timetable[semester], orient="index")
            st.dataframe(df)

        # CSV Download
        def convert_df(df):
            return df.to_csv(index=True).encode('utf-8')

        st.download_button(
            label="📥 Download Timetable as CSV",
            data=convert_df(df),
            file_name="timetable.csv",
            mime="text/csv",
        )
