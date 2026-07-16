"""
suggester_using_by_web_search.py
--------------------------------

Görsel odaklı web araması yapar.

Önce Bing Görseller sonuç sayfasındaki kartlardan gerçek görsel/thumbnail
adreslerini çıkarır. Yeterli sonuç alınamazsa DuckDuckGo Görseller'e düşer.

Dönen veri mevcut sunucuyla uyumludur:
    (photos, videos)

Her photo kaydı:
    - page_url: görselin bulunduğu sayfa
    - image_url: arayüzde gösterilecek thumbnail
    - original_image_url: mümkünse orijinal görsel
    - photographer: kaynak alan adı
    - title: sonuç başlığı
"""

from __future__ import annotations

import html
import json
import re
import urllib.parse
from typing import Any, Dict, Iterable, List, Tuple

import requests
from bs4 import BeautifulSoup

from config import DEFAULT_RESULT_COUNT as DEFAULT_COUNT


BING_IMAGES_URL = "https://www.bing.com/images/search"
DUCKDUCKGO_HOME_URL = "https://duckduckgo.com/"
DUCKDUCKGO_IMAGES_URL = "https://duckduckgo.com/i.js"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}


def _is_http_url(value: str | None) -> bool:
    if not value:
        return False
    try:
        parsed = urllib.parse.urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


