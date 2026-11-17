"""
Tests de validation automatisés pour la Phase 7 — Interface à quatre cadrans.
Vérifie le service de données, les routes API REST, la sécurité en lecture seule,
l'intégrité des 4 fichiers protégés et la cohérence des quatre cadrans.
Fonctionne intégralement en mémoire sans nécessiter de socket réseau physique.
"""

import hashlib
import io
import json
from http import HTTPStatus
from pathlib import Path

import pytest

from src.interface.api_service import DashboardDataService
from src.interface.server import DashboardRequestHandler

ROOT_DIR = Path(__file__).resolve().parent.parent

# Empreintes SHA-256 certifiées des 4 fichiers protégés
PROTECTED_FILES = {
    "data/processed/delivery_points_40.csv": "03590423ea8a69eb97fc8ee62735777fbe12d8cb95e3aaca8d35a20051d1b200",
    "data/processed/distance_matrix.csv": "35a6dafdb3525e208bce807b10c6bf314c4b612b154a170fd98fe3f69612a34a",
    "data/processed/duration_matrix.csv": "891a3af33e8c35211200adadd1f1cc8c304e2207d850ea5e43ec05aa2c726426",
    "data/results/tsp_optimized_route.json": "6bf918b8d69998d9063790714437f10edadf7ebf1fc1289973516527cc906933",
}


@pytest.fixture(scope="module")
def data_service():
    """Instance du service de données pour les tests unitaires."""
    return DashboardDataService()


class InMemoryClient:
    """Simulateur de client HTTP en mémoire pour tester DashboardRequestHandler sans sockets TCP."""

    @staticmethod
    def request(method: str, path: str, body: bytes = b"", headers: dict = None):
        raw_req = f"{method} {path} HTTP/1.1\r\nHost: localhost\r\n".encode("utf-8")
        if headers:
            for k, v in headers.items():
                raw_req += f"{k}: {v}\r\n".encode("utf-8")
        if body:
            raw_req += f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8") + body
        else:
            raw_req += b"\r\n"

        class MockSocket:
            def __init__(self, req_bytes):
                self.rfile = io.BytesIO(req_bytes)
                self.wfile = io.BytesIO()

            def makefile(self, mode, *args, **kwargs):
                if "r" in mode:
                    return self.rfile
                return self.wfile

            def sendall(self, b):
                self.wfile.write(b)

        class DummyServer:
            pass

        mock_sock = MockSocket(raw_req)
        # L'initialisation exécute le traitement complet de la requête
        DashboardRequestHandler(mock_sock, ("127.0.0.1", 54321), DummyServer())

        response_bytes = mock_sock.wfile.getvalue()
        header_end = response_bytes.find(b"\r\n\r\n")
        if header_end == -1:
            header_part = response_bytes.decode("utf-8", errors="replace")
            body_part = b""
        else:
            header_part = response_bytes[:header_end].decode("utf-8", errors="replace")
            body_part = response_bytes[header_end + 4:]

        lines = header_part.split("\r\n")
        status_line = lines[0] if lines else ""
        status_code = int(status_line.split(" ")[1]) if len(status_line.split(" ")) > 1 else 500

        res_headers = {}
        for line in lines[1:]:
            if ": " in line:
                k, v = line.split(": ", 1)
                res_headers[k.lower()] = v

        return status_code, res_headers, body_part


# ==============================================================================
# 1. TESTS UNITAIRES DU SERVICE DE DONNÉES (api_service.py)
# ==============================================================================

