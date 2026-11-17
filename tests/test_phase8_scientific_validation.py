"""
Tests de validation scientifique pour la Phase 8 — AGADIR MAPPING.
Vérifie la reproductibilité des résultats, les propriétés topologiques d'asymétrie,
le facteur de circuité urbain, la stabilité d'Optuna et la protection absolue des données certifiées.
"""

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.multi_agent.audit_logger import verify_audit_trail_chain

ROOT_DIR = Path(__file__).resolve().parent.parent

# Empreintes SHA-256 certifiées des 4 fichiers protégés
PROTECTED_FILES = {
    "data/processed/delivery_points_40.csv": "03590423ea8a69eb97fc8ee62735777fbe12d8cb95e3aaca8d35a20051d1b200",
    "data/processed/distance_matrix.csv": "35a6dafdb3525e208bce807b10c6bf314c4b612b154a170fd98fe3f69612a34a",
    "data/processed/duration_matrix.csv": "891a3af33e8c35211200adadd1f1cc8c304e2207d850ea5e43ec05aa2c726426",
    "data/results/tsp_optimized_route.json": "6bf918b8d69998d9063790714437f10edadf7ebf1fc1289973516527cc906933",
}


@pytest.fixture(scope="module")
def distance_matrix():
    """Charge la matrice OSRM 41x41 certifiée."""
    csv_path = ROOT_DIR / "data" / "processed" / "distance_matrix.csv"
    df = pd.read_csv(csv_path, index_col=0)
    return df.values.astype(float)


@pytest.fixture(scope="module")
def tour_json():
    """Charge les données de la tournée optimisée certifiée."""
    json_path = ROOT_DIR / "data" / "results" / "tsp_optimized_route.json"
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def experiment_data():
    """Charge les données de l'expérience scientifique Phase 8."""
    json_path = ROOT_DIR / "outputs" / "reports" / "phase8_experiment_data.json"
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ==============================================================================
# 1. VALIDATION DE LA TOURNÉE CERTIFIÉE ET RECALCUL EXACT
# ==============================================================================

def test_reference_tour_invariants_and_distance(distance_matrix, tour_json):
    """Vérifie les 6 invariants stricts et recalcule la distance exacte sur la matrice."""
    tour = tour_json["tour"]
    assert len(tour) == 42, f"Attendu 42 arrêts, reçu {len(tour)}"
    assert tour[0] == 0, "La tournée doit débuter au Dépôt #0"
    assert tour[-1] == 0, "La tournée doit s'achever au Dépôt #0"
    assert 40 in tour, "Le point littoral singulier #40 doit être visité"

    clients_visited = tour[1:-1]
    assert len(clients_visited) == 40
    assert len(set(clients_visited)) == 40, "Tous les 40 clients doivent être uniques"
    assert set(clients_visited) == set(range(1, 41)), "Les clients 1 à 40 doivent tous être présents"

    # Recalcul mathématique déterministe sur distance_matrix.csv
    recalculated = sum(distance_matrix[tour[k], tour[k+1]] for k in range(41))
    assert pytest.approx(recalculated, abs=0.01) == 18933.1, (
        f"Incohérence mathématique : attendu 18933.1 m, calculé {recalculated} m"
    )
    assert tour_json["metadata"]["total_distance_meters"] == 18933.1


# ==============================================================================
# 2. PROPRIÉTÉS TOPOLOGIQUES ET ASYMÉTRIE ROUTIÈRE
# ==============================================================================

def test_osrm_matrix_asymmetry_index(distance_matrix, experiment_data):
    """Vérifie que la matrice OSRM justifie mathématiquement la modélisation ATSP."""
    asym = experiment_data["asymmetry"]

    # Norme de Frobenius de l'asymétrie
    diff = distance_matrix - distance_matrix.T
    frobenius_index = np.linalg.norm(diff) / np.linalg.norm(distance_matrix)
    assert frobenius_index > 0.15, f"L'asymétrie ({frobenius_index:.4f}) doit dépasser le seuil de 0.15"
    assert pytest.approx(asym["frobenius_asymmetry_index"], abs=0.01) == frobenius_index

    # Pourcentage de paires asymétriques
    assert asym["asymmetric_pairs_pct"] > 80.0, "Plus de 80% des paires doivent être asymétriques"
    assert asym["max_asymmetry_ratio"] > 2.0, "Le ratio max d'asymétrie doit dépasser 2.0 (sens uniques)"


