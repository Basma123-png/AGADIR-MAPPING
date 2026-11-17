"""
Agents spécialisés pour le système multi-agents AGADIR MAPPING.
Web Research Agent, Semantic Scholar Agent, Gemini Analyst Agent et Judge Agent.
"""

from src.multi_agent.agents.web_research import WebResearchAgent
from src.multi_agent.agents.scholar_research import SemanticScholarAgent
from src.multi_agent.agents.gemini_analyst import GeminiAnalystAgent
from src.multi_agent.agents.judge import (
    JudgeAgent,
    DEFAULT_SCORING_WEIGHTS,
    DeterministicJudgeValidator,
    OFFICIAL_CERTIFIED_TOUR,
    OFFICIAL_CERTIFIED_DISTANCE_M,
)

__all__ = [
    "WebResearchAgent",
    "SemanticScholarAgent",
    "GeminiAnalystAgent",
    "JudgeAgent",
    "DEFAULT_SCORING_WEIGHTS",
    "DeterministicJudgeValidator",
    "OFFICIAL_CERTIFIED_TOUR",
    "OFFICIAL_CERTIFIED_DISTANCE_M",
]
