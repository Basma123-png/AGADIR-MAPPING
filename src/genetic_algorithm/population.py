"""
Gestion d'une population d'individus pour le TSP asymétrique.

Gère :
- L'initialisation (aléatoire ou hybride avec amorçage Nearest Neighbor)
- L'évaluation collective sur la matrice OSRM
- Le tri, la sélection des élites et les statistiques de population
"""

from typing import List, Optional
import numpy as np

from src.genetic_algorithm.individual import Individual


class Population:
    """
    Population de solutions candidates pour AGADIR MAPPING.
    """

    def __init__(self, individuals: Optional[List[Individual]] = None):
        self.individuals: List[Individual] = individuals or []

    def __len__(self) -> int:
        return len(self.individuals)

    def __getitem__(self, idx: int) -> Individual:
        return self.individuals[idx]

    def add(self, individual: Individual) -> None:
        self.individuals.append(individual)

    def evaluate_all(self, distance_matrix: np.ndarray) -> None:
        """
        Évalue l'ensemble des individus de la population.
        """
        for ind in self.individuals:
            ind.evaluate(distance_matrix)

    def sort_by_fitness(self) -> None:
        """
        Trie la population de la plus performante à la moins performante (distance croissante).
        """
        self.individuals.sort(key=lambda ind: ind.distance)

    def best_individual(self) -> Individual:
        """
        Retourne l'individu ayant la plus faible distance totale.
        """
        if not self.individuals:
            raise ValueError("Population vide")
        return min(self.individuals, key=lambda ind: ind.distance)

    def worst_individual(self) -> Individual:
        """
        Retourne l'individu le moins performant.
        """
        if not self.individuals:
            raise ValueError("Population vide")
        return max(self.individuals, key=lambda ind: ind.distance)

    def average_distance(self) -> float:
        """
        Calcule la distance moyenne de la population.
        """
        if not self.individuals:
            return 0.0
        return float(np.mean([ind.distance for ind in self.individuals]))

    def get_elites(self, elite_size: int) -> List[Individual]:
        """
        Retourne les k meilleurs individus (copies profondes).
        """
        self.sort_by_fitness()
        return [ind.copy() for ind in self.individuals[:elite_size]]

    @classmethod
    def create_random(
        cls,
        pop_size: int,
        n_destinations: int = 40,
        distance_matrix: Optional[np.ndarray] = None,
        rng: Optional[np.random.Generator] = None,
    ) -> "Population":
        """
        Génère une population aléatoire de taille pop_size.
        Chaque individu est une permutation aléatoire des entiers {1..n_destinations}.
        """
        if rng is None:
            rng = np.random.default_rng()

        individuals = []
        base = np.arange(1, n_destinations + 1, dtype=int)

        for _ in range(pop_size):
            perm = list(rng.permutation(base))
            ind = Individual(perm, distance_matrix=distance_matrix)
            individuals.append(ind)

        pop = cls(individuals)
        return pop

    @classmethod
    def create_hybrid(
        cls,
        pop_size: int,
        distance_matrix: np.ndarray,
        n_destinations: int = 40,
        rng: Optional[np.random.Generator] = None,
    ) -> "Population":
        """
        Initialisation hybride : intègre 1 individu généré par l'heuristique du Plus Proche Voisin (Nearest Neighbor)
        et complète avec des permutations aléatoires diversifiées.
        """
        if rng is None:
            rng = np.random.default_rng()

        pop = cls.create_random(pop_size - 1, n_destinations=n_destinations, distance_matrix=distance_matrix, rng=rng)

        # Génération du Nearest Neighbor
        nn_perm = cls.generate_nearest_neighbor(distance_matrix, n_destinations=n_destinations)
        nn_ind = Individual(nn_perm, distance_matrix=distance_matrix)
        pop.add(nn_ind)
        pop.sort_by_fitness()
        return pop

    @staticmethod
    def generate_nearest_neighbor(distance_matrix: np.ndarray, n_destinations: int = 40) -> List[int]:
        """
        Construit une tournée gloutonne du plus proche voisin partant du Dépôt #0.
        """
        unvisited = set(range(1, n_destinations + 1))
        current = 0  # Dépôt
        tour = []

        while unvisited:
            next_node = min(unvisited, key=lambda node: distance_matrix[current, node])
            tour.append(next_node)
            unvisited.remove(next_node)
            current = next_node

        return tour

    @staticmethod
    def generate_nearest_neighbor_from_start(
        distance_matrix: np.ndarray, start_node: int, n_destinations: int = 40
    ) -> List[int]:
        """
        Construit une tournée gloutonne du plus proche voisin partant d'un nœud donné (0 ou 1..n_destinations).
        """
        unvisited = set(range(1, n_destinations + 1))
        tour = []
        if start_node in unvisited:
            tour.append(start_node)
            unvisited.remove(start_node)
            current = start_node
        else:
            current = start_node

        while unvisited:
            next_node = min(unvisited, key=lambda node: distance_matrix[current, node])
            tour.append(next_node)
            unvisited.remove(next_node)
            current = next_node

        return tour

    @classmethod
    def create_multi_nn(
        cls,
        pop_size: int,
        distance_matrix: np.ndarray,
        n_destinations: int = 40,
        start_nodes: Optional[List[int]] = None,
        rng: Optional[np.random.Generator] = None,
    ) -> "Population":
        """
        Initialisation multi-heuristique : injecte plusieurs tournées Nearest Neighbor
        initiées depuis des nœuds stratégiques (Dépôt #0, Littoral #40, etc.)
        et complète avec des permutations aléatoires diversifiées.
        """
        if rng is None:
            rng = np.random.default_rng()

        if start_nodes is None:
            # Dépôt #0, Point littoral #40, et nœuds stratégiques
            start_nodes = [0, n_destinations]

        seeds_to_inject = []
        for s in start_nodes:
            perm = cls.generate_nearest_neighbor_from_start(distance_matrix, s, n_destinations=n_destinations)
            seeds_to_inject.append(Individual(perm, distance_matrix=distance_matrix))

        n_random = max(0, pop_size - len(seeds_to_inject))
        pop = cls.create_random(n_random, n_destinations=n_destinations, distance_matrix=distance_matrix, rng=rng)

        for ind in seeds_to_inject:
            pop.add(ind)

        pop.sort_by_fitness()
        return pop
