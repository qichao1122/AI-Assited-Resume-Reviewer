from pypdf import PdfReader

def get_resume(file_path):
    reader = PdfReader(file_path)

    resume_text = ""

    for index, page in enumerate(reader.pages):
        text = page.extract_text(extraction_mode="layout")

        if text:
            resume_text += text + "\n"

    return resume_text


def extract_skills(text):
    if not text:
        return set()

    skills = [
        "Python",
        "Java",
        "JavaScript",
        "Programming",
        "Large Language Models (LLMs)",
        "Machine Learning",
        "Data Analysis",
        "Structured Query Language (SQL)",
        "SQL",
        "CI/CD",
        "GitHub",
        "Git",
        "AWS",
        "Azure",
        "Docker",
        "Excel",
    ]

    found = set()
    text_lower = text.lower()

    for skill in skills:
        if skill.lower() in text_lower:
            found.add(skill)

    return found