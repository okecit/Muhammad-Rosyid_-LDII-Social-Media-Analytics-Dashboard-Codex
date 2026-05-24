from __future__ import annotations

import csv
import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET = PROJECT_ROOT / "data" / "raw" / "youtube_comments.csv"

POSITIVE_TERMS = {
    "aamiin",
    "amin",
    "bagus",
    "baik",
    "bangga",
    "benar",
    "berkah",
    "hebat",
    "keren",
    "mantap",
    "masyaallah",
    "setuju",
    "suka",
    "salut",
    "terima kasih",
}

NEGATIVE_TERMS = {
    "aneh",
    "buruk",
    "benci",
    "bohong",
    "fitnah",
    "jangan",
    "jelek",
    "kafir",
    "keliru",
    "sesat",
    "takut",
    "tidak benar",
    "tolak",
}


def json_response(handler, status: int, payload: dict) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def classify_text(text: str) -> tuple[str, float]:
    lowered = re.sub(r"\s+", " ", str(text).lower())
    positive_score = sum(1 for term in POSITIVE_TERMS if term in lowered)
    negative_score = sum(1 for term in NEGATIVE_TERMS if term in lowered)

    if positive_score > negative_score:
        return "positif", min(0.95, 0.55 + positive_score * 0.12)
    if negative_score > positive_score:
        return "negatif", min(0.95, 0.55 + negative_score * 0.12)
    return "netral", 0.5


def load_scored_comments(limit: int = 2000) -> list[dict]:
    comments = []
    with DATASET.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            comment = (row.get("comment") or "").strip()
            if not comment:
                continue

            sentiment, score = classify_text(comment)
            comments.append(
                {
                    "author": row.get("author") or "Tidak diketahui",
                    "comment": comment,
                    "sentiment": sentiment,
                    "sentiment_score": score,
                    "voteCount": int(row.get("voteCount") or 0),
                    "replyCount": int(row.get("replyCount") or 0),
                    "publishedTimeText": row.get("publishedTimeText") or "",
                    "title": row.get("title") or "Tanpa judul",
                    "pageUrl": row.get("pageUrl") or "",
                }
            )
            if len(comments) >= limit:
                break
    return comments


def build_payload(comments: list[dict]) -> dict:
    counts = {"positif": 0, "netral": 0, "negatif": 0}
    videos = {}
    total_votes = 0

    for row in comments:
        sentiment = row["sentiment"]
        counts[sentiment] = counts.get(sentiment, 0) + 1
        total_votes += row["voteCount"]
        title = row["title"]
        if title not in videos:
            videos[title] = {"title": title, "total_komentar": 0, "positif": 0, "netral": 0, "negatif": 0}
        videos[title]["total_komentar"] += 1
        videos[title][sentiment] += 1

    video_summary = sorted(videos.values(), key=lambda item: item["total_komentar"], reverse=True)
    return {
        "metrics": {
            "total_comments": len(comments),
            "unique_videos": len(videos),
            "total_votes": total_votes,
            "method": "kamus sederhana Vercel",
        },
        "sentiment_counts": counts,
        "video_summary": video_summary,
        "comments": comments,
    }


def build_openai_prompt(payload: dict) -> str:
    comments = sorted(
        payload["comments"],
        key=lambda item: (item.get("voteCount", 0), item.get("replyCount", 0)),
        reverse=True,
    )[:25]
    examples = "\n".join(
        f"- [{item['sentiment']}] votes={item['voteCount']}, replies={item['replyCount']}, "
        f"video={item['title']}: {item['comment'][:240]}"
        for item in comments
    )

    return f"""
Anda adalah asisten riset untuk mahasiswa S3 Komunikasi Islam.
Analisis data komentar YouTube tentang dakwah digital di Indonesia.

Konteks data:
- Metrik: {payload["metrics"]}
- Distribusi sentimen: {payload["sentiment_counts"]}
- Video dengan komentar terbanyak: {payload["video_summary"][:5]}

Contoh komentar penting:
{examples}

Tugas:
Buat ringkasan analitik dalam Bahasa Indonesia sebanyak tepat 5 poin bernomor.
Setiap poin harus memuat interpretasi akademik singkat, bukan sekadar mengulang angka.
Soroti implikasi untuk studi dakwah digital, persepsi audiens, potensi kontroversi, dan peluang riset lanjutan.
"""