def test_data_service_points_count_and_structure(data_service):
    """Vérifie le chargement exact des 41 points (dépôt + 40 destinations)."""
    points = data_service.get_points()
    assert len(points) == 41, f"Attendu 41 points, reçu {len(points)}"

    # Vérification du dépôt #0
    depot = points[0]
    assert depot["point_id"] == 0
    assert "Place Al Amal" in depot["name"]
    assert depot["latitude"] == pytest.approx(30.4215, abs=0.001)
    assert depot["longitude"] == pytest.approx(-9.5985, abs=0.001)
    assert depot["point_type"] == "Dépôt"

    # Vérification du point littoral #40
    p40 = points[40]
    assert p40["point_id"] == 40
    assert "Restaurant Les Blancs" in p40["name"]
    assert p40["is_coastal"] is True
    assert p40["district"] == "Corniche / Marina"
    assert p40["point_type"] == "Littoral"


def test_data_service_tour_certified_distance(data_service):
    """Vérifie que la tournée officielle est strictement identique à la référence certifiée."""
    tour = data_service.get_tour()
    assert tour["total_distance_m"] == 18933.1
    assert tour["total_distance_km"] == 18.9331
    assert tour["total_stops"] == 42
    assert tour["unique_destinations"] == 40
    assert tour["is_closed_tour"] is True

    # Ordre de visite officiel
    expected_tour = [
        0, 36, 13, 30, 21, 6, 33, 27, 25, 26, 7, 9, 38, 3, 10, 11, 17, 28, 37, 2,
        14, 12, 5, 35, 16, 22, 39, 8, 1, 19, 20, 32, 40, 24, 29, 4, 23, 31, 15, 18, 34, 0
    ]
    assert tour["tour"] == expected_tour

    # Vérification des 41 étapes détaillées
    steps = tour["steps"]
    assert len(steps) == 41
    assert steps[0]["from_point_id"] == 0
    assert steps[0]["to_point_id"] == 36
    assert steps[-1]["from_point_id"] == 34
    assert steps[-1]["to_point_id"] == 0
    assert steps[-1]["cumulative_distance_m"] == 18933.1


def test_data_service_multi_agent_pilot_results(data_service):
    """Vérifie les résultats du système multi-agents issus de la mission pilote 6.8."""
    ma = data_service.get_multi_agent_data()
    assert ma["mission_id"] == "AGADIR_MAPPING_PILOT_001"
    assert ma["workflow_status"] == "SUCCESS"
    assert ma["final_execution_status"] == "COMPLETED_SUCCESS"

    # Vérification des 3 agents métier
    assert ma["web_research"]["sources_count"] == 3
    assert ma["semantic_scholar"]["papers_count"] == 3
    assert len(ma["gemini_analyst"]["findings"]) == 5

    # Vérification du Judge Agent
    judge = ma["judge_agent"]
    assert judge["weighted_score"] == pytest.approx(0.9340, abs=0.001)
    assert judge["overall_verdict"] == "ACCEPTED_PENDING_VALIDATION"
    assert judge["criteria_scores"]["source_reliability"] == 0.95
    assert judge["criteria_scores"]["scientific_consistency"] == 0.94

    # Vérification du Validateur Déterministe Python
    val = ma["deterministic_validator"]
    assert val["is_valid"] is True
    assert val["reference_distance_m"] == 18933.1
    assert val["recalculated_distance_m"] == 18933.1
    assert val["gain_m"] == 0.0
    assert val["rules_count"] == "6/6 validées"


def test_data_service_metrics_provenance(data_service):
    """Vérifie la présence et la provenance de tous les indicateurs scientifiques."""
    metrics = data_service.get_metrics()
    assert metrics["geographic"]["total_points"] == 41
    assert metrics["optimization"]["official_distance_m"] == 18933.1
    assert metrics["algorithmic"]["phase4_best_distance_m"] == 21014.3
    assert metrics["algorithmic"]["absolute_gain_m"] == 2081.2
    assert metrics["algorithmic"]["relative_gain_pct"] == 9.90
    assert metrics["multi_agent"]["tests_passed"] == "172/172 (100%)"
    assert metrics["budget"]["pilot_cost_usd"] == 0.00619


# ==============================================================================
# 2. TESTS D'INTÉGRATION DU SERVEUR HTTP ET DES ROUTES API (EN MÉMOIRE)
# ==============================================================================

