from resume import extract_skills, extract_keywords_from_job


def test_extract_skills_returns_empty_set_for_falsy_input():
    assert extract_skills(None) == set()
    assert extract_skills("") == set()


def test_extract_skills_is_case_insensitive():
    text = "Experienced with python, sql, and AWS."
    found = extract_skills(text)
    assert "Python" in found
    assert "SQL" in found
    assert "AWS" in found


def test_extract_skills_ignores_unrelated_text():
    text = "I enjoy hiking and painting on weekends."
    assert extract_skills(text) == set()


def test_extract_keywords_from_job_returns_empty_set_for_falsy_input():
    assert extract_keywords_from_job(None) == set()
    assert extract_keywords_from_job("") == set()


def test_extract_keywords_from_job_pulls_non_tech_terms():
    jd = (
        "We are seeking a Pharmacy Technician. Responsibilities include "
        "Patient Care, Prescription processing, and HIPAA compliance."
    )
    keywords = extract_keywords_from_job(jd)
    assert "Patient Care" in keywords
    assert "HIPAA" in keywords
    assert "Prescription" in keywords


def test_extract_keywords_from_job_filters_stopword_phrases():
    jd = "The Job Description below outlines Requirements for this role."
    keywords = extract_keywords_from_job(jd)
    # phrases starting with filtered stopwords shouldn't appear
    assert "The" not in keywords
    assert not any(kw.startswith("The ") for kw in keywords)


def test_extract_keywords_from_job_respects_max_keywords():
    jd = " ".join(f"Skill{i} Name{i}" for i in range(100))
    keywords = extract_keywords_from_job(jd, max_keywords=10)
    assert len(keywords) <= 10