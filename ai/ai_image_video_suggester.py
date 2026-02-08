"""
ai_image_video_suggester.py
----------------------------------

This script implements a simple command‑line application that takes a text query
from the user and returns three image and three video suggestions related to
that query using the Pexels API.  Pexels provides a RESTful interface to
search its library of royalty‑free photos and videos; each request requires
an API key passed in the ``Authorization`` header【898083509155206†L130-L147】.

Usage
~~~~~
1. Obtain a free API key by creating an account on Pexels.  According to the
   Pexels API documentation, any user with a Pexels account can request an
   API key and immediately receive it【898083509155206†L130-L147】.  The key
   authenticates requests by including it in the ``Authorization`` header when
   calling Pexels endpoints【898083509155206†L130-L147】.
2. Set the environment variable ``PEXELS_API_KEY`` to your API key.  This
   script reads the key from that variable to avoid hard‑coding secrets.
3. Run the script and enter a search term when prompted.  The script
   queries the photo search endpoint ``https://api.pexels.com/v1/search``
   and the video search endpoint ``https://api.pexels.com/videos/search`` with
   the given query and a ``per_page`` parameter of 3.  The Pexels API
   documentation notes that the search endpoints accept a ``query`` string
   (e.g. "Nature") and an optional ``per_page`` parameter to limit results【898083509155206†L385-L427】【898083509155206†L1111-L1148】.
4. The script prints the photographer or author, the page URL on Pexels and
   a direct link to the medium‑sized image for photos, and prints the user,
   page URL and a link to an MP4 file for videos.  Only the first three
   results are displayed.

The purpose of this tool is to illustrate how to build a lightweight AI
application that connects a natural language query to external multimedia
content on the internet.  Because Pexels enforces strict attribution and
rate limits, remember to credit photographers and abide by their API terms
when integrating this script into a larger application.
"""

import os
import sys
from typing import List, Tuple, Dict, Any
from dotenv import load_dotenv

import requests


class PexelsClient:
    """Minimal client for searching photos and videos on Pexels.

    The client wraps the Pexels photo and video search endpoints.  It uses a
    user‑supplied API key for authorization, sends HTTP requests via the
    ``requests`` library and returns parsed JSON dictionaries.  See the
    "Search for Photos" and "Search for Videos" sections of the Pexels API
    documentation for parameter descriptions【898083509155206†L385-L427】【898083509155206†L1111-L1148】.
    """

    PHOTO_ENDPOINT = "https://api.pexels.com/v1/search"
    VIDEO_ENDPOINT = "https://api.pexels.com/videos/search"

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("A valid Pexels API key must be provided.")
        self.headers = {"Authorization": api_key}

    def search_photos(self, query: str, per_page: int = 3) -> List[Dict[str, Any]]:
        """Search Pexels for photos matching the query.

        Args:
            query: The search query string.  According to the API docs the
                ``query`` parameter can be broad (e.g. ``Nature``) or specific
                (e.g. ``Group of people working")【898083509155206†L385-L390】.
            per_page: Number of results to return (max 80【898083509155206†L425-L428】).

        Returns:
            A list of photo dictionaries extracted from the API response.  Each
            dictionary contains the Pexels photo ID, photographer name, the
            Pexels page URL and a medium sized image URL.

        Raises:
            HTTPError: if the request fails.
        """
        params = {"query": query, "per_page": per_page}
        response = requests.get(self.PHOTO_ENDPOINT, headers=self.headers, params=params)
        response.raise_for_status()
        data = response.json()
        photos = []
        for photo in data.get("photos", [])[:per_page]:
            # Extract relevant fields: id, photographer, url and medium image link
            photos.append({
                "id": photo.get("id"),
                "photographer": photo.get("photographer"),
                "page_url": photo.get("url"),
                # Use the medium size for a reasonable balance of quality and bandwidth
                "image_url": photo.get("src", {}).get("medium"),
            })
        return photos

    def search_videos(self, query: str, per_page: int = 3) -> List[Dict[str, Any]]:
        """Search Pexels for videos matching the query.

        Args:
            query: The search query string.
            per_page: Number of results to return (max 80【898083509155206†L1145-L1148】).

        Returns:
            A list of video dictionaries extracted from the API response.  Each
            dictionary contains the Pexels video ID, user name, the Pexels page
            URL and a link to a video file.  The script chooses a medium or
            small MP4 file when available, falling back to the first available
            video file.

        Raises:
            HTTPError: if the request fails.
        """
        params = {"query": query, "per_page": per_page}
        response = requests.get(self.VIDEO_ENDPOINT, headers=self.headers, params=params)
        response.raise_for_status()
        data = response.json()
        videos = []
        for video in data.get("videos", [])[:per_page]:
            video_file_link: str = ""
            # Each video contains a list of video_files with quality and file_type
            files = video.get("video_files", [])
            # Try to choose a medium or small MP4 file for a good compromise
            preferred_qualities = ["sd", "hd"]
            for quality in preferred_qualities:
                match = next((f for f in files
                               if f.get("quality") == quality and f.get("file_type", "").lower().startswith("video/mp4")), None)
                if match:
                    video_file_link = match.get("link")
                    break
            if not video_file_link and files:
                # Fall back to the first available file
                video_file_link = files[0].get("link")
            videos.append({
                "id": video.get("id"),
                "user": video.get("user", {}).get("name"),
                "page_url": video.get("url"),
                "video_url": video_file_link,
            })
        return videos


def fetch_suggestions(query: str, api_key: str, per_page: int = 3) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Return photo and video suggestions for a query using the Pexels API.

    Args:
        query: Text describing the desired subject.
        api_key: Pexels API key used for authorization.
        per_page: Number of suggestions to retrieve for photos and videos.

    Returns:
        A tuple ``(photos, videos)`` where each element is a list of dictionaries
        representing suggestions.  See ``PexelsClient`` methods for details.
    """
    client = PexelsClient(api_key)
    photos = client.search_photos(query, per_page)
    videos = client.search_videos(query, per_page)
    return photos, videos


def main() -> None:
    """Entry point for the command‑line application.

    Prompts the user for a search query, retrieves suggestions from Pexels, and
    prints formatted results to stdout.  If the ``PEXELS_API_KEY`` environment
    variable is missing, an error message is displayed.
    """
    load_dotenv()
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        print(
            "Error: PEXELS_API_KEY environment variable not set.\n"
            "Obtain an API key from Pexels and set it via\n"
            "    export PEXELS_API_KEY=your_api_key\n"
            "Then rerun this script."
        )
        sys.exit(1)

    query = input("Enter a search term: ").strip()
    if not query:
        print("No query provided. Exiting.")
        return

    try:
        photos, videos = fetch_suggestions(query, api_key)
    except requests.HTTPError as exc:
        print(f"Error during API request: {exc}")
        return

    # Display results
    if photos:
        print(f"\nTop {len(photos)} photo suggestions for '{query}':")
        for idx, photo in enumerate(photos, start=1):
            print(f"{idx}. Photographer: {photo['photographer']}")
            print(f"   Pexels page: {photo['page_url']}")
            print(f"   Image URL:   {photo['image_url']}\n")
    else:
        print("\nNo photos found for your query.")

    if videos:
        print(f"\nTop {len(videos)} video suggestions for '{query}':")
        for idx, video in enumerate(videos, start=1):
            print(f"{idx}. Uploaded by: {video['user']}")
            print(f"   Pexels page: {video['page_url']}")
            print(f"   Video URL:   {video['video_url']}\n")
    else:
        print("\nNo videos found for your query.")


if __name__ == "__main__":
    main()