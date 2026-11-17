"""
Package multi-agents AGADIR MAPPING.
Socle d'orchestration, configuration découplée et traçabilité cryptographique.
"""

from src.multi_agent.config import MultiAgentConfig, load_multi_agent_config
from src.multi_agent.budget_manager import BudgetManager
from src.multi_agent.audit_logger import AuditLogger, verify_audit_trail_chain
from src.multi_agent.security import SecurityValidator
from src.multi_agent.base_provider import BaseLLMProvider, MockLLMProvider
from src.multi_agent.orchestrator import CentralOrchestrator
from src.multi_agent.exceptions import (
    MultiAgentException,
    BudgetException,
    BudgetExceededException,
    BudgetReservationException,
    UnverifiedPricingException,
    ConfigurationException,
    SchemaValidationException,
    AuditIntegrityException,
    SecurityViolationException,
)
from src.multi_agent.schemas import (
    FinalReport,
    AnalysisReport,
    JudgeDecision,
    ValidationResult,
    VerdictStatus,
    ExecutionMode,
    TokenUsage,
)

__all__ = [
    "MultiAgentConfig",
    "load_multi_agent_config",
    "BudgetManager",
    "AuditLogger",
    "verify_audit_trail_chain",
    "SecurityValidator",
    "BaseLLMProvider",
    "MockLLMProvider",
    "CentralOrchestrator",
    "MultiAgentException",
    "BudgetException",
    "BudgetExceededException",
    "BudgetReservationException",
    "UnverifiedPricingException",
    "ConfigurationException",
    "SchemaValidationException",
    "AuditIntegrityException",
    "SecurityViolationException",
    "FinalReport",
    "AnalysisReport",
    "JudgeDecision",
    "ValidationResult",
    "VerdictStatus",
    "ExecutionMode",
    "TokenUsage",
]
