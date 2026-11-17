"""
Opérateurs génétiques adaptés aux représentations par permutation pour le TSP asymétrique.

Contient :
- Méthodes de sélection : Tournoi (Tournament) et Roue de Roulette biaisée (Roulette Wheel)
- Méthodes de croisement : Order Crossover (OX) et Partially Mapped Crossover (PMX)
- Méthodes de mutation : Inversion de sous-séquence (Inversion) et Échange de deux positions (Swap)
- Recherche locale 2-opt adaptée au TSP asymétrique (ATSP)
"""

from typing import List, Tuple, Optional
import numpy as np


# ------------------------------------------------------------------------------
# 1. Opérateurs de Sélection
# ------------------------------------------------------------------------------

def tournament_selection(
    population: List["Individual"], tournament_size: int = 3, rng: Optional[np.random.Generator] = None
) -> "Individual":
    """
    Sélection par tournoi : sélectionne aléatoirement k individus et retient le plus performant (meilleure fitness).
    """
    if rng is None:
        rng = np.random.default_rng()

    indices = rng.choice(len(population), size=min(tournament_size, len(population)), replace=False)
    candidates = [population[i] for i in indices]
    # Tri par fitness décroissante (ou distance croissante)
    best = min(candidates, key=lambda ind: ind.distance)
    return best.copy()


def roulette_wheel_selection(
    population: List["Individual"], rng: Optional[np.random.Generator] = None
) -> "Individual":
    """
    Sélection par roulette biaisée : la probabilité de sélection est proportionnelle à la fitness.
    """
    if rng is None:
        rng = np.random.default_rng()

    fitnesses = np.array([ind.fitness for ind in population], dtype=float)
    total_fitness = fitnesses.sum()

    if total_fitness <= 0 or np.isnan(total_fitness):
        # Fallback uniforme si fitness anormale
        idx = rng.integers(0, len(population))
        return population[idx].copy()

    probabilities = fitnesses / total_fitness
    selected_idx = rng.choice(len(population), p=probabilities)
    return population[selected_idx].copy()


# ------------------------------------------------------------------------------
# 2. Opérateurs de Croisement (Crossover)
# ------------------------------------------------------------------------------

def order_crossover_ox(
    parent1: List[int], parent2: List[int], rng: Optional[np.random.Generator] = None
) -> Tuple[List[int], List[int]]:
    """
    Order Crossover (OX) :
    1. Sélectionne un sous-segment aléatoire entre deux points de coupure chez Parent 1.
    2. Copie ce sous-segment à la même position chez l'enfant 1.
    3. Remplit les positions restantes dans l'ordre où elles apparaissent chez Parent 2 en partant du second point de coupure.
    Garantit une permutation stricte sans doublon ni manque.
    """
    if rng is None:
        rng = np.random.default_rng()

    size = len(parent1)
    if size < 2:
        return list(parent1), list(parent2)

    # Choix de deux points de coupure
    cx1, cx2 = sorted(rng.choice(size, size=2, replace=False))

    def _ox_single(p1: List[int], p2: List[int]) -> List[int]:
        child = [-1] * size
        # 1. Copie du segment
        child[cx1 : cx2 + 1] = p1[cx1 : cx2 + 1]
        copied_set = set(child[cx1 : cx2 + 1])

        # 2. Remplissage cyclique depuis p2
        p2_order = p2[cx2 + 1 :] + p2[: cx2 + 1]
        remaining = [item for item in p2_order if item not in copied_set]

        # Remplir les positions après cx2 jusqu'à la fin, puis du début à cx1
        fill_positions = list(range(cx2 + 1, size)) + list(range(0, cx1))
        for pos, item in zip(fill_positions, remaining):
            child[pos] = item

        return child

    child1 = _ox_single(parent1, parent2)
    child2 = _ox_single(parent2, parent1)
    return child1, child2


