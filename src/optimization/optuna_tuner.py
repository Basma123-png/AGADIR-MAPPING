"""
Module d'Optimisation Automatique des Hyperparamètres avec Optuna (AGADIR MAPPING).

Explore de manière bayésienne (TPE - Tree-structured Parzen Estimator) l'espace des hyperparamètres
de l'Algorithme Génétique Memétique pour résoudre le TSP Asymétrique (ATSP) à Agadir.

Garantit :
- L'évaluation multi-graines (multi-seed) pour la stabilité et la reproductibilité
- La persistance complète dans une base de données SQLite (optuna_study.db)
- L'export standardisé des résultats (CSV, JSON, graphiques PNG)
- La préservation stricte de la matrice OSRM originale et des 41 points
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
import optuna
from optuna.samplers import TPESampler

from config.settings import (
    PROCESSED_DATA_DIR,
    RESULTS_DATA_DIR,
    REPORTS_DIR,
    FIGURES_DIR,
)
from src.genetic_algorithm.engine import GeneticAlgorithm
from src.genetic_algorithm.individual import Individual
from src.genetic_algorithm.population import Population

logger = logging.getLogger(__name__)


def _json_default(obj):
    if isinstance(obj, (np.integer, int)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return str(obj)


class OptunaTuner:
    """
    Gestionnaire d'optimisation bayésienne des hyperparamètres de l'Algorithme Génétique.
    """

    def __init__(
        self,
        distance_matrix: np.ndarray,
        n_destinations: int = 40,
        study_name: str = "agadir_tsp_tuning",
        db_path: Optional[Path] = None,
        eval_seeds: Optional[List[int]] = None,
        validation_seeds: Optional[List[int]] = None,
    ):
        self.distance_matrix = distance_matrix
        self.n_destinations = n_destinations
        self.study_name = study_name
        self.db_path = db_path or (RESULTS_DATA_DIR / "optuna_study.db")
        self.eval_seeds = eval_seeds or [42, 101, 777]
        self.validation_seeds = validation_seeds or [
            42, 101, 777, 1234, 9999, 2024, 31415, 27182, 1337, 4242
        ]
        self.study: Optional[optuna.Study] = None
        self.best_params: Dict[str, Any] = {}
        self.best_overall_individual: Optional[Individual] = None
        self.validation_summary: Dict[str, Any] = {}

    def _objective(self, trial: optuna.Trial) -> float:
        """
        Fonction objectif évaluée par Optuna pour un ensemble d'hyperparamètres.
        Évalue la configuration sur plusieurs graines aléatoires et retourne une métrique
        combinant distance moyenne et stabilité (écart-type).
        """
        # 1. Échantillonnage des hyperparamètres
        population_size = trial.suggest_categorical("population_size", [40, 50, 60, 80, 100, 120])
        max_generations = trial.suggest_categorical("max_generations", [200, 300, 500, 750])
        crossover_rate = trial.suggest_float("crossover_rate", 0.65, 0.95, step=0.05)
        mutation_rate = trial.suggest_float("mutation_rate", 0.01, 0.25, log=True)
        elite_size = trial.suggest_int("elite_size", 1, 5)
        selection_method = trial.suggest_categorical("selection_method", ["tournament", "roulette"])
        tournament_size = (
            trial.suggest_int("tournament_size", 2, 6)
            if selection_method == "tournament"
            else 3
        )
        crossover_operator = trial.suggest_categorical("crossover_operator", ["ox", "pmx"])
        mutation_operator = trial.suggest_categorical(
            "mutation_operator", ["inversion", "swap", "insertion", "scramble"]
        )
        seeding_strategy = trial.suggest_categorical(
            "seeding_strategy", ["random", "hybrid_nn", "multi_nn"]
        )
        use_memetic_2opt = trial.suggest_categorical("use_memetic_2opt", [True, False])

        if use_memetic_2opt:
            memetic_frequency = trial.suggest_categorical("memetic_frequency", [10, 25, 50, 100])
            memetic_max_passes = trial.suggest_categorical("memetic_max_passes", [5, 10, 20])
            local_search_operator = trial.suggest_categorical(
                "local_search_operator", ["2opt", "relocate", "combined"]
            )
        else:
            memetic_frequency = 50
            memetic_max_passes = 10
            local_search_operator = "2opt"

        # 2. Évaluation sur les graines d'évaluation
        distances = []
        times = []

        for seed in self.eval_seeds:
            ga = GeneticAlgorithm(
                distance_matrix=self.distance_matrix,
                population_size=population_size,
                crossover_rate=crossover_rate,
                mutation_rate=mutation_rate,
                selection_method=selection_method,
                tournament_size=tournament_size,
                crossover_operator=crossover_operator,
                mutation_operator=mutation_operator,
                elite_size=elite_size,
                max_generations=max_generations,
                seed=seed,
                n_destinations=self.n_destinations,
                use_memetic_2opt=use_memetic_2opt,
                memetic_frequency=memetic_frequency,
                memetic_max_passes=memetic_max_passes,
                local_search_operator=local_search_operator,
                seeding_strategy=seeding_strategy,
            )
            best_ind, summary = ga.run()
            distances.append(best_ind.distance)
            times.append(summary["computation_time_seconds"])

            # Sauvegarde du meilleur individu absolu rencontré
            if self.best_overall_individual is None or best_ind.distance < self.best_overall_individual.distance:
                self.best_overall_individual = best_ind.copy()

        mean_dist = float(np.mean(distances))
        std_dist = float(np.std(distances))
        min_dist = float(np.min(distances))
        max_dist = float(np.max(distances))
        mean_time = float(np.mean(times))

        # Attributs utilisateur pour analyse ultérieure
        trial.set_user_attr("mean_distance_m", round(mean_dist, 2))
        trial.set_user_attr("std_distance_m", round(std_dist, 2))
        trial.set_user_attr("min_distance_m", round(min_dist, 2))
        trial.set_user_attr("max_distance_m", round(max_dist, 2))
        trial.set_user_attr("mean_time_s", round(mean_time, 3))
        trial.set_user_attr("stability_ratio_pct", round((std_dist / max(mean_dist, 1e-6)) * 100.0, 2))

        # Score objectif : pénalise légèrement la variance pour favoriser les solutions stables
        objective_score = mean_dist + 0.10 * std_dist
        return objective_score

    def run_study(self, n_trials: int = 50, enqueue_baseline: bool = True) -> optuna.Study:
        """
        Lance la recherche bayésienne Optuna avec persistance SQLite.
        """
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        storage_url = f"sqlite:///{self.db_path}"

        sampler = TPESampler(seed=42)
        study = optuna.create_study(
            study_name=self.study_name,
            storage=storage_url,
            sampler=sampler,
            direction="minimize",
            load_if_exists=True,
        )

        # Enqueue la configuration de référence Phase 4 si l'étude est vierge
        if enqueue_baseline and len(study.trials) == 0:
            baseline_trial = {
                "population_size": 50,
                "max_generations": 500,
                "crossover_rate": 0.80,
                "mutation_rate": 0.05,
                "elite_size": 2,
                "selection_method": "tournament",
                "tournament_size": 3,
                "crossover_operator": "ox",
                "mutation_operator": "inversion",
                "seeding_strategy": "hybrid_nn",
                "use_memetic_2opt": True,
                "memetic_frequency": 50,
                "memetic_max_passes": 10,
                "local_search_operator": "2opt",
            }
            study.enqueue_trial(baseline_trial)
            logger.info("Configuration de référence Phase 4 ajoutée en file d'attente (Trial #0).")

        logger.info("Démarrage de l'étude Optuna : %s (%d essais prévus)...", self.study_name, n_trials)
        study.optimize(self._objective, n_trials=n_trials)

        self.study = study
        self.best_params = study.best_params
        logger.info("Étude Optuna achevée. Meilleur score: %.2f", study.best_value)
        return study

    def run_extended_validation(
        self, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Évalue de manière approfondie les meilleurs paramètres sur 10 graines aléatoires distinctes.
        """
        if params is None:
            params = self.best_params

        logger.info("Lancement de la validation statistique approfondie sur 10 graines...")
        runs = []
        best_overall = None

        pop_size = params["population_size"]
        max_gen = params["max_generations"]
        cx_rate = params["crossover_rate"]
        mut_rate = params["mutation_rate"]
        elite_size = params["elite_size"]
        sel_method = params["selection_method"]
        tourn_size = params.get("tournament_size", 3)
        cx_op = params["crossover_operator"]
        mut_op = params["mutation_operator"]
        seed_strat = params["seeding_strategy"]
        use_memetic = params["use_memetic_2opt"]
        mem_freq = params.get("memetic_frequency", 50)
        mem_passes = params.get("memetic_max_passes", 10)
        loc_op = params.get("local_search_operator", "2opt")

        for seed in self.validation_seeds:
            ga = GeneticAlgorithm(
                distance_matrix=self.distance_matrix,
                population_size=pop_size,
                crossover_rate=cx_rate,
                mutation_rate=mut_rate,
                selection_method=sel_method,
                tournament_size=tourn_size,
                crossover_operator=cx_op,
                mutation_operator=mut_op,
                elite_size=elite_size,
                max_generations=max_gen,
                seed=seed,
                n_destinations=self.n_destinations,
                use_memetic_2opt=use_memetic,
                memetic_frequency=mem_freq,
                memetic_max_passes=mem_passes,
                local_search_operator=loc_op,
                seeding_strategy=seed_strat,
            )
            best_ind, summary = ga.run()
            dist = float(best_ind.distance)

            # Identification de la génération de convergence
            history = summary["history"]["best_distance"]
            min_val = min(history)
            conv_gen = history.index(min_val) + 1

            runs.append({
                "seed": seed,
                "distance_m": round(dist, 2),
                "distance_km": round(dist / 1000.0, 3),
                "computation_time_seconds": summary["computation_time_seconds"],
                "convergence_generation": conv_gen,
            })

            if best_overall is None or dist < best_overall.distance:
                best_overall = best_ind.copy()

        distances = [r["distance_m"] for r in runs]
        times = [r["computation_time_seconds"] for r in runs]
        conv_gens = [r["convergence_generation"] for r in runs]

        summary_stats = {
            "best_params": params,
            "seeds_evaluated": len(self.validation_seeds),
            "min_distance_m": round(float(np.min(distances)), 2),
            "min_distance_km": round(float(np.min(distances)) / 1000.0, 3),
            "mean_distance_m": round(float(np.mean(distances)), 2),
            "mean_distance_km": round(float(np.mean(distances)) / 1000.0, 3),
            "max_distance_m": round(float(np.max(distances)), 2),
            "max_distance_km": round(float(np.max(distances)) / 1000.0, 3),
            "std_distance_m": round(float(np.std(distances)), 2),
            "stability_ratio_pct": round((float(np.std(distances)) / float(np.mean(distances))) * 100.0, 2),
            "mean_execution_time_seconds": round(float(np.mean(times)), 3),
            "mean_convergence_generation": round(float(np.mean(conv_gens)), 1),
            "runs": runs,
            "best_tour": best_overall.get_full_tour() if best_overall else [],
        }

        self.validation_summary = summary_stats
        if best_overall is not None:
            if self.best_overall_individual is None or best_overall.distance < self.best_overall_individual.distance:
                self.best_overall_individual = best_overall

        return summary_stats

    def export_results(
        self,
        output_dir: Optional[Path] = None,
        figures_dir: Optional[Path] = None,
    ) -> Dict[str, Path]:
        """
        Exporte les données et artefacts de la Phase 5 :
        - optuna_best_params.json
        - optuna_trials.csv
        - optuna_optimization_history.png
        - optuna_param_importances.png
        - tsp_optimized_route.json
        """
        if self.study is None:
            raise ValueError("L'étude Optuna doit être exécutée avant d'exporter les résultats.")

        out_dir = output_dir or RESULTS_DATA_DIR
        fig_dir = figures_dir or FIGURES_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        fig_dir.mkdir(parents=True, exist_ok=True)

        files = {}

        # 1. Sauvegarde des meilleurs paramètres en JSON
        best_params_path = out_dir / "optuna_best_params.json"
        export_params = {
            "study_name": self.study_name,
            "best_trial_number": self.study.best_trial.number,
            "best_objective_value": round(self.study.best_value, 2),
            "best_params": self.study.best_params,
            "user_attrs": self.study.best_trial.user_attrs,
            "validation_statistics": self.validation_summary,
        }
        with open(best_params_path, "w", encoding="utf-8") as f:
            json.dump(export_params, f, indent=2, ensure_ascii=False, default=_json_default)
        files["best_params_json"] = best_params_path

        # 2. Sauvegarde du tableau des essais en CSV
        trials_df = self.study.trials_dataframe()
        trials_csv_path = out_dir / "optuna_trials.csv"
        trials_df.to_csv(trials_csv_path, index=False)
        files["trials_csv"] = trials_csv_path

        # Configuration de l'environnement Matplotlib sécurisé
        os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib"
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import optuna.visualization.matplotlib as ovm

        # 3. Figure : Historique de l'optimisation
        history_fig_path = fig_dir / "optuna_optimization_history.png"
        try:
            ax = ovm.plot_optimization_history(self.study)
            fig = ax.figure
            fig.set_size_inches(10, 6)
            plt.title("Historique d'Optimisation Bayésienne Optuna (TPE) — AGADIR MAPPING", fontsize=12, fontweight="bold")
            plt.tight_layout()
            plt.savefig(history_fig_path, dpi=300)
            plt.close(fig)
            files["optimization_history_png"] = history_fig_path
        except Exception as e:
            logger.warning("Échec de génération automatique plot_optimization_history: %s", e)

        # 4. Figure : Importances des hyperparamètres
        importance_fig_path = fig_dir / "optuna_param_importances.png"
        try:
            ax = ovm.plot_param_importances(self.study)
            fig = ax.figure
            fig.set_size_inches(10, 6)
            plt.title("Importance Relative des Hyperparamètres — AGADIR MAPPING", fontsize=12, fontweight="bold")
            plt.tight_layout()
            plt.savefig(importance_fig_path, dpi=300)
            plt.close(fig)
            files["param_importances_png"] = importance_fig_path
        except Exception as e:
            logger.warning("Échec de génération automatique plot_param_importances: %s", e)

        # 5. Sauvegarde de la tournée optimisée détaillée (tsp_optimized_route.json)
        if self.best_overall_individual is not None:
            route_path = out_dir / "tsp_optimized_route.json"
            full_tour = self.best_overall_individual.get_full_tour()
            total_dist = float(self.best_overall_individual.distance)

            # Lecture des points de livraison pour enrichir le fichier
            pts_df = pd.read_csv(PROCESSED_DATA_DIR / "delivery_points_40.csv")
            pts_map = {row["point_id"]: row.to_dict() for _, row in pts_df.iterrows()}

            steps = []
            cumulative_dist = 0.0
            for k in range(len(full_tour) - 1):
                p_from = full_tour[k]
                p_to = full_tour[k + 1]
                leg_dist = float(self.distance_matrix[p_from, p_to])
                cumulative_dist += leg_dist
                dest_info = pts_map.get(p_to, {})
                steps.append({
                    "step": k + 1,
                    "from_point_id": p_from,
                    "to_point_id": p_to,
                    "to_name": dest_info.get("name", f"Point #{p_to}"),
                    "category": dest_info.get("category", "Inconnue"),
                    "district": dest_info.get("district", "Inconnu"),
                    "latitude": dest_info.get("latitude", 0.0),
                    "longitude": dest_info.get("longitude", 0.0),
                    "is_coastal": bool(dest_info.get("is_coastal", False)),
                    "leg_distance_m": round(leg_dist, 2),
                    "cumulative_distance_m": round(cumulative_dist, 2),
                })

            optimized_data = {
                "metadata": {
                    "title": "Tournée ATSP Optimisée via Optuna — AGADIR MAPPING",
                    "total_distance_meters": round(total_dist, 2),
                    "total_distance_km": round(total_dist / 1000.0, 3),
                    "baseline_phase4_distance_m": 21014.30,
                    "gain_meters": round(21014.30 - total_dist, 2),
                    "gain_percent": round((21014.30 - total_dist) / 21014.30 * 100.0, 2),
                    "total_stops": len(full_tour),
                    "destinations_visited": self.n_destinations,
                    "is_closed_tour": True,
                    "best_params": self.best_params,
                },
                "tour": full_tour,
                "steps": steps,
            }
            with open(route_path, "w", encoding="utf-8") as f:
                json.dump(optimized_data, f, indent=2, ensure_ascii=False, default=_json_default)
            files["tsp_optimized_route_json"] = route_path

        return files
