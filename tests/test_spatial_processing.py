"""
Tests unitaires pour le module d'analyse spatiale (src/geographic/spatial_processing.py).
"""

import pytest
import pandas as pd
from src.geographic.spatial_processing import SpatialProcessor


@pytest.fixture
def spatial_proc():
    test_bbox = {
        "south": 30.4150,
        "west": -9.6080,
        "north": 30.4350,
        "east": -9.5840,
    }
    return SpatialProcessor(bbox=test_bbox)


def test_get_bbox_metrics(spatial_proc):
    metrics = spatial_proc.get_bbox_metrics()

    # Vérification des dimensions
    assert metrics["width_km"] > 0
    assert metrics["height_km"] > 0
    assert metrics["area_km2"] > 0

    # Pour cette BBOX d'Agadir, la largeur est d'environ 2.3 km et la hauteur d'environ 2.2 km
    assert 1.5 < metrics["width_km"] < 3.5
    assert 1.5 < metrics["height_km"] < 3.5
    assert 3.0 < metrics["area_km2"] < 10.0

    # Centroïde
    assert 30.4150 < metrics["center_gps"]["latitude"] < 30.4350
    assert -9.6080 < metrics["center_gps"]["longitude"] < -9.5840


def test_analyze_distribution(spatial_proc):
    sample_df = pd.DataFrame([
        {
            "osm_id": 1,
            "name": "Café Talborjt",
            "category": "Restauration & Cafés",
            "subcategory": "cafe",
            "latitude": 30.4220,
            "longitude": -9.5980,
            "x_utm": 442500.0,
            "y_utm": 3365200.0,
        },
        {
            "osm_id": 2,
            "name": "Pharmacie Centrale",
            "category": "Santé & Pharmacie",
            "subcategory": "pharmacy",
            "latitude": 30.4240,
            "longitude": -9.5960,
            "x_utm": 442700.0,
            "y_utm": 3365400.0,
        },
    ])

    analysis = spatial_proc.analyze_distribution(sample_df)

    assert analysis["total_points"] == 2
    assert analysis["named_points"] == 2
    assert analysis["unnamed_or_generic"] == 0
    assert analysis["categories"]["Restauration & Cafés"] == 1
    assert analysis["categories"]["Santé & Pharmacie"] == 1
    assert analysis["density_pois_per_km2"] > 0


def test_get_bbox_polygon_geojson(spatial_proc):
    geojson = spatial_proc.get_bbox_polygon_geojson()
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 1
    assert geojson["features"][0]["geometry"]["type"] == "Polygon"
