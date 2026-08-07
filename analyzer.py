from llm import get_llm
from resume import extract_skills

def _keyword_result(resume_skills, job_skills):
    """Fallback scoring when the LLM isn't available: simple overlap %."""

    if not job_skills:
        return "Score: 0\nCouldn't detect any known skills in that job description."

    matched = [skill for skill in resume_skills if skill.lower() in job_skills]
    missing = [skill for skill in job_skills if skill not in matched]
    score = round(len(matched) / len(job_skills) * 100)

    return (
        f"Score: {score}/100\n"
        f"Matched skills: {', '.join(matched) if matched else 'none'}\n"
        f"Missing skills: {', '.join(missing) if missing else 'none'}"
    )


def analyze_jobs(resume_text, resume_skills, job_title, job_description_text):
    """
    Compare a resume against a list of job dicts ({"title", "skills"}).
    Uses the LLM if available; falls back to keyword matching per-job
    if the LLM call fails or isn't configured.

    Returns a list of {"title": str, "analysis": str}.
    """
    llm = get_llm()
    job_skills = extract_skills(resume_text)

    if llm is not None:
        prompt = (
            "You are a career expert. Given the resume below, "
            f"evaluate fit for the role of '{job_title['title']}', which requires "
            f"these skills: {', '.join(job_skills['skills'])}.\n\n"
            f"Resume:\n{resume_text}\n\n"
            "Respond in this exact format:\n"
            "Score: <0-100>\n"
            "Explanation: <2-3 sentences on strengths and gaps>"
        )
        try:
            response = llm.invoke(prompt)
            analysis = response.content
        except Exception as e:
            analysis = (
                    f"(LLM unavailable, used keyword match instead — {e})\n"
                    + _keyword_result(resume_skills, job_skills)
            )
    else:
        analysis = _keyword_result(resume_skills, job_skills)


    return {"title": job_title, "analysis": analysis}