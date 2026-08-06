from llm import get_llm


def keyword_match_score(resume_skills, job_skills):
    """Fallback scoring when no LLM is available: simple overlap %."""
    if not job_skills:
        return 0, [], []

    resume_lower = [skill.lower() for skill in resume_skills]
    matched = [skill for skill in job_skills if skill.lower() in resume_lower]
    missing = [skill for skill in job_skills if skill not in matched]
    score = round(len(matched) / len(job_skills) * 100)
    return score, matched, missing


def _keyword_result(resume_skills, job):
    score, matched, missing = keyword_match_score(resume_skills, job["skills"])
    return (
        f"Score: {score}/100\n"
        f"Matched skills: {', '.join(matched) if matched else 'none'}\n"
        f"Missing skills: {', '.join(missing) if missing else 'none'}"
    )


def analyze_jobs(resume_text, resume_skills, jobs):
    """
    Compare a resume against a list of job dicts ({"title", "skills"}).
    Uses the LLM if available; falls back to keyword matching per-job
    if the LLM call fails or isn't configured.

    Returns a list of {"title": str, "analysis": str}.
    """
    llm = get_llm()
    results = []

    for job in jobs:
        if llm is not None:
            prompt = (
                "You are a helpful career advisor. Given the resume below, "
                f"evaluate fit for the role of '{job['title']}', which requires "
                f"these skills: {', '.join(job['skills'])}.\n\n"
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
                    + _keyword_result(resume_skills, job)
                )
        else:
            analysis = _keyword_result(resume_skills, job)

        results.append({"title": job["title"], "analysis": analysis})

    return results