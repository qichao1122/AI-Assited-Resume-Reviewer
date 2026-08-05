from pypdf import PdfReader

def get_resume(file_path):
    #file_path = r"C:\Users\qicha\OneDrive\桌面\Resume.pdf"

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
        "Programming",
        "Large Language Models (LLMs)",
        "Data Analysis",
        "Structured Query Language(SQL)",
        "CI/CD",
        "GitHub"
    ]

    found = []

    for skill in skills:
        if skill.lower() in text.lower():
            found.append(skill)

    return found





