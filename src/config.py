from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_DATASET = RAW_DATA_DIR / "youtube_comments.csv"

REQUIRED_COLUMNS = [
    "author",
    "comment",
    "type",
    "voteCount",
    "replyCount",
    "publishedTimeText",
    "hasCreatorHeart",
    "authorIsChannelOwner",
    "title",
    "pageUrl",
]

SENTIMENT_LABELS = ["positif", "netral", "negatif"]
