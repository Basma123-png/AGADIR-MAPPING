"""
Exceptions personnalisées pour le système multi-agents AGADIR MAPPING.
Hiérarchie d'exceptions typée pour la gestion robuste des erreurs et des politiques fail-closed.
"""


class MultiAgentException(Exception):
    """Exception racine pour tous les modules multi-agents."""
    pass


class ConfigurationException(MultiAgentException):
    """Levée en cas d'erreur de chargement ou de validation de la configuration."""
    pass


class SchemaValidationException(MultiAgentException):
    """Levée lors d'un non-respect strict des schémas Pydantic v2."""
    pass


class BudgetException(MultiAgentException):
    """Exception de base pour les incidents budgétaires."""
    pass


class BudgetExceededException(BudgetException):
    """Levée lorsque le coût cumulé réel franchit le disjoncteur strict (kill switch à 0.50 USD)."""
    pass


class BudgetReservationException(BudgetException):
    """Levée lorsque la réservation préalable estimée excède le budget autorisé."""
    pass


class UnverifiedPricingException(BudgetException):
    """Levée en mode Fail-Closed lorsqu'un modèle ne dispose pas d'un tarif vérifié."""
    pass


class NetworkTimeoutException(MultiAgentException):
    """Levée lors de l'expiration d'un délai d'attente réseau."""
    pass


class ProviderException(MultiAgentException):
    """Levée en cas d'erreur du fournisseur LLM ou d'API externe."""
    pass


class AuditIntegrityException(MultiAgentException):
    """Levée en cas de détection d'une rupture ou falsification dans l'audit trail."""
    pass


class SecurityViolationException(MultiAgentException):
    """Levée en cas d'altération détectée des fichiers de référence ou de tentative d'écriture interdite."""
    pass


class TaskCancelledException(MultiAgentException):
    """Levée lorsqu'une tâche asynchrone est annulée."""
    pass
