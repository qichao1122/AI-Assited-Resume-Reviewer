# Job Hunter

A Streamlit app for reviewing resumes against job postings.

## What it does

Upload a resume (PDF), create an account to save it, then paste a job
posting link or its description text. The app compares your resume to that
job and gives you a fit score and explanation. If you have Ollama running
locally with qwen2.5:7b, it uses that LLM for the analysis. If not, it falls
back to a simple keyword-matching score, so it still works either way.

Works for any type of job, not just tech roles, since it pulls the relevant
keywords directly from whatever job description you give it.

## Setup

pip install -r requirements.txt

Optional, for AI-powered analysis:

1. Install Ollama from ollama.com
2. Run: ollama pull qwen2.5:7b

If you skip this, the app just uses keyword matching instead.

## Run

streamlit run app.py

It'll open in your browser, usually at http://localhost:8501

## Tests

pip install pytest
pytest tests/ -v

## Lint

pip install pylint
pylint app.py analyzer.py databse.py job_scraper.py llm.py resume.py

## Files

- app.py - the Streamlit UI (login, upload, analysis, history)
- databse.py - SQLite setup and queries
- resume.py - PDF text extraction and keyword extraction
- job_scraper.py - fetches and cleans text from a job posting URL
- analyzer.py - does the actual resume vs job comparison
- llm.py - sets up the Ollama connection
- tests/ - pytest tests for the above
- .github/workflows/tests.yml - runs lint + tests on every push

## Notes

Some job sites (LinkedIn, Indeed, big company career pages built on
Workday) block scraping or need JavaScript to load the real content, so
fetching the URL won't always work. If that happens, just paste the job
description text into the text box instead - it works the same way.

Login is basic (salted/hashed passwords in SQLite) - fine for a personal
project, not meant for production use with real user data.
