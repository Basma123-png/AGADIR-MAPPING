"""
Solveur TSP et comparateur d'algorithmes pour AGADIR MAPPING.

Permet de :
- Résoudre le TSP asymétrique par différentes approches (Nearest Neighbor, 2-opt, GA, Memetic GA)
- Comparer rigoureusement les performances (distances, gains %, temps CPU)
- Vérifier la validité des tournées générées
- Exporter les résultats au format CSV et JSON pour l'IHM et les rapports
"""

import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd

from config.settings import RESULTS_DATA_DIR, PROCESSED_DATA_DIR
from src.genetic_algorithm.individual import Individual
from src.genetic_algorithm.population import Population
from src.genetic_algorithm.engine import GeneticAlgorithm
from src.genetic_algorithm.operators import asymmetric_2opt, calculate_tour_cost

logger = logging.getLogger(__name__)


class TSPSolver:
    """
    Solveur et banc d'essai comparatif pour le TSP asymétrique d'Agadir.
    """

    def __init__(
        self,
        distance_matrix: Optional[np.ndarray] = None,
        points_df: Optional[pd.DataFrame] = None,
    ):
        if distance_matrix is not None:
            self.distance_matrix = distance_matrix
        else:
            self.distance_matrix = pd.read_csv(
                PROCESSED_DATA_DIR / "distance_matrix.csv", index_col=0
            ).values

        if points_df is not None:
            self.points_df = points_df
        else:
            self.points_df = pd.read_csv(
                PROCESSED_DATA_DIR / "delivery_points_40.csv"
            ).sort_values("point_id").reset_index(drop=True)

        self.n_destinations = len(self.points_df) - 1  # 40

    def solve_nearest_neighbor(self) -> Dict[str, Any]:
        """
        Résout le TSP via l'heuristique du Plus Proche Voisin (Nearest Neighbor).
        Départ du Dépôt #0, choix glouton du voisin le plus proche non visité, retour au Dépôt #0.
        """
        start_time = time.time()
        perm = Population.generate_nearest_neighbor(self.distance_matrix, self.n_destinations)
        ind = Individual(perm, self.distance_matrix)
        elapsed = time.time() - start_time

        return {
            "method": "Nearest Neighbor (Glouton)",
            "distance_m": round(ind.distance, 1),
            "distance_km": round(ind.distance / 1000.0, 3),
            "time_seconds": round(elapsed, 4),
            "tour": ind.get_full_tour(),
            "individual": ind,
        }

    def solve_2opt(self, initial_permutation: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Amélioration locale 2-opt asymétrique appliquée à une solution initiale
        (par défaut, initialisée avec la tournée Nearest Neighbor).
        """
        start_time = time.time()
        if initial_permutation is None:
            initial_permutation = Population.generate_nearest_neighbor(self.distance_matrix, self.n_destinations)

        improved_perm = asymmetric_2opt(initial_permutation, self.distance_matrix, max_passes=25)
        ind = Individual(improved_perm, self.distance_matrix)
        elapsed = time.time() - start_time

        return {
            "method": "2-opt Local Search (sur NN)",
            "distance_m": round(ind.distance, 1),
            "distance_km": round(ind.distance / 1000.0, 3),
            "time_seconds": round(elapsed, 4),
            "tour": ind.get_full_tour(),
            "individual": ind,
        }

    def solve_genetic(
        self,
        population_size: int = 50,
        crossover_rate: float = 0.8,
        mutation_rate: float = 0.05,
        selection_method: str = "tournament",
        crossover_operator: str = "ox",
        mutation_operator: str = "inversion",
        max_generations: int = 500,
        seed: Optional[int] = 42,
        use_memetic_2opt: bool = False,
        hybrid_init: bool = False,
        label: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Résout le TSP avec l'Algorithme Génétique.
        """
        ga = GeneticAlgorithm(
            distance_matrix=self.distance_matrix,
            population_size=population_size,
            crossover_rate=crossover_rate,
            mutation_rate=mutation_rate,
            selection_method=selection_method,
            crossover_operator=crossover_operator,
            mutation_operator=mutation_operator,
            max_generations=max_generations,
            seed=seed,
            n_destinations=self.n_destinations,
            use_memetic_2opt=use_memetic_2opt,
        )

        init_pop = None
        if hybrid_init:
            init_pop = Population.create_hybrid(
                pop_size=population_size,
                distance_matrix=self.distance_matrix,
                n_destinations=self.n_destinations,
                rng=ga.rng,
            )

        best_ind, summary = ga.run(initial_population=init_pop)
        method_name = label or f"Algorithme Génétique (Pop={population_size}, Gen={max_generations}, Seed={seed})"

        return {
            "method": method_name,
            "distance_m": round(best_ind.distance, 1),
            "distance_km": round(best_ind.distance / 1000.0, 3),
            "time_seconds": summary["computation_time_seconds"],
            "tour": best_ind.get_full_tour(),
            "individual": best_ind,
            "summary": summary,
            "ga_instance": ga,
        }

    def run_benchmark_comparison(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Exécute la batterie de comparaisons exigée en Phase 4 :
        1. Heuristique Nearest Neighbor (Référence de base)
        2. Recherche locale 2-opt adaptée à l'ATSP
        3. AG classique (Pop=50, Gen=500, Seed=42)
        4. AG classique (Pop=50, Gen=500, Seed=101)
        5. AG classique (Pop=50, Gen=500, Seed=777)
        6. AG avec population étendue (Pop=100, Gen=500, Seed=42)
        7. AG Memétique Hybride (GA + 2-opt local search)
        """
        results = []
        all_runs = {}

        # 1. Nearest Neighbor
        logger.info("Exécution du benchmark : Nearest Neighbor...")
        nn_res = self.solve_nearest_neighbor()
        all_runs["nn"] = nn_res
        ref_distance = nn_res["distance_m"]
        results.append({
            "Méthode": nn_res["method"],
            "Distance (m)": nn_res["distance_m"],
            "Distance (km)": nn_res["distance_km"],
            "Gain vs NN (%)": 0.0,
            "Temps CPU (s)": nn_res["time_seconds"],
            "Graines / Paramètres": "Déterministe (Glouton)",
        })

        # 2. 2-opt sur NN
        logger.info("Exécution du benchmark : 2-opt sur NN...")
        two_opt_res = self.solve_2opt(nn_res["tour"][1:-1])
        all_runs["2opt"] = two_opt_res
        gain_2opt = round((ref_distance - two_opt_res["distance_m"]) / ref_distance * 100.0, 2)
        results.append({
            "Méthode": two_opt_res["method"],
            "Distance (m)": two_opt_res["distance_m"],
            "Distance (km)": two_opt_res["distance_km"],
            "Gain vs NN (%)": gain_2opt,
            "Temps CPU (s)": two_opt_res["time_seconds"],
            "Graines / Paramètres": "Max passes = 25",
        })

        # 3. AG avec graines multiples (Pop=50, Gen=500)
        seeds = [42, 101, 777]
        for s in seeds:
            logger.info("Exécution du benchmark : AG Pop=50, Gen=500, Seed=%d...", s)
            ga_res = self.solve_genetic(
                population_size=50,
                max_generations=500,
                mutation_rate=0.08,
                crossover_rate=0.8,
                seed=s,
                label=f"Algorithme Génétique (Pop=50, Gen=500, Seed={s})",
            )
            all_runs[f"ga_seed_{s}"] = ga_res
            gain = round((ref_distance - ga_res["distance_m"]) / ref_distance * 100.0, 2)
            results.append({
                "Méthode": ga_res["method"],
                "Distance (m)": ga_res["distance_m"],
                "Distance (km)": ga_res["distance_km"],
                "Gain vs NN (%)": gain,
                "Temps CPU (s)": ga_res["time_seconds"],
                "Graines / Paramètres": f"Seed={s}, OX, Inversion",
            })

        # 4. AG avec grande population (Pop=100, Gen=500)
        logger.info("Exécution du benchmark : AG Pop=100, Gen=500, Seed=42...")
        ga_large = self.solve_genetic(
            population_size=100,
            max_generations=500,
            mutation_rate=0.06,
            crossover_rate=0.85,
            seed=42,
            label="Algorithme Génétique (Pop=100, Gen=500, Seed=42)",
        )
        all_runs["ga_large"] = ga_large
        gain_large = round((ref_distance - ga_large["distance_m"]) / ref_distance * 100.0, 2)
        results.append({
            "Méthode": ga_large["method"],
            "Distance (m)": ga_large["distance_m"],
            "Distance (km)": ga_large["distance_km"],
            "Gain vs NN (%)": gain_large,
            "Temps CPU (s)": ga_large["time_seconds"],
            "Graines / Paramètres": "Pop=100, Gen=500, Seed=42",
        })

        # 5. AG Memétique Hybride (GA + Amorçage NN + 2-opt)
        logger.info("Exécution du benchmark : AG Memétique Hybride...")
        ga_memetic = self.solve_genetic(
            population_size=50,
            max_generations=500,
            mutation_rate=0.08,
            crossover_rate=0.8,
            seed=42,
            use_memetic_2opt=True,
            hybrid_init=True,
            label="Algorithme Génétique Memétique (Hybride GA + Amorçage NN + 2-opt)",
        )
        all_runs["ga_memetic"] = ga_memetic
        gain_memetic = round((ref_distance - ga_memetic["distance_m"]) / ref_distance * 100.0, 2)
        results.append({
            "Méthode": ga_memetic["method"],
            "Distance (m)": ga_memetic["distance_m"],
            "Distance (km)": ga_memetic["distance_km"],
            "Gain vs NN (%)": gain_memetic,
            "Temps CPU (s)": ga_memetic["time_seconds"],
            "Graines / Paramètres": "GA + 2-opt Local Search périodique",
        })

        df_bench = pd.DataFrame(results)

        # Identification de la meilleure solution globale
        best_run_key = min(all_runs.keys(), key=lambda k: all_runs[k]["distance_m"])
        best_run = all_runs[best_run_key]

        return df_bench, best_run

    def build_route_details(self, tour: List[int]) -> List[Dict[str, Any]]:
        """
        Construit l'itinéraire détaillé pas à pas de la tournée pour export et cartographie.
        """
        steps = []
        cumul_m = 0.0

        for seq, pid in enumerate(tour):
            row = self.points_df[self.points_df["point_id"] == pid].iloc[0]

            if seq == 0:
                leg_dist_m = 0.0
                leg_dist_km = 0.0
            else:
                prev_pid = tour[seq - 1]
                leg_dist_m = float(self.distance_matrix[prev_pid, pid])
                leg_dist_km = round(leg_dist_m / 1000.0, 3)
                cumul_m += leg_dist_m

            steps.append({
                "sequence_order": seq,
                "point_id": int(pid),
                "name": str(row["name"]),
                "point_type": str(row["point_type"]),
                "district": str(row["district"]),
                "category": str(row["category"]),
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "x_utm": float(row["x_utm"]),
                "y_utm": float(row["y_utm"]),
                "is_coastal": bool(row.get("is_coastal", False)),
                "leg_distance_m": leg_dist_m,
                "leg_distance_km": leg_dist_km,
                "cumulative_distance_km": round(cumul_m / 1000.0, 3),
            })

        return steps

    def save_results(self, df_bench: pd.DataFrame, best_run: Dict[str, Any]) -> Tuple[Path, Path]:
        """
        Enregistre tsp_results.csv et tsp_best_route.json dans data/results/.
        """
        RESULTS_DATA_DIR.mkdir(parents=True, exist_ok=True)
        csv_path = RESULTS_DATA_DIR / "tsp_results.csv"
        json_path = RESULTS_DATA_DIR / "tsp_best_route.json"

        df_bench.to_csv(csv_path, index=False, encoding="utf-8")

        tour_steps = self.build_route_details(best_run["tour"])

        best_route_data = {
            "metadata": {
                "title": "Meilleure Tournée TSP Last Mile — Agadir Mapping",
                "method": best_run["method"],
                "total_distance_meters": best_run["distance_m"],
                "total_distance_km": best_run["distance_km"],
                "computation_time_seconds": best_run["time_seconds"],
                "total_stops": len(tour_steps),
                "number_of_destinations": self.n_destinations,
                "depot_id": 0,
                "coastal_point_id": 40,
                "is_closed_tour": tour_steps[0]["point_id"] == tour_steps[-1]["point_id"] == 0,
            },
            "tour": best_run["tour"],
            "steps": tour_steps,
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(best_route_data, f, ensure_ascii=False, indent=2)

        return csv_path, json_path
