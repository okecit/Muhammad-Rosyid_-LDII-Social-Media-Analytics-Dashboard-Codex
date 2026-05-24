from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import pandas as pd

from src.config import REQUIRED_COLUMNS


def load_comments(source: str | Path | BinaryIO) -> pd.DataFrame:
    """Load a YouTube comments CSV and normalize common field types."""
    df = pd.read_csv(source)
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Kolom wajib tidak ditemukan: {', '.join(missing)}")

    df = df[REQUIRED_COLUMNS].copy()
    df["comment"] = df["comment"].fillna("").astype(str).str.strip()
    df["author"] = df["author"].fillna("Tidak diketahui").astype(str)
    df["title"] = df["title"].fillna("Tanpa judul").astype(str)
    df["pageUrl"] = df["pageUrl"].fillna("").astype(str)
    df["voteCount"] = pd.to_numeric(df["voteCount"], errors="coerce").fillna(0).astype(int)
    df["replyCount"] = pd.to_numeric(df["replyCount"], errors="coerce").fillna(0).astype(int)
    df["hasCreatorHeart"] = df["hasCreatorHeart"].astype(str).str.lower().eq("true")
    df["authorIsChannelOwner"] = df["authorIsChannelOwner"].astype(str).str.lower().eq("true")
    df = df[df["comment"].str.len() > 0].reset_index(drop=True)
    return df


def build_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate sentiment by video title for the dashboard."""
    summary = (
        df.groupby(["title", "sentiment"], dropna=False)
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    for label in ["positif", "netral", "negatif"]:
        if label not in summary.columns:
            summary[label] = 0
    summary["total_komentar"] = summary[["positif", "netral", "negatif"]].sum(axis=1)
    return summary[["title", "total_komentar", "positif", "netral", "negatif"]].sort_values(
        "total_komentar", ascending=False
    )
