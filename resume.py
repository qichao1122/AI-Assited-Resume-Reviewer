import re
from pypdf import PdfReader


def get_resume(file_path):
    """
    Extract text from a PDF resume.
    Accepts either a path/string or a file-like object (e.g. Streamlit's
    UploadedFile from st.file_uploader).
    Always returns a string — empty "" if the PDF has no extractable text
    layer (e.g. a scanned image PDF).
    """
    reader = PdfReader(file_path)

    resume_text = ""
    for page in reader.pages:
        text = page.extract_text(extraction_mode="layout")
        if text:
            resume_text += text + "\n"

    return resume_text


# A broad, cross-industry starter list. Not exhaustive on purpose — the
# real coverage comes from extract_keywords_from_job() below, which pulls
# skill/requirement terms out of whatever job description you give it, so
# it isn't limited to whatever industries we thought to hardcode here.
COMMON_SKILLS = [
    # Tech / programming
    "Python",
    "Java",
    "JavaScript",
    "SQL",
    "Git",
    "GitHub",
    "CI/CD",
    "Machine Learning",
    "Data Analysis",
    "AWS",
    "Azure",
    "Docker",
    # Healthcare / pharmacy
    "Patient Care",
    "HIPAA",
    "Pharmacy",
    "Medication",
    "Prescription",
    "Clinical",
    "Nursing",
    "CPR",
    "First Aid",
    "EMR",
    "Electronic Health Records",
    # Retail / sales
    "Customer Service",
    "Sales",
    "POS",
    "Point of Sale",
    "Merchandising",
    "Inventory Management",
    "Cash Handling",
    "Upselling",
    "Retail",
    # Food service / hospitality
    "Food Safety",
    "ServSafe",
    "Hospitality",
    "Catering",
    "Barista",
    # Office / admin / finance
    "Microsoft Office",
    "Excel",
    "Scheduling",
    "Data Entry",
    "Administrative",
    "Bookkeeping",
    "Accounting",
    "QuickBooks",
    # Education
    "Teaching",
    "Curriculum Development",
    "Tutoring",
    "Classroom Management",
    # Trades / manufacturing
    "Forklift",
    "Welding",
    "Quality Control",
    "Assembly",
    "Manufacturing",
    "OSHA",
    "Construction",
    # Soft skills / general
    "Leadership",
    "Communication",
    "Teamwork",
    "Problem Solving",
    "Time Management",
    "Project Management",
    "Multitasking",
    "Bilingual",
    "Customer Relations",
]

# Job-posting boilerplate words that happen to be capitalized but aren't
# skills — filtered out of the dynamic keyword extraction below.
_STOPWORD_STARTS = {
    "The",
    "This",
    "That",
    "You",
    "We",
    "Our",
    "Your",
    "Job",
    "Apply",
    "About",
    "Please",
    "Note",
    "Job Description",
    "Requirements",
    "Responsibilities",
    "Qualifications",
    "Benefits",
    "Requires",
    "Required",
    "Requiring",
    "Include",
    "Includes",
    "Including",
    "Looking",
    "Seeking",
    "Must",
    "Should",
    "Will",
    "Candidates",
    "Candidate",
    "Applicants",
    "Ideal",
    "Position",
}


def extract_skills(text):
    """Check text against the fixed cross-industry skill list. Returns a set."""
    if not text:
        return set()
    text_lower = text.lower()
    return {skill for skill in COMMON_SKILLS if skill.lower() in text_lower}


def extract_keywords_from_job(job_description_text, max_keywords=40):
    """
    Pull candidate skill/requirement keywords directly out of a job
    description, so matching isn't limited to a pre-written list and
    works for any industry — pharmacy, retail, sales, trades, etc.

    Combines:
      - Any COMMON_SKILLS terms that appear in the text
      - Capitalized 1-3 word phrases in the text (a decent heuristic for
        named skills, tools, and certifications in job postings, e.g.
        "Medication Therapy Management", "ServSafe Certification")
    """
    if not job_description_text:
        return set()

    keywords = extract_skills(job_description_text)

    phrase_pattern = re.compile(r"\b([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+){0,2})\b")
    for phrase in phrase_pattern.findall(job_description_text):
        first_word = phrase.split()[0]
        if first_word in _STOPWORD_STARTS:
            continue
        keywords.add(phrase)
        if len(keywords) >= max_keywords:
            break

    return keywords