# Kick Kora Pro - SportAPI proxy. API secret stays on the local server.
import json, os, time, urllib.request, urllib.error
from datetime import date
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path

BASE = Path(__file__).resolve().parent
PUBLIC = BASE / "public"
PORT = int(os.environ.get("PORT", "3000"))
API_KEY = os.environ.get("SPORTAPI_KEY", "")

env_file = BASE / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8-sig").splitlines():
        if line.strip().startswith("SPORTAPI_KEY="):
            API_KEY = line.split("=", 1)[1].strip()
        elif line.strip().startswith("PORT="):
            try:
                PORT = int(line.split("=", 1)[1].strip())
            except ValueError:
                pass

CACHE = {}

def api_get(endpoint, cache_key, ttl=180):
    now = time.time()
    cached = CACHE.get(cache_key)
    if cached and now - cached[0] < ttl:
        return cached[1]
    if not API_KEY:
        raise RuntimeError("لم يتم إعداد مفتاح SportAPI. شغّل SETUP_KICK_KORA.bat أولاً.")
    req = urllib.request.Request(
        "https://sportapi.ai/api" + endpoint,
        headers={"X-Api-Key": API_KEY, "Accept": "application/json", "User-Agent": "KickKora/2.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            raise RuntimeError("مفتاح SportAPI غير صالح أو تم إلغاؤه. أعد إدخال مفتاح جديد.")
        if exc.code == 429:
            raise RuntimeError("تم بلوغ حد طلبات SportAPI المجانية. انتظر حتى إعادة ضبط الحد.")
        if exc.code == 404:
            raise RuntimeError("لم يعثر SportAPI على هذه البيانات أو البطولة.")
        raise RuntimeError("تعذر جلب البيانات من SportAPI (HTTP %s)." % exc.code)
    except Exception as exc:
        raise RuntimeError("تعذر الاتصال بـ SportAPI: " + str(exc))
    if not isinstance(payload, dict) or payload.get("success") is False:
        raise RuntimeError((payload or {}).get("error", "أعاد مزود البيانات استجابة غير متوقعة."))
    CACHE[cache_key] = (now, payload)
    return payload

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC), **kwargs)

    def send_json(self, status, obj):
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        parsed = urlparse(self.path)
        q = parse_qs(parsed.query)
        try:
            if parsed.path.startswith("/api/"):
                if parsed.path == "/api/fixtures":
                    match_date = q.get("date", [date.today().isoformat()])[0]
                    if len(match_date) != 10:
                        return self.send_json(400, {"error": "صيغة التاريخ غير صحيحة"})
                    result = api_get("/fixtures/date/" + match_date, "fixtures:" + match_date, 120)
                elif parsed.path == "/api/leagues":
                    result = api_get("/standings/leagues", "leagues", 21600)
                elif parsed.path == "/api/standings":
                    league = q.get("league", [""])[0]
                    if not league or not league.replace("-", "").isalnum():
                        return self.send_json(400, {"error": "معرّف البطولة غير صحيح"})
                    result = api_get("/standings/" + league, "standings:" + league, 1800)
                elif parsed.path == "/api/scorers":
                    league = q.get("league", [""])[0]
                    if not league or not league.replace("-", "").isalnum():
                        return self.send_json(400, {"error": "معرّف البطولة غير صحيح"})
                    result = api_get("/leagues/" + league + "/topscorers?limit=10", "scorers:" + league, 1800)
                elif parsed.path.startswith("/api/team-logo/"):
                    team_id = parsed.path.rsplit("/", 1)[-1]
                    if not team_id.isdigit():
                        return self.send_json(400, {"error": "معرّف النادي غير صحيح"})
                    req = urllib.request.Request(
                        "https://sportapi.ai/api/teams/" + team_id + "/logo",
                        headers={"X-Api-Key": API_KEY, "User-Agent": "KickKora/2.0"}
                    )
                    with urllib.request.urlopen(req, timeout=20) as response:
                        body = response.read()
                        content_type = response.headers.get("Content-Type", "image/png")
                    self.send_response(200)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Content-Length", str(len(body)))
                    self.send_header("Cache-Control", "public, max-age=86400")
                    self.end_headers()
                    self.wfile.write(body)
                    return
                else:
                    return self.send_json(404, {"error": "المسار غير موجود"})
                return self.send_json(200, result)
            return super().do_GET()
        except Exception as exc:
            return self.send_json(503, {"error": str(exc)})

    def log_message(self, fmt, *args):
        print("[Kick Kora] " + (fmt % args))

if __name__ == "__main__":
    print("Kick Kora Pro (SportAPI) يعمل على http://localhost:%d" % PORT)
    print("اترك هذه النافذة مفتوحة أثناء استخدام الموقع.")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
