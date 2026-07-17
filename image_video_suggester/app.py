from concurrent.futures import ThreadPoolExecutor, as_completed
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import inspect
import json
import os
import sys
import traceback


# .env desteği isteğe bağlıdır.
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs) -> None:
        pass


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


# Pexels
try:
    from suggester_using_by_pexels_api import (
        fetch_suggestions as fetch_from_pexels,
    )
except ImportError:
    fetch_from_pexels = None


# Web arama yalnızca tekli arama sekmesinde kullanılır.
try:
    from suggester_using_by_web_search import (
        fetch_suggestions as fetch_from_web,
    )
except ImportError:
    fetch_from_web = None


# Pixabay: bütün HTTP ve sonuç dönüştürme işlemleri ayrı modüldedir.
try:
    from suggester_using_by_pixabay_api import (
        fetch_suggestions as fetch_pixabay_all,
        fetch_video_suggestions as fetch_pixabay_videos,
    )
except ImportError:
    fetch_pixabay_all = None
    fetch_pixabay_videos = None


# Yapay zekâ robot oluşturucu
try:
    from suggester_using_by_ai_robot_generator import (
        fetch_suggestions as fetch_from_ai_robot_generator,
    )
except ImportError:
    fetch_from_ai_robot_generator = None


from config import DEFAULT_RESULT_COUNT, MAX_RESULT_COUNT, MIN_RESULT_COUNT


APPLICATION_JSON_HEADER = "application/json; charset=utf-8"

# Arayüz büyük listeleri küçük paketler hâlinde gönderir.
MAX_BATCH_SENTENCES_PER_REQUEST = 25
MAX_SENTENCE_LENGTH = 2_000
MAX_REQUEST_BODY_BYTES = 5 * 1024 * 1024
MAX_PROVIDER_WORKERS = 9


PROVIDER_ENDPOINTS = {
    "/searchByPexels": {
        "name": "PEXELS",
        "label": "Pexels",
        "fetch_function": fetch_from_pexels,
        "api_key_env": "PEXELS_API_KEY",
    },
    "/searchByPixabay": {
        "name": "PIXABAY",
        "label": "Pixabay",
        "fetch_function": fetch_pixabay_all,
        "api_key_env": "PIXABAY_API_KEY",
    },
    "/searchByPixabayVideos": {
        "name": "PIXABAY",
        "label": "Pixabay",
        "fetch_function": fetch_pixabay_videos,
        "api_key_env": "PIXABAY_API_KEY",
    },
    "/searchByWeb": {
        "name": "WEB",
        "label": "Web Arama",
        "fetch_function": fetch_from_web,
        "api_key_env": None,
    },
    "/createRobot": {
        "name": "AI_ROBOT",
        "label": "Robot Resmi",
        "fetch_function": fetch_from_ai_robot_generator,
        "api_key_env": None,
    },
}

# Toplu video sekmesi yalnızca Pexels ve Pixabay kullanır; Web Arama tekli sekmeye özeldir.
BATCH_VIDEO_ENDPOINTS = (
    "/searchByPexels",
    "/searchByPixabayVideos",
)


def make_json_safe(value):
    """JSON'a doğrudan dönüştürülemeyen değerleri güvenli hâle getirir."""

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
        return [make_json_safe(item) for item in value]

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


def clamp_result_count(value, default=None):
    """Sonuç sayısını uygulamanın izin verdiği aralığa çeker."""

    try:
        parsed_value = int(value)
    except (TypeError, ValueError):
        return default

    return min(MAX_RESULT_COUNT, max(MIN_RESULT_COUNT, parsed_value))


def parse_result_count(raw_values):
    """GET isteğindeki count parametresini doğrular."""

    if not raw_values:
        return None

    return clamp_result_count(raw_values[0], default=None)


