from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    )
}

IRRELEVANT_TAGS = ["script", "style", "img", "input", "button", "svg", "noscript"]


def _fetch_soup(url: str, timeout: int = 15) -> BeautifulSoup:
    response = requests.get(url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    return BeautifulSoup(response.content, "html.parser")


def fetch_website_links(url: str) -> list[str]:
    """Return unique absolute HTTP(S) links found on the given page."""
    soup = _fetch_soup(url)
    seen: set[str] = set()
    links: list[str] = []

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        absolute = urljoin(url, href)
        parsed = urlparse(absolute)
        if parsed.scheme not in ("http", "https"):
            continue

        normalized = absolute.split("#", 1)[0]
        if normalized not in seen:
            seen.add(normalized)
            links.append(normalized)

    return links


def fetch_website_contents(url: str) -> str:
    """Return the page title and cleaned visible text for the given URL."""
    soup = _fetch_soup(url)
    title = soup.title.string.strip() if soup.title and soup.title.string else "No title"

    body = soup.body
    if body is None:
        return f"Title: {title}\n\n"

    for tag in body(IRRELEVANT_TAGS):
        tag.decompose()

    text = body.get_text(separator="\n", strip=True)
    return f"Title: {title}\n\n{text}"
