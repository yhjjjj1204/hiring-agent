"""LangChain callback for automatic token usage recording."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from monitoring.usage_service import record_usage_with_context

class TokenUsageCallbackHandler(BaseCallbackHandler):
    """
    Callback handler that automatically records token usage to the DB 
    based on the current execution context (username and function).
    """
    
    def __init__(self, username: Optional[str] = None, function_id: Optional[str] = None):
        self.username_override = username
        self.function_id_override = function_id

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        # 1. Try to get total usage from llm_output
        total_input = 0
        total_output = 0
        
        if response.llm_output and "token_usage" in response.llm_output:
            u = response.llm_output["token_usage"]
            total_input = u.get("prompt_tokens", 0)
            total_output = u.get("completion_tokens", 0)
        
        # 2. If not found, aggregate from generations
        if total_input == 0 and total_output == 0:
            for generations in response.generations:
                for gen in generations:
                    # Message usage metadata (newer LangChain)
                    msg = getattr(gen, "message", None)
                    if msg:
                        usage = getattr(msg, "usage_metadata", {})
                        if usage:
                            total_input += usage.get("input_tokens", 0)
                            total_output += usage.get("output_tokens", 0)
                    
                    # Generation info
                    info = getattr(gen, "generation_info", {})
                    if info and "token_usage" in info:
                        u = info["token_usage"]
                        total_input += u.get("prompt_tokens", 0)
                        total_output += u.get("completion_tokens", 0)

        if total_input > 0 or total_output > 0:
            record_usage_with_context(
                input_tokens=total_input,
                output_tokens=total_output,
                username=self.username_override,
                function_id=self.function_id_override,
                default_function_id="unknown",
            )

def get_token_callback(username: Optional[str] = None, function_id: Optional[str] = None) -> List[TokenUsageCallbackHandler]:
    """Returns a list with the callback handler for easy inclusion in LLM calls."""
    return [TokenUsageCallbackHandler(username=username, function_id=function_id)]
