"""
config.py
---------

Shared configuration for the image/video suggester provider modules
(Pexels, Pixabay, web search, AI robot generator).

Each provider previously hard‑coded its own "how many results per query"
constant (``AI_IMAGE_COUNT``, ``search_count``, ``DEFAULT_COUNT``, ...).
That value is now defined in a single place here and can be overridden
without touching any provider code by setting the ``SUGGESTION_RESULT_COUNT``
environment variable (e.g. in the project's ``.env`` file).
"""

from __future__ import annotations

import os

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> None:
        pass

load_dotenv()

_DEFAULT_RESULT_COUNT = 4


def _read_result_count() -> int:
    raw_value = os.getenv("SUGGESTION_RESULT_COUNT")
    if not raw_value:
        return _DEFAULT_RESULT_COUNT
    try:
        value = int(raw_value)
    except ValueError:
        return _DEFAULT_RESULT_COUNT
    return value if value > 0 else _DEFAULT_RESULT_COUNT


# Number of results each provider returns per query. Override via the
# SUGGESTION_RESULT_COUNT environment variable, or per-request from the UI
# (see app.py's "count" query parameter).
DEFAULT_RESULT_COUNT: int = _read_result_count()

# Bounds enforced by app.py when a "count" value is supplied by the client.
MIN_RESULT_COUNT: int = 1
MAX_RESULT_COUNT: int = 50
