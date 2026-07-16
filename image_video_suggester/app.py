from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from pathlib import Path

import inspect
import json
import os
import sys
import traceback


# .env desteği isteğe bağlıdır.
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> None:
        pass


load_dotenv()


# Pexels
try:
    from suggester_using_by_pexels_api import (
        fetch_suggestions as fetch_from_pexels
    )
except ImportError:
    fetch_from_pexels = None


# Pixabay
try:
    from suggester_using_by_pixabay_api import (
        fetch_suggestions as fetch_from_pixabay
    )
except ImportError:
    fetch_from_pixabay = None


# Web arama
try:
    from suggester_using_by_web_search import (
        fetch_suggestions as fetch_from_web
    )
except ImportError:
    fetch_from_web = None


# Yapay zekâ robot oluşturucu
try:
    from suggester_using_by_ai_robot_generator import (
        fetch_suggestions as fetch_from_ai_robot_generator
    )
except ImportError:
    fetch_from_ai_robot_generator = None


BASE_DIR = Path(__file__).resolve().parent

APPLICATION_JSON_HEADER = "application/json; charset=utf-8"


def make_json_safe(value):
    """
    JSON'a doğrudan dönüştürülemeyen değerleri güvenli hâle getirir.
    """

    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return value.hex()

    if isinstance(value, dict):
        return {
            str(key): make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            make_json_safe(item)
            for item in value
        ]

    if hasattr(value, "to_dict") and callable(value.to_dict):
        try:
            return make_json_safe(value.to_dict())
        except Exception:
            pass

    if hasattr(value, "__dict__"):
        try:
            return make_json_safe(vars(value))
        except Exception:
            pass

    return str(value)


def call_fetch_function(fetch_function, query, api_key=None):
    """
    fetch_suggestions fonksiyonunun bir veya iki parametre almasını destekler.

    Desteklenen örnekler:

        fetch_suggestions(query)

        fetch_suggestions(query, api_key)
    """

    if fetch_function is None:
        raise RuntimeError("İlgili sağlayıcının Python modülü yüklenemedi.")

    try:
        signature = inspect.signature(fetch_function)

        positional_parameters = [
            parameter
            for parameter in signature.parameters.values()
            if parameter.kind in {
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD
            }
        ]

        accepts_varargs = any(
            parameter.kind == inspect.Parameter.VAR_POSITIONAL
            for parameter in signature.parameters.values()
        )

        if accepts_varargs or len(positional_parameters) >= 2:
            return fetch_function(query, api_key)

        return fetch_function(query)

    except ValueError:
        # Bazı fonksiyonlarda signature okunamayabilir.
        return fetch_function(query, api_key)


def normalize_fetch_result(raw_result):
    """
    Sağlayıcılardan gelen farklı sonuç biçimlerini şu biçime dönüştürür:

        {
            "photos": [],
            "videos": []
        }
    """

    photos = []
    videos = []

    # Sağlayıcı zaten sözlük döndürüyorsa
    if isinstance(raw_result, dict):
        photos = raw_result.get("photos") or []
        videos = raw_result.get("videos") or []

    # Genellikle kullanılan biçim: (photos, videos)
    elif isinstance(raw_result, tuple) and len(raw_result) == 2:
        photos, videos = raw_result

    # [photos, videos] biçimi
    elif (
        isinstance(raw_result, list)
        and len(raw_result) == 2
        and isinstance(raw_result[0], list)
        and isinstance(raw_result[1], list)
    ):
        photos, videos = raw_result

    # Yalnızca fotoğraf listesi dönüyorsa
    elif isinstance(raw_result, list):
        photos = raw_result

    # Tek bir resim URL'si dönüyorsa
    elif isinstance(raw_result, str):
        photos = [
            {
                "image_url": raw_result
            }
        ]

    elif raw_result is None:
        photos = []
        videos = []

    else:
        raise TypeError(
            "fetch_suggestions desteklenmeyen bir veri biçimi döndürdü: "
            f"{type(raw_result).__name__}"
        )

    if photos is None:
        photos = []

    if videos is None:
        videos = []

    if not isinstance(photos, list):
        photos = [photos]

    if not isinstance(videos, list):
        videos = [videos]

    return {
        "photos": make_json_safe(photos),
        "videos": make_json_safe(videos)
    }


