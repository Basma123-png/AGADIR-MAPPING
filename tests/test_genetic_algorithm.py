"""
Tests unitaires pour le moteur de l'Algorithme Génétique TSP (src/genetic_algorithm/).
"""

import pytest
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
    asymmetric_2opt,
)
from src.genetic_algorithm.engine import GeneticAlgorithm


@pytest.fixture
def mock_asymmetric_matrix():
    # Matrice 41x41 (dépôt 0 + 40 destinations) asymétrique
    n = 41
    rng = np.random.default_rng(42)
    mat = rng.uniform(200, 3000, size=(n, n))
    np.fill_diagonal(mat, 0.0)
    # Assurer une nette asymétrie
    mat[1, 2] = 100.0
    mat[2, 1] = 500.0
    return mat


def test_individual_evaluation(mock_asymmetric_matrix):
    perm = list(range(1, 41))
    ind = Individual(perm, mock_asymmetric_matrix)

    assert ind.is_valid(40) is True
    assert ind.distance > 0.0
    assert ind.fitness > 0.0

    full_tour = ind.get_full_tour()
    assert len(full_tour) == 42
    assert full_tour[0] == 0
    assert full_tour[-1] == 0
    assert set(full_tour[1:-1]) == set(range(1, 41))


def test_operators_validity():
    rng = np.random.default_rng(42)
    p1 = list(range(1, 41))
    p2 = list(reversed(range(1, 41)))

    # 1. Order Crossover (OX)
    c1, c2 = order_crossover_ox(p1, p2, rng)
    assert len(c1) == 40 and len(c2) == 40
    assert set(c1) == set(range(1, 41))
    assert set(c2) == set(range(1, 41))

    # 2. Partially Mapped Crossover (PMX)
    c3, c4 = partially_mapped_crossover_pmx(p1, p2, rng)
    assert len(c3) == 40 and len(c4) == 40
    assert set(c3) == set(range(1, 41))
    assert set(c4) == set(range(1, 41))

    # 3. Mutations
    mut_inv = inversion_mutation(p1, mutation_rate=1.0, rng=rng)
    assert len(mut_inv) == 40
    assert set(mut_inv) == set(range(1, 41))

    mut_swap = swap_mutation(p1, mutation_rate=1.0, rng=rng)
    assert len(mut_swap) == 40
    assert set(mut_swap) == set(range(1, 41))


def test_asymmetric_2opt(mock_asymmetric_matrix):
    perm = list(range(1, 41))
    ind_before = Individual(perm, mock_asymmetric_matrix)

    improved_perm = asymmetric_2opt(perm, mock_asymmetric_matrix, max_passes=5)
    ind_after = Individual(improved_perm, mock_asymmetric_matrix)

    assert ind_after.is_valid(40)
    # 2-opt ne doit jamais dégrader la tournée
    assert ind_after.distance <= ind_before.distance


def test_population_management(mock_asymmetric_matrix):
    rng = np.random.default_rng(42)
    pop = Population.create_random(pop_size=20, n_destinations=40, distance_matrix=mock_asymmetric_matrix, rng=rng)

    assert len(pop) == 20
    best = pop.best_individual()
    worst = pop.worst_individual()
    assert best.distance <= worst.distance
    assert pop.average_distance() >= best.distance

    elites = pop.get_elites(3)
    assert len(elites) == 3
    assert elites[0].distance == best.distance


def test_genetic_algorithm_reproducibility(mock_asymmetric_matrix):
    # Deux runs avec la même graine doivent produire rigoureusement les mêmes résultats
    ga1 = GeneticAlgorithm(
        distance_matrix=mock_asymmetric_matrix,
        population_size=10,
        max_generations=15,
        seed=123,
    )
    best1, sum1 = ga1.run()

    ga2 = GeneticAlgorithm(
        distance_matrix=mock_asymmetric_matrix,
        population_size=10,
        max_generations=15,
        seed=123,
    )
    best2, sum2 = ga2.run()

    assert best1.distance == best2.distance
    assert best1.permutation == best2.permutation
    assert sum1["final_distance_m"] == sum2["final_distance_m"]
    assert sum1["history"]["best_distance"] == sum2["history"]["best_distance"]
    # La solution finale doit s'être améliorée par rapport à l'initiale
    assert best1.distance <= sum1["initial_distance_m"]
