from llm import get_llm



def keyword_result(resume_skills,job_skills):
    matching_scores = 0
    for skill in resume_skills:
        if skill in job_skills:
            matching_scores += 1



def analyze_job(resume_text,resume_skills,jobs):
    llm = get_llm()
    job_results = []

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
                        f"(LLM unavailable, used keyword match instead — {e})\n" + keyword_result(resume_skills, job)
                )
        else:
            analysis = keyword_result(resume_skills, job)

        job_results.append({"title": job["title"], "analysis": analysis})

    return job_results