def partially_mapped_crossover_pmx(
    parent1: List[int], parent2: List[int], rng: Optional[np.random.Generator] = None
) -> Tuple[List[int], List[int]]:
    """
    Partially Mapped Crossover (PMX) :
    Préserve l'ordre et la position absolue des gènes en construisant une table de correspondance.
    """
    if rng is None:
        rng = np.random.default_rng()

    size = len(parent1)
    if size < 2:
        return list(parent1), list(parent2)

    cx1, cx2 = sorted(rng.choice(size, size=2, replace=False))

    def _pmx_single(p1: List[int], p2: List[int]) -> List[int]:
        child = [-1] * size
        child[cx1 : cx2 + 1] = p1[cx1 : cx2 + 1]

        # Table de correspondance p1 <-> p2 sur la fenêtre
        mapping = {p1[i]: p2[i] for i in range(cx1, cx2 + 1)}

        for i in list(range(0, cx1)) + list(range(cx2 + 1, size)):
            val = p2[i]
            # Résolution des conflits par chaîne de correspondance
            while val in mapping:
                val = mapping[val]
            child[i] = val

        return child

    child1 = _pmx_single(parent1, parent2)
    child2 = _pmx_single(parent2, parent1)
    return child1, child2


# ------------------------------------------------------------------------------
# 3. Opérateurs de Mutation
# ------------------------------------------------------------------------------

def inversion_mutation(
    permutation: List[int], mutation_rate: float = 0.05, rng: Optional[np.random.Generator] = None
) -> List[int]:
    """
    Mutation par inversion (2-opt mutation) :
    Inverse l'ordre d'un sous-segment choisi aléatoirement avec une probabilité mutation_rate.
    """
    if rng is None:
        rng = np.random.default_rng()

    mutated = list(permutation)
    if rng.random() < mutation_rate and len(mutated) >= 2:
        i, j = sorted(rng.choice(len(mutated), size=2, replace=False))
        mutated[i : j + 1] = reversed(mutated[i : j + 1])
    return mutated


def swap_mutation(
    permutation: List[int], mutation_rate: float = 0.05, rng: Optional[np.random.Generator] = None
) -> List[int]:
    """
    Mutation par échange (Swap) :
    Échange les positions de deux éléments choisis aléatoirement avec une probabilité mutation_rate.
    """
    if rng is None:
        rng = np.random.default_rng()

    mutated = list(permutation)
    if rng.random() < mutation_rate and len(mutated) >= 2:
        i, j = rng.choice(len(mutated), size=2, replace=False)
        mutated[i], mutated[j] = mutated[j], mutated[i]
    return mutated


def insertion_mutation(
    permutation: List[int], mutation_rate: float = 0.05, rng: Optional[np.random.Generator] = None
) -> List[int]:
    """
    Mutation par insertion (Relocation / Shift) :
    Extrait un élément aléatoire et le réinsère à une autre position aléatoire.
    Préserve l'ordre relatif des autres éléments.
    """
    if rng is None:
        rng = np.random.default_rng()

    mutated = list(permutation)
    if rng.random() < mutation_rate and len(mutated) >= 2:
        src = rng.integers(0, len(mutated))
        elem = mutated.pop(src)
        dst = rng.integers(0, len(mutated) + 1)
        mutated.insert(dst, elem)
    return mutated


def scramble_mutation(
    permutation: List[int], mutation_rate: float = 0.05, rng: Optional[np.random.Generator] = None
) -> List[int]:
    """
    Mutation par mélange (Scramble) :
    Sélectionne un sous-segment et permute aléatoirement ses éléments.
    """
    if rng is None:
        rng = np.random.default_rng()

    mutated = list(permutation)
    if rng.random() < mutation_rate and len(mutated) >= 3:
        i, j = sorted(rng.choice(len(mutated), size=2, replace=False))
        sub = mutated[i : j + 1]
        rng.shuffle(sub)
        mutated[i : j + 1] = sub
    return mutated


# ------------------------------------------------------------------------------
# 4. Amélioration Locale 2-opt & Relocate Asymétriques (ATSP Local Search)
# ------------------------------------------------------------------------------

def calculate_tour_cost(tour: List[int], matrix: np.ndarray) -> float:
    """
    Calcule le coût total orienté d'une tournée incluant le retour au dépôt (tour[0] == tour[-1] == 0).
    """
    total = 0.0
    for k in range(len(tour) - 1):
        total += matrix[tour[k], tour[k + 1]]
    return total


