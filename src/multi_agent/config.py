"""
Gestionnaire et validateur de configuration pour le système multi-agents AGADIR MAPPING.
Charge la configuration découplée depuis un fichier JSON indépendant et applique Pydantic v2.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

from src.multi_agent.exceptions import ConfigurationException, UnverifiedPricingException


class ModelPricing(BaseModel):
    """Tarification d'un modèle en USD par million de tokens."""
    model_config = ConfigDict(extra="forbid", strict=True)

    input: float = Field(ge=0.0, description="Coût par 1M tokens d'entrée (prompt)")
    output: float = Field(ge=0.0, description="Coût par 1M tokens de sortie (réponse + thinking)")
    cached: float = Field(ge=0.0, default=0.0, description="Coût par 1M tokens de lecture de cache")
    storage_per_hour: float = Field(ge=0.0, default=0.0, description="Coût horaire de stockage de cache par 1M tokens")


class LLMProviderConfig(BaseModel):
    """Configuration du fournisseur de modèle de langage."""
    model_config = ConfigDict(extra="forbid", strict=True)

    type: str = Field(default="google_genai")
    api_key_env_var: str = Field(default="GEMINI_API_KEY")
    default_timeout_seconds: float = Field(default=30.0, gt=0.0)
    max_retries: int = Field(default=3, ge=0)


class ModelsRegistryConfig(BaseModel):
    """Registre des modèles configurés."""
    model_config = ConfigDict(extra="forbid", strict=True)

    default_fast: str = Field(default="gemini-3.8-flash")
    advanced_reasoning: str = Field(default="gemini-4-carbon")
    fallback: str = Field(default="gemini-3.8-flash")


class SemanticScholarConfig(BaseModel):
    """Configuration du connecteur Semantic Scholar."""
    model_config = ConfigDict(extra="forbid", strict=True)

    api_endpoint: str = Field(default="https://api.semanticscholar.org/graph/v1")
    api_key_env_var: str = Field(default="SEMANTIC_SCHOLAR_API_KEY")
    max_retries: int = Field(default=3, ge=0)
    backoff_base_seconds: float = Field(default=2.0, gt=0.0)
    rate_limit_delay_seconds: float = Field(default=1.1, gt=0.0)
    batch_size_limit: int = Field(default=500, gt=0, le=1000)
    cache_ttl_days: int = Field(default=30, gt=0)


class WebResearchConfig(BaseModel):
    """Configuration du connecteur Web Research."""
    model_config = ConfigDict(extra="forbid", strict=True)

    engine: str = Field(default="duckduckgo_lite")
    timeout_seconds: float = Field(default=15.0, gt=0.0)
    max_queries_per_mission: int = Field(default=5, gt=0)
    delay_between_queries_seconds: float = Field(default=2.0, ge=0.0)
    cache_ttl_days: int = Field(default=7, gt=0)


class BudgetGuardrailsConfig(BaseModel):
    """Garde-fous budgétaires et disjoncteurs financiers."""
    model_config = ConfigDict(extra="forbid", strict=True)

    warning_threshold_usd: float = Field(default=0.10, gt=0.0)
    kill_switch_usd: float = Field(default=0.50, gt=0.0)
    pre_allocation_check: bool = Field(default=True)
    fail_closed_if_unverified: bool = Field(default=True)
    max_output_tokens_default: int = Field(default=2048, gt=0)

    @field_validator("kill_switch_usd")
    @classmethod
    def validate_thresholds(cls, v: float, info) -> float:
        warning = info.data.get("warning_threshold_usd", 0.10)
        if v <= warning:
            raise ValueError(f"kill_switch_usd ({v}) doit être strictement supérieur à warning_threshold_usd ({warning})")
        return v


class SecurityConfig(BaseModel):
    """Configuration de la sécurité et de la traçabilité."""
    model_config = ConfigDict(extra="forbid", strict=True)

    audit_trail_dir: str = Field(default="outputs/audit")
    audit_sqlite_db: str = Field(default="outputs/audit/orchestrator_audit.db")
    fingerprints_file: str = Field(default="outputs/audit/mission_fingerprints.json")
    protected_files: List[str] = Field(default_factory=lambda: [
        "data/processed/delivery_points_40.csv",
        "data/processed/distance_matrix.csv",
        "data/processed/duration_matrix.csv",
        "data/results/tsp_optimized_route.json"
    ])


class MultiAgentConfig(BaseModel):
    """Configuration racine du système multi-agents."""
    model_config = ConfigDict(extra="forbid", strict=True)

    system_version: str = Field(default="6.2.0")
    project_name: str = Field(default="AGADIR MAPPING — Multi-Agent System")
    environment: str = Field(default="development")
    llm_provider: LLMProviderConfig = Field(default_factory=LLMProviderConfig)
    models: ModelsRegistryConfig = Field(default_factory=ModelsRegistryConfig)
    pricing_per_million_tokens: Dict[str, ModelPricing] = Field(default_factory=dict)
    semantic_scholar: SemanticScholarConfig = Field(default_factory=SemanticScholarConfig)
    web_research: WebResearchConfig = Field(default_factory=WebResearchConfig)
    budget_guardrails: BudgetGuardrailsConfig = Field(default_factory=BudgetGuardrailsConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    def get_pricing_for_model(self, model_name: str) -> ModelPricing:
        """
        Récupère la tarification vérifiée pour un modèle donné.
        En mode fail-closed, lève UnverifiedPricingException si le modèle est inconnu.
        """
        if model_name in self.pricing_per_million_tokens:
            return self.pricing_per_million_tokens[model_name]
        
        if self.budget_guardrails.fail_closed_if_unverified:
            raise UnverifiedPricingException(
                f"Modèle '{model_name}' non répertorié dans la table des tarifs vérifiés. "
                "Politique Fail-Closed active : appel interdit."
            )
        raise ConfigurationException(f"Tarification manquante pour le modèle '{model_name}'.")


def load_multi_agent_config(config_path: Optional[Path | str] = None) -> MultiAgentConfig:
    """
    Charge et valide la configuration multi-agents depuis le fichier JSON découplé.
    Prend en compte les surcharges éventuelles par variables d'environnement.
    """
    if config_path is None:
        # Chemin par défaut : config/multi_agent_config.json
        base_dir = Path(__file__).resolve().parent.parent.parent
        config_path = base_dir / "config" / "multi_agent_config.json"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise ConfigurationException(f"Fichier de configuration introuvable : {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except Exception as e:
        raise ConfigurationException(f"Erreur lors de la lecture du fichier JSON {config_path}: {e}")

    try:
        config = MultiAgentConfig.model_validate(raw_data)
    except Exception as e:
        raise ConfigurationException(f"Erreur de validation de la configuration multi-agents : {e}")

    # Prise en compte des surcharges d'environnement si présentes
    env_fast_model = os.getenv("GEMINI_FAST_MODEL")
    if env_fast_model:
        config.models.default_fast = env_fast_model

    env_pro_model = os.getenv("GEMINI_PRO_MODEL")
    if env_pro_model:
        config.models.advanced_reasoning = env_pro_model

    return config
