"""
Tests unitaires pour le sélecteur des 40 destinations (src/data_collection/destination_selector.py).
"""

from unittest.mock import MagicMock, patch
import pytest
import pandas as pd
from src.data_collection.destination_selector import DestinationSelector


@pytest.fixture
def selector(tmp_path):
    # Création d'un échantillon représentatif de POIs pour tester la sélection
    records = []
    # 25 points Talborjt
    for i in range(1, 26):
        records.append({
            "osm_id": 1000 + i,
            "osm_type": "node",
            "name": f"POI Talborjt #{i}",
            "category": "Commerce & Magasin" if i % 2 == 0 else "Santé & Pharmacie",
            "subcategory": "supermarket" if i % 2 == 0 else "pharmacy",
            "latitude": 30.4230 + (i * 0.0002),
            "longitude": -9.5970 + (i * 0.0002),
            "x_utm": 442500.0 + i * 20,
            "y_utm": 3365300.0 + i * 20,
            "street": "Avenue des FAR",
        })
    # 25 points Centre-Ville
    for i in range(1, 26):
        records.append({
            "osm_id": 2000 + i,
            "osm_type": "node",
            "name": f"POI Centre #{i}",
            "category": "Banque & Finance" if i % 2 == 0 else "Restauration & Cafés",
            "subcategory": "bank" if i % 2 == 0 else "restaurant",
            "latitude": 30.4180 + (i * 0.0001),
            "longitude": -9.6000 + (i * 0.0001),
            "x_utm": 442200.0 + i * 20,
            "y_utm": 3364700.0 + i * 20,
            "street": "Boulevard Mohammed V",
        })

    csv_path = tmp_path / "mock_all_pois.csv"
    pd.DataFrame(records).to_csv(csv_path, index=False)
    return DestinationSelector(all_pois_csv=csv_path)


def test_select_40_destinations_structure(selector):
    # Mock OSRM pour un test unitaire rapide hors-ligne
    with patch.object(
        selector.osrm,
        "nearest",
        return_value={"success": True, "snapped_lat": 30.4200, "snapped_lon": -9.6000, "distance_m": 8.0, "street_name": "Rue Test"},
    ), patch.object(
        selector.osrm,
        "route",
        return_value={"success": True, "distance_m": 1200.0, "distance_km": 1.2, "duration_s": 180.0, "duration_min": 3.0, "geometry": {}},
    ):
        df_final, stats = selector.select_40_destinations()

        # 41 lignes au total : 1 dépôt (point 0) + 40 destinations (points 1 à 40)
        assert len(df_final) == 41

        # Dépôt
        depot = df_final[df_final["point_id"] == 0]
        assert len(depot) == 1
        assert "Place Al Amal" in depot.iloc[0]["name"]
        assert depot.iloc[0]["point_type"] == "Dépôt"

        # Destinations de livraison (1 à 40)
        destinations = df_final[df_final["point_id"] > 0]
        assert len(destinations) == 40

        # Destination Littorale (strictement 1)
        coastal = destinations[destinations["is_coastal"] == True]
        assert len(coastal) == 1
        assert coastal.iloc[0]["point_type"] == "Littoral"
        assert coastal.iloc[0]["district"] == "Corniche / Marina"
        assert coastal.iloc[0]["point_id"] == 40

        # Destinations Urbaines (strictement 39)
        urban = destinations[destinations["is_coastal"] == False]
        assert len(urban) == 39
        assert set(urban["district"].unique()).issubset({"Talborjt", "Centre-Ville"})

        # Vérification des colonnes métriques et GPS
        for col in ["latitude", "longitude", "x_utm", "y_utm", "osrm_snapped_lat", "osrm_snapped_lon", "osrm_snap_distance_m"]:
            assert col in df_final.columns
            assert df_final[col].notna().all()