def asymmetric_2opt(
    permutation: List[int], distance_matrix: np.ndarray, max_passes: int = 15
) -> List[int]:
    """
    Recherche locale 2-opt adaptée au TSP asymétrique (ATSP).
    
    Pour un problème asymétrique, inverser un sous-segment pi[i:j] inverse également
    l'orientation de tous les arcs internes du sous-segment :
    Le coût évalue le changement global exact des arcs orientés.
    """
    best_perm = list(permutation)
    tour = [0] + best_perm + [0]
    n = len(best_perm)

    improved = True
    passes = 0

    while improved and passes < max_passes:
        improved = False
        passes += 1

        for i in range(1, n):
            for j in range(i + 1, n + 1):
                # Ancien coût des segments concernés :
                old_cost = distance_matrix[tour[i - 1], tour[i]] + distance_matrix[tour[j], tour[j + 1]]
                for k in range(i, j):
                    old_cost += distance_matrix[tour[k], tour[k + 1]]

                # Nouveau coût après inversion du sous-segment [i:j] :
                new_cost = distance_matrix[tour[i - 1], tour[j]] + distance_matrix[tour[i], tour[j + 1]]
                for k in range(i, j):
                    new_cost += distance_matrix[tour[k + 1], tour[k]]

                delta = new_cost - old_cost
                if delta < -1e-4:
                    tour[i : j + 1] = reversed(tour[i : j + 1])
                    improved = True
                    break
            if improved:
                break

    return tour[1:-1]


def asymmetric_relocate(
    permutation: List[int], distance_matrix: np.ndarray, max_passes: int = 10, max_seg_len: int = 3
) -> List[int]:
    """
    Recherche locale par relocalisation de sous-segments (Or-opt) adaptée à l'ATSP.
    Déplace un bloc contigu de longueur 1 à max_seg_len vers une autre position dans la tournée.
    Contrairement au 2-opt, l'orientation interne du bloc déplacé est conservée.
    """
    best_perm = list(permutation)
    improved = True
    passes = 0

    while improved and passes < max_passes:
        improved = False
        passes += 1
        best_cost = calculate_tour_cost([0] + best_perm + [0], distance_matrix)

        for seg_len in range(1, max_seg_len + 1):
            if seg_len >= len(best_perm):
                continue
            for i in range(len(best_perm) - seg_len + 1):
                seg = best_perm[i : i + seg_len]
                rem = best_perm[:i] + best_perm[i + seg_len :]
                for ins in range(len(rem) + 1):
                    cand = rem[:ins] + seg + rem[ins:]
                    cand_cost = calculate_tour_cost([0] + cand + [0], distance_matrix)
                    if cand_cost < best_cost - 1e-4:
                        best_perm = cand
                        best_cost = cand_cost
                        improved = True
                        break
                if improved:
                    break
            if improved:
                break

    return best_perm


def asymmetric_combined_local_search(
    permutation: List[int], distance_matrix: np.ndarray, max_passes: int = 15
) -> List[int]:
    """
    Recherche locale combinée alternant 2-opt asymétrique et Relocalisation (Or-opt).
    Permet d'échapper aux minima locaux spécifiques à chaque opérateur.
    """
    current_perm = list(permutation)
    best_cost = calculate_tour_cost([0] + current_perm + [0], distance_matrix)

    for _ in range(max_passes):
        # 1. 2-opt
        after_2opt = asymmetric_2opt(current_perm, distance_matrix, max_passes=10)
        c_2opt = calculate_tour_cost([0] + after_2opt + [0], distance_matrix)

        # 2. Relocate
        after_reloc = asymmetric_relocate(after_2opt, distance_matrix, max_passes=5, max_seg_len=3)
        c_reloc = calculate_tour_cost([0] + after_reloc + [0], distance_matrix)

        best_step = after_reloc if c_reloc <= c_2opt else after_2opt
        step_cost = min(c_reloc, c_2opt)

        if step_cost < best_cost - 1e-4:
            current_perm = best_step
            best_cost = step_cost
        else:
            break

    return current_perm
