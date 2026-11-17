"""
Interface abstraite pour les fournisseurs de modèles de langage (LLM) et implémentation Mock.
Permet d'isoler le code métier du SDK externe et de tester le pipeline sans aucun appel réseau payant.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.multi_agent.config import MultiAgentConfig
from src.multi_agent.exceptions import NetworkTimeoutException, ProviderException
from src.multi_agent.schemas import (
    AnalysisReport,
    AnalysisReportRequest,
    FindingItem,
    JudgeDecision,
    ThesisEvaluation,
    ThesisItem,
    TokenUsage,
    VerdictStatus,
)


class BaseLLMProvider(ABC):
    """Contrat d'interface abstrait pour tout moteur LLM (Google GenAI, Claude, Mock, etc.)."""

    def __init__(self, config: MultiAgentConfig):
        self.config = config

    @abstractmethod
    async def generate_analysis(self, request: AnalysisReportRequest) -> AnalysisReport:
        """Génère le rapport d'analyse critique à partir des évidences collectées."""
        pass

    @abstractmethod
    async def evaluate_proposals(
        self,
        analysis_report: AnalysisReport,
        project_context: Dict[str, Any]
    ) -> JudgeDecision:
        """Effectue l'arbitrage contradictoire des thèses d'optimisation."""
        pass


