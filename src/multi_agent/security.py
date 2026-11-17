"""
Module de sécurité, de contrôle d'intégrité et de confinement système pour AGADIR MAPPING.
Vérifie les empreintes SHA-256 des données certifiées et impose l'accès en lecture seule.
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.multi_agent.exceptions import SecurityViolationException

# Empreintes officielles certifiées des données des Phases 1 à 5
CERTIFIED_SHA256_HASHES: Dict[str, str] = {
    "data/processed/delivery_points_40.csv": "03590423ea8a69eb97fc8ee62735777fbe12d8cb95e3aaca8d35a20051d1b200",
    "data/processed/distance_matrix.csv": "35a6dafdb3525e208bce807b10c6bf314c4b612b154a170fd98fe3f69612a34a",
    "data/processed/duration_matrix.csv": "891a3af33e8c35211200adadd1f1cc8c304e2207d850ea5e43ec05aa2c726426",
    "data/results/tsp_optimized_route.json": "6bf918b8d69998d9063790714437f10edadf7ebf1fc1289973516527cc906933",
}


class SecurityValidator:
    """
    Validateur de sécurité garantissant l'intégrité physique et logique des données du projet.
    """

    def __init__(self, base_dir: Optional[Path | str] = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parent.parent.parent

    def compute_file_sha256(self, rel_path: str) -> str:
        """Calcule l'empreinte SHA-256 d'un fichier."""
        abs_path = self.base_dir / rel_path
        if not abs_path.exists():
            raise SecurityViolationException(f"Fichier protégé introuvable : {rel_path}")

        hasher = hashlib.sha256()
        with open(abs_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def verify_all_protected_files(self) -> Dict[str, bool]:
        """
        Vérifie l'intégrité de tous les fichiers certifiés par rapport aux hashes de référence.
        Lève SecurityViolationException en cas d'écart.
        """
        results: Dict[str, bool] = {}
        for rel_path, expected_hash in CERTIFIED_SHA256_HASHES.items():
            actual_hash = self.compute_file_sha256(rel_path)
            if actual_hash != expected_hash:
                raise SecurityViolationException(
                    f"ALTÉRATION DÉTECTÉE sur le fichier protégé '{rel_path}' ! "
                    f"Hash actuel: '{actual_hash}' != Certifié: '{expected_hash}'."
                )
            results[rel_path] = True
        return results

    def get_protected_files_hashes(self) -> Dict[str, str]:
        """Retourne un dictionnaire associant chaque chemin protégé à son empreinte SHA-256 actuelle."""
        return {rel_path: self.compute_file_sha256(rel_path) for rel_path in CERTIFIED_SHA256_HASHES}

    def open_protected_file_read_only(self, rel_path: str, mode: str = "r"):
        """
        Ouvre un fichier protégé en garantissant le mode lecture seule strict.
        Rejette toute tentative d'ouverture en mode écriture ('w', 'a', '+').
        """
        if any(w in mode for w in ("w", "a", "+", "x")):
            raise SecurityViolationException(
                f"Tentative d'ouverture interdite en écriture ({mode}) sur le fichier protégé '{rel_path}'."
            )
        abs_path = self.base_dir / rel_path
        return open(abs_path, mode, encoding="utf-8" if "b" not in mode else None)

    @staticmethod
    def sanitize_untrusted_evidence(text: str, source_id: str, domain: str = "web") -> str:
        """
        Sanitise et encapsule un flux textuel externe non fiable dans des balises XML étanches.
        Neutralise les tentatives d'évasion et d'injection de prompt.
        """
        # Suppression des balises de contrôle ou script potentielles
        cleaned = re.sub(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", "", text, flags=re.IGNORECASE | re.DOTALL)
        cleaned = cleaned.replace("</untrusted_evidence>", "[ESCAPED_TAG]")
        
        # Confinement étanche
        return (
            f'<untrusted_evidence source_id="{source_id}" domain="{domain}">\n'
            f'{cleaned.strip()}\n'
            f'</untrusted_evidence>'
        )
