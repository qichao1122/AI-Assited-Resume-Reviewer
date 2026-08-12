import streamlit as st

from resume import get_resume, extract_skills
from analyzer import analyze_jobs
import job_scraper
import databse

st.set_page_config(page_title="Job Hunter")
databse.init_db()

if "user" not in st.session_state:
    st.session_state.user = None
if "current_resume_id" not in st.session_state:
    st.session_state.current_resume_id = None


def login_signup():
    st.title("Job Hunter")
    st.caption("Log in or create an account to upload and save your resume.")

    tab_login, tab_signup = st.tabs(["Log in", "Sign up"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Log in", type="primary"):
            if not email or not password:
                st.error("Enter both email and password.")
            else:
                user = databse.verify_user(email, password)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

    with tab_signup:
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        confirm = st.text_input("Confirm password", type="password", key="signup_confirm")
        if st.button("Create account", type="primary"):
            if not email or not password:
                st.error("Email and password are required.")
            elif password != confirm:
                st.error("Passwords don't match.")
            elif len(password) < 6:
                st.error("Password should be at least 6 characters.")
            else:
                ok, msg = databse.create_user(email, password)
                if ok:
                    st.success(msg + " You can log in now.")
                else:
                    st.error(msg)

def main_app():
    user = st.session_state.user

    with st.sidebar:
        st.write(f"Logged in as **{user['email']}**")
        if st.button("Log out"):
            st.session_state.user = None
            st.session_state.current_resume_id = None
            st.rerun()

    st.title("Resume Reviewer")


    st.subheader("Your resume")
    resume_file = st.file_uploader("Upload your resume (PDF)", type="pdf")

    resume_text = None
    skills_found = []

    if resume_file:
        resume_text = get_resume(resume_file)
        st.write(resume_text)
        st.write(type(resume_text))
        skills_found = extract_skills(resume_text)

        st.success("Resume uploaded successfully.")
        with st.expander("Extracted resume text"):
            st.write(resume_text)
        st.write("**Detected skills:**", ", ".join(skills_found) if skills_found else "none detected")

        if st.button("Save resume to my account"):
            resume_id = databse.save_resume(user["id"], resume_file.name, resume_text)
            st.session_state.current_resume_id = resume_id
            st.success("Saved.")

    st.divider()

    st.subheader("Job posting")
    job_title_input = st.text_input("Job title (used to label the result)", placeholder="e.g. Software Engineer")
    job_url = st.text_input("Job posting URL", placeholder="https://...")
    job_text_manual = st.text_area(
        "Or paste the job description text directly "
        "(use this if the link fails — many job boards block automated fetches)",
        height=150,
    )

    if st.button("Analyze fit", type="primary"):
        if not resume_file:
            st.error("Upload a resume first.")
        elif not job_url.strip() and not job_text_manual.strip():
            st.error("Enter a job posting URL or paste the description text.")
        else:
            job_description_text = None

            if job_text_manual.strip():
                job_description_text = job_text_manual.strip()
            else:
                with st.spinner("Fetching job posting..."):
                    try:
                        job_description_text = job_scraper.get_job_description(job_url.strip())
                    except RuntimeError as e:
                        st.error(str(e))

            if job_description_text:
                title = job_title_input.strip() or "Job posting"
                with st.spinner("Analyzing fit..."):
                    result = analyze_jobs(resume_text, skills_found, title, job_description_text)

                st.subheader("AI Recommendation")
                st.markdown(f"**{result['title']}**")
                st.write(result["analysis"])

                resume_id = st.session_state.current_resume_id
                if resume_id:
                    databse.save_analysis(resume_id, result["title"], result["analysis"])
                else:
                    st.info("Save your resume above if you'd like this analysis kept in your history.")

    st.divider()


    st.subheader("Your saved resumes")
    resumes = databse.get_user_resumes(user["id"])
    if not resumes:
        st.write("No resumes saved yet — upload one above and click **Save resume**.")
    else:
        for r in resumes:
            with st.expander(f"{r['filename']} — uploaded {r['uploaded_at'][:19]}"):
                preview = r["resume_text"][:500]
                st.text(preview + ("..." if len(r["resume_text"]) > 500 else ""))

                analyses = databse.get_analyses_for_resume(r["id"])
                if analyses:
                    st.markdown("**Past analyses:**")
                    for a in analyses:
                        st.markdown(f"*{a['job_title']}* — {a['created_at'][:19]}")
                        st.write(a["result"])
                        st.markdown("---")


if st.session_state.user is None:
    login_signup()
else:
    main_app()