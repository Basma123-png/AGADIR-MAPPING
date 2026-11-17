"""
Moteur principal de l'Algorithme Génétique pour le TSP Asymétrique (AGADIR MAPPING).

Gère :
- Le cycle complet de reproduction (Élitisme, Sélection, Croisement OX/PMX, Mutation Inversion/Swap)
- Le suivi en temps réel de la convergence (meilleure distance, moyenne, fitness)
- L'arrêt propre via signal d'interruption (pour l'interface Tkinter)
- La reproductibilité stricte via graine aléatoire (seed)
"""

import time
import logging
from typing import Dict, Any, List, Optional, Callable, Tuple
import numpy as np

from src.genetic_algorithm.individual import Individual
from src.genetic_algorithm.population import Population
from src.genetic_algorithm.operators import (
    tournament_selection,
    roulette_wheel_selection,
    order_crossover_ox,
    partially_mapped_crossover_pmx,
    inversion_mutation,
    swap_mutation,
    insertion_mutation,
    scramble_mutation,
    asymmetric_2opt,
    asymmetric_relocate,
    asymmetric_combined_local_search,
)

logger = logging.getLogger(__name__)


class GeneticAlgorithm:
    """
    Moteur génétique hautement configurable pour l'optimisation Last-Mile à Agadir.
    """

    def __init__(
        self,
        distance_matrix: np.ndarray,
        population_size: int = 50,
        crossover_rate: float = 0.8,
        mutation_rate: float = 0.05,
        selection_method: str = "tournament",
        tournament_size: int = 3,
        crossover_operator: str = "ox",
        mutation_operator: str = "inversion",
        elite_size: int = 2,
        max_generations: int = 500,
        seed: Optional[int] = 42,
        n_destinations: int = 40,
        use_memetic_2opt: bool = False,
        memetic_frequency: int = 50,
        memetic_max_passes: int = 10,
        local_search_operator: str = "2opt",
        seeding_strategy: str = "random",
    ):
        self.distance_matrix = distance_matrix
        self.population_size = population_size
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.selection_method = selection_method.lower()
        self.tournament_size = tournament_size
        self.crossover_operator = crossover_operator.lower()
        self.mutation_operator = mutation_operator.lower()
        self.elite_size = elite_size
        self.max_generations = max_generations
        self.seed = seed
        self.n_destinations = n_destinations
        self.use_memetic_2opt = use_memetic_2opt
        self.memetic_frequency = memetic_frequency
        self.memetic_max_passes = memetic_max_passes
        self.local_search_operator = local_search_operator.lower()
        self.seeding_strategy = seeding_strategy.lower()

        self.rng = np.random.default_rng(seed)
        self.stop_requested = False

        # Historique d'exécution
        self.history: Dict[str, List[float]] = {
            "generation": [],
            "best_distance": [],
            "avg_distance": [],
            "worst_distance": [],
            "best_fitness": [],
            "elapsed_seconds": [],
        }

    def stop(self) -> None:
        """
        Demande l'arrêt anticipé de la simulation (pour le bouton STOP Tkinter).
        """
        self.stop_requested = True

    def run(
        self,
        callback: Optional[Callable[[int, Individual, Dict[str, Any]], None]] = None,
        initial_population: Optional[Population] = None,
    ) -> Tuple[Individual, Dict[str, Any]]:
        """
        Exécute l'algorithme génétique sur les générations spécifiées.
        
        Args:
            callback: Fonction appelée à chaque génération avec (gen, best_ind, metrics).
            initial_population: Population optionnelle déjà instanciée.
            
        Returns:
            Tuple (meilleur individu final, dictionnaire historique et métriques).
        """
        start_time = time.time()
        self.stop_requested = False
        self.history = {
            "generation": [],
            "best_distance": [],
            "avg_distance": [],
            "worst_distance": [],
            "best_fitness": [],
            "elapsed_seconds": [],
        }

        # 1. Initialisation de la population
        if initial_population is not None:
            population = initial_population
        elif self.seeding_strategy == "hybrid_nn":
            population = Population.create_hybrid(
                pop_size=self.population_size,
                distance_matrix=self.distance_matrix,
                n_destinations=self.n_destinations,
                rng=self.rng,
            )
        elif self.seeding_strategy == "multi_nn":
            population = Population.create_multi_nn(
                pop_size=self.population_size,
                distance_matrix=self.distance_matrix,
                n_destinations=self.n_destinations,
                start_nodes=[0, self.n_destinations],
                rng=self.rng,
            )
        else:
            population = Population.create_random(
                pop_size=self.population_size,
                n_destinations=self.n_destinations,
                distance_matrix=self.distance_matrix,
                rng=self.rng,
            )

        population.evaluate_all(self.distance_matrix)
        population.sort_by_fitness()

        best_overall = population.best_individual().copy()

        # 2. Boucle des générations
        for gen in range(self.max_generations):
            if self.stop_requested:
                logger.info("Arrêt demandé par l'utilisateur à la génération %d", gen)
                break

            # 2a. Préservation des élites
            new_individuals = population.get_elites(self.elite_size)

            # 2b. Sélection du mécanisme de reproduction
            select_fn = (
                (lambda pop: tournament_selection(pop.individuals, self.tournament_size, self.rng))
                if self.selection_method == "tournament"
                else (lambda pop: roulette_wheel_selection(pop.individuals, self.rng))
            )

            # 2c. Croisement et mutation pour générer la descendance
            while len(new_individuals) < self.population_size:
                parent1 = select_fn(population)
                parent2 = select_fn(population)

                # Croisement
                if self.rng.random() < self.crossover_rate:
                    if self.crossover_operator == "pmx":
                        c1_perm, c2_perm = partially_mapped_crossover_pmx(parent1.permutation, parent2.permutation, self.rng)
                    else:
                        c1_perm, c2_perm = order_crossover_ox(parent1.permutation, parent2.permutation, self.rng)
                else:
                    c1_perm = list(parent1.permutation)
                    c2_perm = list(parent2.permutation)

                # Mutation
                if self.mutation_operator == "swap":
                    mutate_fn = swap_mutation
                elif self.mutation_operator in ("insertion", "relocate"):
                    mutate_fn = insertion_mutation
                elif self.mutation_operator == "scramble":
                    mutate_fn = scramble_mutation
                else:
                    mutate_fn = inversion_mutation

                c1_perm = mutate_fn(c1_perm, self.mutation_rate, self.rng)
                c2_perm = mutate_fn(c2_perm, self.mutation_rate, self.rng)

                new_individuals.append(Individual(c1_perm, self.distance_matrix))
                if len(new_individuals) < self.population_size:
                    new_individuals.append(Individual(c2_perm, self.distance_matrix))

            population = Population(new_individuals)
            population.sort_by_fitness()

            # 2d. Amélioration locale memétique facultative
            if self.use_memetic_2opt and (gen % self.memetic_frequency == 0 or gen == self.max_generations - 1):
                best_ind = population.best_individual()
                if self.local_search_operator == "relocate":
                    improved_perm = asymmetric_relocate(best_ind.permutation, self.distance_matrix, max_passes=self.memetic_max_passes)
                elif self.local_search_operator == "combined":
                    improved_perm = asymmetric_combined_local_search(best_ind.permutation, self.distance_matrix, max_passes=self.memetic_max_passes)
                else:
                    improved_perm = asymmetric_2opt(best_ind.permutation, self.distance_matrix, max_passes=self.memetic_max_passes)

                improved_ind = Individual(improved_perm, self.distance_matrix)
                if improved_ind.distance < best_ind.distance:
                    population.individuals[0] = improved_ind
                    population.sort_by_fitness()
                improved_ind = Individual(improved_perm, self.distance_matrix)
                if improved_ind.distance < best_ind.distance:
                    population.individuals[0] = improved_ind
                    population.sort_by_fitness()

            current_best = population.best_individual()
            if current_best.distance < best_overall.distance:
                best_overall = current_best.copy()

            # 2e. Enregistrement des métriques
            elapsed = time.time() - start_time
            self.history["generation"].append(gen + 1)
            self.history["best_distance"].append(float(best_overall.distance))
            self.history["avg_distance"].append(float(population.average_distance()))
            self.history["worst_distance"].append(float(population.worst_individual().distance))
            self.history["best_fitness"].append(float(best_overall.fitness))
            self.history["elapsed_seconds"].append(round(elapsed, 4))

            # 2f. Callback vers l'IHM
            if callback is not None:
                metrics = {
                    "generation": gen + 1,
                    "max_generations": self.max_generations,
                    "best_distance_m": float(best_overall.distance),
                    "best_distance_km": round(float(best_overall.distance) / 1000.0, 3),
                    "avg_distance_km": round(float(population.average_distance()) / 1000.0, 3),
                    "elapsed_seconds": round(elapsed, 2),
                    "progress_pct": round(((gen + 1) / self.max_generations) * 100.0, 1),
                }
                callback(gen + 1, best_overall, metrics)

        total_time = time.time() - start_time

        summary = {
            "initial_distance_m": self.history["best_distance"][0] if self.history["best_distance"] else best_overall.distance,
            "final_distance_m": float(best_overall.distance),
            "final_distance_km": round(float(best_overall.distance) / 1000.0, 3),
            "gain_pct": round(
                (self.history["best_distance"][0] - best_overall.distance) / max(self.history["best_distance"][0], 1e-6) * 100.0,
                2
            ) if self.history["best_distance"] else 0.0,
            "generations_completed": len(self.history["generation"]),
            "computation_time_seconds": round(total_time, 3),
            "best_tour": best_overall.get_full_tour(),
            "history": self.history,
        }

        return best_overall, summary
