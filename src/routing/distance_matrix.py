"""
Module de calcul, validation et sauvegarde des matrices de distances et de durées routières.

Fournit :
- Le calcul de la matrice routière 41x41 (OSRM Table API)
- Le calcul de la matrice cartésienne euclidienne 41x41 (UTM Zone 29N / EPSG:32629)
- L'audit strict de complétude (zéro valeur nulle, diagonale nulle, dimensions exactes)
- L'analyse de l'asymétrie routière urbaine et du facteur de détour (circuity factor)
- La sauvegarde standardisée en formats CSV et JSON documentés
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

import numpy as np
import pandas as pd

from config.settings import (
    PROCESSED_DATA_DIR,
    RESULTS_DATA_DIR,
    REPORTS_DIR,
    FIGURES_DIR,
)
from src.geographic.projection import GeoProjector
from src.routing.osrm_client import OSRMClient

logger = logging.getLogger(__name__)


class DistanceMatrixBuilder:
    """
    Constructeur et validateur des matrices de coûts pour les 40 destinations et le dépôt.
    """

    def __init__(self, points_csv: Optional[Path] = None):
        self.points_csv = points_csv or (PROCESSED_DATA_DIR / "delivery_points_40.csv")
        self.projector = GeoProjector()
        self.osrm = OSRMClient()

    def load_ordered_points(self) -> pd.DataFrame:
        """
        Charge et ordonne strictement les 41 points par point_id croissant (0 à 40).
        """
        df = pd.read_csv(self.points_csv)
        df = df.sort_values("point_id").reset_index(drop=True)
        if len(df) != 41:
            raise ValueError(f"Attendu 41 points (1 dépôt + 40 destinations), trouvé {len(df)}")
        if list(df["point_id"]) != list(range(41)):
            raise ValueError("Les point_id doivent couvrir strictement l'intervalle 0 à 40 sans discontinuité")
        return df

    def compute_cartesian_matrix(self, df: pd.DataFrame) -> np.ndarray:
        """
        Calcule la matrice des distances cartésiennes euclidiennes en mètres
        projetées en UTM Zone 29N (EPSG:32629).
        """
        xs = df["x_utm"].values
        ys = df["y_utm"].values
        n = len(df)
        cart_matrix = np.zeros((n, n), dtype=float)

        for i in range(n):
            for j in range(n):
                cart_matrix[i, j] = self.projector.euclidean_distance_meters(
                    xs[i], ys[i], xs[j], ys[j]
                )
        return cart_matrix

    def compute_osrm_matrices(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Interroge OSRM Table API pour extraire les matrices de distances (mètres)
        et de durées (secondes) entre tous les 41 points.
        """
        coords = list(zip(df["latitude"], df["longitude"]))
        res = self.osrm.table(coords, annotations="duration,distance")

        if not res["success"]:
            raise RuntimeError(f"Échec du calcul OSRM Table : {res.get('error')}")

        dist_raw = res["distances"]
        dur_raw = res["durations"]

        dist_matrix = np.array(dist_raw, dtype=float)
        dur_matrix = np.array(dur_raw, dtype=float)

        # Nettoyage physique : éliminer les artefacts d'arrondi OSRM (< 0.0 m) et forcer la diagonale stricte à 0.0
        dist_matrix = np.maximum(dist_matrix, 0.0)
        dur_matrix = np.maximum(dur_matrix, 0.0)
        np.fill_diagonal(dist_matrix, 0.0)
        np.fill_diagonal(dur_matrix, 0.0)

        return dist_matrix, dur_matrix

    def audit_matrices(
        self,
        dist_matrix: np.ndarray,
        dur_matrix: np.ndarray,
        cart_matrix: np.ndarray,
        df: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Audit rigoureux et exhaustif des propriétés mathématiques et physiques des matrices.
        """
        n = len(df)
        report: Dict[str, Any] = {
            "matrix_shape": list(dist_matrix.shape),
            "expected_shape": [n, n],
            "shape_valid": dist_matrix.shape == (n, n) and dur_matrix.shape == (n, n),
        }

        # 1. Vérification de la diagonale
        diag_dist = np.diag(dist_matrix)
        diag_dur = np.diag(dur_matrix)
        report["diagonal_zero"] = bool(np.all(diag_dist == 0) and np.all(diag_dur == 0))
        report["max_diagonal_dist"] = float(np.max(diag_dist))
        report["max_diagonal_dur"] = float(np.max(diag_dur))

        # 2. Vérification des valeurs nulles / manquantes / inaccessibles
        null_dist_count = int(np.isnan(dist_matrix).sum() + np.isinf(dist_matrix).sum())
        null_dur_count = int(np.isnan(dur_matrix).sum() + np.isinf(dur_matrix).sum())
        report["unreachable_paths_count"] = null_dist_count + null_dur_count
        report["all_paths_feasible"] = (null_dist_count == 0 and null_dur_count == 0)

        # 3. Statistiques descriptives globales
        off_diag_mask = ~np.eye(n, dtype=bool)
        off_dist = dist_matrix[off_diag_mask]
        off_dur = dur_matrix[off_diag_mask]
        off_cart = cart_matrix[off_diag_mask]

        report["distance_stats_meters"] = {
            "min": round(float(np.min(off_dist)), 1),
            "mean": round(float(np.mean(off_dist)), 1),
            "median": round(float(np.median(off_dist)), 1),
            "max": round(float(np.max(off_dist)), 1),
            "total_pairs": int(len(off_dist)),
        }
        report["duration_stats_seconds"] = {
            "min": round(float(np.min(off_dur)), 1),
            "mean": round(float(np.mean(off_dur)), 1),
            "median": round(float(np.median(off_dur)), 1),
            "max": round(float(np.max(off_dur)), 1),
        }

        # 4. Indice d'asymétrie routière
        # Asymétrie(i,j) = |D_ij - D_ji| / max(D_ij, D_ji)
        abs_diff_dist = np.abs(dist_matrix - dist_matrix.T)
        denom_dist = np.maximum(dist_matrix, dist_matrix.T)
        # Éviter la division par zéro sur la diagonale
        with np.errstate(divide="ignore", invalid="ignore"):
            rel_asym_dist = np.where(denom_dist > 0, abs_diff_dist / denom_dist, 0.0)

        mean_asymmetry_dist = float(np.mean(rel_asym_dist[off_diag_mask]))
        report["mean_distance_asymmetry_pct"] = round(mean_asymmetry_dist * 100.0, 2)
        report["max_distance_asymmetry_m"] = round(float(np.max(abs_diff_dist)), 1)

        # Recherche de la paire la plus asymétrique
        i_max, j_max = np.unravel_index(np.argmax(abs_diff_dist), abs_diff_dist.shape)
        report["most_asymmetric_pair"] = {
            "point_a": {"id": int(df.iloc[i_max]["point_id"]), "name": str(df.iloc[i_max]["name"])},
            "point_b": {"id": int(df.iloc[j_max]["point_id"]), "name": str(df.iloc[j_max]["name"])},
            "dist_a_to_b_m": round(float(dist_matrix[i_max, j_max]), 1),
            "dist_b_to_a_m": round(float(dist_matrix[j_max, i_max]), 1),
            "absolute_diff_m": round(float(abs_diff_dist[i_max, j_max]), 1),
        }

        # 5. Ratio de détour / Facteur de sinuosité (Circuity Factor) : Road / Euclidean
        with np.errstate(divide="ignore", invalid="ignore"):
            detour_ratios = np.where(off_cart > 0, off_dist / off_cart, 1.0)

        report["circuity_factor"] = {
            "mean": round(float(np.mean(detour_ratios)), 3),
            "median": round(float(np.median(detour_ratios)), 3),
            "min": round(float(np.min(detour_ratios)), 3),
            "max": round(float(np.max(detour_ratios)), 3),
        }

        # 6. Statistiques d'accessibilité depuis le Dépôt (Point 0)
        depot_dists = dist_matrix[0, 1:]
        depot_durs = dur_matrix[0, 1:]
        report["depot_outbound"] = {
            "min_dist_m": round(float(np.min(depot_dists)), 1),
            "mean_dist_m": round(float(np.mean(depot_dists)), 1),
            "max_dist_m": round(float(np.max(depot_dists)), 1),
            "min_dur_min": round(float(np.min(depot_durs) / 60.0), 2),
            "mean_dur_min": round(float(np.mean(depot_durs) / 60.0), 2),
            "max_dur_min": round(float(np.max(depot_durs) / 60.0), 2),
        }

        return report

    def export_matrices(
        self,
        dist_matrix: np.ndarray,
        dur_matrix: np.ndarray,
        cart_matrix: np.ndarray,
        df: pd.DataFrame,
        output_dir: Optional[Path] = None,
        results_dir: Optional[Path] = None,
    ) -> Dict[str, Path]:
        """
        Enregistre les matrices sous les formats demandés (CSV et JSON) dans output_dir et results_dir.
        """
        out_dir = output_dir or PROCESSED_DATA_DIR
        res_dir = results_dir or RESULTS_DATA_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        res_dir.mkdir(parents=True, exist_ok=True)

        point_ids = [int(p) for p in df["point_id"]]
        point_names = [str(n) for n in df["name"]]
        col_names = [f"P{pid}" for pid in point_ids]

        # 1. Export CSV
        df_dist = pd.DataFrame(dist_matrix, index=col_names, columns=col_names)
        df_dur = pd.DataFrame(dur_matrix, index=col_names, columns=col_names)
        df_cart = pd.DataFrame(cart_matrix, index=col_names, columns=col_names)

        paths = {}
        paths["dist_csv"] = out_dir / "distance_matrix.csv"
        paths["dur_csv"] = out_dir / "duration_matrix.csv"
        paths["dist_json"] = out_dir / "distance_matrix.json"
        paths["dur_json"] = out_dir / "duration_matrix.json"
        paths["cart_csv"] = out_dir / "cartesian_distance_matrix.csv"

        df_dist.to_csv(paths["dist_csv"])
        df_dur.to_csv(paths["dur_csv"])
        df_cart.to_csv(paths["cart_csv"])

        # Sauvegarde miroir dans results_dir
        if res_dir != out_dir:
            df_dist.to_csv(res_dir / "distance_matrix.csv")
            df_dur.to_csv(res_dir / "duration_matrix.csv")

        # 2. Export JSON avec métadonnées complètes
        dist_json_data = {
            "metadata": {
                "description": "Matrice des distances routières réelles via OSRM",
                "city": "Agadir, Maroc",
                "district": "Talborjt, Centre-Ville & Corniche/Marina",
                "units": "mètres",
                "dimension": [len(point_ids), len(point_ids)],
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "routing_profile": "driving",
            },
            "points": [
                {
                    "point_id": int(row["point_id"]),
                    "name": str(row["name"]),
                    "category": str(row["category"]),
                    "latitude": float(row["latitude"]),
                    "longitude": float(row["longitude"]),
                    "x_utm": float(row["x_utm"]),
                    "y_utm": float(row["y_utm"]),
                    "is_coastal": bool(row.get("is_coastal", False)),
                }
                for _, row in df.iterrows()
            ],
            "matrix": dist_matrix.tolist(),
        }

        dur_json_data = {
            "metadata": {
                "description": "Matrice des durées de trajet routières réelles via OSRM",
                "city": "Agadir, Maroc",
                "district": "Talborjt, Centre-Ville & Corniche/Marina",
                "units": "secondes",
                "dimension": [len(point_ids), len(point_ids)],
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "routing_profile": "driving",
            },
            "points": dist_json_data["points"],
            "matrix": dur_matrix.tolist(),
        }

        with open(paths["dist_json"], "w", encoding="utf-8") as f:
            json.dump(dist_json_data, f, ensure_ascii=False, indent=2)

        with open(paths["dur_json"], "w", encoding="utf-8") as f:
            json.dump(dur_json_data, f, ensure_ascii=False, indent=2)

        if res_dir != out_dir:
            with open(res_dir / "distance_matrix.json", "w", encoding="utf-8") as f:
                json.dump(dist_json_data, f, ensure_ascii=False, indent=2)

            with open(res_dir / "duration_matrix.json", "w", encoding="utf-8") as f:
                json.dump(dur_json_data, f, ensure_ascii=False, indent=2)

        logger.info("Matrices exportées avec succès (CSV & JSON).")
        return paths
