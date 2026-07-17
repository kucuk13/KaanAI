"""Pixabay görsel ve video önerileri.

Bu modül Pixabay ile ilgili bütün işlemleri içerir. ``app.py`` yalnızca
buradaki arayüz fonksiyonlarını çağırır:

- ``fetch_suggestions``: tekli arama için görsel ve videoyu birlikte döndürür.
- ``fetch_video_suggestions``: toplu arama için yalnızca video döndürür.
- ``fetch_image_suggestions``: yalnızca görsel gereken diğer kullanımlar içindir.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, List, Optional, Tuple

import requests

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args: Any, **kwargs: Any) -> None:
        return None

try:
    from config import DEFAULT_RESULT_COUNT
except ImportError:
    DEFAULT_RESULT_COUNT = 4


PIXABAY_IMAGE_ENDPOINT = "https://pixabay.com/api/"
PIXABAY_VIDEO_ENDPOINT = "https://pixabay.com/api/videos/"
PIXABAY_MIN_PER_PAGE = 3
PIXABAY_MAX_PER_PAGE = 200
PIXABAY_QUERY_MAX_LENGTH = 100
PIXABAY_TIMEOUT_SECONDS = 30


def _requested_count(value: Any) -> int:
    """Kullanıcının istediği sonuç sayısını güvenli bir tam sayıya çevirir."""

    try:
        count = int(value)
    except (TypeError, ValueError):
        count = int(DEFAULT_RESULT_COUNT)

    return max(1, min(PIXABAY_MAX_PER_PAGE, count))


def _api_count(requested_count: int) -> int:
    """Pixabay'ın kabul ettiği 3-200 aralığındaki ``per_page`` değerini üretir."""

    return max(PIXABAY_MIN_PER_PAGE, min(PIXABAY_MAX_PER_PAGE, requested_count))


def _normalized_query(query: Any) -> str:
    return str(query or "").strip()[:PIXABAY_QUERY_MAX_LENGTH]


