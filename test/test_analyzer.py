from unittest.mock import patch

from analyzer import keyword_result, analyze_job


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