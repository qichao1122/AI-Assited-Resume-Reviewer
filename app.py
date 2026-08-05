import streamlit as st
from resume import get_resume
from resume import extract_skills


st.title("Resume Reviewer")
resume_file = st.file_uploader(
    "Upload your resume in PDF",
    type="pdf"
)
if resume_file:
    resume_text = get_resume(resume_file)

    st.success("Resume Uploaded successfully")
    st.write(resume_text)

    jobs = [
        {
            "title": "Software Engineer",
            "skills": [
                "Python",
                "AWS",
                "SQL"
            ]
        },
        {
            "title": "Data Analyst",
            "skills": [
                "SQL",
                "Excel"
            ]
        }
    ]

    if st.button("Analyze Jobs"):
        result = analyze_jobs(
            resume_text,
            jobs
        )

        st.subheader("AI Recommendation")
        st.write(result)



