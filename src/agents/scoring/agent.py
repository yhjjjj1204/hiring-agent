"""Integrated scoring for Job-Resume-Background match using competing experts."""

from __future__ import annotations

import json
from typing import List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

import config
from agents.scoring.models import Scorecard, CompetingAnalysis, AnalysisPoint
from agents.scoring.prompts import (
    ADVOCATE_AGENT_PROMPT,
    CRITIC_AGENT_PROMPT,
    ADVOCATE_AUDITOR_PROMPT,
    CRITIC_AUDITOR_PROMPT,
    JUDGE_AGENT_PROMPT,
)
from fairness.blind_screening import (
    blind_screen_background_for_scoring,
    blind_screen_resume_profile,
)
from monitoring.token_callback import get_token_callback


class PointInput(BaseModel):
    title: str
    description: str

class AnalysisPoints(BaseModel):
    points: List[PointInput]

class PointRefutation(BaseModel):
    refutation: Optional[str] = Field(None, description="Max 60 words. Leave None if the point is solid.")

class PointRefutations(BaseModel):
    refutations: List[PointRefutation] = Field(description="One refutation per input point, in the same order.")


def score_match(
    job_spec: dict,
    arranged_resume: dict,
    background_result: dict,
    personal_statement: str | None = None,
) -> Scorecard:
    if not config.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set; scoring cannot run")

    blind_resume = blind_screen_resume_profile(arranged_resume)
    blind_bg = blind_screen_background_for_scoring(background_result)

    payload = {
        "job_spec": job_spec,
        "arranged_resume": blind_resume,
        "background_result": blind_bg,
        "personal_statement": personal_statement,
    }
    body = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    
    from monitoring.context import current_username, current_function_id
    
    # Base LLM for text analysis
    llm_struct = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=config.OPENAI_API_KEY,
        callbacks=get_token_callback(username=current_username.get(), function_id=current_function_id.get() or "auto_score"),
    )

    # 1. Advocate Agent
    advocate_out = llm_struct.with_structured_output(AnalysisPoints).invoke([
        SystemMessage(content=ADVOCATE_AGENT_PROMPT),
        HumanMessage(content=f"Analyze this candidate:\n\n{body}")
    ])
    adv_points = [AnalysisPoint(title=p.title, description=p.description) for p in advocate_out.points]

    # 2. Critic Agent
    critic_out = llm_struct.with_structured_output(AnalysisPoints).invoke([
        SystemMessage(content=CRITIC_AGENT_PROMPT),
        HumanMessage(content=f"Analyze this candidate:\n\n{body}")
    ])
    cri_points = [AnalysisPoint(title=p.title, description=p.description) for p in critic_out.points]

    # 3. Advocate Auditor
    if adv_points:
        adv_points_json = json.dumps([{"title": p.title, "description": p.description} for p in adv_points], indent=2, default=str)
        adv_audit_out = llm_struct.with_structured_output(PointRefutations).invoke([
            SystemMessage(content=ADVOCATE_AUDITOR_PROMPT),
            HumanMessage(content=f"Candidate Data:\n{body}\n\nAdvocate Points:\n{adv_points_json}")
        ])
        for i, p in enumerate(adv_points):
            if i < len(adv_audit_out.refutations):
                p.refutation = adv_audit_out.refutations[i].refutation

    # 4. Critic Auditor
    if cri_points:
        cri_points_json = json.dumps([{"title": p.title, "description": p.description} for p in cri_points], indent=2, default=str)
        cri_audit_out = llm_struct.with_structured_output(PointRefutations).invoke([
            SystemMessage(content=CRITIC_AUDITOR_PROMPT),
            HumanMessage(content=f"Candidate Data:\n{body}\n\nCritic Points:\n{cri_points_json}")
        ])
        for i, p in enumerate(cri_points):
            if i < len(cri_audit_out.refutations):
                p.refutation = cri_audit_out.refutations[i].refutation

    # 5. Judge Agent (Structured Output)
    llm_judge = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=config.OPENAI_API_KEY,
        callbacks=get_token_callback(username=current_username.get(), function_id=current_function_id.get() or "auto_score"),
    ).with_structured_output(Scorecard)

    judge_input = {
        "candidate_data": payload,
        "advocate_points": [
            {
                "title": p.title, 
                "description": p.description, 
                "auditor_challenge": p.refutation
            } for p in adv_points
        ],
        "critic_points": [
            {
                "title": p.title, 
                "description": p.description, 
                "auditor_challenge": p.refutation
            } for p in cri_points
        ]
    }

    out = llm_judge.invoke([
        SystemMessage(content=JUDGE_AGENT_PROMPT),
        HumanMessage(content=f"Review all evidence and provide the final Scorecard:\n\n{json.dumps(judge_input, indent=2, default=str)}")
    ])

    competing_analysis = CompetingAnalysis(
        advocate_points=adv_points,
        critic_points=cri_points
    )

    if isinstance(out, Scorecard):
        out.competing_analysis = competing_analysis
        return out
    if isinstance(out, dict):
        card = Scorecard.model_validate(out)
        card.competing_analysis = competing_analysis
        return card
    
    raise TypeError("structured_output returned an unexpected type")
