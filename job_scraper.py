import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}

# Phrases that show up on JS-rendered app shells / bot-block pages instead
# of real content. If these dominate the page, the real job description
# almost certainly wasn't in the HTML we got back.
JS_REQUIRED_MARKERS = [
    "enable javascript",
    "please enable cookies",
    "verify you are human",
    "checking your browser",
    "just a moment",
]

MIN_USABLE_LENGTH = 200  # short static-only fetches are usually shell/boilerplate, not a real posting


def get_job_description(url, timeout=10):
    """
    Fetch a job posting URL and return its cleaned, visible text.

    Raises RuntimeError with a user-friendly message on failure — callers
    should catch this and offer the "paste the text manually" fallback.
    Many career sites (Workday, iCIMS, and most large-company ATS pages,
    including Walgreens') render the actual posting with JavaScript, so a
    plain HTTP fetch like this one often gets only the page shell, not the
    real description. This function tries to detect that case rather than
    silently returning junk.
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

    lowered = cleaned.lower()
    if any(marker in lowered for marker in JS_REQUIRED_MARKERS):
        raise RuntimeError(
            "This page needs JavaScript to load the actual job description "
            "— a plain fetch only got the page shell, not the real content. "
            "Please paste the job description text instead."
        )

    if len(cleaned) < MIN_USABLE_LENGTH:
        raise RuntimeError(
            "That page had very little readable text once scripts/styles "
            "were stripped out — it likely needs JavaScript to render the "
            "actual posting. Please paste the job description text instead."
        )

    return cleaned