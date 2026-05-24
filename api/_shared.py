from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
YOUTUBE_DATASET = RAW_DATA_DIR / "youtube_comments.csv"
FACEBOOK_DATASETS = sorted(RAW_DATA_DIR.glob("facebook_comments_post_*.csv"))

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

STOPWORDS = {
    "yang",
    "dan",
    "atau",
    "ini",
    "itu",
    "dari",
    "dengan",
    "untuk",
    "pada",
    "dalam",
    "ada",
    "aja",
    "saja",
    "saya",
    "kami",
    "kita",
    "mereka",
    "dia",
    "nya",
    "ke",
    "di",
    "ya",
    "kok",
    "lah",
    "pun",
    "kan",
    "bisa",
    "tidak",
    "gak",
    "ga",
    "nggak",
    "karena",
    "kalau",
    "jadi",
    "orang",
    "ldii",
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


def _safe_int(value: object) -> int:
    try:
        return int(float(str(value or "0").replace(",", "")))
    except ValueError:
        return 0


def _content_name_from_url(url: str, fallback: str) -> str:
    if not url:
        return fallback
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    if "youtube.com" in parsed.netloc and path:
        return path.split("/")[-1] or fallback
    if "facebook.com" in parsed.netloc and path:
        parts = [part for part in path.split("/") if part]
        if len(parts) >= 2:
            return f"Facebook {parts[0]} {parts[1]}"
    return fallback


def _score_row(row: dict, platform: str, source: str) -> dict:
    if platform == "YouTube":
        comment = (row.get("comment") or "").strip()
        author = row.get("author") or "Tidak diketahui"
        title = row.get("title") or _content_name_from_url(row.get("pageUrl") or "", "Video YouTube")
        url = row.get("pageUrl") or ""
        reactions = _safe_int(row.get("voteCount"))
        replies = _safe_int(row.get("replyCount"))
        depth = 0
        published = row.get("publishedTimeText") or ""
    else:
        comment = (row.get("Content") or "").strip()
        author = row.get("Author") or "Tidak diketahui"
        url = row.get("Url") or ""
        title = _content_name_from_url(url, source.replace(".csv", ""))
        reactions = _safe_int(row.get("ReactionsCount"))
        replies = _safe_int(row.get("SubCommentsCount"))
        depth = _safe_int(row.get("Depth"))
        published = row.get("CommentAt") or ""

    sentiment, score = classify_text(comment)
    return {
        "platform": platform,
        "source": source,
        "author": author,
        "comment": comment,
        "sentiment": sentiment,
        "sentiment_score": score,
        "reactions": reactions,
        "replies": replies,
        "engagement": reactions + replies,
        "depth": depth,
        "is_reply": depth > 0,
        "published": published,
        "title": title,
        "url": url,
        "word_count": len(re.findall(r"[A-Za-zÀ-ÿ0-9_]+", comment)),
        "char_count": len(comment),
    }


def load_scored_comments(limit: int = 5000) -> list[dict]:
    comments: list[dict] = []

    if YOUTUBE_DATASET.exists():
        with YOUTUBE_DATASET.open("r", encoding="utf-8-sig", newline="") as file:
            for row in csv.DictReader(file):
                if row.get("comment"):
                    comments.append(_score_row(row, "YouTube", YOUTUBE_DATASET.name))

    for dataset in FACEBOOK_DATASETS:
        with dataset.open("r", encoding="utf-8-sig", newline="") as file:
            for row in csv.DictReader(file):
                if row.get("Content"):
                    comments.append(_score_row(row, "Facebook", dataset.name))

    return comments[:limit]


def _pct(part: int, whole: int) -> float:
    return round((part / whole) * 100, 1) if whole else 0.0


def _length_bin(word_count: int) -> str:
    if word_count <= 5:
        return "1-5 kata"
    if word_count <= 15:
        return "6-15 kata"
    if word_count <= 35:
        return "16-35 kata"
    return ">35 kata"


def _top_words(comments: list[dict], platform: str | None = None, sentiment: str | None = None, limit: int = 25) -> list[dict]:
    counter: Counter[str] = Counter()
    for row in comments:
        if platform and row["platform"] != platform:
            continue
        if sentiment and row["sentiment"] != sentiment:
            continue
        words = re.findall(r"[a-zA-ZÀ-ÿ0-9_]{3,}", row["comment"].lower())
        counter.update(word for word in words if word not in STOPWORDS)
    return [{"word": word, "count": count} for word, count in counter.most_common(limit)]


def build_payload(comments: list[dict]) -> dict:
    sentiment_counts = {"positif": 0, "netral": 0, "negatif": 0}
    platform_counts: Counter[str] = Counter()
    platform_sentiment = defaultdict(lambda: {"positif": 0, "netral": 0, "negatif": 0, "total": 0})
    content_summary = {}
    length_distribution = defaultdict(Counter)

    total_engagement = 0
    total_replies = 0
    unique_authors = set()

    for row in comments:
        sentiment = row["sentiment"]
        platform = row["platform"]
        title = row["title"]

        sentiment_counts[sentiment] += 1
        platform_counts[platform] += 1
        platform_sentiment[platform][sentiment] += 1
        platform_sentiment[platform]["total"] += 1
        length_distribution[platform][_length_bin(row["word_count"])] += 1

        total_engagement += row["engagement"]
        total_replies += row["replies"]
        unique_authors.add(row["author"].lower())

        if title not in content_summary:
            content_summary[title] = {
                "title": title,
                "platform": platform,
                "total": 0,
                "positif": 0,
                "netral": 0,
                "negatif": 0,
                "engagement": 0,
                "avg_words": 0.0,
                "_words": 0,
            }
        item = content_summary[title]
        item["total"] += 1
        item[sentiment] += 1
        item["engagement"] += row["engagement"]
        item["_words"] += row["word_count"]

    for item in content_summary.values():
        item["avg_words"] = round(item["_words"] / item["total"], 1) if item["total"] else 0
        item["positive_rate"] = _pct(item["positif"], item["total"])
        item["negative_rate"] = _pct(item["negatif"], item["total"])
        del item["_words"]

    total_comments = len(comments)
    positive = sentiment_counts["positif"]
    negative = sentiment_counts["negatif"]
    polarity_index = round(((positive - negative) / total_comments) * 100, 1) if total_comments else 0.0

    top_positive_content = sorted(content_summary.values(), key=lambda row: (row["positive_rate"], row["total"]), reverse=True)[:5]
    top_negative_content = sorted(content_summary.values(), key=lambda row: (row["negative_rate"], row["total"]), reverse=True)[:5]

    insights = [
        {
            "label": "Indeks polaritas",
            "value": polarity_index,
            "note": "positif dikurangi negatif per 100 komentar",
        },
        {
            "label": "Rasio respons",
            "value": _pct(total_replies, total_comments),
            "note": "balasan/subkomentar dibanding total komentar",
        },
        {
            "label": "Engagement rata-rata",
            "value": round(total_engagement / total_comments, 2) if total_comments else 0,
            "note": "reaksi dan balasan per komentar",
        },
        {
            "label": "Komentar panjang",
            "value": _pct(sum(1 for row in comments if row["word_count"] > 35), total_comments),
            "note": "indikasi argumen atau narasi panjang",
        },
    ]

    return {
        "metrics": {
            "total_comments": total_comments,
            "unique_authors": len(unique_authors),
            "unique_contents": len(content_summary),
            "total_engagement": total_engagement,
            "total_replies": total_replies,
            "positive_rate": _pct(positive, total_comments),
            "negative_rate": _pct(negative, total_comments),
            "neutral_rate": _pct(sentiment_counts["netral"], total_comments),
            "polarity_index": polarity_index,
            "method": "kamus sentimen ringan untuk Vercel",
        },
        "sentiment_counts": sentiment_counts,
        "platform_counts": dict(platform_counts),
        "platform_sentiment": dict(platform_sentiment),
        "content_summary": sorted(content_summary.values(), key=lambda item: item["total"], reverse=True),
        "top_comments": sorted(comments, key=lambda item: item["engagement"], reverse=True)[:20],
        "top_positive_content": top_positive_content,
        "top_negative_content": top_negative_content,
        "length_distribution": {platform: dict(counter) for platform, counter in length_distribution.items()},
        "word_frequency": {
            "all": _top_words(comments),
            "youtube": _top_words(comments, platform="YouTube"),
            "facebook": _top_words(comments, platform="Facebook"),
            "positive": _top_words(comments, sentiment="positif"),
            "negative": _top_words(comments, sentiment="negatif"),
        },
        "insights": insights,
        "comments": sorted(comments, key=lambda item: item["engagement"], reverse=True),
    }


def build_openai_prompt(payload: dict) -> str:
    examples = "\n".join(
        f"- [{item['platform']} | {item['sentiment']}] engagement={item['engagement']}, "
        f"konten={item['title']}: {item['comment'][:260]}"
        for item in payload["top_comments"][:25]
    )

    return f"""
Anda adalah asisten riset untuk mahasiswa S3 Komunikasi Islam.
Analisis data komentar YouTube dan Facebook tentang LDII, dakwah digital, dan percakapan publik di Indonesia.

Konteks data:
- Metrik utama: {payload["metrics"]}
- Distribusi platform: {payload["platform_counts"]}
- Distribusi sentimen: {payload["sentiment_counts"]}
- Sentimen per platform: {payload["platform_sentiment"]}
- Konten paling ramai: {payload["content_summary"][:6]}
- Konten dengan kecenderungan positif: {payload["top_positive_content"]}
- Konten dengan kecenderungan negatif: {payload["top_negative_content"]}
- Kata dominan: {payload["word_frequency"]["all"][:15]}

Contoh komentar ber-engagement tinggi:
{examples}

Tugas:
Buat ringkasan analitik dalam Bahasa Indonesia sebanyak tepat 5 poin bernomor.
Setiap poin harus memuat interpretasi akademik singkat, bukan sekadar mengulang angka.
Soroti implikasi untuk studi dakwah digital, framing LDII, persepsi audiens, potensi kontroversi,
dan peluang riset lanjutan. Jika ada keterbatasan metode kamus sentimen, nyatakan secara ringkas di poin terakhir.
"""
