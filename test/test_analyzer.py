from unittest.mock import patch

from analyzer import (
    keyword_result,
    analyze_job,
    suggest_resume_improvements,
    generate_cover_letter,
    parse_score,
)


def test_parse_score_extracts_number():
    assert parse_score("Score: 85\nExplanation: Good fit.") == 85


def test_parse_score_case_insensitive():
    assert parse_score("score: 42") == 42


def test_parse_score_returns_none_when_absent():
    assert parse_score("No score line here.") is None
    assert parse_score("") is None
    assert parse_score(None) is None


def test_parse_score_clamps_out_of_range_values():
    assert parse_score("Score: 150") == 100


def test_keyword_result_no_keywords_found():
    result = keyword_result("Some resume text", "")
    assert "Score: 0" in result


def test_keyword_result_full_match():
    jd = "Requires Customer Service and Sales experience."
    resume = "I have 5 years of Customer Service and Sales experience."
    result = keyword_result(resume, jd)
    assert "Score: 100" in result


def test_keyword_result_partial_match():
    jd = "Requires Patient Care and HIPAA compliance."
    resume = "Experienced in Patient Care in a retail setting."
    result = keyword_result(resume, jd)
    assert "Matched: Patient Care" in result
    assert "HIPAA" in result  # should show up in Missing


@patch("analyzer.get_llm")
def test_analyze_job_falls_back_to_keywords_when_llm_unavailable(mock_get_llm):
    mock_get_llm.return_value = None

    result = analyze_job(
        resume_text="Customer Service and Sales background.",
        job_title="Retail Associate",
        job_description_text="Looking for Customer Service and Sales skills.",
    )

    assert result["title"] == "Retail Associate"
    assert "Score:" in result["analysis"]


@patch("analyzer.get_llm")
def test_analyze_job_uses_llm_response_when_available(mock_get_llm):
    mock_llm = mock_get_llm.return_value
    mock_llm.invoke.return_value.content = "Score: 90\nExplanation: Great fit."

    result = analyze_job(
        resume_text="Some resume",
        job_title="Data Analyst",
        job_description_text="Some job description",
    )

    assert result["title"] == "Data Analyst"
    assert result["analysis"] == "Score: 90\nExplanation: Great fit."
    mock_llm.invoke.assert_called_once()


@patch("analyzer.get_llm")
def test_analyze_job_falls_back_when_llm_raises(mock_get_llm):
    mock_llm = mock_get_llm.return_value
    mock_llm.invoke.side_effect = RuntimeError("connection refused")

    result = analyze_job(
        resume_text="Customer Service background.",
        job_title="Retail Associate",
        job_description_text="Needs Customer Service skills.",
    )

    assert "LLM unavailable" in result["analysis"]
    assert "Score:" in result["analysis"]


@patch("analyzer.get_llm")
def test_suggest_resume_improvements_uses_llm_when_available(mock_get_llm):
    mock_llm = mock_get_llm.return_value
    mock_llm.invoke.return_value.content = "- Add more detail about X"

    result = suggest_resume_improvements("Some resume", "Some job description")

    assert result == "- Add more detail about X"
    mock_llm.invoke.assert_called_once()


@patch("analyzer.get_llm")
def test_suggest_resume_improvements_falls_back_without_llm(mock_get_llm):
    mock_get_llm.return_value = None

    jd = "Requires Patient Care and HIPAA compliance."
    resume = "Experienced in Customer Service."

    result = suggest_resume_improvements(resume, jd)

    assert "Patient Care" in result
    assert "HIPAA" in result


@patch("analyzer.get_llm")
def test_suggest_resume_improvements_notes_full_coverage(mock_get_llm):
    mock_get_llm.return_value = None

    jd = "Requires Customer Service."
    resume = "Extensive Customer Service background."

    result = suggest_resume_improvements(resume, jd)

    assert "already mentions" in result


@patch("analyzer.get_llm")
def test_generate_cover_letter_uses_llm_when_available(mock_get_llm):
    mock_llm = mock_get_llm.return_value
    mock_llm.invoke.return_value.content = "Dear Hiring Manager, ..."

    result = generate_cover_letter(
        "Some resume", "Data Analyst", "Some job description", applicant_name="Alex"
    )

    assert result == "Dear Hiring Manager, ..."
    mock_llm.invoke.assert_called_once()


@patch("analyzer.get_llm")
def test_generate_cover_letter_falls_back_without_llm(mock_get_llm):
    mock_get_llm.return_value = None

    result = generate_cover_letter("Some resume", "Data Analyst", "Some job description")

    assert "Data Analyst" in result
    assert "[Your Name]" in result


@patch("analyzer.get_llm")
def test_generate_cover_letter_uses_provided_name_in_fallback(mock_get_llm):
    mock_get_llm.return_value = None

    result = generate_cover_letter(
        "Some resume", "Data Analyst", "Some job description", applicant_name="Alex Kim"
    )

    assert "Alex Kim" in result
    assert "[Your Name]" not in result


@patch("analyzer.get_llm")
def test_generate_cover_letter_falls_back_when_llm_raises(mock_get_llm):
    mock_llm = mock_get_llm.return_value
    mock_llm.invoke.side_effect = RuntimeError("connection refused")

    result = generate_cover_letter("Some resume", "Data Analyst", "Some job description")

    assert "LLM unavailable" in result
    assert "Data Analyst" in result