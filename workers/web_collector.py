"""
workers/web_collector.py
Fetches articles from URLs listed in sources.txt.

Improvement 4: Tries RSS/Atom feeds before falling back to raw HTML scraping.
  - If a URL is itself an RSS feed, feedparser parses it directly.
  - If a URL is an HTML page, the collector looks for a <link> feed tag and
    follows it, returning up to MAX_ARTICLES_PER_SOURCE individual article entries.
  - Only falls back to scraping the raw HTML when no feed is found.
This produces real article content instead of navigation-menu noise.
"""

import os
import socket
import warnings
from ipaddress import ip_address, ip_network
from urllib.parse import urljoin, urlparse

import feedparser
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

# Suppress BeautifulSoup warning when RSS/XML content is parsed with html.parser
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

SOURCES_FILE      = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sources.txt")
TIMEOUT           = 15
MAX_CONTENT_CHARS = 12000
MIN_CONTENT_CHARS = 200


def _get_int_env(name, default, minimum=0):
    try:
        return max(minimum, int(os.environ.get(name, str(default))))
    except (TypeError, ValueError):
        return default


MAX_ARTICLES_PER_SOURCE = _get_int_env("MAX_ARTICLES_PER_SOURCE", 2, minimum=1)
MAX_TOTAL_ARTICLES = _get_int_env("MAX_TOTAL_ARTICLES", 0, minimum=0)

PRIVATE_NETWORKS = tuple(
    ip_network(cidr)
    for cidr in (
        "10.0.0.0/8",
        "127.0.0.0/8",
        "169.254.0.0/16",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "::1/128",
        "fc00::/7",
        "fe80::/10",
    )
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _strip_html(html_text):
    return BeautifulSoup(html_text or "", "html.parser").get_text(separator="\n", strip=True)


def _is_safe_url(url):
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    hostname = parsed.hostname
    if not hostname:
        return False
    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(hostname, None)}
    except socket.gaierror:
        return False
    for addr in addresses:
        parsed_ip = ip_address(addr)
        if parsed_ip.is_private or parsed_ip.is_loopback or parsed_ip.is_link_local:
            return False
        if any(parsed_ip in network for network in PRIVATE_NETWORKS):
            return False
    return True


def _get_url(url):
    if not _is_safe_url(url):
        raise requests.RequestException(f"Unsafe or unsupported URL skipped: {url}")
    return requests.get(url, headers=HEADERS, timeout=TIMEOUT)


def _parse_feed(feed_url):
    """
    Parse feed_url with feedparser.
    Returns list of (title, content) tuples, or [] if nothing useful found.
    """
    try:
        resp = _get_url(feed_url)
        resp.raise_for_status()
    except requests.RequestException:
        return []

    feed = feedparser.parse(resp.content)

    # bozo=True means feedparser hit a parse error; skip if no entries either
    if feed.bozo and not feed.entries:
        return []

    results = []
    for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
        title = entry.get("title", "Untitled").strip()

        # Prefer full content, fall back to summary / description
        content = ""
        if entry.get("content"):
            content = _strip_html(entry.content[0].get("value", ""))
        elif entry.get("summary"):
            content = _strip_html(entry.summary)
        elif entry.get("description"):
            content = _strip_html(entry.description)

        if content and len(content) >= MIN_CONTENT_CHARS:
            results.append((title, content[:MAX_CONTENT_CHARS]))

    return results


def _find_feed_link(page_url, soup):
    """
    Look for an RSS or Atom <link> tag in the page <head>.
    Returns an absolute feed URL, or None.
    """
    for link in soup.find_all(
        "link", type=["application/rss+xml", "application/atom+xml"]
    ):
        href = (link.get("href") or "").strip()
        if href:
            return urljoin(page_url, href)
    return None


# ── Per-URL fetcher ────────────────────────────────────────────────────────────

def fetch_from_source(url):
    """
    Try to get article content from *url* using three strategies in order:

    1. Direct feed parse — url might already be an RSS/Atom endpoint.
    2. HTML feed discovery — fetch the HTML page, find its <link> feed tag,
       then parse that feed.
    3. HTML scrape fallback — extract body text directly from the page.

    Returns a list of (title, content) tuples (may be more than one for feeds).
    Returns [] on unrecoverable failure.
    """
    # Strategy 1: URL is already a feed
    articles = _parse_feed(url)
    if articles:
        return articles

    # Fetch the page for strategies 2 and 3
    try:
        resp = _get_url(url)
        resp.raise_for_status()
    except requests.RequestException:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    # Strategy 2: Discover and parse feed linked in <head>
    feed_url = _find_feed_link(url, soup)
    if feed_url:
        articles = _parse_feed(feed_url)
        if articles:
            return articles

    # Strategy 3: Fall back to scraping body text
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else url

    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    container = soup.find("main") or soup.find("article") or soup.find("body")
    content = (
        container.get_text(separator="\n", strip=True)
        if container
        else soup.get_text(separator="\n", strip=True)
    )

    content = content[:MAX_CONTENT_CHARS]
    if len(content) < MIN_CONTENT_CHARS:
        return []
    return [(title, content)]


# ── Batch collector ────────────────────────────────────────────────────────────

def load_sources():
    if not os.path.exists(SOURCES_FILE):
        raise FileNotFoundError(
            f"sources.txt not found at {SOURCES_FILE}\n"
            "Please create it and add one URL per line."
        )
    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        urls = [
            line.strip()
            for line in f
            if line.strip() and not line.strip().startswith("#")
        ]
    valid_urls = []
    for url in urls:
        if _is_safe_url(url):
            valid_urls.append(url)
        else:
            print(f"  Skipping unsupported or unsafe URL: {url}")
    return valid_urls


def collect_all(run_id, store, verbose=True):
    """
    Fetch content from every URL in sources.txt, try RSS first,
    save each article to the store, and return a list of article dicts.
    One URL may yield multiple articles when an RSS feed is found.
    """
    urls = load_sources()
    results = []

    for url in urls:
        if MAX_TOTAL_ARTICLES and len(results) >= MAX_TOTAL_ARTICLES:
            break

        if verbose:
            print(f"  Processing: {url}")

        articles = fetch_from_source(url)

        if not articles:
            if verbose:
                print(f"    Could not retrieve content from: {url}")
            continue

        for title, content in articles:
            if MAX_TOTAL_ARTICLES and len(results) >= MAX_TOTAL_ARTICLES:
                break
            article_id = store.save_article(run_id, url, title, content)
            results.append(
                {
                    "article_id": article_id,
                    "url": url,
                    "title": title,
                    "content": content,
                }
            )
            if verbose:
                print(f"    Saved: {title}")

    return results
