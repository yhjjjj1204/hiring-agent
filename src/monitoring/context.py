"""Context management for tracking current user and execution path across async/threads."""

from contextvars import ContextVar
from typing import Optional

# Current active username (recruiter or candidate)
current_username: ContextVar[Optional[str]] = ContextVar("current_username", default=None)

# Current active thread ID (for pipeline runs)
current_thread_id: ContextVar[Optional[str]] = ContextVar("current_thread_id", default=None)

# Current active agent/function ID
current_function_id: ContextVar[Optional[str]] = ContextVar("current_function_id", default=None)

def set_execution_context(username: Optional[str] = None, thread_id: Optional[str] = None, function_id: Optional[str] = None):
    """Convenience to set multiple context variables."""
    if username is not None:
        current_username.set(username)
    if thread_id is not None:
        current_thread_id.set(thread_id)
    if function_id is not None:
        current_function_id.set(function_id)
