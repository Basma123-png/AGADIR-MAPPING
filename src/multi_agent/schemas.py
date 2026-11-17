"""
Modèles de données et schémas d'interface Pydantic v2 pour AGADIR MAPPING.
Assure un typage strict, la validation structurelle et la sérialisation canonique.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator


class ExecutionMode(str, Enum):
    ECONOMIC = "ECONOMIC"
    COMPLETE = "COMPLETE"
    OFFLINE_CACHE = "OFFLINE_CACHE"


class AgentRole(str, Enum):
    ORCHESTRATOR = "central_orchestrator"
    WEB_RESEARCH = "web_research_agent"
    SEMANTIC_SCHOLAR = "semantic_scholar_agent"
    GEMINI_ANALYST = "gemini_analyst"
    JUDGE = "judge_agent"
    VALIDATOR = "deterministic_validator"


class VerdictStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    ACCEPTED_WITH_RESERVATIONS = "ACCEPTED_WITH_RESERVATIONS"
    NEEDS_MORE_EVIDENCE = "NEEDS_MORE_EVIDENCE"
    CONFLICT_UNRESOLVED = "CONFLICT_UNRESOLVED"
    REJECTED = "REJECTED"
    VALIDATION_REQUIRED = "VALIDATION_REQUIRED"
    # Valeurs de compatibilité ascendante
    ACCEPTED_PENDING_VALIDATION = "ACCEPTED_PENDING_VALIDATION"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class TokenUsage(BaseModel):
    """Comptabilisation précise des tokens et calcul du coût d'un appel d'inférence."""
    model_config = ConfigDict(extra="forbid", strict=True)

    prompt_tokens: int = Field(ge=0, default=0)
    completion_tokens: int = Field(ge=0, default=0)
    thinking_tokens: int = Field(ge=0, default=0, description="Inclus dans les tokens de sortie")
    cached_tokens: int = Field(ge=0, default=0)
    tool_cost_usd: float = Field(ge=0.0, default=0.0)
    total_cost_usd: float = Field(ge=0.0, default=0.0)


# --- Modèles Agent 1 : Web Research ---

class WebSourceItem(BaseModel):
    """Source web unitaire isolée."""
    model_config = ConfigDict(extra="forbid")

    url: str
    title: str
    snippet: str
    published_year: Optional[int] = None
    is_reputable_domain: bool = False
    crawled_at_utc: str


class WebSearchRequest(BaseModel):
    """Requête de recherche web."""
    model_config = ConfigDict(extra="forbid")

    request_id: str
    query: str
    max_results: int = Field(default=5, ge=1, le=20)
    target_domains: Optional[List[str]] = None
    language: str = "en"


class WebSearchResponse(BaseModel):
    """Réponse de recherche web contenant des évidences balisées."""
    model_config = ConfigDict(extra="forbid")

    request_id: str
    status: str
    sources_found: int
    sources: List[WebSourceItem] = Field(default_factory=list)
    execution_time_seconds: float = Field(ge=0.0)


# --- Modèles Agent 2 : Semantic Scholar ---

class ScientificPaperItem(BaseModel):
    """Article scientifique unitaire vérifié."""
    model_config = ConfigDict(extra="forbid")

    paper_id: str
    doi: Optional[str] = None
    title: str
    authors: List[str] = Field(default_factory=list)
    year: Optional[int] = None
    venue: Optional[str] = None
    citation_count: int = Field(default=0, ge=0)
    abstract: str
    open_access_pdf_url: Optional[str] = None


class ScholarSearchRequest(BaseModel):
    """Requête de recherche bibliographique sur Semantic Scholar."""
    model_config = ConfigDict(extra="forbid")

    request_id: str
    query: str
    fields: List[str] = Field(default_factory=lambda: [
        "title", "authors", "year", "abstract", "citationCount", "doi", "openAccessPdf"
    ])
    limit: int = Field(default=5, ge=1, le=100)
    min_year: Optional[int] = None


class ScholarSearchResponse(BaseModel):
    """Réponse de recherche académique."""
    model_config = ConfigDict(extra="forbid")

    request_id: str
    status: str
    total_papers: int
    papers: List[ScientificPaperItem] = Field(default_factory=list)
    is_authenticated_key: bool = False
    rate_limit_remaining: Optional[int] = None
    execution_time_seconds: float = Field(ge=0.0)


# --- Modèles Agent 3 : Gemini Analyst ---

class FindingItem(BaseModel):
    """Constat analytique unitaire relié à ses sources justificatives."""
    model_config = ConfigDict(extra="forbid")

    finding_id: str
    statement: str
    category: str = "general"
    supporting_source_ids: List[str] = Field(default_factory=list)
    confidence: str = "MODERATE"


class ThesisItem(BaseModel):
    """Thèse d'optimisation ou proposition formulée par l'Analyste."""
    model_config = ConfigDict(extra="forbid")

    thesis_id: str
    hypothesis: str
    scientific_rationale: str
    cited_papers: List[str] = Field(default_factory=list)
    cited_web_sources: List[str] = Field(default_factory=list)
    proposed_action: str
    requires_deterministic_validation: bool = True
    candidate_permutation: Optional[List[int]] = None


class GeminiAnalystLLMOutput(BaseModel):
    """Schéma de sortie JSON structurée pour l'inférence Gemini (Structured Outputs)."""
    model_config = ConfigDict(extra="forbid")

    general_critique: str
    confidence_level: str = "MODERATE"
    main_findings: List[FindingItem] = Field(default_factory=list)
    convergences: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    theses: List[ThesisItem] = Field(default_factory=list)


