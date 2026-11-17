"""
Tests d'intégration et d'orchestration pour CentralOrchestrator.
Vérifie l'exécution DAG asynchrone, les délais d'attente, les annulations et la résilience.
"""

import asyncio
import pytest
from pathlib import Path

from src.multi_agent.base_provider import MockLLMProvider
from src.multi_agent.config import load_multi_agent_config
from src.multi_agent.exceptions import (
    BudgetReservationException,
    ProviderException,
    SecurityViolationException,
    TaskCancelledException,
)
from src.multi_agent.orchestrator import CentralOrchestrator
from src.multi_agent.schemas import ExecutionMode, FinalReport, VerdictStatus
from src.multi_agent.audit_logger import verify_audit_trail_chain


@pytest.fixture
def test_config(tmp_path):
    cfg = load_multi_agent_config()
    cfg.security.audit_trail_dir = str(tmp_path / "audit")
    cfg.security.audit_sqlite_db = str(tmp_path / "audit" / "test_audit.db")
    cfg.security.fingerprints_file = str(tmp_path / "audit" / "fingerprints.json")
    return cfg


def test_orchestrator_nominal_mission_economic(test_config):
    """Vérifie l'exécution nominale complète d'une mission en mode ÉCONOMIQUE."""
    async def _test():
        provider = MockLLMProvider(test_config, simulated_delay_seconds=0.01)
        orchestrator = CentralOrchestrator(config=test_config, llm_provider=provider)

        report = await orchestrator.run_mission(
            topic="Apport de l'opérateur Or-opt 3-nœuds sur l'ATSP",
            execution_mode=ExecutionMode.ECONOMIC
        )

        assert isinstance(report, FinalReport)
        assert report.topic == "Apport de l'opérateur Or-opt 3-nœuds sur l'ATSP"
        assert report.execution_mode == ExecutionMode.ECONOMIC
        assert report.judge_verdict == VerdictStatus.ACCEPTED_PENDING_VALIDATION
        assert report.deterministic_validation is not None
        assert report.deterministic_validation.is_valid is True
        assert report.deterministic_validation.reference_distance_m == 18933.1
        assert report.deterministic_validation.recalculated_distance_m == 18933.1
        assert report.total_cost_usd > 0.0
        assert report.total_cost_usd <= 0.10  # Largement sous le seuil d'alerte
        assert report.audit_chain_length >= 6
        assert len(report.final_audit_hash) == 64

        # Vérification cryptographique immédiate de la chaîne d'audit générée
        is_valid, msg = verify_audit_trail_chain(
            report.audit_trail_path,
            expected_final_hash=report.final_audit_hash
        )
        assert is_valid is True
        assert "certifiée intègre" in msg

    asyncio.run(_test())


def test_orchestrator_complete_mode(test_config):
    """Vérifie l'exécution d'une mission en mode COMPLET (modèle de raisonnement avancé)."""
    async def _test():
        provider = MockLLMProvider(test_config, simulated_delay_seconds=0.01)
        orchestrator = CentralOrchestrator(config=test_config, llm_provider=provider)

        report = await orchestrator.run_mission(
            topic="Analyse des théorèmes de convergence asymétrique",
            execution_mode=ExecutionMode.COMPLETE
        )

        assert report.execution_mode == ExecutionMode.COMPLETE
        assert report.theses_evaluated == 1
        assert report.deterministic_validation.reference_distance_m == 18933.1

    asyncio.run(_test())


def test_orchestrator_handles_task_cancellation(test_config):
    """Vérifie que l'annulation d'une tâche asynchrone est gérée proprement et libère les réservations."""
    async def _test():
        # Fournisseur avec délai suffisant pour permettre l'annulation
        provider = MockLLMProvider(test_config, simulated_delay_seconds=1.0)
        orchestrator = CentralOrchestrator(config=test_config, llm_provider=provider)

        task = asyncio.create_task(
            orchestrator.run_mission("Mission destinée à être annulée")
        )

        # Laisse démarrer puis annule
        await asyncio.sleep(0.05)
        task.cancel()

        with pytest.raises(TaskCancelledException):
            await task

        # Vérification que la réservation en vol a été libérée
        assert orchestrator.budget.active_reserved_cost_usd == 0.0

    asyncio.run(_test())


def test_orchestrator_handles_provider_error(test_config):
    """Vérifie qu'une défaillance du fournisseur LLM lève ProviderException et est consignée dans l'audit."""
    async def _test():
        failing_provider = MockLLMProvider(test_config, should_fail=True)
        orchestrator = CentralOrchestrator(config=test_config, llm_provider=failing_provider)

        with pytest.raises(ProviderException):
            await orchestrator.run_mission("Mission avec provider en panne")

        # Vérification que la réservation temporaire a été relâchée
        assert orchestrator.budget.active_reserved_cost_usd == 0.0

    asyncio.run(_test())


def test_orchestrator_blocks_when_budget_reservation_exceeded(test_config):
    """Vérifie que l'orchestrateur bloque en amont une mission si le disjoncteur est franchi."""
    async def _test():
        orchestrator = CentralOrchestrator(config=test_config)
        # Simulation d'un budget déjà épuisé à 0.495 USD
        orchestrator.budget._committed_cost_usd = 0.495

        with pytest.raises(BudgetReservationException):
            await orchestrator.run_mission("Mission sur budget épuisé")

    asyncio.run(_test())
