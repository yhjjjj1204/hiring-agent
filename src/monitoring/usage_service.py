"""Service for persisting token usage statistics to MongoDB."""

from datetime import datetime, timezone
from typing import Any, Optional

from db.mongo import get_database


def _resolve_identity(
    username: Optional[str] = None,
    function_id: Optional[str] = None,
    user_role: Optional[str] = None,
    default_function_id: str = "unknown",
) -> tuple[Optional[str], str, Optional[str]]:
    """Resolve usage identity from explicit args or execution context."""
    if username is None or function_id is None or user_role is None:
        from monitoring.context import current_function_id, current_user_role, current_username

        if username is None:
            username = current_username.get()
        if function_id is None:
            function_id = current_function_id.get()
        if user_role is None:
            user_role = current_user_role.get()

    fid = function_id or default_function_id
    return username, fid, user_role


def record_usage(
    username: str,
    function_id: str,
    input_tokens: int,
    output_tokens: int,
    user_role: Optional[str] = None,
) -> None:
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
    if user_role:
        query["role"] = user_role
    
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
    if user_role:
        update["$set"]["role"] = user_role
    
    try:
        db.token_usage.update_one(query, update, upsert=True)
    except Exception as e:
        # Log but don't crash the main flow for monitoring failures
        import logging
        logging.getLogger(__name__).error(f"Failed to record token usage: {e}")


def record_usage_with_context(
    input_tokens: int,
    output_tokens: int,
    *,
    username: Optional[str] = None,
    function_id: Optional[str] = None,
    user_role: Optional[str] = None,
    default_function_id: str = "unknown",
) -> None:
    """Record usage with context fallback for identity fields."""
    resolved_username, resolved_function_id, resolved_role = _resolve_identity(
        username=username,
        function_id=function_id,
        user_role=user_role,
        default_function_id=default_function_id,
    )
    if not resolved_username:
        return
    record_usage(
        username=resolved_username,
        function_id=resolved_function_id,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        user_role=resolved_role,
    )


def record_openai_usage(
    usage: Any,
    *,
    username: Optional[str] = None,
    function_id: Optional[str] = None,
    user_role: Optional[str] = None,
    default_function_id: str = "unknown",
) -> None:
    """Record usage from OpenAI SDK usage object shape."""
    if usage is None:
        return
    input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
    output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
    record_usage_with_context(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        username=username,
        function_id=function_id,
        user_role=user_role,
        default_function_id=default_function_id,
    )

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