def test_api_health_endpoint():
    """Vérifie la route /api/health."""
    status, headers, body = InMemoryClient.request("GET", "/api/health")
    assert status == HTTPStatus.OK
    data = json.loads(body.decode("utf-8"))
    assert data["status"] == "healthy"
    assert data["phase"] == "Phase 7 : Interface à quatre cadrans"
    assert data["mode"] == "READ_ONLY_PROTECTED"


def test_api_points_endpoint():
    """Vérifie la route /api/points."""
    status, headers, body = InMemoryClient.request("GET", "/api/points")
    assert status == HTTPStatus.OK
    data = json.loads(body.decode("utf-8"))
    assert isinstance(data, list)
    assert len(data) == 41


def test_api_tour_endpoint():
    """Vérifie la route /api/tour."""
    status, headers, body = InMemoryClient.request("GET", "/api/tour")
    assert status == HTTPStatus.OK
    data = json.loads(body.decode("utf-8"))
    assert data["total_distance_m"] == 18933.1
    assert len(data["steps"]) == 41


def test_api_multi_agent_endpoint():
    """Vérifie la route /api/multi-agent."""
    status, headers, body = InMemoryClient.request("GET", "/api/multi-agent")
    assert status == HTTPStatus.OK
    data = json.loads(body.decode("utf-8"))
    assert data["mission_id"] == "AGADIR_MAPPING_PILOT_001"
    assert data["judge_agent"]["weighted_score"] == pytest.approx(0.9340, abs=0.001)


def test_api_metrics_endpoint():
    """Vérifie la route /api/metrics."""
    status, headers, body = InMemoryClient.request("GET", "/api/metrics")
    assert status == HTTPStatus.OK
    data = json.loads(body.decode("utf-8"))
    assert data["optimization"]["official_distance_m"] == 18933.1


def test_static_files_served():
    """Vérifie la distribution des fichiers statiques HTML, CSS et JS."""
    # 1. Page d'accueil index.html
    status, headers, body = InMemoryClient.request("GET", "/")
    assert status == HTTPStatus.OK
    html = body.decode("utf-8")
    assert "AGADIR MAPPING" in html
    assert "CADRAN 1" in html
    assert "CADRAN 2" in html
    assert "CADRAN 3" in html
    assert "CADRAN 4" in html

    # 2. Feuille de style CSS
    status, headers, body = InMemoryClient.request("GET", "/css/dashboard.css")
    assert status == HTTPStatus.OK
    assert "dashboard-grid" in body.decode("utf-8")

    # 3. Scripts JS
    status, headers, body = InMemoryClient.request("GET", "/js/app.js")
    assert status == HTTPStatus.OK
    assert "AppState" in body.decode("utf-8")


def test_api_read_only_protection_blocks_post():
    """Vérifie que les requêtes d'écriture POST/PUT/DELETE sont formellement refusées (405)."""
    status, headers, body = InMemoryClient.request("POST", "/api/tour", body=b"{}")
    assert status == HTTPStatus.METHOD_NOT_ALLOWED
    error_body = json.loads(body.decode("utf-8"))
    assert error_body["error"] is True
    assert "LECTURE SEULE" in error_body["message"]


def test_api_unknown_route_returns_404():
    """Vérifie la gestion des erreurs 404 sur point d'API inexistant."""
    status, headers, body = InMemoryClient.request("GET", "/api/non_existent_route")
    assert status == HTTPStatus.NOT_FOUND


def test_directory_traversal_attack_blocked():
    """Vérifie la protection contre les tentatives de traversée de répertoire."""
    status, headers, body = InMemoryClient.request("GET", "/../../../../etc/passwd")
    assert status in (HTTPStatus.FORBIDDEN, HTTPStatus.NOT_FOUND)


# ==============================================================================
# 3. CONTRÔLE D'INTÉGRITÉ SHA-256 DES 4 FICHIERS PROTÉGÉS
# ==============================================================================

