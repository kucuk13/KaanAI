"""
suggester_using_by_web_search.py
-------------------------------

"Web" provider for the local suggestion server.

This module performs a web search based on the user's query and returns the
top N results in the same shape as the other providers so the existing
front‑end can render them.  It first attempts to use DuckDuckGo's HTML
search, and if that is blocked or returns no results, it falls back to
Bing and then Google.  Because these providers do not expose a stable,
public API, the module scrapes the returned HTML to extract titles and
links; changes to the providers' markup may break the parser.

For each result we return:
  - ``page_url``: the resolved destination URL
  - ``image_url``: a favicon URL for the destination domain (so ``<img>`` always has a valid ``src``)
  - ``photographer``: the destination domain (used as a label in the UI)
  - ``title``: the result title text (kept for possible future UI use)
"""

from __future__ import annotations

import urllib.parse
from typing import Any, Dict, List, Tuple

import requests
from bs4 import BeautifulSoup


# Base URLs for web search providers.  The suggester will try DuckDuckGo first
# and fall back to Bing or Google if DuckDuckGo returns no results or is
# unreachable.  These search providers return HTML pages that we parse for
# titles and links.  Note that scraping search engines may be fragile if they
# change their markup, and some providers rate‑limit or block automated
# clients.  A modern User‑Agent is supplied in DEFAULT_HEADERS to reduce the
# likelihood of being blocked.
DUCKDUCKGO_URL = "https://duckduckgo.com/html/"
BING_SEARCH_URL = "https://www.bing.com/search"
GOOGLE_SEARCH_URL = "https://www.google.com/search"
DEFAULT_COUNT = 4
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def _resolve_ddg_href(href: str) -> str:
    """
    DuckDuckGo HTML results often use redirect links that include an 'uddg'
    parameter containing the real destination.
    """
    try:
        parsed = urllib.parse.urlparse(href)
        qs = urllib.parse.parse_qs(parsed.query)
        if "uddg" in qs and qs["uddg"]:
            return qs["uddg"][0]
    except Exception:
        pass
    return href


def _favicon_for_url(url: str) -> str:
    """Return a stable favicon URL for the destination domain."""
    try:
        host = urllib.parse.urlparse(url).netloc
        if host:
            return f"https://www.google.com/s2/favicons?domain={host}&sz=128"
    except Exception:
        pass
    # 1x1 transparent gif fallback
    return "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="


