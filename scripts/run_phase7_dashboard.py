#!/usr/bin/env python3
"""
Script de lancement officiel de la Phase 7 — Tableau de bord à quatre cadrans.
Projet AGADIR MAPPING.

Usage :
    python scripts/run_phase7_dashboard.py [--port 8050] [--host 127.0.0.1] [--check-only]
"""

import argparse
import hashlib
import logging
import sys
from pathlib import Path

# Ajout du répertoire racine au PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.interface.server import run_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] agadir.phase7: %(message)s"
)
logger = logging.getLogger("agadir.phase7")

# Empreintes SHA-256 certifiées des 4 fichiers protégés
PROTECTED_FILES = {
    "data/processed/delivery_points_40.csv": "03590423ea8a69eb97fc8ee62735777fbe12d8cb95e3aaca8d35a20051d1b200",
    "data/processed/distance_matrix.csv": "35a6dafdb3525e208bce807b10c6bf314c4b612b154a170fd98fe3f69612a34a",
    "data/processed/duration_matrix.csv": "891a3af33e8c35211200adadd1f1cc8c304e2207d850ea5e43ec05aa2c726426",
    "data/results/tsp_optimized_route.json": "6bf918b8d69998d9063790714437f10edadf7ebf1fc1289973516527cc906933",
}


def verify_protected_files() -> bool:
    """Contrôle cryptographique strict des 4 fichiers protégés."""
    logger.info("Vérification de l'intégrité SHA-256 des fichiers protégés...")
    for rel_path, expected_hash in PROTECTED_FILES.items():
        file_path = ROOT_DIR / rel_path
        if not file_path.exists():
            logger.error(f"Fichier protégé manquant : {rel_path}")
            return False
        with open(file_path, "rb") as f:
            computed = hashlib.sha256(f.read()).hexdigest()
        if computed != expected_hash:
            logger.error(f"Corruption détectée sur {rel_path} : attendu {expected_hash}, calculé {computed}")
            return False
        logger.info(f"✓ {rel_path} : Hash certifié conforme ({computed[:16]}...)")
    return True


def main():
    parser = argparse.ArgumentParser(description="Lancement du Dashboard à quatre cadrans — AGADIR MAPPING")
    parser.add_argument("--host", default="127.0.0.1", help="Adresse IP d'écoute (défaut : 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8050, help="Port d'écoute HTTP (défaut : 8050)")
    parser.add_argument("--check-only", action="store_true", help="Vérifie l'intégrité et quitte sans lancer le serveur")
    args = parser.parse_args()

    logger.info("================================================================================")
    logger.info("AGADIR MAPPING — PHASE 7 : INTERFACE À QUATRE CADRANS")
    logger.info("================================================================================")

    if not verify_protected_files():
        logger.critical("Échec de la vérification d'intégrité des fichiers protégés. Lancement annulé.")
        sys.exit(1)

    logger.info("Tous les fichiers protégés sont intègres et conformes.")

    if args.check_only:
        logger.info("Mode --check-only : vérifications validées avec succès. Fin.")
        sys.exit(0)

    logger.info(f"Démarrage du tableau de bord sur : http://{args.host}:{args.port}")
    logger.info("Cadran 1 : Cartographie géographique d'Agadir (40 destinations + Dépôt #0)")
    logger.info("Cadran 2 : Tournée optimisée officielle (18 933,1 m, 42 arrêts)")
    logger.info("Cadran 3 : Multi-Agents (Web, Scholar, Analyst, Judge 0.9340, Veto Python)")
    logger.info("Cadran 4 : Indicateurs & Performances (Gain -9.90%, Budget, 172/172 tests)")
    logger.info("================================================================================")

    run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