class PixabayClient:
    """Pixabay görsel ve video API istemcisi."""

    def __init__(
        self,
        api_key: str,
        timeout: int = PIXABAY_TIMEOUT_SECONDS,
        session: Optional[requests.Session] = None,
    ) -> None:
        normalized_key = str(api_key or "").strip()
        if not normalized_key:
            raise ValueError(
                "PIXABAY_API_KEY ayarlı değil. Anahtarı .env dosyasına ekleyin."
            )

        self.api_key = normalized_key
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "VideoSuggestionApp/1.0",
            }
        )

    def _get_json(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Pixabay isteğini yapar ve API anahtarını hata mesajından gizler."""

        safe_params = {"key": self.api_key, **params}

        try:
            response = self.session.get(
                endpoint,
                params=safe_params,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.Timeout as exception:
            raise RuntimeError("Pixabay API isteği zaman aşımına uğradı.") from exception
        except requests.ConnectionError as exception:
            raise RuntimeError(
                "Pixabay API bağlantısı kurulamadı."
            ) from exception
        except requests.HTTPError as exception:
            status_code = getattr(exception.response, "status_code", "?")
            detail = ""

            if exception.response is not None:
                try:
                    payload = exception.response.json()
                    if isinstance(payload, dict):
                        detail = str(
                            payload.get("message")
                            or payload.get("error")
                            or ""
                        ).strip()
                except (ValueError, TypeError):
                    detail = ""

            message = f"Pixabay API hatası (HTTP {status_code})"
            if detail:
                message += f": {detail[:300]}"
            raise RuntimeError(message) from None
        except requests.RequestException as exception:
            raise RuntimeError(f"Pixabay isteği başarısız: {exception}") from exception

        try:
            payload = response.json()
        except ValueError as exception:
            raise RuntimeError(
                "Pixabay API geçerli bir JSON yanıtı döndürmedi."
            ) from exception

        if not isinstance(payload, dict):
            raise RuntimeError("Pixabay API beklenmeyen bir yanıt döndürdü.")

        return payload

    def search_images(
        self,
        query: str,
        per_page: int = DEFAULT_RESULT_COUNT,
    ) -> List[Dict[str, Any]]:
        """Tekli arama için Pixabay görsellerini döndürür."""

        normalized_query = _normalized_query(query)
        if not normalized_query:
            return []

        requested_count = _requested_count(per_page)
        payload = self._get_json(
            PIXABAY_IMAGE_ENDPOINT,
            {
                "q": normalized_query,
                "lang": "tr",
                "image_type": "photo",
                "safesearch": "true",
                "per_page": _api_count(requested_count),
            },
        )

        hits = payload.get("hits")
        if not isinstance(hits, list):
            return []

        images: List[Dict[str, Any]] = []
        for hit in hits:
            if not isinstance(hit, dict):
                continue

            image_url = (
                hit.get("largeImageURL")
                or hit.get("webformatURL")
                or hit.get("previewURL")
            )
            if not image_url:
                continue

            images.append(
                {
                    "id": hit.get("id"),
                    "photographer": hit.get("user"),
                    "author": hit.get("user"),
                    "page_url": hit.get("pageURL"),
                    "source_url": hit.get("pageURL"),
                    "image_url": image_url,
                    "width": hit.get("imageWidth"),
                    "height": hit.get("imageHeight"),
                    "tags": hit.get("tags"),
                    "source": "Pixabay",
                }
            )

            if len(images) >= requested_count:
                break

        return images

    @staticmethod
    def _select_video_stream(streams: Any) -> Optional[Dict[str, Any]]:
        if not isinstance(streams, dict):
            return None

        for quality in ("medium", "small", "large", "tiny"):
            stream = streams.get(quality)
            if isinstance(stream, dict) and stream.get("url"):
                return stream

        return None

    def search_videos(
        self,
        query: str,
        per_page: int = DEFAULT_RESULT_COUNT,
    ) -> List[Dict[str, Any]]:
        """Toplu arama için Pixabay videolarını döndürür."""

        normalized_query = _normalized_query(query)
        if not normalized_query:
            return []

        requested_count = _requested_count(per_page)
        payload = self._get_json(
            PIXABAY_VIDEO_ENDPOINT,
            {
                "q": normalized_query,
                "lang": "tr",
                "video_type": "all",
                "safesearch": "true",
                "per_page": _api_count(requested_count),
            },
        )

        hits = payload.get("hits")
        if not isinstance(hits, list):
            return []

        videos: List[Dict[str, Any]] = []
        for hit in hits:
            if not isinstance(hit, dict):
                continue

            stream = self._select_video_stream(hit.get("videos"))
            if not stream:
                continue

            videos.append(
                {
                    "id": hit.get("id"),
                    "user": hit.get("user"),
                    "author": hit.get("user"),
                    "creator": hit.get("user"),
                    "page_url": hit.get("pageURL"),
                    "source_url": hit.get("pageURL"),
                    "video_url": stream.get("url"),
                    "poster_url": stream.get("thumbnail"),
                    "duration": hit.get("duration"),
                    "width": stream.get("width"),
                    "height": stream.get("height"),
                    "tags": hit.get("tags"),
                    "source": "Pixabay",
                }
            )

            if len(videos) >= requested_count:
                break

        return videos


def fetch_image_suggestions(
    query: str,
    api_key: str,
    per_page: int = DEFAULT_RESULT_COUNT,
) -> Dict[str, List[Dict[str, Any]]]:
    """Tekli Pixabay araması: yalnızca görsel sonuçları."""

    client = PixabayClient(api_key)
    return {
        "photos": client.search_images(query, per_page),
        "videos": [],
    }


def fetch_video_suggestions(
    query: str,
    api_key: str,
    per_page: int = DEFAULT_RESULT_COUNT,
) -> Dict[str, List[Dict[str, Any]]]:
    """Toplu Pixabay araması: yalnızca video sonuçları."""

    client = PixabayClient(api_key)
    return {
        "photos": [],
        "videos": client.search_videos(query, per_page),
    }


def fetch_suggestions(
    query: str,
    api_key: str,
    per_page: int = DEFAULT_RESULT_COUNT,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Tekli Pixabay araması için görsel ve videoyu birlikte döndürür."""

    client = PixabayClient(api_key)
    return (
        client.search_images(query, per_page),
        client.search_videos(query, per_page),
    )


def main() -> None:
    load_dotenv()
    api_key = os.getenv("PIXABAY_API_KEY", "").strip()
    if not api_key:
        print("PIXABAY_API_KEY ayarlı değil.")
        sys.exit(1)

    query = input("Arama metni: ").strip()
    if not query:
        print("Arama metni boş olamaz.")
        return

    try:
        photos, videos = fetch_suggestions(query, api_key)
    except RuntimeError as exception:
        print(f"Hata: {exception}")
        return

    print(f"{len(photos)} görsel, {len(videos)} video bulundu.")


if __name__ == "__main__":
    main()
