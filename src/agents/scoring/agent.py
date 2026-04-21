"""Integrated scoring for Job-Resume-Background match."""

from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

import config
from agents.scoring.models import Scorecard
from agents.scoring.prompts import SCORING_SYSTEM
from fairness.blind_screening import (
    blind_screen_background_for_scoring,
    blind_screen_resume_profile,
)
from monitoring.token_callback import get_token_callback


def score_match(
    job_spec: dict,
    arranged_resume: dict,
    background_result: dict,
) -> Scorecard:
    if not config.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set; scoring cannot run")

    blind_resume = blind_screen_resume_profile(arranged_resume)
    blind_bg = blind_screen_background_for_scoring(background_result)

    payload = {
        "job_spec": job_spec,
        "arranged_resume": blind_resume,
        "background_result": blind_bg,
    }
    body = json.dumps(payload, ensure_ascii=False, indent=2)
    from monitoring.context import current_username, current_function_id
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=config.OPENAI_API_KEY,
        callbacks=get_token_callback(username=current_username.get(), function_id=current_function_id.get() or "auto_score"),
    ).with_structured_output(Scorecard)
    out = llm.invoke(
        [
            SystemMessage(content=SCORING_SYSTEM),
            HumanMessage(content=f"Score the following JSON payload:\n\n{body}"),
        ],
    )
    if isinstance(out, Scorecard):
        return out
    if isinstance(out, dict):
        return Scorecard.model_validate(out)
    raise TypeError("structured_output returned an unexpected type")
