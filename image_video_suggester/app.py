"""
A simple HTTP server exposing the `suggester_using_by_pexels_api` functionality.

This server is intended for local use. It listens on `localhost:8000` and
provides a single endpoint `/search` that accepts a `query` parameter via the
query string. When a GET request is made to `/search?query=...`, the server
retrieves photo and video suggestions from the Pexels API using the
`fetch_suggestions` function and returns the results as JSON.  To authorize
requests to Pexels, set your API key in the environment variable
`PEXELS_API_KEY` before starting the server.  Without a valid key, the server
will respond with an error message.

This implementation uses only Python's standard library (http.server and
urllib.parse) so no external dependencies are required.  CORS headers are
added to allow the HTML page to request data from this server when opened
locally.

Usage::

    export PEXELS_API_KEY=your_api_key
    python3 api_server.py

After starting the server, open `index.html` in your browser and enter a
search term.  The page will call this server, which will in turn call the
Pexels API and return three photos and three videos.
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
# Attempt to import dotenv.  If unavailable, define a no‑op replacement.  This
# allows the server to run without requiring the external package.
try:
    from dotenv import load_dotenv  # type: ignore
except ImportError:
    def load_dotenv() -> None:  # type: ignore
        return None
import json
import os
import sys

from suggester_using_by_pexels_api import fetch_suggestions as fetch_from_pexels
from suggester_using_by_web_search import fetch_suggestions as fetch_from_web
from suggester_using_by_ai_robot_generator import fetch_suggestions as fetch_from_ai_robot_generator
# Import the Pixabay suggester.  This allows serving results from a
# different provider without changing the front‑end logic.
try:
    from suggester_using_by_pixabay_api import fetch_suggestions as fetch_from_pixabay
except ImportError:
    # If the Pixabay module is missing for any reason, define a placeholder
    fetch_from_pixabay = None  # type: ignore

APPLICATION_JSON_HEADER = "application/json"


class PexelsRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the Pexels suggestion service."""
    load_dotenv()

    def do_OPTIONS(self) -> None:
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        """Handle GET requests.  Only the /search endpoint is supported."""
        parsed = urlparse(self.path)
        if parsed.path not in {"/searchByPexels", "/searchByPixabay", "/searchByWeb", "/createRobot"}:
            self.send_response(404)
            self.send_header("Content-Type", APPLICATION_JSON_HEADER)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode())
            return
        query_params = parse_qs(parsed.query)
        search_query_list = query_params.get("query", [])
        if not search_query_list:
            self.send_response(400)
            self.send_header("Content-Type", APPLICATION_JSON_HEADER)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Missing query parameter"}).encode())
            return
        search_query = search_query_list[0].strip()
        if not search_query:
            self.send_response(400)
            self.send_header("Content-Type", APPLICATION_JSON_HEADER)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Empty query parameter"}).encode())
            return
        # Choose the provider based on the request path
        if parsed.path == "/searchByPexels":
            provider_name = "PEXELS"
            api_key = os.environ.get("PEXELS_API_KEY")
            fetch_fn = fetch_from_pexels
        elif parsed.path == "/searchByWeb":
            fetch_fn = fetch_from_web
            api_key = "NO_KEY"
        elif parsed.path == "/createRobot":
            fetch_fn = fetch_from_ai_robot_generator
            api_key = "NO_KEY"
        else:
            provider_name = "PIXABAY"
            api_key = os.environ.get("PIXABAY_API_KEY")
            fetch_fn = fetch_from_pixabay
        if not api_key:
            self.send_response(500)
            self.send_header("Content-Type", APPLICATION_JSON_HEADER)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": f"{provider_name}_API_KEY environment variable not set"
            }).encode())
            return
        if fetch_fn is None:
            self.send_response(500)
            self.send_header("Content-Type", APPLICATION_JSON_HEADER)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": "Pixabay functionality is unavailable"
            }).encode())
            return
        try:
            photos, videos = fetch_fn(search_query, api_key)
        except Exception as exc:
            # Catch any error from the API request
            self.send_response(500)
            self.send_header("Content-Type", APPLICATION_JSON_HEADER)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(exc)}).encode())
            return
        result = {
            "photos": photos,
            "videos": videos
        }
        self.send_response(200)
        self.send_header("Content-Type", APPLICATION_JSON_HEADER)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())


def run_server(host: str = "localhost", port: int = 8000) -> None:
    """Run the HTTP server until interrupted."""
    server = HTTPServer((host, port), PexelsRequestHandler)
    print(f"Pexels suggestion server running at http://{host}:{port}/")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        server.server_close()


if __name__ == "__main__":
    # Optionally allow host/port to be specified via command-line arguments
    host = "localhost"
    port = 8000
    if len(sys.argv) >= 2:
        host = sys.argv[1]
    if len(sys.argv) >= 3:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print(f"Invalid port number: {sys.argv[2]}")
            sys.exit(1)
    run_server(host, port)