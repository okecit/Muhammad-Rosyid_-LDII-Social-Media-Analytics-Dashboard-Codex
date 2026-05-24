from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.openai_summary import generate_ai_summary
from src.config import DEFAULT_DATASET, SENTIMENT_LABELS
from src.data_loader import build_summary_table, load_comments
from src.sentiment import DEFAULT_HF_MODEL, classify_comments


st.set_page_config(
    page_title="Dashboard Sentimen Dakwah Digital",
    page_icon=":bar_chart:",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def cached_load_default(path: str) -> pd.DataFrame:
    return load_comments(path)


@st.cache_data(show_spinner=True)
def cached_classify(
    df: pd.DataFrame,
    model_name: str,
    use_transformer: bool,
    max_rows: int,
) -> pd.DataFrame:
    working = df.head(max_rows).copy() if max_rows else df.copy()
    return classify_comments(working, model_name=model_name, use_transformer=use_transformer)


def metric_card(label: str, value: str | int) -> None:
    st.metric(label, value)


st.title("Analisis Sentimen Komentar YouTube Dakwah Digital di Indonesia")
st.caption("Dashboard riset komunikasi Islam berbasis komentar YouTube, model sentimen Bahasa Indonesia, dan ringkasan OpenAI API.")

with st.sidebar:
    st.header("Sumber Data")
    uploaded = st.file_uploader("Unggah CSV komentar YouTube", type=["csv"])
    st.divider()
    st.header("Model Sentimen")
    use_transformer = st.toggle("Gunakan model IndoBERT/RoBERTa Bahasa Indonesia", value=True)
    model_name = st.text_input("Hugging Face model", value=DEFAULT_HF_MODEL)
    max_rows = st.number_input(
        "Batas komentar dianalisis",
        min_value=100,
        max_value=10000,
        value=2000,
        step=100,
        help="Turunkan nilai ini bila komputer lambat saat memuat model transformer.",
    )

try:
    raw_df = load_comments(uploaded) if uploaded else cached_load_default(str(DEFAULT_DATASET))
except Exception as exc:
    st.error(f"Gagal membaca CSV: {exc}")
    st.stop()

with st.spinner("Menganalisis sentimen komentar..."):
    df = cached_classify(raw_df, model_name, use_transformer, int(max_rows))

sentiment_counts = (
    df["sentiment"]
    .value_counts()
    .reindex(SENTIMENT_LABELS, fill_value=0)
    .rename_axis("sentiment")
    .reset_index(name="jumlah")
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    metric_card("Total komentar", f"{len(df):,}")
with col2:
    metric_card("Video unik", f"{df['title'].nunique():,}")
with col3:
    metric_card("Total vote", f"{df['voteCount'].sum():,}")
with col4:
    metric_card("Metode", df["sentiment_method"].iloc[0])

chart_col, table_col = st.columns([0.9, 1.1])

with chart_col:
    st.subheader("Distribusi Sentimen")
    fig = px.pie(
        sentiment_counts,
        names="sentiment",
        values="jumlah",
        color="sentiment",
        color_discrete_map={"positif": "#2E7D32", "netral": "#607D8B", "negatif": "#C62828"},
        hole=0.38,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(showlegend=True, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

with table_col:
    st.subheader("Ringkasan per Video")
    st.dataframe(build_summary_table(df), use_container_width=True, hide_index=True)

st.subheader("Tabel Komentar dan Sentimen")
sentiment_filter = st.multiselect("Filter sentimen", SENTIMENT_LABELS, default=SENTIMENT_LABELS)
filtered_df = df[df["sentiment"].isin(sentiment_filter)].copy()
st.dataframe(
    filtered_df[
        [
            "author",
            "comment",
            "sentiment",
            "sentiment_score",
            "voteCount",
            "replyCount",
            "publishedTimeText",
            "title",
            "pageUrl",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

csv = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Unduh hasil sentimen CSV",
    data=csv,
    file_name="hasil_sentimen_youtube.csv",
    mime="text/csv",
)

st.subheader("Ringkasan AI")
st.caption("Gunakan environment variable atau Streamlit secrets: OPENAI_API_KEY. Model bisa diubah lewat OPENAI_MODEL.")
if st.button("Generate AI Summary", type="primary"):
    try:
        with st.spinner("OpenAI sedang menyusun ringkasan analitik..."):
            summary = generate_ai_summary(df)
        st.markdown(summary)
    except Exception as exc:
        st.error(f"Gagal membuat ringkasan AI: {exc}")
