"""
Tests unitaires pour le client OSRM (src/routing/osrm_client.py).
"""

from unittest.mock import MagicMock, patch
import pytest
from src.routing.osrm_client import OSRMClient


@pytest.fixture
def osrm_client():
    return OSRMClient()


def test_osrm_initialization(osrm_client):
    assert "project-osrm.org" in osrm_client.base_url
    assert osrm_client.timeout > 0


def test_nearest_parsing_success(osrm_client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "code": "Ok",
        "waypoints": [
            {
                "location": [-9.5980, 30.4220],
                "distance": 8.5,
                "name": "Avenue Hassan II",
            }
        ],
    }

    with patch.object(osrm_client.session, "get", return_value=mock_resp):
        res = osrm_client.nearest(30.4221, -9.5981)
        assert res["success"] is True
        assert res["snapped_lat"] == 30.4220
        assert res["snapped_lon"] == -9.5980
        assert res["distance_m"] == 8.5
        assert res["street_name"] == "Avenue Hassan II"


def test_route_parsing_success(osrm_client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "code": "Ok",
        "routes": [
            {
                "distance": 1500.0,
                "duration": 240.0,
                "geometry": {"type": "LineString", "coordinates": []},
            }
        ],
    }

    with patch.object(osrm_client.session, "get", return_value=mock_resp):
        res = osrm_client.route(30.4215, -9.5985, 30.4300, -9.5900)
        assert res["success"] is True
        assert res["distance_m"] == 1500.0
        assert res["distance_km"] == 1.5
        assert res["duration_s"] == 240.0
        assert res["duration_min"] == 4.0


def test_validate_points_accessibility(osrm_client):
    points = [
        {"id": 1, "latitude": 30.4220, "longitude": -9.5980},
        {"id": 2, "latitude": 30.4250, "longitude": -9.5950},
    ]

    with patch.object(
        osrm_client,
        "nearest",
        side_effect=[
            {"success": True, "snapped_lat": 30.4220, "snapped_lon": -9.5980, "distance_m": 5.0, "street_name": "Rue A"},
            {"success": True, "snapped_lat": 30.4250, "snapped_lon": -9.5950, "distance_m": 80.0, "street_name": "Rue B"},
        ],
    ):
        valid, rejected = osrm_client.validate_points_accessibility(points, max_snap_distance_m=35.0)
        assert len(valid) == 1
        assert valid[0]["id"] == 1
        assert len(rejected) == 1
        assert rejected[0]["point"]["id"] == 2
