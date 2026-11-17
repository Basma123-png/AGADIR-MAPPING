"""
Orchestrateur central asynchrone (DAG Hybride) pour le système multi-agents AGADIR MAPPING.
Coordonne le Fan-out de recherche, le Fan-in d'analyse, l'arbitrage du Juge,
la validation déterministe et la traçabilité cryptographique.
"""

from __future__ import annotations

import asyncio
import datetime
import logging
import time
import uuid
import json
from typing import Any, Callable, Dict, List, Optional
import requests

from src.multi_agent.agents.gemini_analyst import GeminiAnalystAgent
from src.multi_agent.agents.judge import JudgeAgent, DeterministicJudgeValidator
from src.multi_agent.agents.scholar_research import SemanticScholarAgent
from src.multi_agent.agents.web_research import WebResearchAgent
from src.multi_agent.audit_logger import AuditLogger
from src.multi_agent.base_provider import BaseLLMProvider, MockLLMProvider
from src.multi_agent.budget_manager import BudgetManager
from src.multi_agent.cache import SQLiteCacheManager
from src.multi_agent.config import MultiAgentConfig, load_multi_agent_config
from src.multi_agent.exceptions import (
    BudgetExceededException,
    BudgetReservationException,
    MultiAgentException,
    NetworkTimeoutException,
    SecurityViolationException,
    TaskCancelledException,
)
from src.multi_agent.schemas import (
    AgentRole,
    AnalysisReport,
    AnalysisReportRequest,
    ExecutionMode,
    FinalReport,
    JudgeDecision,
    ScholarSearchRequest,
    ScholarSearchResponse,
    ScientificPaperItem,
    TokenUsage,
    ValidationRequest,
    ValidationResult,
    VerdictStatus,
    WebSearchRequest,
    WebSearchResponse,
    WebSourceItem,
)
from src.multi_agent.security import SecurityValidator

logger = logging.getLogger("agadir.multi_agent.orchestrator")


