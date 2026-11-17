"""
Module Interface — Phase 7 du projet AGADIR MAPPING.
Expose le serveur HTTP et les services de données pour le tableau de bord à 4 cadrans.
"""

from src.interface.api_service import DashboardDataService
from src.interface.server import create_server, run_server

__all__ = ["DashboardDataService", "create_server", "run_server"]
