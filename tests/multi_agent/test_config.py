"""
Tests unitaires pour le chargeur et validateur de configuration découplée.
Vérifie la robustesse de Pydantic v2 et la politique fail-closed.
"""

import json
import os
import pytest
from pathlib import Path
from pydantic import ValidationError

from src.multi_agent.config import (
    MultiAgentConfig,
    ModelPricing,
    load_multi_agent_config,
)
from src.multi_agent.exceptions import (
    ConfigurationException,
    UnverifiedPricingException,
)


def test_load_default_config():
    """Vérifie le chargement nominal du fichier de configuration par défaut."""
    config = load_multi_agent_config()
    assert isinstance(config, MultiAgentConfig)
    assert config.system_version == "6.2.0"
    assert config.models.default_fast == "gemini-3.8-flash"
    assert config.models.advanced_reasoning == "gemini-4-carbon"
    assert config.budget_guardrails.warning_threshold_usd == 0.10
    assert config.budget_guardrails.kill_switch_usd == 0.50
    assert config.budget_guardrails.fail_closed_if_unverified is True


def test_pricing_lookup_and_fail_closed():
    """Vérifie que les modèles connus retournent leur tarif et les inconnus lèvent UnverifiedPricingException."""
    config = load_multi_agent_config()
    
    # Modèle connu
    pricing = config.get_pricing_for_model("gemini-3.8-flash")
    assert isinstance(pricing, ModelPricing)
    assert pricing.input == 0.75
    assert pricing.output == 3.75
    assert pricing.cached == 0.075

    # Modèle inconnu -> Fail-closed
    with pytest.raises(UnverifiedPricingException) as exc_info:
        config.get_pricing_for_model("unknown-obscure-model-v9")
    assert "Politique Fail-Closed active" in str(exc_info.value)


def test_missing_config_file_raises():
    """Vérifie qu'un chemin inexistant lève une ConfigurationException."""
    with pytest.raises(ConfigurationException) as exc_info:
        load_multi_agent_config("/path/to/non_existent_config_file.json")
    assert "introuvable" in str(exc_info.value)


def test_invalid_kill_switch_threshold_raises(tmp_path):
    """Vérifie que kill_switch <= warning_threshold est rejeté par validation Pydantic."""
    bad_data = {
        "budget_guardrails": {
            "warning_threshold_usd": 0.50,
            "kill_switch_usd": 0.20  # Invalide : inférieur à warning
        }
    }
    bad_file = tmp_path / "bad_config.json"
    bad_file.write_text(json.dumps(bad_data), encoding="utf-8")

    with pytest.raises(ConfigurationException):
        load_multi_agent_config(bad_file)


def test_extra_fields_forbidden(tmp_path):
    """Vérifie que les champs non documentés sont interdits (extra='forbid')."""
    bad_data = {
        "unknown_rogue_parameter": "illegal_value"
    }
    bad_file = tmp_path / "rogue_config.json"
    bad_file.write_text(json.dumps(bad_data), encoding="utf-8")

    with pytest.raises(ConfigurationException):
        load_multi_agent_config(bad_file)


def test_env_var_overrides(monkeypatch):
    """Vérifie la surcharge des modèles via variables d'environnement."""
    monkeypatch.setenv("GEMINI_FAST_MODEL", "custom-fast-test")
    monkeypatch.setenv("GEMINI_PRO_MODEL", "custom-pro-test")

    config = load_multi_agent_config()
    assert config.models.default_fast == "custom-fast-test"
    assert config.models.advanced_reasoning == "custom-pro-test"