def call_fetch_function(fetch_function, query, api_key=None, result_count=None):
    """
    fetch_suggestions fonksiyonunun farklı imzalarını destekler.

    Desteklenen örnekler:
        fetch_suggestions(query)
        fetch_suggestions(query, api_key)
        fetch_suggestions(query, api_key, per_page=result_count)
    """

    if fetch_function is None:
        raise RuntimeError("İlgili sağlayıcının Python modülü yüklenemedi.")

    try:
        signature = inspect.signature(fetch_function)
        parameters = signature.parameters

        positional_parameters = [
            parameter
            for parameter in parameters.values()
            if parameter.kind
            in {
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            }
        ]

        accepts_varargs = any(
            parameter.kind == inspect.Parameter.VAR_POSITIONAL
            for parameter in parameters.values()
        )
        accepts_varkwargs = any(
            parameter.kind == inspect.Parameter.VAR_KEYWORD
            for parameter in parameters.values()
        )

        supports_result_count = accepts_varkwargs or "per_page" in parameters
        extra_kwargs = {}

        if result_count is not None and supports_result_count:
            extra_kwargs["per_page"] = result_count

        if accepts_varargs or len(positional_parameters) >= 2:
            return fetch_function(query, api_key, **extra_kwargs)

        return fetch_function(query, **extra_kwargs)

    except ValueError:
        # Bazı C uzantılarında veya sarmalanmış fonksiyonlarda imza okunamayabilir.
        return fetch_function(query, api_key)


def normalize_fetch_result(raw_result):
    """Sağlayıcı sonuçlarını {photos: [], videos: []} biçimine dönüştürür."""

    photos = []
    videos = []

    if isinstance(raw_result, dict):
        photos = raw_result.get("photos") or []
        videos = raw_result.get("videos") or []

    elif isinstance(raw_result, tuple) and len(raw_result) == 2:
        photos, videos = raw_result

    elif (
        isinstance(raw_result, list)
        and len(raw_result) == 2
        and isinstance(raw_result[0], list)
        and isinstance(raw_result[1], list)
    ):
        photos, videos = raw_result

    elif isinstance(raw_result, list):
        photos = raw_result

    elif isinstance(raw_result, str):
        photos = [{"image_url": raw_result}]

    elif raw_result is None:
        photos = []
        videos = []

    else:
        raise TypeError(
            "fetch_suggestions desteklenmeyen bir veri biçimi döndürdü: "
            f"{type(raw_result).__name__}"
        )

    if not isinstance(photos, list):
        photos = [] if photos is None else [photos]

    if not isinstance(videos, list):
        videos = [] if videos is None else [videos]

    return {
        "photos": make_json_safe(photos),
        "videos": make_json_safe(videos),
    }


def get_provider(endpoint, usage="single"):
    """Endpoint ayarlarını ve kullanım türüne uygun çağrı fonksiyonunu döndürür."""

    provider = PROVIDER_ENDPOINTS.get(endpoint)

    if provider is None:
        raise ValueError("Geçersiz arama kaynağı seçildi.")

    if usage == "batch":
        fetch_function = provider.get("batch_fetch_function")
        if fetch_function is None:
            fetch_function = provider.get("fetch_function")
    else:
        fetch_function = provider.get("fetch_function")

    if fetch_function is None:
        raise RuntimeError(
            f"{provider['label']} sağlayıcısının Python modülü yüklenemedi."
        )

    api_key = None
    api_key_env = provider["api_key_env"]

    if api_key_env:
        api_key = (os.environ.get(api_key_env) or "").strip()
        if not api_key:
            raise RuntimeError(
                f"{api_key_env} ayarlı değil. Anahtarı .env dosyasına ekleyin."
            )

    return provider, api_key, fetch_function


def fetch_provider_results(
    endpoint,
    query,
    result_count=None,
    usage="single",
):
    """Tek bir sorguyu uygun sağlayıcı fonksiyonuyla çalıştırır."""

    provider, api_key, fetch_function = get_provider(endpoint, usage=usage)

    print(
        f"[ARAMA] Sağlayıcı: {provider['name']}, "
        f"Kullanım: {usage}, Sorgu: {query!r}"
    )

    raw_result = call_fetch_function(
        fetch_function=fetch_function,
        query=query,
        api_key=api_key,
        result_count=result_count,
    )

    return provider, normalize_fetch_result(raw_result)

def provider_error_result(endpoint, error_message):
    """Bir sağlayıcının başarısız sonucunu standart biçimde oluşturur."""

    provider = PROVIDER_ENDPOINTS[endpoint]
    return {
        "provider": provider["name"],
        "provider_label": provider["label"],
        "endpoint": endpoint,
        "videos": [],
        "error": error_message,
    }


