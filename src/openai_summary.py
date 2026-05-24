from __future__ import annotations

import os

import pandas as pd


DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"


def _compact_examples(df: pd.DataFrame, limit: int = 25) -> str:
    columns = ["author", "comment", "sentiment", "voteCount", "replyCount", "title"]
    sample = df.sort_values(["voteCount", "replyCount"], ascending=False).head(limit)
    lines = []
    for _, row in sample[columns].iterrows():
        comment = str(row["comment"]).replace("\n", " ")[:240]
        lines.append(
            f"- [{row['sentiment']}] votes={row['voteCount']}, replies={row['replyCount']}, "
            f"video={row['title']}: {comment}"
        )
    return "\n".join(lines)


def build_summary_prompt(df: pd.DataFrame) -> str:
    counts = df["sentiment"].value_counts().to_dict()
    total_comments = len(df)
    total_videos = df["title"].nunique()
    top_videos = (
        df.groupby("title")
        .size()
        .sort_values(ascending=False)
        .head(5)
        .rename("jumlah")
        .reset_index()
        .to_dict("records")
    )

    return f"""
Anda adalah asisten riset untuk mahasiswa S3 Komunikasi Islam.
Analisis data komentar YouTube tentang dakwah digital di Indonesia.

Konteks data:
- Total komentar: {total_comments}
- Jumlah video unik: {total_videos}
- Distribusi sentimen: {counts}
- Video dengan komentar terbanyak: {top_videos}

Contoh komentar penting:
{_compact_examples(df)}

Tugas:
Buat ringkasan analitik dalam Bahasa Indonesia sebanyak tepat 5 poin bernomor.
Setiap poin harus memuat interpretasi akademik singkat, bukan sekadar mengulang angka.
Soroti implikasi untuk studi dakwah digital, persepsi audiens, potensi kontroversi, dan peluang riset lanjutan.
"""


def generate_ai_summary(df: pd.DataFrame, model: str | None = None) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY belum diatur di environment atau Streamlit secrets.")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=model or os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL),
        input=build_summary_prompt(df),
        max_output_tokens=900,
        temperature=0.2,
    )
    return response.output_text
