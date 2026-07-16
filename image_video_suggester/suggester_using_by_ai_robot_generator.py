"""
suggester_using_by_ai_generator.py
----------------------------------

This module provides a simple wrapper for generating AI-like image suggestions
without requiring any API keys or external dependencies.  Instead of using
commercial text‑to‑image services (which typically require authentication or
payment), it leverages the RoboHash service to produce deterministic,
robot‑style illustrations based on the input prompt.  Each unique query
generates a distinctive robot image, and by appending different suffixes to
the prompt, multiple variations can be produced.  RoboHash is publicly
accessible and does not require an API key, making it suitable as a fallback
for demonstration or educational purposes.

The ``fetch_suggestions`` function below returns a tuple of lists mimicking
the interface of the other suggestion providers.  Only ``photos`` are
returned because RoboHash produces static PNG images; the ``videos`` list
remains empty.  Each photo dictionary contains an ``id`` (sequential
integer), a fixed ``photographer`` label ("AI Generator"), a ``page_url``
pointing back to the RoboHash website for attribution, and the direct
``image_url`` for embedding in the UI.

Note: While RoboHash images are generated algorithmically, they are not
traditional text‑to‑image artworks.  They serve as a lightweight, free
example of AI‑generated content without external dependencies.
"""

from __future__ import annotations

import urllib.parse
from typing import Any, Dict, List, Tuple

from config import DEFAULT_RESULT_COUNT as AI_IMAGE_COUNT


def _robohash_url(prompt: str, variant: int) -> str:
    """Return a RoboHash URL for the given prompt and variant.

    Args:
        prompt: The base text to incorporate into the image seed.  Spaces and
            special characters are percent‑encoded for safe inclusion in a URL.
        variant: A unique integer appended to the prompt to generate distinct
            images for the same query.

    Returns:
        A URL that points to a PNG image hosted on RoboHash.
    """
    # Combine the prompt and variant to form a unique seed.  Variants help
    # ensure multiple images differ from each other even when the prompt is
    # identical.
    seed = f"{prompt}{variant}"
    # Percent‑encode the seed to ensure it is safe to embed in the path
    encoded_seed = urllib.parse.quote(seed, safe="")
    # Use the PNG endpoint with a fixed size; RoboHash supports parameters
    # like ``size`` and ``set`` to tweak the output style.  Here we choose
    # set=1 (classic robots) and a 512x512 image for a good balance between
    # quality and bandwidth.
    return f"https://robohash.org/{encoded_seed}.png?set=set1&size=512x512"


def fetch_suggestions(query: str, _api_key: str | None = None, per_page: int = AI_IMAGE_COUNT) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Generate AI‑like image suggestions based on a text query.

    This function returns a tuple of ``(photos, videos)`` similar to other
    providers.  For each of the ``per_page`` requested images, it constructs
    a RoboHash URL by combining the query with a variant index.  The
    resulting list of photo dictionaries can be consumed directly by the
    front‑end without any additional processing.

    Args:
        query: Text describing the desired subject.  This is used as the
            base seed for RoboHash to produce deterministic images.
        _api_key: Ignored; present to maintain a consistent signature with
            other provider functions.  No API key is required for RoboHash.
        per_page: Number of images to return.  Defaults to ``AI_IMAGE_COUNT``.

    Returns:
        A tuple where the first element is a list of photo dictionaries and
        the second element is always an empty list (since videos are not
        supported).
    """
    query = (query or "").strip()
    if not query:
        return [], []
    photos: List[Dict[str, Any]] = []
    # Generate ``per_page`` unique images by varying the seed
    for idx in range(1, per_page + 1):
        image_url = _robohash_url(query, idx)
        photos.append({
            "id": idx,
            "photographer": "AI Generator",
            "page_url": "https://robohash.org/",
            "image_url": image_url,
        })
    return photos, []


def main() -> None:
    """Simple CLI for ad‑hoc testing of the AI image generator."""
    query = input("Enter a search term: ").strip()
    if not query:
        print("No query provided. Exiting.")
        return
    photos, _videos = fetch_suggestions(query)
    print(f"Generated {len(photos)} AI images for '{query}':")
    for idx, photo in enumerate(photos, start=1):
        print(f"{idx}. URL: {photo['image_url']}")


if __name__ == "__main__":
    main()