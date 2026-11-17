"""
Serveur HTTP multi-threadé pour le tableau de bord à quatre cadrans AGADIR MAPPING.
Sert l'application Single Page (HTML5/CSS3/JavaScript) et expose l'API REST en lecture seule.
"""

from __future__ import annotations

import datetime
import json
import logging
import mimetypes
import os
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

from src.interface.api_service import DashboardDataService

logger = logging.getLogger("agadir.interface.server")

STATIC_DIR = Path(__file__).resolve().parent / "static"


class DashboardRequestHandler(BaseHTTPRequestHandler):
    """Gestionnaire de requêtes HTTP pour l'interface de visualisation."""

    data_service = DashboardDataService()

    def do_OPTIONS(self):
        """Répond aux requêtes de pré-vol CORS."""
        self.send_response(HTTPStatus.OK)
        self._send_cors_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        """Achemine les requêtes GET vers l'API REST ou les fichiers statiques."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        # 1. Routes API REST
        if path.startswith("/api/"):
            self._handle_api_route(path)
            return

        # 2. Servir les fichiers statiques de l'application
        self._handle_static_file(path)

    def do_POST(self):
        """Refuse formellement toute modification des données certifiées."""
        self._send_error_json(
            HTTPStatus.METHOD_NOT_ALLOWED,
            "Méthode non autorisée : L'interface de la Phase 7 fonctionne en LECTURE SEULE stricte pour protéger les données certifiées."
        )

    def do_PUT(self):
        self.do_POST()

    def do_DELETE(self):
        self.do_POST()

    def _handle_api_route(self, path: str):
        """Traite les requêtes de l'API REST."""
        try:
            if path == "/api/health":
                response_data = {
                    "status": "healthy",
                    "system": "AGADIR MAPPING — Dashboard 4 Cadrans",
                    "phase": "Phase 7 : Interface à quatre cadrans",
                    "mode": "READ_ONLY_PROTECTED",
                    "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "endpoints": [
                        "/api/health",
                        "/api/points",
                        "/api/tour",
                        "/api/multi-agent",
                        "/api/metrics",
                        "/api/geojson"
                    ]
                }
            elif path == "/api/points":
                response_data = self.data_service.get_points()
            elif path == "/api/tour":
                response_data = self.data_service.get_tour()
            elif path == "/api/multi-agent":
                response_data = self.data_service.get_multi_agent_data()
            elif path == "/api/metrics":
                response_data = self.data_service.get_metrics()
            elif path == "/api/geojson":
                response_data = self.data_service.get_geojson()
            else:
                self._send_error_json(HTTPStatus.NOT_FOUND, f"Point de terminaison API introuvable : {path}")
                return

            self._send_json(HTTPStatus.OK, response_data)

        except Exception as e:
            logger.exception(f"Erreur interne lors du traitement de {path}: {e}")
            self._send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, f"Erreur serveur interne : {str(e)}")

    def _handle_static_file(self, path: str):
        """Sert un fichier statique depuis le dossier static/."""
        if path == "/" or path == "":
            path = "/index.html"

        # Sécurité : empêcher les attaques de traversée de répertoire
        relative_path = path.lstrip("/")
        target_path = (STATIC_DIR / relative_path).resolve()

        if not str(target_path).startswith(str(STATIC_DIR.resolve())):
            self._send_error_json(HTTPStatus.FORBIDDEN, "Accès interdit.")
            return

        if not target_path.exists() or not target_path.is_file():
            self._send_error_json(HTTPStatus.NOT_FOUND, f"Fichier statique introuvable : {path}")
            return

        mime_type, _ = mimetypes.guess_type(str(target_path))
        if not mime_type:
            mime_type = "application/octet-stream"

        try:
            with open(target_path, "rb") as f:
                content = f.read()

            self.send_response(HTTPStatus.OK)
            self._send_cors_headers()
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache, must-revalidate")
            self.end_headers()
            self.wfile.write(content)

        except Exception as e:
            logger.exception(f"Erreur lors de la lecture du fichier {target_path}: {e}")
            self._send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, "Erreur de lecture du fichier.")

    def _send_cors_headers(self):
        """Envoie les en-têtes CORS pour autoriser l'accès web local."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def _send_json(self, status: HTTPStatus, data: Any):
        """Sérialise et expédie une réponse JSON."""
        encoded = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_error_json(self, status: HTTPStatus, message: str):
        """Expédie une erreur standardisée au format JSON."""
        error_payload = {
            "error": True,
            "status_code": status.value,
            "status_name": status.name,
            "message": message,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        self._send_json(status, error_payload)

    def log_message(self, format, *args):
        """Redirige les logs HTTP vers le module logging."""
        logger.debug("%s - - [%s] %s" % (self.client_address[0], self.log_date_time_string(), format % args))


def create_server(host: str = "127.0.0.1", port: int = 8050) -> ThreadingHTTPServer:
    """Instancie le serveur HTTP multithreadé."""
    server_address = (host, port)
    server = ThreadingHTTPServer(server_address, DashboardRequestHandler)
    return server


def run_server(host: str = "127.0.0.1", port: int = 8050):
    """Démarre le serveur et écoute les requêtes."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    server = create_server(host, port)
    logger.info(f"=== AGADIR MAPPING DASHBOARD (PHASE 7) ===")
    logger.info(f"Serveur opérationnel à l'adresse : http://{host}:{port}")
    logger.info(f"Appuyez sur Ctrl+C pour arrêter le serveur.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Arrêt du serveur demandé par l'utilisateur.")
    finally:
        server.server_close()
        logger.info("Serveur arrêté proprement.")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8050
    run_server(port=port)
