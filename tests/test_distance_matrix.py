"""
Tests unitaires pour le constructeur et validateur des matrices de distances et durées (src/routing/distance_matrix.py).
"""

from unittest.mock import MagicMock, patch
import pytest
import numpy as np
import pandas as pd

from src.routing.distance_matrix import DistanceMatrixBuilder


@pytest.fixture
def sample_points_csv(tmp_path):
    records = []
    # Création de 41 points ordonnés 0 à 40
    for i in range(41):
        records.append({
            "point_id": i,
            "osm_id": 1000 + i,
            "name": f"Point #{i}" if i > 0 else "Dépôt Central",
            "category": "Commerce" if i > 0 else "Dépôt Central",
            "subcategory": "shop",
            "latitude": 30.4200 + (i * 0.0003),
            "longitude": -9.6000 + (i * 0.0003),
            "x_utm": 442000.0 + i * 30,
            "y_utm": 3365000.0 + i * 30,
            "district": "Talborjt",
            "point_type": "Dépôt" if i == 0 else "Urbain",
            "is_coastal": (i == 40),
        })
    csv_file = tmp_path / "test_41_points.csv"
    pd.DataFrame(records).to_csv(csv_file, index=False)
    return csv_file


def test_load_ordered_points(sample_points_csv):
    builder = DistanceMatrixBuilder(points_csv=sample_points_csv)
    df = builder.load_ordered_points()
    assert len(df) == 41
    assert list(df["point_id"]) == list(range(41))
    assert df.iloc[0]["point_id"] == 0
    assert df.iloc[40]["point_id"] == 40


def test_cartesian_matrix_properties(sample_points_csv):
    builder = DistanceMatrixBuilder(points_csv=sample_points_csv)
    df = builder.load_ordered_points()
    cart_matrix = builder.compute_cartesian_matrix(df)

    assert cart_matrix.shape == (41, 41)
    # Diagonale strictement nulle
    assert np.all(np.diag(cart_matrix) == 0.0)
    # Symétrie parfaite de la distance euclidienne
    assert np.allclose(cart_matrix, cart_matrix.T, atol=1e-5)
    # Positivité
    assert np.all(cart_matrix >= 0.0)


def test_audit_matrices_logic(sample_points_csv):
    builder = DistanceMatrixBuilder(points_csv=sample_points_csv)
    df = builder.load_ordered_points()
    n = 41

    # Matrice simulée avec légère asymétrie
    np.random.seed(42)
    base_dist = np.random.uniform(500, 3000, size=(n, n))
    np.fill_diagonal(base_dist, 0.0)
    base_dur = base_dist / 10.0  # ~10 m/s

    cart_dist = base_dist * 0.8  # Cartésien inférieur au routier
    np.fill_diagonal(cart_dist, 0.0)

    report = builder.audit_matrices(base_dist, base_dur, cart_dist, df)

    assert report["shape_valid"] is True
    assert report["matrix_shape"] == [41, 41]
    assert report["diagonal_zero"] is True
    assert report["all_paths_feasible"] is True
    assert report["unreachable_paths_count"] == 0
    assert report["circuity_factor"]["mean"] > 1.0
    assert report["mean_distance_asymmetry_pct"] >= 0.0


def test_export_matrices(sample_points_csv, tmp_path):
    builder = DistanceMatrixBuilder(points_csv=sample_points_csv)
    df = builder.load_ordered_points()
    n = 41

    dist_matrix = np.ones((n, n), dtype=float) * 1500.0
    np.fill_diagonal(dist_matrix, 0.0)
    dur_matrix = np.ones((n, n), dtype=float) * 180.0
    np.fill_diagonal(dur_matrix, 0.0)
    cart_matrix = np.ones((n, n), dtype=float) * 1200.0
    np.fill_diagonal(cart_matrix, 0.0)

    paths = builder.export_matrices(
        dist_matrix, dur_matrix, cart_matrix, df, output_dir=tmp_path, results_dir=tmp_path
    )

    assert paths["dist_csv"].exists()
    assert paths["dur_csv"].exists()
    assert paths["dist_json"].exists()
    assert paths["dur_json"].exists()

    # Relecture CSV
    df_read = pd.read_csv(paths["dist_csv"], index_col=0)
    assert df_read.shape == (41, 41)
    assert df_read.iloc[0, 0] == 0.0
    assert df_read.iloc[0, 1] == 1500.0
