"""
suggester_using_by_pixabay_api.py
--------------------------------

This module implements a simple command‑line application that performs a
text search against the Pixabay API and returns a handful of royalty‑free
images and videos related to the query.  Pixabay offers separate REST
endpoints for images and videos: images are retrieved via
``https://pixabay.com/api/`` while videos are served from
``https://pixabay.com/api/videos/``【545351800694730†L143-L166】【545351800694730†L288-L331】.

The API requires a **key** query parameter on all requests; the
documentation explains that the ``key`` parameter must contain your
personal API token【545351800694730†L149-L154】.  Without a valid token, requests will
fail with an error.  Additional parameters include ``q`` for the
URL‑encoded search term and ``per_page`` to control the number of
results returned (between 3 and 200, defaulting to 20)【545351800694730†L190-L195】.  We
set ``per_page`` to 4 by default so that the application returns four
images and four videos per query.

To use this script you should first create a free Pixabay account and
retrieve an API key.  Store the key in the environment variable
``PIXABAY_API_KEY``.  Then run the script and enter a search term when
prompted.  The script will query both Pixabay endpoints and display
information about the first few hits.  For images we include the
photographer (``user``), a link to the Pixabay page and the medium
resolution image URL (``webformatURL``)【545351800694730†L203-L224】.  For videos we
select the ``medium`` or ``small`` MP4 stream when available; the
Pixabay API returns several versions of each video at different
resolutions【545351800694730†L346-L373】.

Note that the API terms require proper attribution and limit the
number of requests per minute; consult the official documentation for
details.
"""

import os
import sys
from typing import List, Tuple, Dict, Any
# Attempt to import load_dotenv.  If python-dotenv is not installed,
# define a dummy function to avoid ImportError.  Environment variables
# can still be read via os.environ when load_dotenv is absent.
try:
    from dotenv import load_dotenv  # type: ignore
except ImportError:
    def load_dotenv() -> None:  # type: ignore
        return None
import requests

# Number of results per media type.  Pixabay accepts between 3 and 200
# items per page【545351800694730†L190-L195】.
search_count: int = 4


class PixabayClient:
    """Minimal client for searching images and videos on Pixabay.

    The client encapsulates the Pixabay search endpoints and handles
    HTTP requests.  It expects an API key string that will be passed
    as the ``key`` query parameter on every request.  See the
    Pixabay API documentation for parameter descriptions and examples【545351800694730†L143-L166】【545351800694730†L288-L331】.
    """

    IMAGE_ENDPOINT = "https://pixabay.com/api/"
    VIDEO_ENDPOINT = "https://pixabay.com/api/videos/"

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("A valid Pixabay API key must be provided.")
        self.api_key = api_key

    def search_images(self, query: str, per_page: int = search_count) -> List[Dict[str, Any]]:
        """Search Pixabay for images matching the query.

        Args:
            query: The search term (URL encoded automatically by ``requests``).
            per_page: Number of results to return, between 3 and 200【545351800694730†L190-L195】.

        Returns:
            A list of image dictionaries containing id, user, page URL and
            a medium sized image URL.

        Raises:
            HTTPError: if the request fails.
        """
        params = {
            "key": self.api_key,
            "q": query,
            "per_page": per_page,
            "image_type": "photo",
        }
        response = requests.get(self.IMAGE_ENDPOINT, params=params)
        response.raise_for_status()
        data = response.json()
        images: List[Dict[str, Any]] = []
        for hit in data.get("hits", [])[:per_page]:
            images.append({
                "id": hit.get("id"),
                "photographer": hit.get("user"),
                "page_url": hit.get("pageURL"),
                # Pixabay provides several image sizes; webformatURL is a
                # medium sized variant (max dimension 640px)【545351800694730†L203-L224】.
                "image_url": hit.get("webformatURL"),
            })
        return images

    def search_videos(self, query: str, per_page: int = search_count) -> List[Dict[str, Any]]:
        """Search Pixabay for videos matching the query.

        Args:
            query: The search term.
            per_page: Number of results to return, between 3 and 200【545351800694730†L329-L331】.

        Returns:
            A list of video dictionaries containing id, user, page URL and
            a link to a medium or small MP4 file.

        Raises:
            HTTPError: if the request fails.
        """
        params = {
            "key": self.api_key,
            "q": query,
            "per_page": per_page,
        }
        response = requests.get(self.VIDEO_ENDPOINT, params=params)
        response.raise_for_status()
        data = response.json()
        videos: List[Dict[str, Any]] = []
        for hit in data.get("hits", [])[:per_page]:
            video_files = hit.get("videos", {})
            # Try to select a medium or small quality stream; these keys
            # correspond to 720p and 480p/tiny sizes respectively【545351800694730†L346-L373】.
            chosen_url = ""
            if video_files.get("medium") and video_files["medium"].get("url"):
                chosen_url = video_files["medium"]["url"]
            elif video_files.get("small") and video_files["small"].get("url"):
                chosen_url = video_files["small"]["url"]
            else:
                # Fall back to the first available stream if present
                for info in video_files.values():
                    if info.get("url"):
                        chosen_url = info["url"]
                        break
            videos.append({
                "id": hit.get("id"),
                "user": hit.get("user"),
                "page_url": hit.get("pageURL"),
                "video_url": chosen_url,
            })
        return videos


def fetch_suggestions(query: str, api_key: str, per_page: int = search_count) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Return image and video suggestions for a query using the Pixabay API.

    Args:
        query: Text describing the desired subject.
        api_key: Pixabay API key used for authorization.
        per_page: Number of suggestions to retrieve for images and videos.

    Returns:
        A tuple ``(images, videos)`` where each element is a list of dictionaries
        representing suggestions.  See ``PixabayClient`` methods for details.
    """
    client = PixabayClient(api_key)
    images = client.search_images(query, per_page)
    videos = client.search_videos(query, per_page)
    return images, videos


def main() -> None:
    """Entry point for the command‑line application.

    Prompts the user for a search query, retrieves suggestions from Pixabay,
    and prints formatted results to stdout.  If the ``PIXABAY_API_KEY``
    environment variable is missing, an error message is displayed.
    """
    load_dotenv()
    api_key = os.getenv("PIXABAY_API_KEY")
    if not api_key:
        print(
            "Error: PIXABAY_API_KEY environment variable not set.\n"
            "Obtain an API key from Pixabay and set it via\n"
            "    export PIXABAY_API_KEY=your_api_key\n"
            "Then rerun this script."
        )
        sys.exit(1)
    query = input("Enter a search term: ").strip()
    if not query:
        print("No query provided. Exiting.")
        return
    try:
        images, videos = fetch_suggestions(query, api_key)
    except requests.HTTPError as exc:
        print(f"Error during API request: {exc}")
        return
    # Display results
    if images:
        print(f"\nTop {len(images)} image suggestions for '{query}':")
        for idx, img in enumerate(images, start=1):
            print(f"{idx}. Photographer: {img['photographer']}")
            print(f"   Pixabay page: {img['page_url']}")
            print(f"   Image URL:   {img['image_url']}\n")
    else:
        print("\nNo images found for your query.")
    if videos:
        print(f"\nTop {len(videos)} video suggestions for '{query}':")
        for idx, vid in enumerate(videos, start=1):
            print(f"{idx}. Uploaded by: {vid['user']}")
            print(f"   Pixabay page: {vid['page_url']}")
            print(f"   Video URL:   {vid['video_url']}\n")
    else:
        print("\nNo videos found for your query.")


if __name__ == "__main__":
    main()