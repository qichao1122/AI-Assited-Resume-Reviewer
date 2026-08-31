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


def analyze_job(resume_text, job_title, job_description_text):
    """
    Compare a resume against a single job description's full text
    (fetched from a URL or pasted by the user).

    Returns {"title": str, "analysis": str}.
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
            analysis = f"(LLM unavailable, used keyword match instead — {e})\n" + keyword_result(
                resume_text, job_description_text
            )
    else:
        analysis = keyword_result(resume_text, job_description_text)

    return {"title": job_title, "analysis": analysis}


def _missing_keywords_fallback(resume_text, job_description_text):
    """Non-LLM improvement suggestions: list job requirements absent from the resume."""
    job_keywords = extract_keywords_from_job(job_description_text)
    resume_lower = resume_text.lower()
    missing = [kw for kw in job_keywords if kw.lower() not in resume_lower]

    if not missing:
        return "Your resume already mentions the key terms found in this job description."

    lines = ["Consider addressing these requirements from the posting that aren't in your resume yet:"]
    for kw in missing:
        lines.append(f"- {kw}: add a bullet point or line mentioning relevant experience, if you have any.")
    return "\n".join(lines)


def suggest_resume_improvements(resume_text, job_description_text):
    """
    Suggest specific, concrete edits to better align the resume with a
    given job description. LLM primary; falls back to a missing-keyword
    checklist if the LLM isn't available.
    """
    llm = get_llm()

    if llm is not None:
        prompt = (
            "You are a professional resume coach. Given the resume and job "
            "description below, suggest specific improvements to the resume "
            "so it better matches this job.\n\n"
            f"Resume:\n{resume_text}\n\n"
            f"Job description:\n{job_description_text}\n\n"
            "Base every suggestion ONLY on experience the candidate actually "
            "has in their resume — do not invent skills or experience they "
            "don't have. Where a real gap exists (something the job wants "
            "that the resume doesn't show), say so plainly rather than "
            "papering over it.\n\n"
            "Give 3-5 concrete suggestions as a bulleted list. For each, "
            "point to a specific line or bullet in the resume and suggest "
            "how to rephrase or reframe it, or flag it as a genuine gap."
        )
        try:
            response = llm.invoke(prompt)
            return response.content
        except Exception as e:
            return (
                f"(LLM unavailable, used a keyword-based fallback instead — {e})\n"
                + _missing_keywords_fallback(resume_text, job_description_text)
            )

    return _missing_keywords_fallback(resume_text, job_description_text)


def _template_cover_letter(job_title, applicant_name):
    """Very basic non-LLM cover letter template, used only when the LLM is unavailable."""
    return (
        f"Dear Hiring Manager,\n\n"
        f"I am writing to express my interest in the {job_title} position. "
        "Based on my background and experience, I believe I would be a "
        "strong fit for this role and would welcome the opportunity to "
        "discuss my qualifications further.\n\n"
        "Thank you for your time and consideration.\n\n"
        f"Sincerely,\n{applicant_name}"
    )


def generate_cover_letter(resume_text, job_title, job_description_text, applicant_name=None):
    """
    Draft a cover letter tailored to the resume and job description.
    LLM primary; falls back to a generic template if the LLM isn't
    available (the fallback can't personalize to real experience, since
    it has no way to summarize the resume without an LLM).
    """
    llm = get_llm()
    name_line = applicant_name.strip() if applicant_name and applicant_name.strip() else "[Your Name]"

    if llm is not None:
        prompt = (
            "You are a professional career coach. Write a concise, "
            f"professional cover letter (3-4 short paragraphs) for the role "
            f"of '{job_title}', based on the resume and job description "
            "below. Reference specific requirements from the job description "
            "and connect them to specific, real experience from the resume. "
            "Do not invent experience, skills, or credentials that aren't in "
            "the resume.\n\n"
            f"Applicant name for the sign-off: {name_line}\n\n"
            f"Resume:\n{resume_text}\n\n"
            f"Job description:\n{job_description_text}\n\n"
            "Write only the cover letter text itself, no preamble or notes."
        )
        try:
            response = llm.invoke(prompt)
            return response.content
        except Exception as e:
            return (
                f"(LLM unavailable, used a basic template instead — {e})\n\n"
                + _template_cover_letter(job_title, name_line)
            )

    return (
        "(No LLM available, so this is a generic template — it can't "
        "reference your actual experience without one.)\n\n"
        + _template_cover_letter(job_title, name_line)
    )