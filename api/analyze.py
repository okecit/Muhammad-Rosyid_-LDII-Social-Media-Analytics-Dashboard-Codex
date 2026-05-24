from http.server import BaseHTTPRequestHandler

from api._shared import build_payload, json_response, load_scored_comments


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        json_response(self, 200, {"ok": True})

    def do_GET(self):
        try:
            payload = build_payload(load_scored_comments())
            json_response(self, 200, payload)
        except Exception as exc:
            json_response(self, 500, {"error": str(exc)})