class MockLLMProvider(BaseLLMProvider):
    """
    Fournisseur simulé déterministe pour les tests unitaires et le mode hors-ligne.
    Ne réalise AUCUN appel réseau externe et ne consomme AUCUN token facturable.
    """

    def __init__(
        self,
        config: MultiAgentConfig,
        simulated_delay_seconds: float = 0.05,
        should_timeout: bool = False,
        should_fail: bool = False
    ):
        super().__init__(config)
        self.simulated_delay_seconds = simulated_delay_seconds
        self.should_timeout = should_timeout
        self.should_fail = should_fail
        self.call_count: int = 0

    async def generate_analysis(self, request: AnalysisReportRequest) -> AnalysisReport:
        self.call_count += 1
        if self.should_timeout:
            await asyncio.sleep(self.simulated_delay_seconds + 5.0)
            raise NetworkTimeoutException("Délai d'attente simulé dépassé lors de l'analyse.")

        if self.should_fail:
            raise ProviderException("Erreur simulée du fournisseur d'inférence.")

        await asyncio.sleep(self.simulated_delay_seconds)

        # Simulation d'une thèse constructive basée sur le contexte ATSP
        thesis = ThesisItem(
            thesis_id="TH-SIM-01",
            hypothesis="L'application d'un opérateur Or-opt asymétrique de relocalisation de chaînes de 3 nœuds peut réduire les segments de détour vers le littoral.",
            scientific_rationale="Inspiré par les propriétés de relocalisation adaptative sur l'ATSP.",
            cited_papers=["10.1016/j.cor.2022.105842"],
            cited_web_sources=["https://arxiv.org/abs/atsp-relocation"],
            proposed_action="Intégrer Or-opt-3 dans l'étape d'amélioration locale du GA.",
            requires_deterministic_validation=True,
            candidate_permutation=None  # La tournée officielle reste la référence
        )

        token_usage = TokenUsage(
            prompt_tokens=1200,
            completion_tokens=450,
            thinking_tokens=150,
            cached_tokens=0,
            tool_cost_usd=0.0,
            total_cost_usd=0.0
        )

        input_sources = (
            [s.url for s in request.web_evidence]
            + [f"WEB-{i:02d}" for i in range(1, len(request.web_evidence) + 1)]
            + [p.paper_id for p in request.academic_evidence]
        )
        supporting = [s for s in ["WEB-01", "paper-atsp-001"] if s in input_sources]
        if not supporting and input_sources:
            supporting = [input_sources[0]]

        return AnalysisReport(
            mission_id=request.mission_id,
            analysis_id=f"ana-{uuid.uuid4().hex[:8]}",
            agent_id="gemini_analyst",
            model_id=self.config.models.default_fast,
            model_name=self.config.models.default_fast,
            input_source_ids=input_sources,
            main_findings=[
                FindingItem(
                    finding_id="F-01",
                    statement="L'asymétrie du réseau d'Agadir nécessite des heuristiques de voisinage adaptées (Or-opt, 2-opt asymétrique).",
                    category="atsp",
                    supporting_source_ids=supporting,
                    confidence="HIGH"
                )
            ],
            scientific_evidence=[p.title for p in request.academic_evidence],
            web_evidence=[s.title for s in request.web_evidence],
            convergences=["Les sources académiques et empiriques s'accordent sur le gain des relocalisations de chaînes de nœuds sur graphes orientés."],
            contradictions=[],
            limitations=["Absence de données de trafic en temps réel dans les matrices statiques."],
            uncertainties=["Variabilité potentielle des temps d'arrêt aux carrefours côtiers."],
            missing_information=["Profil altimétrique dynamique par tranche horaire."],
            confidence_level="HIGH",
            recommendations=["Conserver la tournée certifiée de 18 933,1 m comme référence intouchable."],
            theses=[thesis],
            general_critique="L'analyse simulée confirme que la matrice OSRM 41x41 asymétrique doit être strictement préservée.",
            token_usage=token_usage,
            estimated_cost=0.0,
            execution_status="SUCCESS",
            execution_time_seconds=self.simulated_delay_seconds
        )

    async def evaluate_proposals(
        self,
        analysis_report: AnalysisReport,
        project_context: Dict[str, Any]
    ) -> JudgeDecision:
        self.call_count += 1
        if self.should_timeout:
            await asyncio.sleep(self.simulated_delay_seconds + 5.0)
            raise NetworkTimeoutException("Délai d'attente simulé dépassé lors du jugement.")

        if self.should_fail:
            raise ProviderException("Erreur simulée lors de l'arbitrage du Juge.")

        await asyncio.sleep(self.simulated_delay_seconds)

        evaluations: List[ThesisEvaluation] = []
        for thesis in analysis_report.theses:
            evaluations.append(
                ThesisEvaluation(
                    thesis_id=thesis.thesis_id,
                    status=VerdictStatus.ACCEPTED_PENDING_VALIDATION,
                    confidence_score=0.85,
                    justification="Hypothèse théoriquement cohérente avec la littérature ATSP. Nécessite vérification sur matrice OSRM.",
                    contradictions_found=[]
                )
            )

        token_usage = TokenUsage(
            prompt_tokens=850,
            completion_tokens=220,
            thinking_tokens=80,
            cached_tokens=0,
            tool_cost_usd=0.0,
            total_cost_usd=0.0
        )

        criterion_scores = {
            "source_reliability": 0.90,
            "scientific_consistency": 0.88,
            "evidence_quality": 0.85,
            "agent_consistency": 0.92,
            "uncertainty_transparency": 0.80
        }
        weighted_score = round(
            0.25 * criterion_scores["source_reliability"]
            + 0.25 * criterion_scores["scientific_consistency"]
            + 0.20 * criterion_scores["evidence_quality"]
            + 0.15 * criterion_scores["agent_consistency"]
            + 0.15 * criterion_scores["uncertainty_transparency"],
            4
        )

        return JudgeDecision(
            mission_id=analysis_report.mission_id,
            judgment_id=f"jdg-{uuid.uuid4().hex[:8]}",
            agent_id="judge_agent",
            input_analysis_ids=[analysis_report.analysis_id],
            evaluated_source_ids=analysis_report.input_source_ids,
            source_reliability_assessment="Sources académiques et techniques vérifiées sans anomalies.",
            scientific_consistency_assessment="Raisonnement conforme aux propriétés du Last-Mile ATSP.",
            evidence_quality_assessment="Preuves documentaires solides et corroborées.",
            agent_consistency_assessment="Convergence observée entre la littérature et le web technique.",
            contradictions=[],
            resolved_contradictions=[],
            unresolved_contradictions=[],
            hallucination_flags=[],
            missing_evidence=[],
            criterion_scores=criterion_scores,
            weighted_score=weighted_score,
            decision_status=VerdictStatus.ACCEPTED_PENDING_VALIDATION,
            decision_rationale="Arbitrage simulé réalisé selon la grille contradictoire à 5 critères.",
            recommendations=["Conserver la solution de référence certifiée de 18 933,1 m."],
            evaluations=evaluations,
            human_review_required=False,
            model_id=self.config.models.default_fast,
            decision_id=f"dec-{uuid.uuid4().hex[:8]}",
            overall_verdict=VerdictStatus.ACCEPTED_PENDING_VALIDATION,
            audit_notes="Arbitrage simulé réalisé selon la grille contradictoire à 5 critères.",
            token_usage=token_usage,
            estimated_cost=0.0,
            execution_status="SUCCESS",
            execution_time_seconds=self.simulated_delay_seconds
        )
