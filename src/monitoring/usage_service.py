"""Service for persisting token usage statistics to MongoDB."""

from datetime import datetime, timezone
from typing import Any
from db.mongo import get_database

def record_usage(username: str, function_id: str, input_tokens: int, output_tokens: int) -> None:
    """
    Increments token usage for a specific user, function, and day.
    
    Args:
        username: The identifier of the user (recruiter or candidate)
        function_id: The ID of the agent or feature (e.g. 'auto_score', 'chatbot')
        input_tokens: Number of prompt tokens
        output_tokens: Number of completion tokens
    """
    if not username or (input_tokens <= 0 and output_tokens <= 0):
        return

    db = get_database()
    # Use YYYY-MM-DD for daily aggregation
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Unique key: user + function + date
    query = {
        "username": username,
        "function": function_id,
        "date": today_str
    }
    
    update = {
        "$inc": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_calls": 1
        },
        "$set": {
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    }
    
    try:
        db.token_usage.update_one(query, update, upsert=True)
    except Exception as e:
        # Log but don't crash the main flow for monitoring failures
        import logging
        logging.getLogger(__name__).error(f"Failed to record token usage: {e}")

def get_user_usage_summary(username: str) -> list[dict[str, Any]]:
    """Retrieves usage history for a specific user."""
    db = get_database()
    docs = list(db.token_usage.find({"username": username}).sort("date", -1))
    for d in docs:
        d.pop("_id", None)
    return docs

def get_global_usage_summary() -> list[dict[str, Any]]:
    """Retrieves global usage history across all users."""
    db = get_database()
    docs = list(db.token_usage.find().sort("date", -1))
    for d in docs:
        d.pop("_id", None)
    return docs