def _domain_for_url(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc.removeprefix("www.") or "web"
    except Exception:
        return "web"


def _clean_text(value: Any) -> str:
    return html.unescape(str(value or "")).strip()


def _make_result(
    *,
    title: str,
    page_url: str,
    image_url: str,
    original_image_url: str | None = None,
) -> Dict[str, Any] | None:
    if not _is_http_url(image_url):
        return None

    if not _is_http_url(page_url):
        page_url = original_image_url or image_url

    original = (
        original_image_url
        if _is_http_url(original_image_url)
        else image_url
    )

    return {
        "title": _clean_text(title) or "Web görseli",
        "page_url": page_url,
        "image_url": image_url,
        "original_image_url": original,
        "photographer": _domain_for_url(page_url),
    }


def _search_bing_images(
    query: str,
    result_limit: int,
) -> List[Dict[str, Any]]:
    """
    Bing Görseller sayfasındaki ``a.iusc`` kartlarını ayrıştırır.

    Kartların ``m`` niteliğinde JSON bulunur:
      - murl: orijinal görsel
      - turl: Bing thumbnail'i
      - purl: görselin bulunduğu sayfa
      - t: başlık
    """
    params = {
        "q": query,
        "first": 1,
        "count": max(20, result_limit),
        "adlt": "moderate",
    }

    try:
        response = requests.get(
            BING_IMAGES_URL,
            params=params,
            headers=DEFAULT_HEADERS,
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"[WEB/BING-IMAGES] İstek başarısız: {exc}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    results: List[Dict[str, Any]] = []

    for card in soup.select("a.iusc"):
        raw_metadata = card.get("m")
        if not raw_metadata:
            continue

        try:
            metadata = json.loads(raw_metadata)
        except (TypeError, json.JSONDecodeError):
            continue

        original_url = _clean_text(metadata.get("murl"))
        thumbnail_url = _clean_text(metadata.get("turl"))
        page_url = _clean_text(metadata.get("purl"))
        title = _clean_text(metadata.get("t"))

        # Thumbnail genellikle daha hızlı ve hotlink açısından daha güvenlidir.
        display_url = (
            thumbnail_url
            if _is_http_url(thumbnail_url)
            else original_url
        )

        item = _make_result(
            title=title,
            page_url=page_url,
            image_url=display_url,
            original_image_url=original_url,
        )
        if item:
            results.append(item)

        if len(results) >= result_limit:
            break

    return results


def _extract_ddg_vqd(page_text: str) -> str | None:
    """DuckDuckGo Görseller isteği için gereken geçici ``vqd`` değerini bulur."""
    patterns = (
        r'vqd=["\']([^"\']+)["\']',
        r'"vqd"\s*:\s*"([^"]+)"',
        r"vqd=([0-9-]+)",
    )
    for pattern in patterns:
        match = re.search(pattern, page_text)
        if match:
            return match.group(1)
    return None


def _search_duckduckgo_images(
    query: str,
    result_limit: int,
) -> List[Dict[str, Any]]:
    """DuckDuckGo Görseller JSON uç noktasından sonuç çıkarır."""
    try:
        token_response = requests.get(
            DUCKDUCKGO_HOME_URL,
            params={"q": query},
            headers=DEFAULT_HEADERS,
            timeout=15,
        )
        token_response.raise_for_status()
    except requests.RequestException as exc:
        print(f"[WEB/DDG-IMAGES] Token isteği başarısız: {exc}")
        return []

    vqd = _extract_ddg_vqd(token_response.text)
    if not vqd:
        print("[WEB/DDG-IMAGES] vqd değeri bulunamadı.")
        return []

    headers = {
        **DEFAULT_HEADERS,
        "Referer": token_response.url,
    }
    params = {
        "l": "wt-wt",
        "o": "json",
        "q": query,
        "vqd": vqd,
        "f": ",,,",
        "p": "1",
        "s": "0",
    }

    try:
        response = requests.get(
            DUCKDUCKGO_IMAGES_URL,
            params=params,
            headers=headers,
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        print(f"[WEB/DDG-IMAGES] Görsel isteği başarısız: {exc}")
        return []

    results: List[Dict[str, Any]] = []

    for raw_item in payload.get("results", []):
        original_url = _clean_text(raw_item.get("image"))
        thumbnail_url = _clean_text(raw_item.get("thumbnail"))
        page_url = _clean_text(raw_item.get("url"))
        title = _clean_text(raw_item.get("title"))

        display_url = (
            thumbnail_url
            if _is_http_url(thumbnail_url)
            else original_url
        )

        item = _make_result(
            title=title,
            page_url=page_url,
            image_url=display_url,
            original_image_url=original_url,
        )
        if item:
            results.append(item)

        if len(results) >= result_limit:
            break

    return results


def _query_terms(query: str) -> List[str]:
    return [
        term
        for term in re.findall(r"\w+", query.casefold(), flags=re.UNICODE)
        if len(term) > 1
    ]


def _relevance_score(item: Dict[str, Any], query: str) -> int:
    """
    Sonuçları başlık ve URL içinde sorgu ifadelerinin geçmesine göre sıralar.
    Bu yalnızca hafif bir iyileştirmedir; arama motorunun sırasını tamamen
    değiştirmez.
    """
    title = _clean_text(item.get("title")).casefold()
    page_url = _clean_text(item.get("page_url")).casefold()
    original_url = _clean_text(item.get("original_image_url")).casefold()
    haystack = f"{title} {page_url} {original_url}"

    normalized_query = " ".join(_query_terms(query))
    score = 0

    if normalized_query and normalized_query in haystack:
        score += 20

    for term in _query_terms(query):
        if term in title:
            score += 5
        if term in page_url:
            score += 2
        if term in original_url:
            score += 1

    return score


def _deduplicate(
    items: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    unique: List[Dict[str, Any]] = []
    seen: set[str] = set()

    for item in items:
        key = (
            _clean_text(item.get("original_image_url"))
            or _clean_text(item.get("image_url"))
        )
        if not key or key in seen:
            continue

        seen.add(key)
        unique.append(item)

    return unique


def fetch_suggestions(
    query: str,
    _api_key: str | None = None,
    per_page: int = DEFAULT_COUNT,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Web üzerinde görsel arar ve mevcut uygulamanın beklediği biçimde döndürür.
    """
    query = (query or "").strip()
    if not query:
        return [], []

    try:
        requested_count = max(1, int(per_page))
    except (TypeError, ValueError):
        requested_count = DEFAULT_COUNT

    # Sıralama ve eleme yapabilmek için ihtiyaçtan biraz fazla sonuç çek.
    candidate_limit = max(20, requested_count * 4)

    bing_results = _search_bing_images(query, candidate_limit)
    print(
        f"[WEB] Bing Görseller '{query}' için "
        f"{len(bing_results)} sonuç döndürdü."
    )

    all_results = list(bing_results)

    # Bing yeterli sonuç vermezse DuckDuckGo ile tamamla.
    if len(all_results) < requested_count:
        ddg_results = _search_duckduckgo_images(query, candidate_limit)
        print(
            f"[WEB] DuckDuckGo Görseller '{query}' için "
            f"{len(ddg_results)} sonuç döndürdü."
        )
        all_results.extend(ddg_results)

    unique_results = _deduplicate(all_results)

    # Python sort kararlıdır; eşit puanlarda arama motorunun özgün sırası korunur.
    unique_results.sort(
        key=lambda item: _relevance_score(item, query),
        reverse=True,
    )

    photos = unique_results[:requested_count]

    # Front-end için sıralı id ekle.
    for index, item in enumerate(photos, start=1):
        item["id"] = index

    return photos, []


def main() -> None:
    query = input("Arama metni: ").strip()
    if not query:
        print("Arama metni girilmedi.")
        return

    photos, _videos = fetch_suggestions(query)

    if not photos:
        print("Sonuç bulunamadı.")
        return

    for index, item in enumerate(photos, start=1):
        print(f"{index}. {item['title']}")
        print(f"   Sayfa: {item['page_url']}")
        print(f"   Görsel: {item['image_url']}")


if __name__ == "__main__":
    main()
