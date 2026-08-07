from pypdf import PdfReader

def get_resume(file_path):
    reader = PdfReader(file_path)

    resume_text = ""

    for index, page in enumerate(reader.pages):
        text = page.extract_text(extraction_mode="layout")
        print(text)

        resume_text += text + "\n"

    print("Full Resume:")
    print(resume_text)

def extract_skills(text):
    skills =[
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

    for skill in skills:
        if skill.lower() in text.lower():
            found.add(skill)


    return found