class AnalysisReportRequest(BaseModel):
    """Entrée transmise à l'Analyste pour synthèse contradictoire."""
    model_config = ConfigDict(extra="forbid")

    request_id: str
    mission_id: str
    topic: str
    project_context: Dict[str, Any]
    web_evidence: List[WebSourceItem] = Field(default_factory=list)
    academic_evidence: List[ScientificPaperItem] = Field(default_factory=list)


class AnalysisReport(BaseModel):
    """Rapport structuré d'analyse et de synthèse intelligente du Gemini Analyst."""
    model_config = ConfigDict(extra="forbid")

    mission_id: str = "mission-default"
    analysis_id: str
    agent_id: str = "gemini_analyst"
    model_id: str = "gemini-3.8-flash"
    model_name: Optional[str] = None
    execution_timestamp: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )
    input_source_ids: List[str] = Field(default_factory=list)
    main_findings: List[FindingItem] = Field(default_factory=list)
    scientific_evidence: List[str] = Field(default_factory=list)
    web_evidence: List[str] = Field(default_factory=list)
    convergences: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    confidence_level: str = "MODERATE"
    recommendations: List[str] = Field(default_factory=list)
    theses: List[ThesisItem] = Field(default_factory=list)
    general_critique: str = ""
    token_usage: TokenUsage
    estimated_cost: float = 0.0
    execution_status: str = "SUCCESS"
    execution_time_seconds: float = Field(ge=0.0, default=0.0)

    def model_post_init(self, __context: Any) -> None:
        if self.model_name is None:
            self.model_name = self.model_id
        elif not self.model_id:
            self.model_id = self.model_name


# --- Modèles Agent 4 : Judge Agent ---

class ThesisEvaluation(BaseModel):
    """Évaluation contradictoire d'une proposition par le Juge."""
    model_config = ConfigDict(extra="forbid")

    thesis_id: str
    status: VerdictStatus
    confidence_score: float = Field(ge=0.0, le=1.0)
    justification: str
    contradictions_found: List[str] = Field(default_factory=list)


class JudgeDecision(BaseModel):
    """Décision et rapport d'arbitrage formel de l'arbitre (Judge Agent)."""
    model_config = ConfigDict(extra="forbid")

    mission_id: str = "mission-default"
    judgment_id: str = Field(default_factory=lambda: f"jdg-{uuid.uuid4().hex[:8]}")
    decision_id: Optional[str] = None
    agent_id: str = "judge_agent"
    execution_timestamp: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )
    input_analysis_ids: List[str] = Field(default_factory=list)
    evaluated_source_ids: List[str] = Field(default_factory=list)
    source_reliability_assessment: str = ""
    scientific_consistency_assessment: str = ""
    evidence_quality_assessment: str = ""
    agent_consistency_assessment: str = ""
    contradictions: List[str] = Field(default_factory=list)
    resolved_contradictions: List[str] = Field(default_factory=list)
    unresolved_contradictions: List[str] = Field(default_factory=list)
    hallucination_flags: List[str] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    criterion_scores: Dict[str, float] = Field(default_factory=dict)
    weighted_score: Optional[float] = None
    decision_status: VerdictStatus = VerdictStatus.ACCEPTED
    overall_verdict: Optional[VerdictStatus] = None
    decision_rationale: str = ""
    audit_notes: str = ""
    recommendations: List[str] = Field(default_factory=list)
    evaluations: List[ThesisEvaluation] = Field(default_factory=list)
    human_review_required: bool = False
    model_id: str = "gemini-3.8-flash"
    token_usage: Optional[TokenUsage] = None
    estimated_cost: float = 0.0
    execution_status: str = "SUCCESS"
    execution_time_seconds: float = Field(ge=0.0, default=0.0)

    def model_post_init(self, __context: Any) -> None:
        if self.decision_id is None:
            self.decision_id = self.judgment_id
        elif not self.judgment_id:
            self.judgment_id = self.decision_id

        if self.overall_verdict is None:
            if self.decision_status == VerdictStatus.VALIDATION_REQUIRED:
                self.overall_verdict = VerdictStatus.ACCEPTED_PENDING_VALIDATION
            else:
                self.overall_verdict = self.decision_status
        elif self.decision_status == VerdictStatus.ACCEPTED and self.overall_verdict != VerdictStatus.ACCEPTED:
            self.decision_status = self.overall_verdict

        if not self.decision_rationale and self.audit_notes:
            self.decision_rationale = self.audit_notes
        elif not self.audit_notes and self.decision_rationale:
            self.audit_notes = self.decision_rationale