def _search_duckduckgo(query: str, per_page: int) -> List[Dict[str, Any]]:
    """Return a list of search result dictionaries from DuckDuckGo HTML.

    This helper sends a GET request to the DuckDuckGo HTML endpoint and
    extracts up to ``per_page`` results from the page.  Each result
    contains the destination URL, title, a favicon URL and the domain (used
    as the photographer label in the UI).  If the request fails or no
    results are found, an empty list is returned.
    """
    params = {"q": query}
    try:
        resp = requests.get(
            DUCKDUCKGO_URL,
            params=params,
            headers=DEFAULT_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
    except Exception:
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    results: List[Dict[str, Any]] = []
    anchors = soup.select(".result__a")
    for idx, a in enumerate(anchors[: max(1, per_page)], start=1):
        title = a.get_text(strip=True)
        href = a.get("href") or ""
        dest = _resolve_ddg_href(href)
        domain = urllib.parse.urlparse(dest).netloc or "web"
        results.append({
            "id": idx,
            "title": title,
            "page_url": dest,
            "photographer": domain,
            "image_url": _favicon_for_url(dest),
        })
    return results


def _search_bing(query: str, per_page: int) -> List[Dict[str, Any]]:
    """Return a list of search result dictionaries from Bing search.

    Bing returns results in ``<li class="b_algo">`` elements.  This helper
    extracts up to ``per_page`` results from the search results page.  If
    the request fails or no results are found, an empty list is returned.
    """
    params = {"q": query}
    try:
        resp = requests.get(
            BING_SEARCH_URL,
            params=params,
            headers=DEFAULT_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
    except Exception:
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    results: List[Dict[str, Any]] = []
    for idx, li in enumerate(soup.find_all("li", class_="b_algo"), start=1):
        # Each result item typically contains an <h2><a href="...">Title</a></h2>
        h2 = li.find("h2")
        a = h2.find("a") if h2 else None
        if not a:
            continue
        title = a.get_text(strip=True)
        dest = a.get("href") or ""
        if not dest:
            continue
        domain = urllib.parse.urlparse(dest).netloc or "web"
        results.append({
            "id": idx,
            "title": title,
            "page_url": dest,
            "photographer": domain,
            "image_url": _favicon_for_url(dest),
        })
        if len(results) >= per_page:
            break
    return results


def _search_google(query: str, per_page: int) -> List[Dict[str, Any]]:
    """Return a list of search result dictionaries from Google search.

    Google search pages use a nested structure where each result is within
    a ``div.g`` container.  This parser attempts to extract the title and
    href from each result.  Parsing Google HTML is brittle and may break if
    Google changes its markup.  If no results are found or the request
    fails, an empty list is returned.
    """
    params = {"q": query, "num": max(1, per_page)}
    try:
        resp = requests.get(
            GOOGLE_SEARCH_URL,
            params=params,
            headers=DEFAULT_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
    except Exception:
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    results: List[Dict[str, Any]] = []
    for idx, g in enumerate(soup.select("div.g"), start=1):
        # Look for the first anchor tag inside the result container
        a = g.find("a")
        if not a:
            continue
        dest = a.get("href") or ""
        title = a.get_text(strip=True) or dest
        if not dest:
            continue
        domain = urllib.parse.urlparse(dest).netloc or "web"
        results.append({
            "id": idx,
            "title": title,
            "page_url": dest,
            "photographer": domain,
            "image_url": _favicon_for_url(dest),
        })
        if len(results) >= per_page:
            break
    return results


def fetch_suggestions(
    query: str,
    _api_key: str | None = None,
    per_page: int = DEFAULT_COUNT,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Return "photo-like" suggestions for a query using a web search.

    The provider first attempts to query DuckDuckGo's HTML search.  If the
    request fails or yields no results, it falls back to Bing search, and
    finally to Google search.  The returned tuples follow the same
    structure as the Pexels and Pixabay providers so the existing front-end
    can render them.  Web search results are treated as ``photos`` (even
    though they are generic web pages) so that the UI can display them as
    thumbnail cards using the page favicon.  The second element of the
    returned tuple is always an empty list as there is no concept of
    videos when scraping generic search results.

    Args:
        query: The search query string.
        _api_key: Ignored; included for compatibility with other providers.
        per_page: Maximum number of results to return.

    Returns:
        A tuple ``(photos, videos)`` where ``photos`` is a list of dictionaries
        containing ``id``, ``title``, ``page_url``, ``photographer`` and
        ``image_url``.  ``videos`` is always an empty list.
    """
    query = (query or "").strip()
    if not query:
        return [], []
    # Try DuckDuckGo first
    results = _search_duckduckgo(query, per_page)
    print(f"Web search for '{query}' returned {len(results)} results from DuckDuckGo.")
    if not results:
        # Fall back to Bing
        results = _search_bing(query, per_page)
        print(f"Web search for '{query}' returned {len(results)} results from Bing.")
    if not results:
        # Fall back to Google
        results = _search_google(query, per_page)
        print(f"Web search for '{query}' returned {len(results)} results from Google.")
    return results, []


def main() -> None:
    query = input("Enter a search term: ").strip()
    if not query:
        print("No query provided. Exiting.")
        return

    try:
        photos, _videos = fetch_suggestions(query)
    except requests.HTTPError as exc:
        print(f"Error during web request: {exc}")
        return
    except Exception as exc:
        print(f"Unexpected error: {exc}")
        return

    if photos:
        print(f"\nTop {len(photos)} web results for '{query}':")
        for idx, item in enumerate(photos, start=1):
            print(f"{idx}. {item.get('title')}")
            print(f"   URL: {item.get('page_url')}")
    else:
        print("\nNo results found.")


if __name__ == "__main__":
    main()