class SuggestionRequestHandler(BaseHTTPRequestHandler):
    """Fotoğraf ve video öneri HTTP sunucusu."""

    def log_message(self, format_string, *args):
        print(f"[HTTP] {self.client_address[0]} - {format_string % args}")

    def send_json(self, status_code, payload):
        safe_payload = make_json_safe(payload)
        response_body = json.dumps(
            safe_payload,
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")

        self.send_response(status_code)
        self.send_header("Content-Type", APPLICATION_JSON_HEADER)
        self.send_header("Content-Length", str(len(response_body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept")
        self.end_headers()
        self.wfile.write(response_body)

    def send_html_file(self, file_path):
        if not file_path.exists():
            self.send_json(404, {"error": f"{file_path.name} bulunamadı."})
            return

        content = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(content)

    def read_json_body(self):
        content_length = self.headers.get("Content-Length")

        if not content_length:
            raise ValueError("İstek gövdesi bulunamadı.")

        try:
            body_length = int(content_length)
        except ValueError as exception:
            raise ValueError("Geçersiz Content-Length değeri.") from exception

        if body_length <= 0:
            raise ValueError("İstek gövdesi boş.")

        if body_length > MAX_REQUEST_BODY_BYTES:
            raise ValueError(
                "İstek gövdesi çok büyük. Metni daha küçük paketlere bölün."
            )

        raw_body = self.rfile.read(body_length)

        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exception:
            raise ValueError("Geçerli bir JSON gövdesi gönderilmelidir.") from exception

        if not isinstance(payload, dict):
            raise ValueError("JSON gövdesi bir nesne olmalıdır.")

        return payload

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept")
        self.end_headers()

    def do_GET(self):
        self.run_safely(self.handle_get_request)

    def do_POST(self):
        self.run_safely(self.handle_post_request)

    def run_safely(self, handler_function):
        """Bağlantı ve beklenmeyen sunucu hatalarını ortak biçimde yakalar."""

        try:
            handler_function()

        except BrokenPipeError:
            print("[UYARI] Tarayıcı yanıt tamamlanmadan bağlantıyı kapattı.")

        except ConnectionResetError:
            print("[UYARI] İstemci bağlantıyı sıfırladı.")

        except ValueError as exception:
            self.send_json(400, {"error": str(exception)})

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
                        "error_type": type(exception).__name__,
                    },
                )
            except Exception:
                traceback.print_exc()

    def handle_get_request(self):
        parsed_url = urlparse(self.path)
        request_path = parsed_url.path

        if request_path in {"/", "/index.html"}:
            self.send_html_file(BASE_DIR / "index.html")
            return

        if request_path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return

        if request_path not in PROVIDER_ENDPOINTS:
            self.send_json(
                404,
                {
                    "error": "Endpoint not found",
                    "requested_path": request_path,
                    "available_endpoints": sorted(
                        [*PROVIDER_ENDPOINTS.keys(), "/batchVideoSuggestions"]
                    ),
                },
            )
            return

        query_parameters = parse_qs(parsed_url.query)
        search_query_values = query_parameters.get("query", [])

        if not search_query_values:
            raise ValueError("Missing query parameter")

        search_query = search_query_values[0].strip()
        if not search_query:
            raise ValueError("Empty query parameter")

        result_count = parse_result_count(query_parameters.get("count", []))

        try:
            provider, result = fetch_provider_results(
                endpoint=request_path,
                query=search_query,
                result_count=result_count,
            )
        except Exception as exception:
            print("\n" + "-" * 70)
            print(f"SAĞLAYICI HATASI: {request_path}")
            print("-" * 70)
            traceback.print_exc()
            print("-" * 70 + "\n")

            self.send_json(
                500,
                {
                    "error": str(exception),
                    "error_type": type(exception).__name__,
                    "provider_endpoint": request_path,
                },
            )
            return

        self.send_json(
            200,
            {
                "provider": provider["name"],
                "query": search_query,
                "photos": result["photos"],
                "videos": result["videos"],
            },
        )

    def handle_post_request(self):
        request_path = urlparse(self.path).path

        if request_path != "/batchVideoSuggestions":
            self.send_json(
                404,
                {
                    "error": "Endpoint not found",
                    "requested_path": request_path,
                    "available_endpoints": ["/batchVideoSuggestions"],
                },
            )
            return

        payload = self.read_json_body()
        raw_sentences = payload.get("sentences")

        if not isinstance(raw_sentences, list):
            raise ValueError("sentences alanı bir liste olmalıdır.")

        sentences = []
        for item in raw_sentences:
            sentence = str(item or "").strip()
            if not sentence:
                continue
            if len(sentence) > MAX_SENTENCE_LENGTH:
                raise ValueError(
                    f"Bir satır en fazla {MAX_SENTENCE_LENGTH} karakter olabilir."
                )
            sentences.append(sentence)

        if not sentences:
            raise ValueError("En az bir cümle girilmelidir.")

        if len(sentences) > MAX_BATCH_SENTENCES_PER_REQUEST:
            raise ValueError(
                "Tek istekte en fazla "
                f"{MAX_BATCH_SENTENCES_PER_REQUEST} cümle gönderilebilir. "
                "Arayüz büyük listeleri otomatik olarak parçalara böler."
            )

        result_count = clamp_result_count(
            payload.get("count"),
            default=DEFAULT_RESULT_COUNT,
        )

        # Her sağlayıcıyı bir kez doğrula. Örneğin Pexels anahtarı eksikse
        # Pixabay sonuçları yine çalışmaya devam eder.
        provider_errors = {}
        for endpoint in BATCH_VIDEO_ENDPOINTS:
            try:
                get_provider(endpoint, usage="batch")
                provider_errors[endpoint] = None
            except Exception as exception:
                provider_errors[endpoint] = str(exception)

        batch_results = [
            {
                "index": index,
                "sentence": sentence,
                "providers": [None] * len(BATCH_VIDEO_ENDPOINTS),
            }
            for index, sentence in enumerate(sentences)
        ]

        futures = {}
        available_task_count = sum(
            1
            for endpoint in BATCH_VIDEO_ENDPOINTS
            if provider_errors[endpoint] is None
        ) * len(sentences)

        if available_task_count:
            worker_count = min(MAX_PROVIDER_WORKERS, available_task_count)
            with ThreadPoolExecutor(max_workers=worker_count) as executor:
                for sentence_index, sentence in enumerate(sentences):
                    for provider_index, endpoint in enumerate(BATCH_VIDEO_ENDPOINTS):
                        provider_error = provider_errors[endpoint]
                        if provider_error is not None:
                            batch_results[sentence_index]["providers"][provider_index] = (
                                provider_error_result(endpoint, provider_error)
                            )
                            continue

                        future = executor.submit(
                            fetch_provider_results,
                            endpoint,
                            sentence,
                            result_count,
                            "batch",
                        )
                        futures[future] = (
                            sentence_index,
                            provider_index,
                            endpoint,
                        )

                for future in as_completed(futures):
                    sentence_index, provider_index, endpoint = futures[future]
                    try:
                        provider, result = future.result()
                        provider_result = {
                            "provider": provider["name"],
                            "provider_label": provider["label"],
                            "endpoint": endpoint,
                            "videos": result["videos"],
                            "error": None,
                        }
                    except Exception as exception:
                        traceback.print_exc()
                        provider_result = provider_error_result(
                            endpoint,
                            str(exception),
                        )

                    batch_results[sentence_index]["providers"][provider_index] = (
                        provider_result
                    )
        else:
            for sentence_result in batch_results:
                for provider_index, endpoint in enumerate(BATCH_VIDEO_ENDPOINTS):
                    sentence_result["providers"][provider_index] = (
                        provider_error_result(
                            endpoint,
                            provider_errors[endpoint],
                        )
                    )

        self.send_json(
            200,
            {
                "providers": [
                    PROVIDER_ENDPOINTS[endpoint]["name"]
                    for endpoint in BATCH_VIDEO_ENDPOINTS
                ],
                "count_per_provider": result_count,
                "results": batch_results,
            },
        )


def run_server(host="localhost", port=8000):
    """HTTP sunucusunu çalıştırır."""

    server = ThreadingHTTPServer((host, port), SuggestionRequestHandler)

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
            print(f"Geçersiz port numarası: {sys.argv[2]}")
            sys.exit(1)

    run_server(host=server_host, port=server_port)
