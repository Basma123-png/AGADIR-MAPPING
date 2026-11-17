"""
Agent Gemini Analyst pour AGADIR MAPPING.
Analyse les preuves collectées par les agents Web et Semantic Scholar,
détecte les convergences et contradictions, synthétise les thèses d'optimisation
et interagit de manière atomique avec le gestionnaire de budget et l'audit trail.
"""

from __future__ import annotations

import asyncio
import datetime
import logging
import os
import uuid
from typing import Any, Dict, List, Optional

from src.multi_agent.audit_logger import AuditLogger
from src.multi_agent.base_provider import BaseLLMProvider, MockLLMProvider
from src.multi_agent.budget_manager import BudgetManager
from src.multi_agent.config import MultiAgentConfig, load_multi_agent_config
from src.multi_agent.exceptions import (
    BudgetExceededException,
    BudgetReservationException,
    ProviderException,
    SecurityViolationException,
)
from src.multi_agent.gemini_provider import GeminiProvider
from src.multi_agent.schemas import (
    AgentRole,
    AnalysisReport,
    AnalysisReportRequest,
    ExecutionMode,
)
from src.multi_agent.security import SecurityValidator

logger = logging.getLogger("agadir.multi_agent.gemini_analyst")


class GeminiAnalystAgent:
    """
    Agent autonome d'analyse critique et de synthèse scientifique pour AGADIR MAPPING.
    """

    def __init__(
        self,
        config: Optional[MultiAgentConfig] = None,
        provider: Optional[BaseLLMProvider] = None,
        budget_manager: Optional[BudgetManager] = None,
        security_validator: Optional[SecurityValidator] = None
    ):
        self.config = config or load_multi_agent_config()
        self.security = security_validator or SecurityValidator()
        self.budget = budget_manager or BudgetManager(self.config)

        if provider is not None:
            self.provider = provider
        elif os.getenv(self.config.llm_provider.api_key_env_var):
            self.provider = GeminiProvider(self.config)
        else:
            # Mode sans clé configurée : bascule automatique sécurisée en MockLLMProvider
            self.provider = MockLLMProvider(self.config)

    async def analyze(
        self,
        request: AnalysisReportRequest,
        audit_logger: Optional[AuditLogger] = None,
        execution_mode: ExecutionMode = ExecutionMode.ECONOMIC
    ) -> AnalysisReport:
        """
        Exécute le cycle complet d'analyse critique :
        1. Réservation budgétaire préalable stricte.
        2. Consignation du démarrage dans l'audit cryptographique.
        3. Exécution de l'inférence via le provider configuré.
        4. Engagement du coût réel consommé (tokens entrée, sortie, réflexion, cache).
        5. Consignation de la fin d'analyse ou libération immédiate du budget en cas d'échec.
        """
        model_to_use = (
            self.config.models.default_fast
            if execution_mode == ExecutionMode.ECONOMIC
            else self.config.models.advanced_reasoning
        )

        # 1. Réservation budgétaire atomique préalable
        reservation_id = await self.budget.reserve_budget(
            model=model_to_use,
            prompt_tokens_est=3000,
            max_output_tokens=self.config.budget_guardrails.max_output_tokens_default
        )

        if audit_logger:
            await audit_logger.log_event(
                agent_id=AgentRole.GEMINI_ANALYST,
                action="START_ANALYSIS",
                payload_summary={
                    "mission_id": request.mission_id,
                    "topic": request.topic,
                    "model": model_to_use,
                    "web_sources_count": len(request.web_evidence),
                    "academic_papers_count": len(request.academic_evidence)
                }
            )

        try:
            # 2. Exécution de la synthèse via le provider
            report = await self.provider.generate_analysis(request)

            # 3. Engagement du coût réel consommé
            await self.budget.commit_usage(
                reservation_id=reservation_id,
                model=model_to_use,
                usage=report.token_usage
            )

            if audit_logger:
                await audit_logger.log_event(
                    agent_id=AgentRole.GEMINI_ANALYST,
                    action="COMPLETED_ANALYSIS",
                    payload_summary={
                        "analysis_id": report.analysis_id,
                        "theses_count": len(report.theses),
                        "findings_count": len(report.main_findings),
                        "confidence_level": report.confidence_level,
                        "tokens_used": report.token_usage.model_dump(),
                        "estimated_cost_usd": report.estimated_cost
                    }
                )

            return report

        except asyncio.CancelledError:
            await self.budget.release_reservation(reservation_id)
            if audit_logger:
                await audit_logger.log_event(
                    agent_id=AgentRole.GEMINI_ANALYST,
                    action="ANALYSIS_CANCELLED",
                    payload_summary={"mission_id": request.mission_id}
                )
            raise

        except Exception as e:
            # En cas d'erreur : libération systématique de la réservation budgétaire
            await self.budget.release_reservation(reservation_id)

            if audit_logger:
                await audit_logger.log_event(
                    agent_id=AgentRole.GEMINI_ANALYST,
                    action="ANALYSIS_FAILED",
                    payload_summary={
                        "mission_id": request.mission_id,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )
            raise
