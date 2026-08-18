import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_play_reviews import intent_for, reply_template, sentiment_for, severity_for, topic_for  # noqa: E402
from build_play_reviews_report import rating_stats  # noqa: E402
from play_review_index import connect, export_keys, upsert_records  # noqa: E402


def test_payment_withdrawal_review_is_high_priority():
    text = "I deposited money but my balance disappeared and I cannot withdraw"
    topics = topic_for(text)
    assert "payment_and_withdrawal" in topics
    assert severity_for(text, 1) == "P0"
    assert sentiment_for(text, 1) == "negative"
    assert intent_for(topics, "P0", False) == "customer_follow_up_and_fund_audit"


def test_developer_reply_template_is_classified():
    record = {"developer_reply_text": "Please contact us through Telegram or live chat."}
    assert reply_template(record) == "support_handoff"


def test_positive_withdrawal_signal_is_not_negative_without_negative_words():
    assert sentiment_for("withdrawal was successfully completed and the game is excellent", 5) == "positive"


def test_config_targets_waje_public_page():
    config = json.loads((ROOT / "config/play_reviews.json").read_text(encoding="utf-8"))
    assert config["package_name"] == "com.hfhy.waje.special"
    assert "play.google.com/store/apps/details" in config["url"]
    assert config["sort"] == "Newest"


def test_rating_stats_partition_is_exact():
    stats = rating_stats([{"rating": 5}, {"rating": 4}, {"rating": 3}, {"rating": 2}, {"rating": 1}])
    assert sum(stats["counts"].values()) == stats["total"] == 5
    assert stats["good_count"] == 2
    assert stats["neutral_count"] == 1
    assert stats["bad_count"] == 2


def test_review_index_deduplicates_and_versions_changes():
    record = {
        "review_key": "review-1",
        "review_id": "review-1",
        "identity_key": "identity-1",
        "package_name": "com.hfhy.waje.special",
        "content_hash": "hash-1",
        "captured_at": "2026-08-11T00:00:00Z",
        "review_text": "first",
    }
    with tempfile.TemporaryDirectory() as directory:
        db = connect(Path(directory) / "reviews.sqlite3")
        assert upsert_records(db, [record]) == {"new": 1, "updated": 0, "existing": 0}
        assert upsert_records(db, [record]) == {"new": 0, "updated": 0, "existing": 1}
        changed = {**record, "content_hash": "hash-2", "review_text": "edited"}
        assert upsert_records(db, [changed]) == {"new": 0, "updated": 1, "existing": 0}
        assert export_keys(db) == {"review-1": "hash-2"}
        assert db.execute("SELECT COUNT(*) FROM review_versions").fetchone()[0] == 2
        db.close()