# --- Modèles Agent 5 : Validateur Déterministe ---

class ConstraintsCheck(BaseModel):
    """Contrôle mathématique des invariants du TSP d'Agadir."""
    model_config = ConfigDict(extra="forbid")

    starts_at_depot_0: bool
    ends_at_depot_0: bool
    coastal_point_40_present: bool
    total_stops_count: int
    unique_destinations_count: int
    has_duplicates: bool


class ValidationRequest(BaseModel):
    """Demande de calcul déterministe d'une tournée."""
    model_config = ConfigDict(extra="forbid")

    validation_id: str
    candidate_tour: List[int]
    claimed_distance_m: Optional[float] = None


class ValidationResult(BaseModel):
    """Certificat mathématique émis par le Validateur Déterministe Python."""
    model_config = ConfigDict(extra="forbid")

    validation_id: str
    is_valid: bool
    reference_distance_m: float = 18933.1
    recalculated_distance_m: float
    gain_m: float
    gain_pct: float
    constraints_check: ConstraintsCheck
    verified_on_matrix: str = "distance_matrix.csv"
    timestamp_utc: str
    error_message: Optional[str] = None


# --- Livrable Final de Mission ---

class FinalReport(BaseModel):
    """Livrable final consolidé par l'Orchestrateur (Mandat Phase 6.6, Section 10)."""
    model_config = ConfigDict(extra="forbid")

    mission_id: str
    execution_timestamp: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )
    workflow_status: str = "SUCCESS"
    agent_execution_statuses: Dict[str, str] = Field(default_factory=dict)
    web_research_results: Optional[Union[WebSearchResponse, Dict[str, Any]]] = None
    semantic_scholar_results: Optional[Union[ScholarSearchResponse, Dict[str, Any]]] = None
    gemini_analysis: Optional[Union[AnalysisReport, Dict[str, Any]]] = None
    judge_verdict: VerdictStatus
    deterministic_validation: Optional[ValidationResult] = None
    source_registry: List[str] = Field(default_factory=list)
    resolved_contradictions: List[str] = Field(default_factory=list)
    unresolved_contradictions: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    human_review_required: bool = False
    budget_summary: Dict[str, Any] = Field(default_factory=dict)
    audit_chain_status: Dict[str, Any] = Field(default_factory=dict)
    protected_files_integrity: Dict[str, str] = Field(default_factory=dict)
    final_execution_status: str = "COMPLETED_SUCCESS"

    # Attributs conservés pour compatibilité ascendante
    topic: str
    execution_mode: ExecutionMode
    executive_summary: str
    web_sources_consulted: int = 0
    papers_analyzed: int = 0
    theses_evaluated: int = 0
    total_execution_time_seconds: float = Field(ge=0.0, default=0.0)
    total_cost_usd: float = Field(ge=0.0, default=0.0)
    audit_trail_path: str = ""
    audit_chain_length: int = 0
    final_audit_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


# --- Audit Trail Cryptographique ---

class AuditEventRecord(BaseModel):
    """Enregistrement d'audit scellé dans la chaîne de hachage SHA-256."""
    model_config = ConfigDict(extra="forbid")

    event_index: int = Field(ge=0)
    event_id: str
    mission_id: str
    timestamp_utc: str
    agent_id: str
    action: str
    payload_summary: Dict[str, Any]
    prev_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    event_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


def get_canonical_json_bytes(data: Dict[str, Any]) -> bytes:
    """
    Retourne la sérialisation canonique JSON : clés ordonnées alphabétiquement,
    séparateurs compacts sans espaces superflus, encodée en UTF-8.
    """
    return json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf-8')


def compute_event_hash(record_dict: Dict[str, Any]) -> str:
    """
    Calcule l'empreinte SHA-256 canonique d'un événement d'audit.
    RÈGLES STRICTES :
    - Exclut formellement 'event_hash' du dictionnaire à sérialiser.
    - Inclut obligatoirement 'prev_hash' dans les clés canoniques.
    """
    canonical_dict = {k: v for k, v in record_dict.items() if k != "event_hash"}
    canonical_bytes = get_canonical_json_bytes(canonical_dict)
    return hashlib.sha256(canonical_bytes).hexdigest()