class SuggestionRequestHandler(BaseHTTPRequestHandler):
    """Fotoğraf ve video öneri HTTP sunucusu."""

    def log_message(self, format_string, *args):
        """
        Terminalde istekleri daha okunabilir gösterir.
        """

        print(
            f"[HTTP] {self.client_address[0]} "
            f"- {format_string % args}"
        )

    def send_json(self, status_code, payload):
        """
        Güvenli şekilde JSON yanıtı gönderir.
        """

        safe_payload = make_json_safe(payload)

        response_body = json.dumps(
            safe_payload,
            ensure_ascii=False,
            default=str
        ).encode("utf-8")

        self.send_response(status_code)
        self.send_header("Content-Type", APPLICATION_JSON_HEADER)
        self.send_header("Content-Length", str(len(response_body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, OPTIONS"
        )
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, Accept"
        )
        self.end_headers()

        self.wfile.write(response_body)

    def send_html_file(self, file_path):
        """
        HTML dosyasını tarayıcıya gönderir.
        """

        if not file_path.exists():
            self.send_json(
                404,
                {
                    "error": f"{file_path.name} bulunamadı."
                }
            )
            return

        content = file_path.read_bytes()

        self.send_response(200)
        self.send_header(
            "Content-Type",
            "text/html; charset=utf-8"
        )
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        self.wfile.write(content)

    def do_OPTIONS(self):
        """CORS preflight isteğini karşılar."""

        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, OPTIONS"
        )
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, Accept"
        )
        self.end_headers()

    def do_GET(self):
        """
        GET isteklerini işler.

        Tüm beklenmeyen hatalar burada yakalanır. Böylece tarayıcı
        ERR_EMPTY_RESPONSE yerine gerçek hata mesajını görür.
        """

        try:
            self.handle_get_request()

        except BrokenPipeError:
            print(
                "[UYARI] Tarayıcı yanıt tamamlanmadan bağlantıyı kapattı."
            )

        except ConnectionResetError:
            print(
                "[UYARI] İstemci bağlantıyı sıfırladı."
            )

        except Exception as exception:
            print("\n" + "=" * 70)
            print("BEKLENMEYEN SUNUCU HATASI")
            print("=" * 70)

            traceback.print_exc()

            print("=" * 70 + "\n")

            try:
                self.send_json(
                    500,
                    {
                        "error": str(exception),
                        "error_type": type(exception).__name__
                    }
                )
            except Exception:
                traceback.print_exc()

    def handle_get_request(self):
        """Asıl GET yönlendirmelerini gerçekleştirir."""

        parsed_url = urlparse(self.path)
        request_path = parsed_url.path

        # Ana sayfa
        if request_path in {"/", "/index.html"}:
            self.send_html_file(BASE_DIR / "index.html")
            return

        # Tarayıcının otomatik favicon isteği
        if request_path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return

        allowed_endpoints = {
            "/searchByPexels",
            "/searchByPixabay",
            "/searchByWeb",
            "/createRobot"
        }

        if request_path not in allowed_endpoints:
            self.send_json(
                404,
                {
                    "error": "Endpoint not found",
                    "requested_path": request_path,
                    "available_endpoints": sorted(allowed_endpoints)
                }
            )
            return

        query_parameters = parse_qs(parsed_url.query)
        search_query_values = query_parameters.get("query", [])

        if not search_query_values:
            self.send_json(
                400,
                {
                    "error": "Missing query parameter"
                }
            )
            return

        search_query = search_query_values[0].strip()

        if not search_query:
            self.send_json(
                400,
                {
                    "error": "Empty query parameter"
                }
            )
            return

        provider_name = ""
        fetch_function = None
        api_key = None
        api_key_required = False

        if request_path == "/searchByPexels":
            provider_name = "PEXELS"
            fetch_function = fetch_from_pexels
            api_key = os.environ.get("PEXELS_API_KEY")
            api_key_required = True

        elif request_path == "/searchByPixabay":
            provider_name = "PIXABAY"
            fetch_function = fetch_from_pixabay
            api_key = os.environ.get("PIXABAY_API_KEY")
            api_key_required = True

        elif request_path == "/searchByWeb":
            provider_name = "WEB"
            fetch_function = fetch_from_web

        elif request_path == "/createRobot":
            provider_name = "AI_ROBOT"
            fetch_function = fetch_from_ai_robot_generator

        if fetch_function is None:
            self.send_json(
                500,
                {
                    "error": (
                        f"{provider_name} sağlayıcısının modülü "
                        "yüklenemedi."
                    )
                }
            )
            return

        if api_key_required and not api_key:
            self.send_json(
                500,
                {
                    "error": (
                        f"{provider_name}_API_KEY "
                        "environment variable not set"
                    )
                }
            )
            return

        print(
            f"[ARAMA] Sağlayıcı: {provider_name}, "
            f"Sorgu: {search_query!r}"
        )

        try:
            raw_result = call_fetch_function(
                fetch_function=fetch_function,
                query=search_query,
                api_key=api_key
            )

            result = normalize_fetch_result(raw_result)

        except Exception as exception:
            print("\n" + "-" * 70)
            print(
                f"{provider_name} SAĞLAYICI HATASI"
            )
            print("-" * 70)

            traceback.print_exc()

            print("-" * 70 + "\n")

            self.send_json(
                500,
                {
                    "error": str(exception),
                    "error_type": type(exception).__name__,
                    "provider": provider_name
                }
            )
            return

        self.send_json(
            200,
            {
                "provider": provider_name,
                "query": search_query,
                "photos": result["photos"],
                "videos": result["videos"]
            }
        )


def run_server(
    host="localhost",
    port=8000
):
    """HTTP sunucusunu çalıştırır."""

    server = ThreadingHTTPServer(
        (host, port),
        SuggestionRequestHandler
    )

    print("=" * 70)
    print("Fotoğraf ve video öneri sunucusu çalışıyor")
    print(f"Adres: http://{host}:{port}/")
    print("Durdurmak için Ctrl+C tuşlarına basın.")
    print("=" * 70)

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print("\nSunucu kapatılıyor...")

    finally:
        server.server_close()
        print("Sunucu kapatıldı.")


if __name__ == "__main__":
    server_host = "localhost"
    server_port = 8000

    if len(sys.argv) >= 2:
        server_host = sys.argv[1]

    if len(sys.argv) >= 3:
        try:
            server_port = int(sys.argv[2])
        except ValueError:
            print(
                f"Geçersiz port numarası: {sys.argv[2]}"
            )
            sys.exit(1)

    run_server(
        host=server_host,
        port=server_port
    )
