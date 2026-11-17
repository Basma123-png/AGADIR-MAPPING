"""
Gestionnaire de budget et disjoncteur financier avec réservation préalable atomique.
Empêche tout dépassement du seuil de 0,50 USD et applique une politique fail-closed.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Dict, Optional

from src.multi_agent.config import MultiAgentConfig, ModelPricing
from src.multi_agent.exceptions import (
    BudgetExceededException,
    BudgetReservationException,
    UnverifiedPricingException,
)
from src.multi_agent.schemas import TokenUsage

logger = logging.getLogger("agadir.multi_agent.budget")


class BudgetManager:
    """
    Gestionnaire budgétaire thread/coroutine-safe pour les requêtes d'inférence LLM.
    Gère la réservation préalable du coût pire-cas et l'engagement définitif de la consommation.
    """

    def __init__(self, config: MultiAgentConfig):
        self.config = config
        self.warning_threshold_usd: float = config.budget_guardrails.warning_threshold_usd
        self.kill_switch_usd: float = config.budget_guardrails.kill_switch_usd
        self.fail_closed: bool = config.budget_guardrails.fail_closed_if_unverified

        self._committed_cost_usd: float = 0.0
        self._active_reservations: Dict[str, float] = {}
        self._lock = asyncio.Lock()
        self._warning_emitted: bool = False

    @property
    def committed_cost_usd(self) -> float:
        """Coût réel total engagé et consommé."""
        return self._committed_cost_usd

    @property
    def active_reserved_cost_usd(self) -> float:
        """Total des réservations temporaires actives pour les requêtes en vol."""
        return sum(self._active_reservations.values())

    @property
    def total_allocated_cost_usd(self) -> float:
        """Somme du coût engagé et des réservations actives."""
        return self._committed_cost_usd + self.active_reserved_cost_usd

    @property
    def is_warning_exceeded(self) -> bool:
        """Indique si le seuil d'avertissement (0.10 USD) a été franchi."""
        return self._committed_cost_usd >= self.warning_threshold_usd

    @property
    def is_kill_switch_exceeded(self) -> bool:
        """Indique si le disjoncteur strict (0.50 USD) a été franchi."""
        return self._committed_cost_usd >= self.kill_switch_usd

    def calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        thinking_tokens: int = 0,
        cached_tokens: int = 0,
        tool_cost_usd: float = 0.0
    ) -> float:
        """
        Calcule le coût théorique d'un volume de tokens selon le barème officiel du modèle.
        Note : thinking_tokens est inclus dans les tokens facturés au tarif output.
        """
        pricing: ModelPricing = self.config.get_pricing_for_model(model)

        # Les tokens de sortie incluent les tokens de réponse générés et les tokens de réflexion (thinking)
        effective_output_tokens = completion_tokens + thinking_tokens

        prompt_cost = (prompt_tokens * pricing.input) / 1_000_000.0
        output_cost = (effective_output_tokens * pricing.output) / 1_000_000.0
        cached_cost = (cached_tokens * pricing.cached) / 1_000_000.0

        return prompt_cost + output_cost + cached_cost + tool_cost_usd

    async def reserve_budget(
        self,
        model: str,
        prompt_tokens_est: int,
        max_output_tokens: Optional[int] = None,
        tool_cost_est: float = 0.0
    ) -> str:
        """
        Réserve atomiquement le montant maximal estimé avant d'émettre la requête vers l'API.
        Lève BudgetReservationException si l'enveloppe réservée dépasse le kill switch (0.50 USD).
        """
        if max_output_tokens is None:
            max_output_tokens = self.config.budget_guardrails.max_output_tokens_default

        # Vérification tarifaire préalable
        pricing = self.config.get_pricing_for_model(model)

        # Calcul pire-cas de la requête
        estimated_cost = self.calculate_cost(
            model=model,
            prompt_tokens=prompt_tokens_est,
            completion_tokens=max_output_tokens,
            thinking_tokens=0,
            cached_tokens=0,
            tool_cost_usd=tool_cost_est
        )

        async with self._lock:
            potential_total = self.total_allocated_cost_usd + estimated_cost
            if potential_total > self.kill_switch_usd:
                logger.error(
                    f"[DISJONCTEUR PRÉVENTIF] Requête bloquée en amont : coût cumulé ({self._committed_cost_usd:.4f}$) "
                    f"+ réservations en vol ({self.active_reserved_cost_usd:.4f}$) "
                    f"+ nouvelle réservation ({estimated_cost:.4f}$) = {potential_total:.4f}$ "
                    f"> Seuil strict ({self.kill_switch_usd:.2f}$)."
                )
                raise BudgetReservationException(
                    f"Réservation budgétaire refusée : {potential_total:.4f} USD excède le disjoncteur strict "
                    f"de {self.kill_switch_usd:.2f} USD."
                )

            reservation_id = f"res_{uuid.uuid4().hex[:12]}"
            self._active_reservations[reservation_id] = estimated_cost
            logger.debug(
                f"[BUDGET RESERVE] {reservation_id} : {estimated_cost:.5f}$ pour {model}. "
                f"Total alloué : {self.total_allocated_cost_usd:.4f}$"
            )
            return reservation_id

    async def commit_usage(
        self,
        reservation_id: str,
        model: str,
        usage: TokenUsage
    ) -> float:
        """
        Libère la réservation et enregistre la dépense réelle exacte.
        Lève BudgetExceededException si le coût cumulé franchit le kill switch.
        """
        actual_cost = self.calculate_cost(
            model=model,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            thinking_tokens=usage.thinking_tokens,
            cached_tokens=usage.cached_tokens,
            tool_cost_usd=usage.tool_cost_usd
        )
        usage.total_cost_usd = actual_cost

        async with self._lock:
            # Libération de la réservation préalable
            if reservation_id in self._active_reservations:
                del self._active_reservations[reservation_id]

            self._committed_cost_usd += actual_cost

            # Vérification du seuil d'avertissement
            if self.is_warning_exceeded and not self._warning_emitted:
                self._warning_emitted = True
                logger.warning(
                    f"[ALERTE BUDGET] Le coût cumulé de la mission ({self._committed_cost_usd:.4f}$) "
                    f"a franchi le seuil d'avertissement de {self.warning_threshold_usd:.2f} USD."
                )

            # Vérification du disjoncteur strict
            if self.is_kill_switch_exceeded:
                logger.critical(
                    f"[DISJONCTEUR FINANCIER DÉCLENCHÉ] Coût cumulé ({self._committed_cost_usd:.4f}$) "
                    f">= Seuil de coupure ({self.kill_switch_usd:.2f} USD). Arrêt immédiat."
                )
                raise BudgetExceededException(
                    f"Le disjoncteur financier a été déclenché : {self._committed_cost_usd:.4f} USD "
                    f">= {self.kill_switch_usd:.2f} USD."
                )

            logger.info(
                f"[BUDGET COMMIT] Requête {reservation_id} engagée : {actual_cost:.5f}$ "
                f"(Cumul réel : {self._committed_cost_usd:.4f}$)"
            )
            return actual_cost

    async def release_reservation(self, reservation_id: str) -> None:
        """Libère une réservation en cas d'échec ou d'annulation sans impacter le budget réel."""
        async with self._lock:
            if reservation_id in self._active_reservations:
                released_amt = self._active_reservations.pop(reservation_id)
                logger.debug(f"[BUDGET RELEASE] {reservation_id} annulée ({released_amt:.5f}$).")