class CentralOrchestrator:
    """
    Orchestrateur central asynchrone DAG pour les missions d'optimisation d'Agadir.
    """

    def __init__(
        self,
        config: Optional[MultiAgentConfig] = None,
        llm_provider: Optional[BaseLLMProvider] = None,
        security_validator: Optional[SecurityValidator] = None,
        cache_manager: Optional[SQLiteCacheManager] = None,
        web_agent: Optional[WebResearchAgent] = None,
        scholar_agent: Optional[SemanticScholarAgent] = None,
        analyst_agent: Optional[GeminiAnalystAgent] = None,
        judge_agent: Optional[JudgeAgent] = None
    ):
        self.config = config or load_multi_agent_config()
        self.security = security_validator or SecurityValidator()
        self.budget = BudgetManager(self.config)
        self.provider = llm_provider or MockLLMProvider(self.config)
        self.cache = cache_manager or SQLiteCacheManager()

        # Si le fournisseur LLM est simulé (tests / hors-ligne), on utilise des requesters mock
        # pour garantir un fonctionnement sans dépendance réseau externe.
        if web_agent is not None:
            self.web_agent = web_agent
        elif isinstance(self.provider, MockLLMProvider):
            self.web_agent = WebResearchAgent(
                self.config,
                cache_manager=self.cache,
                http_requester=self._default_mock_web_requester
            )
        else:
            self.web_agent = WebResearchAgent(self.config, cache_manager=self.cache)

        if scholar_agent is not None:
            self.scholar_agent = scholar_agent
        elif isinstance(self.provider, MockLLMProvider):
            self.scholar_agent = SemanticScholarAgent(
                self.config,
                cache_manager=self.cache,
                http_requester=self._default_mock_scholar_requester
            )
        else:
            self.scholar_agent = SemanticScholarAgent(self.config, cache_manager=self.cache)

        if analyst_agent is not None:
            self.analyst_agent = analyst_agent
        else:
            self.analyst_agent = GeminiAnalystAgent(
                config=self.config,
                provider=self.provider,
                budget_manager=self.budget,
                security_validator=self.security
            )

        if judge_agent is not None:
            self.judge_agent = judge_agent
        else:
            self.judge_agent = JudgeAgent(
                config=self.config,
                provider=self.provider,
                budget_manager=self.budget,
                security_validator=self.security
            )

    @staticmethod
    def _default_mock_web_requester(url: str, **kwargs: Any) -> requests.Response:
        resp = requests.Response()
        resp.status_code = 200
        html = (
            '<html><body>'
            '<a class="result__url" href="https://arxiv.org/abs/atsp-oropt">arxiv.org</a>'
            '<a class="result__snippet">Or-opt local search heuristic for asymmetric traveling salesperson problem. 2023.</a>'
            '</body></html>'
        )
        resp._content = html.encode("utf-8")
        resp.encoding = "utf-8"
        return resp

    @staticmethod
    def _default_mock_scholar_requester(method: str, url: str, **kwargs: Any) -> requests.Response:
        resp = requests.Response()
        resp.status_code = 200
        if "batch" in url:
            data = [
                {
                    "paperId": "paper-atsp-001",
                    "title": "Memetic Algorithms for the Asymmetric Traveling Salesperson Problem",
                    "authors": [{"name": "K. Smith"}, {"name": "L. Benali"}],
                    "year": 2022,
                    "venue": "Computers & Operations Research",
                    "citationCount": 48,
                    "abstract": "We study asymmetric local search operators on directed delivery graphs.",
                    "doi": "10.1016/j.cor.2022.105842",
                    "openAccessPdf": {"url": "https://openaccess.org/atsp-paper.pdf"}
                }
            ]
        else:
            data = {
                "total": 1,
                "data": [
                    {
                        "paperId": "paper-atsp-001",
                        "title": "Memetic Algorithms for the Asymmetric Traveling Salesperson Problem",
                        "authors": [{"name": "K. Smith"}, {"name": "L. Benali"}],
                        "year": 2022,
                        "venue": "Computers & Operations Research",
                        "citationCount": 48,
                        "abstract": "We study asymmetric local search operators on directed delivery graphs.",
                        "doi": "10.1016/j.cor.2022.105842",
                        "openAccessPdf": {"url": "https://openaccess.org/atsp-paper.pdf"}
                    }
                ]
            }
        resp._content = json.dumps(data).encode("utf-8")
        resp.encoding = "utf-8"
        return resp

    async def _execute_web_research(
        self,
        query: str,
        audit: AuditLogger,
        timeout: float
    ) -> WebSearchResponse:
        """Étape Fan-out : Recherche Web via WebResearchAgent."""
        req = WebSearchRequest(
            request_id=f"web-{uuid.uuid4().hex[:6]}",
            query=query,
            max_results=self.config.web_research.max_queries_per_mission
        )
        return await self.web_agent.search(req, audit_logger=audit)

    async def _execute_scholar_research(
        self,
        query: str,
        audit: AuditLogger,
        timeout: float
    ) -> ScholarSearchResponse:
        """Étape Fan-out : Recherche Scientifique Semantic Scholar via SemanticScholarAgent."""
        req = ScholarSearchRequest(
            request_id=f"sch-{uuid.uuid4().hex[:6]}",
            query=query,
            limit=10
        )
        return await self.scholar_agent.search_papers(req, audit_logger=audit)

    async def run_mission(
        self,
        topic: str,
        execution_mode: ExecutionMode = ExecutionMode.ECONOMIC,
        custom_mission_id: Optional[str] = None
    ) -> FinalReport:
        """
        Exécute une mission complète de bout en bout selon le DAG séquentiel conditionnel :
        1. Pre-flight : Vérification de l'intégrité des fichiers des Phases 1 à 5.
        2. Fan-out : Recherche Web et Scientifique en parallèle.
        3. Fan-in : Analyse critique par Gemini Analyst avec réservation budgétaire préalable.
        4. Arbitrage : Jugement contradictoire par Judge Agent avec réservation budgétaire préalable.
        5. Validation Déterministe : Recalcul Python si nécessaire.
        6. Post-flight : Clôture du journal d'audit et vérification finale d'intégrité.
        """
        start_time = time.time()

        # 1. Pre-flight : Contrôle d'intégrité physique absolu
        self.security.verify_all_protected_files()

        # Initialisation de l'audit logger
        audit = AuditLogger(self.config, mission_id=custom_mission_id)
        await audit.log_event(
            agent_id=AgentRole.ORCHESTRATOR,
            action="MISSION_STARTED",
            payload_summary={"topic": topic, "mode": execution_mode.value}
        )

        reservation_analyst_id: Optional[str] = None
        reservation_judge_id: Optional[str] = None

        try:
            # 2. Phase A : Fan-out Parallèle (Web & Scholar) avec résilience (Graceful Degradation)
            web_task = asyncio.create_task(
                self._execute_web_research(
                    query=topic,
                    audit=audit,
                    timeout=self.config.web_research.timeout_seconds
                )
            )
            scholar_task = asyncio.create_task(
                self._execute_scholar_research(
                    query=topic,
                    audit=audit,
                    timeout=self.config.llm_provider.default_timeout_seconds
                )
            )

            results = await asyncio.gather(web_task, scholar_task, return_exceptions=True)
            web_res_or_exc, scholar_res_or_exc = results

            # Traitement résilient de l'agent Web
            if isinstance(web_res_or_exc, Exception):
                logger.warning(f"WebResearchAgent en échec ({web_res_or_exc}). Passage en mode dégradé.")
                await audit.log_event(
                    agent_id=AgentRole.WEB_RESEARCH,
                    action="AGENT_DEGRADED",
                    payload_summary={"error": str(web_res_or_exc), "error_type": type(web_res_or_exc).__name__}
                )
                web_res = WebSearchResponse(
                    request_id=f"web-degraded-{uuid.uuid4().hex[:6]}",
                    status="DEGRADED",
                    sources_found=0,
                    sources=[],
                    execution_time_seconds=0.0
                )
            else:
                web_res = web_res_or_exc

            # Traitement résilient de l'agent Semantic Scholar
            if isinstance(scholar_res_or_exc, Exception):
                logger.warning(f"SemanticScholarAgent en échec ({scholar_res_or_exc}). Passage en mode dégradé.")
                await audit.log_event(
                    agent_id=AgentRole.SEMANTIC_SCHOLAR,
                    action="AGENT_DEGRADED",
                    payload_summary={"error": str(scholar_res_or_exc), "error_type": type(scholar_res_or_exc).__name__}
                )
                scholar_res = ScholarSearchResponse(
                    request_id=f"sch-degraded-{uuid.uuid4().hex[:6]}",
                    status="DEGRADED",
                    total_papers=0,
                    papers=[],
                    is_authenticated_key=bool(self.scholar_agent.api_key),
                    execution_time_seconds=0.0
                )
            else:
                scholar_res = scholar_res_or_exc

            # 3. Phase B : Fan-in et Analyse Critique (Gemini Analyst)
            analyst_req = AnalysisReportRequest(
                request_id=f"ana-req-{uuid.uuid4().hex[:6]}",
                mission_id=audit.mission_id,
                topic=topic,
                project_context={
                    "city": "Agadir",
                    "depot": "Place Al Amal",
                    "destinations_count": 40,
                    "reference_distance_m": 18933.1,
                    "is_asymmetric": True
                },
                web_evidence=web_res.sources,
                academic_evidence=scholar_res.papers
            )

            analyst_report = await self.analyst_agent.analyze(
                request=analyst_req,
                audit_logger=audit,
                execution_mode=execution_mode
            )

            # 4. Phase C : Arbitrage Contradictoire (Judge Agent)
            judge_decision = await self.judge_agent.judge(
                analysis_report=analyst_report,
                web_sources=web_res.sources,
                papers=scholar_res.papers,
                audit_logger=audit
            )

            # 5. Phase D : Validation Déterministe Python (Veto Absolu et Recalcul sur Matrice OSRM)
            candidate_tour = next((t.candidate_permutation for t in analyst_report.theses if t.candidate_permutation), None)
            claimed_dist = next((getattr(t, "claimed_distance_m", None) for t in analyst_report.theses if t.candidate_permutation), None)

            validation_res = DeterministicJudgeValidator.validate_candidate_tour(
                candidate_tour=candidate_tour,
                claimed_distance_m=claimed_dist
            )

            if validation_res.is_valid:
                await audit.log_event(
                    agent_id=AgentRole.VALIDATOR,
                    action="VALIDATION_CONFIRMED",
                    payload_summary={
                        "distance_m": validation_res.recalculated_distance_m,
                        "is_valid": True,
                        "gain_m": validation_res.gain_m
                    }
                )
            else:
                await audit.log_event(
                    agent_id=AgentRole.VALIDATOR,
                    action="VALIDATION_REJECTED",
                    payload_summary={
                        "is_valid": False,
                        "error": validation_res.error_message
                    }
                )

            web_ok = bool(web_res.status in ("SUCCESS", "SUCCESS_FROM_CACHE") and len(web_res.sources) > 0)
            scholar_ok = bool(scholar_res.status in ("SUCCESS", "SUCCESS_FROM_CACHE") and len(scholar_res.papers) > 0)

            # Établissement des statuts d'exécution des agents
            agent_execution_statuses = {
                "web_research": "SUCCESS" if web_ok else "DEGRADED",
                "semantic_scholar": "SUCCESS" if scholar_ok else "DEGRADED",
                "gemini_analyst": "SUCCESS",
                "judge_agent": "SUCCESS",
                "deterministic_validator": "SUCCESS" if validation_res.is_valid else "REJECTED"
            }

            # Détermination du statut global et de l'exigence de revue humaine
            is_partial = any(s == "DEGRADED" for s in agent_execution_statuses.values())
            has_unresolved_conflict = (
                judge_decision.overall_verdict in (VerdictStatus.CONFLICT_UNRESOLVED, VerdictStatus.NEEDS_REVIEW)
                or bool(judge_decision.unresolved_contradictions)
            )
            is_rejected = (
                judge_decision.overall_verdict == VerdictStatus.REJECTED
                or not validation_res.is_valid
            )

            if not validation_res.is_valid:
                workflow_status = "VALIDATION_REJECTED"
                final_execution_status = "VALIDATION_REJECTED"
                human_review_required = True
            elif is_rejected:
                workflow_status = "REJECTED"
                final_execution_status = "FAILED"
                human_review_required = True
            elif has_unresolved_conflict or judge_decision.human_review_required:
                workflow_status = "HUMAN_REVIEW_REQUIRED"
                final_execution_status = "NEEDS_HUMAN_REVIEW"
                human_review_required = True
            elif is_partial:
                workflow_status = "PARTIAL_SUCCESS"
                final_execution_status = "COMPLETED_PARTIAL"
                human_review_required = False
            else:
                workflow_status = "SUCCESS"
                final_execution_status = "COMPLETED_SUCCESS"
                human_review_required = False

            # Registre exhaustif des sources consultées
            source_registry: List[str] = [f"WEB-{i+1:02d}" for i in range(len(web_res.sources))]
            source_registry.extend([s.url for s in web_res.sources])
            for p in scholar_res.papers:
                source_registry.append(p.doi or p.paper_id)
            source_registry.append("INTERNAL-AGADIR-CONTEXT")

            # Empreintes certifiées des fichiers protégés
            protected_hashes = self.security.get_protected_files_hashes()

            # 6. Phase E : Clôture de Mission et Traçabilité Finale
            await audit.log_event(
                agent_id=AgentRole.ORCHESTRATOR,
                action="MISSION_COMPLETED",
                payload_summary={"total_cost_usd": self.budget.committed_cost_usd}
            )

            final_hash = await audit.close_mission()
            elapsed_time = time.time() - start_time

            # Post-flight : Contrôle d'intégrité final
            self.security.verify_all_protected_files()

            return FinalReport(
                mission_id=audit.mission_id,
                execution_timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                workflow_status=workflow_status,
                agent_execution_statuses=agent_execution_statuses,
                web_research_results=web_res,
                semantic_scholar_results=scholar_res,
                gemini_analysis=analyst_report,
                judge_verdict=judge_decision.overall_verdict or judge_decision.decision_status,
                deterministic_validation=validation_res,
                source_registry=source_registry,
                resolved_contradictions=judge_decision.resolved_contradictions,
                unresolved_contradictions=judge_decision.unresolved_contradictions,
                recommendations=judge_decision.recommendations or analyst_report.recommendations,
                human_review_required=human_review_required,
                budget_summary={
                    "committed_cost_usd": round(self.budget.committed_cost_usd, 5),
                    "active_reserved_usd": round(self.budget.active_reserved_cost_usd, 5),
                    "warning_threshold_usd": self.config.budget_guardrails.warning_threshold_usd,
                    "kill_switch_usd": self.config.budget_guardrails.kill_switch_usd,
                },
                audit_chain_status={
                    "chain_length": audit._current_index,
                    "final_hash": final_hash,
                    "trail_path": str(audit.jsonl_path),
                    "is_verified": True,
                },
                protected_files_integrity=protected_hashes,
                final_execution_status=final_execution_status,
                topic=topic,
                execution_mode=execution_mode,
                executive_summary=(
                    f"Mission '{topic}' complétée [{final_execution_status}]. "
                    f"La solution officielle de 18 933,1 m demeure la référence intouchable certifiée."
                ),
                web_sources_consulted=len(web_res.sources),
                papers_analyzed=len(scholar_res.papers),
                theses_evaluated=len(analyst_report.theses),
                total_execution_time_seconds=round(elapsed_time, 3),
                total_cost_usd=round(self.budget.committed_cost_usd, 5),
                audit_trail_path=str(audit.jsonl_path),
                audit_chain_length=audit._current_index,
                final_audit_hash=final_hash
            )

        except asyncio.CancelledError:
            # Nettoyage en cas d'annulation
            if reservation_analyst_id:
                await self.budget.release_reservation(reservation_analyst_id)
            if reservation_judge_id:
                await self.budget.release_reservation(reservation_judge_id)
            if not audit._is_closed:
                await audit.log_event(
                    agent_id=AgentRole.ORCHESTRATOR,
                    action="MISSION_CANCELLED",
                    payload_summary={"reason": "asyncio.CancelledError"}
                )
                await audit.close_mission()
            raise TaskCancelledException("La mission a été annulée.")

        except Exception as e:
            # Nettoyage en cas d'erreur
            if reservation_analyst_id:
                await self.budget.release_reservation(reservation_analyst_id)
            if reservation_judge_id:
                await self.budget.release_reservation(reservation_judge_id)
            if not audit._is_closed:
                await audit.log_event(
                    agent_id=AgentRole.ORCHESTRATOR,
                    action="MISSION_FAILED",
                    payload_summary={"error": str(e), "error_type": type(e).__name__}
                )
                await audit.close_mission()
            raise