def test_protected_files_remain_unaltered():
    """Contrôle cryptographique absolu que la Phase 7 n'a modifié aucun fichier de référence."""
    for rel_path, expected_hash in PROTECTED_FILES.items():
        file_path = ROOT_DIR / rel_path
        assert file_path.exists(), f"Fichier protégé manquant : {rel_path}"
        with open(file_path, "rb") as f:
            computed_hash = hashlib.sha256(f.read()).hexdigest()
        assert computed_hash == expected_hash, (
            f"VIOLATION D'INTÉGRITÉ sur {rel_path} : "
            f"attendu {expected_hash}, calculé {computed_hash}"
        )


# ==============================================================================
# 4. TESTS DU CORRECTIF ADDENDUM PHASE 7 (THÈME CLAIR, 6 GRAPHIQUES, LIENS)
# ==============================================================================

def test_phase7_light_theme_palette_compliance():
    """Vérifie la présence et conformité de la palette urbaine claire dans le CSS."""
    status, headers, body = InMemoryClient.request("GET", "/css/dashboard.css")
    assert status == HTTPStatus.OK
    css_content = body.decode("utf-8")

    # Vérification des couleurs officielles prescrites
    assert "#F4F7FA" in css_content, "Couleur de fond #F4F7FA absente du CSS"
    assert "#FFFFFF" in css_content, "Couleur blanche #FFFFFF absente du CSS"
    assert "#263445" in css_content, "Couleur texte #263445 absente du CSS"
    assert "#1E3A5F" in css_content, "Bleu urbain #1E3A5F absent du CSS"
    assert "#2878B5" in css_content, "Bleu secondaire #2878B5 absent du CSS"
    assert "#20A6A6" in css_content, "Turquoise #20A6A6 absent du CSS"
    assert "#32936F" in css_content, "Vert émeraude #32936F absent du CSS"


def test_phase7_scientific_charts_structure():
    """Vérifie l'intégration des 6 graphiques scientifiques réels et de Chart.js."""
    # 1. Présence de Chart.js et des 6 éléments canvas dans index.html
    status, headers, body = InMemoryClient.request("GET", "/index.html")
    assert status == HTTPStatus.OK
    html_content = body.decode("utf-8")

    assert "chart.umd.min.js" in html_content, "Script Chart.js absent de index.html"
    for chart_letter in ("a", "b", "c", "d", "e", "f"):
        canvas_id = f"chart-{chart_letter}-canvas"
        assert canvas_id in html_content, f"Canvas {canvas_id} absent de index.html"

    # 2. Présence des méthodes de rendu dans quadrant4_metrics.js
    status, headers, body = InMemoryClient.request("GET", "/js/quadrant4_metrics.js")
    assert status == HTTPStatus.OK
    js_content = body.decode("utf-8")

    assert "renderChartA" in js_content
    assert "renderChartB" in js_content
    assert "renderChartC" in js_content
    assert "renderChartD" in js_content
    assert "renderChartE" in js_content
    assert "renderChartF" in js_content


def test_phase7_external_links_audit_and_repaired_badges():
    """Vérifie que les liens externes sont sécurisés et dotés d'indicateurs d'état explicites."""
    status, headers, body = InMemoryClient.request("GET", "/js/quadrant3_agents.js")
    assert status == HTTPStatus.OK
    js_content = body.decode("utf-8")

    # Attributs de sécurité sur les liens
    assert 'target="_blank"' in js_content
    assert 'rel="noopener noreferrer"' in js_content

    # Badge explicatif pour le domaine d'archive municipal agadir-urbanisme.ma
    assert "agadir-urbanisme.ma" in js_content
    assert "Lien Documentaire SDAU" in js_content

    # Résolution des publications scientifiques via DOI.org
    assert "https://doi.org/" in js_content
    assert "DOI Vérifié" in js_content
