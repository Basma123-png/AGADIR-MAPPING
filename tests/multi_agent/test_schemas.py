"""
Tests unitaires pour les schémas d'interface Pydantic v2 et la sérialisation canonique.
"""

import json
import pytest
from pydantic import ValidationError

from src.multi_agent.schemas import (
    AnalysisReport,
    AuditEventRecord,
    FinalReport,
    FindingItem,
    GeminiAnalystLLMOutput,
    JudgeDecision,
    ThesisItem,
    TokenUsage,
    ValidationResult,
    VerdictStatus,
    compute_event_hash,
    get_canonical_json_bytes,
)


def test_token_usage_validation():
    """Vérifie le modèle TokenUsage et ses contraintes strictes."""
    usage = TokenUsage(
        prompt_tokens=1000,
        completion_tokens=500,
        thinking_tokens=200,
        cached_tokens=100,
        tool_cost_usd=0.01,
        total_cost_usd=0.05
    )
    assert usage.prompt_tokens == 1000
    assert usage.thinking_tokens == 200

    # Valeur négative interdite
    with pytest.raises(ValidationError):
        TokenUsage(prompt_tokens=-5)

    # Champ non documenté interdit
    with pytest.raises(ValidationError):
        TokenUsage(prompt_tokens=10, rogue_field=123)


def test_canonical_json_determinism():
    """Vérifie que get_canonical_json_bytes est strictement indépendant de l'ordre d'insertion."""
    dict_a = {"b": 2, "a": 1, "c": {"y": 20, "x": 10}}
    dict_b = {"a": 1, "c": {"x": 10, "y": 20}, "b": 2}

    bytes_a = get_canonical_json_bytes(dict_a)
    bytes_b = get_canonical_json_bytes(dict_b)

    assert bytes_a == bytes_b
    assert b" " not in bytes_a  # Pas d'espaces superflus


def test_compute_event_hash_excludes_event_hash_and_includes_prev_hash():
    """Vérifie que le calcul de hash ignore le champ event_hash et dépend de prev_hash."""
    base_data = {
        "event_index": 0,
        "event_id": "evt-001",
        "mission_id": "mission-01",
        "timestamp_utc": "2026-11-16T22:00:00Z",
        "agent_id": "orchestrator",
        "action": "START",
        "payload_summary": {"k": "v"},
        "prev_hash": "0" * 64,
        "event_hash": "dummy_old_hash_to_be_ignored"
    }

    hash_1 = compute_event_hash(base_data)

    # Changer la valeur de event_hash ne doit RIEN changer au hash calculé
    base_data["event_hash"] = "another_arbitrary_value"
    hash_2 = compute_event_hash(base_data)
    assert hash_1 == hash_2

    # Changer prev_hash DOIT modifier le hash calculé
    base_data["prev_hash"] = "1" * 64
    hash_3 = compute_event_hash(base_data)
    assert hash_1 != hash_3


def test_audit_event_record_strict_sha256_pattern():
    """Vérifie que AuditEventRecord exige des hashes hexadécimaux stricts de 64 caractères."""
    valid_record = AuditEventRecord(
        event_index=0,
        event_id="evt-1",
        mission_id="m-1",
        timestamp_utc="2026-11-16T22:00:00Z",
        agent_id="orchestrator",
        action="TEST",
        payload_summary={},
        prev_hash="0" * 64,
        event_hash="a" * 64
    )
    assert valid_record.event_index == 0

    # Hash trop court (invalide)
    with pytest.raises(ValidationError):
        AuditEventRecord(
            event_index=0,
            event_id="evt-1",
            mission_id="m-1",
            timestamp_utc="2026-11-16T22:00:00Z",
            agent_id="orchestrator",
            action="TEST",
            payload_summary={},
            prev_hash="0" * 32,  # 32 au lieu de 64
            event_hash="a" * 64
        )


def test_analysis_report_schema_and_structured_output():
    """Vérifie le modèle enrichi AnalysisReport et la sortie GeminiAnalystLLMOutput."""
    finding = FindingItem(
        finding_id="F-10",
        statement="La matrice asymétrique interdit l'usage du 2-opt symétrique classique.",
        category="atsp",
        supporting_source_ids=["WEB-01", "10.1016/j.cor.2022.105842"],
        confidence="HIGH"
    )
    assert finding.finding_id == "F-10"
    assert finding.confidence == "HIGH"

    thesis = ThesisItem(
        thesis_id="TH-01",
        hypothesis="Or-opt améliore le parcours sans inverser les arcs",
        scientific_rationale="Théorème de relocalisation orientée",
        proposed_action="Appliquer Or-opt",
        requires_deterministic_validation=True
    )

    llm_output = GeminiAnalystLLMOutput(
        general_critique="Synthèse rigoureuse sans hallucination.",
        confidence_level="HIGH",
        main_findings=[finding],
        convergences=["Convergence prouvée sur ATSP."],
        contradictions=["Certaines sources négligent l'asymétrie."],
        limitations=["Pas d'horodatage fin."],
        uncertainties=["Trafic côtier fluctuant."],
        missing_information=["Altitudes fines."],
        recommendations=["Garder 18 933,1 m certifiée."],
        theses=[thesis]
    )
    assert len(llm_output.main_findings) == 1
    assert llm_output.confidence_level == "HIGH"

    token_usage = TokenUsage(prompt_tokens=100, completion_tokens=50, thinking_tokens=20)
    report = AnalysisReport(
        mission_id="m-test-01",
        analysis_id="ana-test-01",
        agent_id="gemini_analyst",
        model_id="gemini-3.8-flash",
        input_source_ids=["WEB-01", "10.1016/j.cor.2022.105842"],
        main_findings=[finding],
        scientific_evidence=["Article ATSP"],
        web_evidence=["Source Web"],
        convergences=llm_output.convergences,
        contradictions=llm_output.contradictions,
        limitations=llm_output.limitations,
        uncertainties=llm_output.uncertainties,
        missing_information=llm_output.missing_information,
        confidence_level=llm_output.confidence_level,
        recommendations=llm_output.recommendations,
        theses=[thesis],
        general_critique=llm_output.general_critique,
        token_usage=token_usage,
        estimated_cost=0.0001,
        execution_status="SUCCESS",
        execution_time_seconds=0.15
    )

    assert report.model_name == "gemini-3.8-flash"  # auto-aliasing vérifié
    assert report.theses[0].thesis_id == "TH-01"
    assert len(report.main_findings) == 1
    assert report.execution_status == "SUCCESS"

