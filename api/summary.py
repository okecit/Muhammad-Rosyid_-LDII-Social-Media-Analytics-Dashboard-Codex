import os
from http.server import BaseHTTPRequestHandler

from api._shared import build_openai_prompt, build_payload, json_response, load_scored_comments


DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        json_response(self, 200, {"ok": True})

    def do_POST(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            json_response(self, 400, {"error": "OPENAI_API_KEY belum diatur di Vercel Environment Variables."})
            return

        try:
            from openai import OpenAI

            payload = build_payload(load_scored_comments())
            client = OpenAI(api_key=api_key)
            response = client.responses.create(
                model=os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL),
                input=build_openai_prompt(payload),
                max_output_tokens=900,
                temperature=0.2,
            )
            json_response(self, 200, {"summary": response.output_text})
        except Exception as exc:
            json_response(self, 500, {"error": str(exc)})
