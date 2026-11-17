"""
Modélisation d'un individu (solution candidate TSP) pour AGADIR MAPPING.

Représentation :
- Un individu est une permutation stricte des 40 destinations : [pi_1, pi_2, ..., pi_40] où pi_k in {1, ..., 40}
- Le Dépôt #0 (Place Al Amal) est le point de départ et d'arrivée implicite ou explicite de la tournée :
  Tournée complète = [0, pi_1, pi_2, ..., pi_40, 0]
- Évaluation exacte sur la matrice asymétrique des distances routières OSRM.
"""

from typing import List, Optional
import numpy as np


class Individual:
    """
    Individu pour le problème TSP asymétrique (ATSP).
    """

    def __init__(self, permutation: List[int], distance_matrix: Optional[np.ndarray] = None):
        """
        Args:
            permutation: Liste des 40 identifiants de destinations [1..40].
            distance_matrix: Matrice asymétrique des distances routières OSRM (41x41).
        """
        self.permutation: List[int] = list(permutation)
        self.distance: float = float("inf")
        self.fitness: float = 0.0

        if distance_matrix is not None:
            self.evaluate(distance_matrix)

    def evaluate(self, distance_matrix: np.ndarray) -> float:
        """
        Calcule la distance routière totale orientée de la tournée fermée avec départ et retour au Dépôt #0.
        
        Coût = D(0, pi_1) + somme_{k=1..39} D(pi_k, pi_{k+1}) + D(pi_40, 0)
        """
        p = self.permutation
        # Départ du dépôt vers la 1ère destination
        total = float(distance_matrix[0, p[0]])
        # Parcours entre destinations consécutives
        for k in range(len(p) - 1):
            total += float(distance_matrix[p[k], p[k + 1]])
        # Retour au dépôt depuis la dernière destination
        total += float(distance_matrix[p[-1], 0])

        self.distance = total
        # Fitness positive inversement proportionnelle à la distance
        self.fitness = 1.0 / max(total, 1e-6)
        return self.distance

    def get_full_tour(self) -> List[int]:
        """
        Retourne la tournée complète incluant le Dépôt #0 au départ et à l'arrivée.
        """
        return [0] + self.permutation + [0]

    def is_valid(self, expected_size: int = 40) -> bool:
        """
        Vérifie qu'aucun point n'est dupliqué et que l'ensemble {1..expected_size} est exactement couvert.
        """
        if len(self.permutation) != expected_size:
            return False
        return set(self.permutation) == set(range(1, expected_size + 1))

    def copy(self) -> "Individual":
        """
        Copie profonde de l'individu.
        """
        ind = Individual(list(self.permutation))
        ind.distance = self.distance
        ind.fitness = self.fitness
        return ind

    def __repr__(self) -> str:
        return f"<Individual dist={self.distance:.1f}m fitness={self.fitness:.6f} stops={len(self.permutation)}>"

    def __lt__(self, other: "Individual") -> bool:
        return self.distance < other.distance
