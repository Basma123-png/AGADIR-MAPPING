"""
Tests unitaires pour le module de projection géographique (src/geographic/projection.py).
Vérifie les conversions bidirectionnelles EPSG:4326 (WGS84) <-> EPSG:32629 (UTM Zone 29N).
"""

import math
import pytest
import numpy as np
from src.geographic.projection import GeoProjector


@pytest.fixture
def projector():
    return GeoProjector()


def test_projector_initialization(projector):
    assert projector.source_crs == "EPSG:4326"
    assert projector.target_crs == "EPSG:32629"


def test_gps_to_utm_and_back(projector):
    # Coordonnées réelles du centre d'Agadir (Place Al Amal)
    lat_orig = 30.421500
    lon_orig = -9.598500

    x, y = projector.gps_to_utm(lat_orig, lon_orig)

    # UTM Zone 29N pour Agadir : X doit être autour de 442000m et Y autour de 3365000m
    assert 400000 < x < 500000, f"X UTM incohérent pour Agadir: {x}"
    assert 3300000 < y < 3400000, f"Y UTM incohérent pour Agadir: {y}"

    # Reconversion en GPS WGS84
    lat_back, lon_back = projector.utm_to_gps(x, y)

    assert math.isclose(lat_orig, lat_back, abs_tol=1e-5), f"Erreur de latitude: {lat_orig} != {lat_back}"
    assert math.isclose(lon_orig, lon_back, abs_tol=1e-5), f"Erreur de longitude: {lon_orig} != {lon_back}"


def test_batch_gps_to_utm(projector):
    lats = np.array([30.4215, 30.4250, 30.4300])
    lons = np.array([-9.5985, -9.6000, -9.5950])

    xs, ys = projector.batch_gps_to_utm(lats, lons)

    assert len(xs) == 3
    assert len(ys) == 3
    assert np.all(xs > 400000)
    assert np.all(ys > 3300000)


def test_euclidean_distance(projector):
    # Distance entre deux points distants de 300m et 400m en X et Y
    d_m = projector.euclidean_distance_meters(0, 0, 300, 400)
    d_km = projector.euclidean_distance_km(0, 0, 300, 400)

    assert math.isclose(d_m, 500.0, rel_tol=1e-6)
    assert math.isclose(d_km, 0.5, rel_tol=1e-6)


def test_out_of_bounds_validation(projector):
    # Coordonnées hors de la région d'Agadir (ex: Paris) doivent lever ValueError
    with pytest.raises(ValueError, match="Latitude hors de la zone d'Agadir"):
        projector.gps_to_utm(48.8566, 2.3522)
