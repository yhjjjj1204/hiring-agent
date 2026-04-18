"""岗位-履历-背调 综合打分。"""

from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from hiring_agent import config
from hiring_agent.agents.scoring.models import Scorecard
from hiring_agent.agents.scoring.prompts import SCORING_SYSTEM
from hiring_agent.fairness.blind_screening import (
    blind_screen_background_for_scoring,
    blind_screen_resume_profile,
)


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
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=config.OPENAI_API_KEY,
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
