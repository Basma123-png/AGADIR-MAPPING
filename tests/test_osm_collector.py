"""
Tests unitaires pour le collecteur de données OpenStreetMap (src/data_collection/osm_collector.py).
"""

import pytest
import pandas as pd
from shapely.geometry import Point

from src.data_collection.osm_collector import OSMDataCollector


@pytest.fixture
def collector():
    test_bbox = {
        "south": 30.4150,
        "west": -9.6080,
        "north": 30.4350,
        "east": -9.5840,
    }
    return OSMDataCollector(bbox=test_bbox)


def test_build_overpass_query(collector):
    query = collector.build_overpass_query()
    assert "shop" in query
    assert "amenity" in query
    assert "30.415,-9.608,30.435,-9.584" in query
    assert "out center;" in query


def test_classify_element():
    cat1, sub1 = OSMDataCollector._classify_element({"shop": "bakery"})
    assert cat1 == "Commerce & Magasin"
    assert sub1 == "bakery"

    cat2, sub2 = OSMDataCollector._classify_element({"amenity": "pharmacy"})
    assert cat2 == "Santé & Pharmacie"
    assert sub2 == "pharmacy"

    cat3, sub3 = OSMDataCollector._classify_element({"amenity": "restaurant"})
    assert cat3 == "Restauration & Cafés"
    assert sub3 == "restaurant"

    cat4, sub4 = OSMDataCollector._classify_element({"office": "lawyer"})
    assert cat4 == "Bureaux & Tertiaire"
    assert sub4 == "lawyer"

    cat_none, _ = OSMDataCollector._classify_element({"natural": "tree"})
    assert cat_none is None


def test_parse_elements(collector):
    # Données simulées au format Overpass
    mock_data = {
        "elements": [
            {
                "type": "node",
                "id": 101,
                "lat": 30.4220,
                "lon": -9.5980,
                "tags": {
                    "shop": "supermarket",
                    "name": "Supermarché Talborjt",
                    "addr:street": "Avenue Hassan II",
                },
            },
            {
                "type": "way",
                "id": 202,
                "center": {"lat": 30.4250, "lon": -9.5950},
                "tags": {
                    "amenity": "cafe",
                    "name": "Café de Paris",
                },
            },
            {
                # Élément hors BBOX (doit être filtré)
                "type": "node",
                "id": 303,
                "lat": 30.5000,
                "lon": -9.5000,
                "tags": {
                    "shop": "bakery",
                    "name": "Boulangerie Lointaine",
                },
            },
            {
                # Doublon du 101 (doit être dédoublonné)
                "type": "node",
                "id": 101,
                "lat": 30.4220,
                "lon": -9.5980,
                "tags": {
                    "shop": "supermarket",
                    "name": "Supermarché Talborjt",
                },
            },
        ]
    }

    df = collector.parse_elements(mock_data)

    assert len(df) == 2  # Le hors BBOX et le doublon ont été exclus
    assert 101 in df["osm_id"].values
    assert 202 in df["osm_id"].values
    assert 303 not in df["osm_id"].values

    # Vérification des colonnes calculées
    assert "x_utm" in df.columns
    assert "y_utm" in df.columns
    assert "category" in df.columns
    assert df.loc[df["osm_id"] == 101, "category"].iloc[0] == "Commerce & Magasin"
    assert df.loc[df["osm_id"] == 202, "category"].iloc[0] == "Restauration & Cafés"


def test_to_geodataframe(collector):
    df = pd.DataFrame([
        {
            "osm_id": 1,
            "name": "Point Test",
            "category": "Commerce & Magasin",
            "subcategory": "bakery",
            "latitude": 30.4220,
            "longitude": -9.5980,
            "x_utm": 442500.0,
            "y_utm": 3365200.0,
            "street": "Rue Test",
            "housenumber": "1",
        }
    ])

    gdf = collector.to_geodataframe(df)
    assert gdf.crs.to_string() == "EPSG:4326"
    assert isinstance(gdf.geometry.iloc[0], Point)
    assert gdf.geometry.iloc[0].x == -9.5980
    assert gdf.geometry.iloc[0].y == 30.4220