def test_circuity_factor_urban_detour(experiment_data):
    """Vérifie que le facteur de circuité traduit les contraintes viaires urbaines."""
    circ = experiment_data["circuity"]
    assert circ["mean_circuity"] > 1.20, f"Le détour moyen ({circ['mean_circuity']}) doit dépasser 1.20"
    assert circ["median_circuity"] > 1.15
    assert len(circ["legs"]) == 41

    # Le point littoral #40 doit avoir une circuité élevée en raison de l'impasse
    leg40 = next(l for l in circ["legs"] if l["to_point_id"] == 40 or l["from_point_id"] == 40)
    assert leg40["circuity_factor"] > 1.0


# ==============================================================================
# 3. BENCHMARK ALGORITHMIQUE ET GAIN OPTUNA
# ==============================================================================

def test_algorithmic_gain_significance(experiment_data):
    """Vérifie la supériorité statistique de la Phase 5 (GA + Optuna TPE) sur les baselines."""
    bench = experiment_data["benchmarks"]
    opt = bench["M4_phase5_certified_optimum_m"]
    base = bench["M2_phase4_ga_baseline_m"]
    nn = bench["M1_nearest_neighbor_m"]
    rnd = bench["M0_random_tour_mean_m"]

    assert opt == 18933.1
    assert base == 21014.3
    assert opt < base, "Optuna doit améliorer la baseline Phase 4"
    assert opt < nn, "Optuna doit surpasser le Plus Proche Voisin"
    assert opt < rnd, "Optuna doit surpasser le Monte Carlo aléatoire"

    # Gain par rapport à Phase 4
    gain_pct = ((base - opt) / base) * 100
    assert pytest.approx(gain_pct, abs=0.05) == 9.90
    assert gain_pct >= 8.0, "Le gain doit dépasser le critère d'acceptation de 8%"


def test_optuna_reproducibility_across_seeds():
    """Vérifie que la solution est rigoureusement reproductible sur 10 graines aléatoires."""
    best_params_path = ROOT_DIR / "data" / "results" / "optuna_best_params.json"
    with open(best_params_path, "r", encoding="utf-8") as f:
        params_data = json.load(f)

    stats = params_data["validation_statistics"]
    assert stats["seeds_evaluated"] == 10
    assert stats["min_distance_m"] == 18933.1
    assert stats["mean_distance_m"] == 18933.1
    assert stats["std_distance_m"] == 0.0
    assert stats["stability_ratio_pct"] == 0.0


# ==============================================================================
# 4. GOUVERNANCE MULTI-AGENTS ET AUDIT SHA-256
# ==============================================================================

def test_multi_agent_judge_and_deterministic_veto(experiment_data):
    """Vérifie l'arbitrage contradictoire et le veto déterministe Python."""
    ma = experiment_data["multi_agent_evaluation"]
    assert ma["judge_weighted_score"] >= 0.90
    assert ma["verdict"] == "ACCEPTED_PENDING_VALIDATION"
    assert ma["deterministic_validator_status"] == "VALIDE"
    assert ma["deterministic_rules_checked"] == "6/6"
    assert ma["recalculated_distance_m"] == 18933.1
    assert ma["gain_m"] == 0.0


def test_audit_trail_chain_integrity():
    """Vérifie mathématiquement la continuité de la chaîne de hachage SHA-256 de la mission pilote."""
    audit_path = ROOT_DIR / "outputs" / "audit" / "AGADIR_MAPPING_PILOT_001.jsonl"
    assert audit_path.exists(), "Journal d'audit de la mission pilote introuvable"

    expected_hash = "cd368bf4e7efbfe93e2a31eeed5a1c6d766b37750f6c604d743f51e881c9ff39"
    is_valid, msg = verify_audit_trail_chain(audit_path, expected_final_hash=expected_hash)
    assert is_valid is True, f"Rupture de chaîne d'audit détectée : {msg}"


# ==============================================================================
# 5. SANCTUARISATION DES 4 FICHIERS PROTÉGÉS
# ==============================================================================

def test_four_protected_files_sha256_unaltered():
    """Contrôle cryptographique absolu que la Phase 8 a préservé les 4 fichiers sanctuarisés."""
    for rel_path, expected_hash in PROTECTED_FILES.items():
        file_path = ROOT_DIR / rel_path
        assert file_path.exists(), f"Fichier protégé manquant : {rel_path}"
        computed = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert computed == expected_hash, (
            f"VIOLATION D'INTÉGRITÉ sur {rel_path} : "
            f"attendu {expected_hash}, calculé {computed}"
        )
