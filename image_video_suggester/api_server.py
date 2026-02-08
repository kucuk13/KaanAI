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
from dotenv import load_dotenv
import json
import os
import sys

from suggester_using_by_pexels_api import fetch_suggestions

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
        if parsed.path != "/search":
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
        api_key = os.environ.get("PEXELS_API_KEY")
        if not api_key:
            self.send_response(500)
            self.send_header("Content-Type", APPLICATION_JSON_HEADER)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": "PEXELS_API_KEY environment variable not set"
            }).encode())
            return
        try:
            photos, videos = fetch_suggestions(search_query, api_key)
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