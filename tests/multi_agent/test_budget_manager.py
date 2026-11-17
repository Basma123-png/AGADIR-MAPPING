"""
Tests unitaires pour le gestionnaire de budget et le disjoncteur financier à réservation préalable.
Vérifie la concurrence atomique, les seuils d'alerte/coupure et la politique fail-closed.
"""

import asyncio
import pytest

from src.multi_agent.budget_manager import BudgetManager
from src.multi_agent.config import load_multi_agent_config
from src.multi_agent.exceptions import (
    BudgetExceededException,
    BudgetReservationException,
    UnverifiedPricingException,
)
from src.multi_agent.schemas import TokenUsage


@pytest.fixture
def config():
    return load_multi_agent_config()


@pytest.fixture
def budget_manager(config):
    return BudgetManager(config)


def test_nominal_budget_reservation_and_commit(budget_manager):
    """Vérifie le cycle nominal : réservation -> commit réel -> mise à jour du budget."""
    async def _test():
        assert budget_manager.committed_cost_usd == 0.0
        assert budget_manager.active_reserved_cost_usd == 0.0

        # Réservation de 1 000 prompt tokens et 2 000 max output tokens sur gemini-3.8-flash
        res_id = await budget_manager.reserve_budget(
            model="gemini-3.8-flash",
            prompt_tokens_est=1000,
            max_output_tokens=2000
        )
        assert res_id.startswith("res_")
        assert budget_manager.active_reserved_cost_usd > 0.0

        # Consommation réelle : 800 prompt, 400 completion, dont 100 thinking
        usage = TokenUsage(
            prompt_tokens=800,
            completion_tokens=400,
            thinking_tokens=100,
            cached_tokens=0
        )
        actual_cost = await budget_manager.commit_usage(res_id, "gemini-3.8-flash", usage)

        assert actual_cost > 0.0
        assert budget_manager.active_reserved_cost_usd == 0.0
        assert budget_manager.committed_cost_usd == actual_cost
        assert usage.total_cost_usd == actual_cost

    asyncio.run(_test())


def test_budget_reservation_exceeds_kill_switch_blocked_upfront(budget_manager):
    """Vérifie qu'une réservation dépassant 0.50 USD est bloquée AVANT l'émission réseau."""
    async def _test():
        # Sur gemini-4-carbon (10$/1M output), 60 000 output tokens = 0.60$ > 0.50$
        with pytest.raises(BudgetReservationException) as exc_info:
            await budget_manager.reserve_budget(
                model="gemini-4-carbon",
                prompt_tokens_est=10000,
                max_output_tokens=60000
            )
        assert "excède le disjoncteur strict" in str(exc_info.value)
        # Vérifie qu'aucune réservation n'a été conservée
        assert budget_manager.active_reserved_cost_usd == 0.0

    asyncio.run(_test())


def test_concurrent_budget_reservations_atomic(budget_manager):
    """Vérifie la robustesse en environnement concurrent : les réservations parallèles ne peuvent dépasser 0.50 USD."""
    async def _test():
        async def try_reserve():
            try:
                return await budget_manager.reserve_budget(
                    model="gemini-4-carbon",
                    prompt_tokens_est=5000,
                    max_output_tokens=7000
                )
            except BudgetReservationException:
                return None

        results = await asyncio.gather(*(try_reserve() for _ in range(12)))
        successes = [r for r in results if r is not None]
        failures = [r for r in results if r is None]

        assert len(successes) > 0
        assert len(failures) > 0  # Des requêtes ont été bloquées
        assert budget_manager.total_allocated_cost_usd <= 0.50

    asyncio.run(_test())


def test_warning_threshold_trigger(budget_manager):
    """Vérifie que le seuil d'avertissement à 0.10 USD est détecté."""
    async def _test():
        assert budget_manager.is_warning_exceeded is False

        res_id = await budget_manager.reserve_budget("gemini-4-carbon", 1000, 15000)
        # Consommation réelle de 12 000 tokens output à 10$/1M = 0.12 USD > 0.10 USD
        usage = TokenUsage(prompt_tokens=1000, completion_tokens=12000)
        await budget_manager.commit_usage(res_id, "gemini-4-carbon", usage)

        assert budget_manager.is_warning_exceeded is True
        assert budget_manager.is_kill_switch_exceeded is False

    asyncio.run(_test())


def test_kill_switch_trigger_on_commit(budget_manager):
    """Vérifie que si la consommation réelle atteint 0.50 USD, BudgetExceededException est levée."""
    async def _test():
        res_id = await budget_manager.reserve_budget("gemini-4-carbon", 1000, 48000)
        # Consommation de 52 000 output tokens = 0.52 USD > 0.50 USD
        usage = TokenUsage(prompt_tokens=1000, completion_tokens=52000)

        with pytest.raises(BudgetExceededException) as exc_info:
            await budget_manager.commit_usage(res_id, "gemini-4-carbon", usage)
        assert "disjoncteur financier a été déclenché" in str(exc_info.value)
        assert budget_manager.is_kill_switch_exceeded is True

    asyncio.run(_test())


def test_release_reservation(budget_manager):
    """Vérifie la libération d'une réservation en cas d'annulation."""
    async def _test():
        res_id = await budget_manager.reserve_budget("gemini-3.8-flash", 2000, 2000)
        assert budget_manager.active_reserved_cost_usd > 0.0

        await budget_manager.release_reservation(res_id)
        assert budget_manager.active_reserved_cost_usd == 0.0
        assert budget_manager.committed_cost_usd == 0.0

    asyncio.run(_test())


def test_unverified_model_fails_closed(budget_manager):
    """Vérifie que réserver sur un modèle inconnu sans tarif lève immédiatement UnverifiedPricingException."""
    async def _test():
        with pytest.raises(UnverifiedPricingException):
            await budget_manager.reserve_budget("unknown-model", 1000, 1000)

    asyncio.run(_test())
