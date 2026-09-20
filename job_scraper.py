"""
Fetches and cleans text from a job posting URL.

Two fetch strategies, tried in order:
  1. A fast, static HTTP fetch (works for plain server-rendered pages).
  2. A headless-browser fetch via Playwright, which actually executes
     JavaScript, so it can see the content on JS-rendered career sites
     (LinkedIn, Indeed, Gem-hosted pages, Workday, etc.) that a static
     fetch can't.

If both fail, get_job_description() raises RuntimeError — callers should
catch it and offer the "paste the description manually" fallback, since
some sites (LinkedIn, Indeed especially) actively block even headless
browsers with login walls, CAPTCHAs, or bot-detection services, and no
amount of scraping can get around that reliably.
"""

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

MIN_USABLE_LENGTH = 200


def _clean_html(html):
    """Strip scripts/styles/nav and return the visible text, line-cleaned."""
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def _looks_like_js_shell(cleaned_text):
    """True if the cleaned text looks like a bot-block page or empty app shell."""
    lowered = cleaned_text.lower()
    if any(marker in lowered for marker in JS_REQUIRED_MARKERS):
        return True
    return len(cleaned_text) < MIN_USABLE_LENGTH


def _fetch_static(url, timeout=10):
    """Plain HTTP fetch. Raises requests exceptions on network/HTTP failure."""
    response = requests.get(url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    return _clean_html(response.text)


def _fetch_with_browser(url, timeout_ms=25000):
    """
    Render the page with a real headless browser so JavaScript-loaded
    content shows up, then extract the text.

    Requires the 'playwright' package AND its browser binary:
        pip install playwright
        playwright install chromium
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise RuntimeError(
            "This page needs JavaScript to load, and browser-based fetching "
            "isn't set up. Run: pip install playwright && playwright install "
            "chromium — or paste the job description text instead."
        ) from e

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page(user_agent=HEADERS["User-Agent"])
                # "domcontentloaded" instead of "networkidle": many sites
                # (ads, analytics, tracking pixels) keep making background
                # requests forever and never actually go network-idle, which
                # made networkidle time out even after the real content had
                # already loaded. A short extra wait lets client-side JS
                # finish rendering the content after the DOM is ready.
                page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)
                html = page.content()
            finally:
                browser.close()
    except Exception as e:
        raise RuntimeError(
            f"Browser-based fetch also failed ({e}). Some sites (LinkedIn, "
            "Indeed especially) block even headless browsers with login "
            "walls or bot detection — please paste the job description "
            "text instead."
        ) from e

    return _clean_html(html)


def get_job_description(url, timeout=10):
    """
    Fetch a job posting URL and return its cleaned, visible text.

    Tries a fast static fetch first. If that fails outright, or the result
    looks like a JS shell / bot-block page, retries with a headless browser
    so JavaScript-rendered sites work too. Raises RuntimeError with a
    user-friendly message if both approaches fail.
    """
    static_error = None

    try:
        cleaned = _fetch_static(url, timeout=timeout)
        if not _looks_like_js_shell(cleaned):
            return cleaned
    except requests.exceptions.RequestException as e:
        static_error = e

    try:
        return _fetch_with_browser(url)
    except RuntimeError as browser_error:
        if static_error is not None:
            raise RuntimeError(
                f"Couldn't fetch that URL with a plain request ({static_error}), "
                f"and the browser-based fetch failed too. {browser_error} "
                "Please paste the job description text instead."
            ) from browser_error
        raise