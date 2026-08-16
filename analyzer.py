from llm import get_llm
from resume import extract_keywords_from_job


def keyword_result(resume_text, job_description_text):
    """
    Fallback scoring when the LLM isn't available: pulls candidate skill
    keywords out of the job description itself (works for any industry,
    not just tech), then checks which of those actually show up in the
    resume text.
    """
    job_keywords = extract_keywords_from_job(job_description_text)

    if not job_keywords:
        return "Score: 0\nCouldn't detect any specific requirements in that job description."

    resume_lower = resume_text.lower()
    matched = [kw for kw in job_keywords if kw.lower() in resume_lower]
    missing = [kw for kw in job_keywords if kw not in matched]
    score = round(len(matched) / len(job_keywords) * 100)

    return (
        f"Score: {score}\n"
        f"Matched: {', '.join(matched) if matched else 'none'}\n"
        f"Missing: {', '.join(missing) if missing else 'none'}"
    )


def analyze_job(resume_text, resume_skills, job_title, job_description_text):
    """
    Compare a resume against a single job description's full text
    (fetched from a URL or pasted by the user).

    Returns {"title": str, "analysis": str}.
    resume_skills is accepted for backward compatibility with callers but
    isn't required for the keyword fallback anymore — matching is now
    driven by keywords pulled from the job description itself, so it
    works across any industry, not just tech.
    """
    llm = get_llm()

    if llm is not None:
        prompt = (
            "You are a helpful career advisor. Given the resume and job "
            f"description below, evaluate fit for the role of '{job_title}'.\n\n"
            f"Resume:\n{resume_text}\n\n"
            f"Job description:\n{job_description_text}\n\n"
            "Base your evaluation ONLY on the specific requirements and "
            "responsibilities listed in the job description above — do not "
            "assume requirements that aren't actually stated in it.\n\n"
            "Respond in this exact format:\n"
            "Score: <0-100>\n"
            "Explanation: <2-3 sentences on strengths and gaps, referencing "
            "specific requirements from the posting>\n"
            "Suggestions: <1-2 sentences on how to improve fit>"
        )
        try:
            response = llm.invoke(prompt)
            analysis = response.content
        except Exception as e:
            analysis = (
                f"(LLM unavailable, used keyword match instead — {e})\n"
                + keyword_result(resume_text, job_description_text)
            )
    else:
        analysis = keyword_result(resume_text, job_description_text)

    return {"title": job_title, "analysis": analysis}