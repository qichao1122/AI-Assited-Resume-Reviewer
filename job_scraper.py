import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}


def get_job_description(url, timeout=10):
    """
    Fetch a job posting URL and return its cleaned, visible text.

    Raises RuntimeError with a user-friendly message on failure — callers
    should catch this and offer the "paste the text manually" fallback,
    since many job boards (LinkedIn, Indeed, etc.) block bots or require
    JavaScript/login and simply won't work with this approach.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(
            f"Couldn't fetch that URL ({e}). The site may block automated "
            "requests — try pasting the job description text instead."
        )

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    cleaned = "\n".join(lines)

    if len(cleaned) < 50:
        raise RuntimeError(
            "That page had little or no readable text once scripts/styles "
            "were stripped out — it likely needs JavaScript to render. "
            "Try pasting the job description text instead."
        )

    return cleaned