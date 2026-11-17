"""
Tests unitaires pour le module d'optimisation Optuna (OptunaTuner).
"""

import json
from pathlib import Path
import numpy as np
import pytest

from src.optimization.optuna_tuner import OptunaTuner
from src.genetic_algorithm.operators import (
    scramble_mutation,
    insertion_mutation,
    asymmetric_relocate,
    asymmetric_combined_local_search,
)


@pytest.fixture
def sample_atsp_matrix():
    """Génère une petite matrice asymétrique 6x6 pour les tests unitaires rapides."""
    rng = np.random.default_rng(42)
    mat = rng.uniform(50.0, 500.0, size=(6, 6))
    np.fill_diagonal(mat, 0.0)
    return mat


def test_new_operators_validity(sample_atsp_matrix):
    """Vérifie la validité des nouveaux opérateurs génétiques et de recherche locale."""
    base_perm = [1, 2, 3, 4, 5]
    rng = np.random.default_rng(42)

    # 1. Insertion mutation
    mut_ins = insertion_mutation(base_perm, mutation_rate=1.0, rng=rng)
    assert sorted(mut_ins) == base_perm
    assert len(mut_ins) == 5

    # 2. Scramble mutation
    mut_scramble = scramble_mutation(base_perm, mutation_rate=1.0, rng=rng)
    assert sorted(mut_scramble) == base_perm
    assert len(mut_scramble) == 5

    # 3. Asymmetric Relocate local search
    reloc_perm = asymmetric_relocate(base_perm, sample_atsp_matrix, max_passes=5)
    assert sorted(reloc_perm) == base_perm
    assert len(reloc_perm) == 5

    # 4. Asymmetric Combined local search
    comb_perm = asymmetric_combined_local_search(base_perm, sample_atsp_matrix, max_passes=5)
    assert sorted(comb_perm) == base_perm
    assert len(comb_perm) == 5


def test_optuna_tuner_initialization(sample_atsp_matrix, tmp_path):
    """Vérifie l'initialisation et la configuration du tuner Optuna."""
    db_file = tmp_path / "test_study.db"
    tuner = OptunaTuner(
        distance_matrix=sample_atsp_matrix,
        n_destinations=5,
        study_name="test_atsp_tuning",
        db_path=db_file,
        eval_seeds=[42, 101],
        validation_seeds=[42, 101, 777],
    )
    assert tuner.study_name == "test_atsp_tuning"
    assert tuner.n_destinations == 5
    assert len(tuner.eval_seeds) == 2
    assert len(tuner.validation_seeds) == 3


def test_optuna_short_study_and_export(sample_atsp_matrix, tmp_path):
    """Exécute une étude très courte (2 essais) et teste l'exportation des fichiers."""
    db_file = tmp_path / "test_study.db"
    out_dir = tmp_path / "results"
    fig_dir = tmp_path / "figures"

    tuner = OptunaTuner(
        distance_matrix=sample_atsp_matrix,
        n_destinations=5,
        study_name="test_atsp_tuning",
        db_path=db_file,
        eval_seeds=[42],
        validation_seeds=[42, 101],
    )

    study = tuner.run_study(n_trials=2)
    assert len(study.trials) == 2
    assert study.best_value > 0

    val_summary = tuner.run_extended_validation()
    assert "mean_distance_m" in val_summary
    assert "min_distance_m" in val_summary
    assert len(val_summary["runs"]) == 2

    files = tuner.export_results(output_dir=out_dir, figures_dir=fig_dir)
    assert files["best_params_json"].exists()
    assert files["trials_csv"].exists()

    with open(files["best_params_json"], "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "best_params" in data
    assert "validation_statistics" in data
