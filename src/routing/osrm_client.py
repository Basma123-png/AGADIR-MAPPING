"""
Client OSRM (Open Source Routing Machine) pour AGADIR MAPPING.

Ce module gère :
- Le rattachement des coordonnées GPS au réseau routier réel via l'endpoint /nearest
- Le calcul d'itinéraires routiers réels entre points via l'endpoint /route
- La validation stricte de l'accessibilité routière pour les 40 destinations et le dépôt
"""

import logging
import time
from typing import Dict, Any, Tuple, Optional, List
import requests

from config.settings import OSRM_BASE_URL, NETWORK_TIMEOUT

logger = logging.getLogger(__name__)


class OSRMClient:
    """
    Interface de communication avec le service OSRM pour le profil de conduite urbaine (driving).
    """

    def __init__(self, base_url: str = OSRM_BASE_URL, timeout: int = NETWORK_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "AgadirMappingTSP/1.0 (academic routing validation)"
        })

    def nearest(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Rattache un point GPS au tronçon de route praticable le plus proche via /nearest/v1/driving/{lon},{lat}.

        Returns:
            Dict contenant :
            - snapped_lat, snapped_lon : Coordonnées réelles projetées sur la chaussée
            - distance_m : Distance euclidienne orthogonale entre le point et la route (en mètres)
            - street_name : Nom de la rue OSM
            - success : Booléen
        """
        url = f"{self.base_url}/nearest/v1/driving/{lon:.6f},{lat:.6f}"
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()

            if data.get("code") == "Ok" and data.get("waypoints"):
                wp = data["waypoints"][0]
                snapped_lon, snapped_lat = wp["location"]
                dist = wp.get("distance", 0.0)
                street = wp.get("name", "")
                return {
                    "success": True,
                    "snapped_lat": round(snapped_lat, 6),
                    "snapped_lon": round(snapped_lon, 6),
                    "distance_m": round(dist, 2),
                    "street_name": street or "Voie urbaine (non nommée)",
                }
            return {"success": False, "error": data.get("code", "Unknown")}

        except Exception as e:
            logger.warning("Échec OSRM nearest pour (lat=%s, lon=%s) : %s", lat, lon, e)
            return {"success": False, "error": str(e)}

    def route(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
        overview: str = "simplified",
    ) -> Dict[str, Any]:
        """
        Calcule l'itinéraire routier réel entre deux points via /route/v1/driving/{lon1},{lat1};{lon2},{lat2}.

        Returns:
            Dict contenant :
            - distance_m : Distance routière réelle en mètres
            - duration_s : Durée estimée en secondes
            - geometry : Coordonnées du tracé (polyline ou GeoJSON)
            - success : Booléen
        """
        url = f"{self.base_url}/route/v1/driving/{lon1:.6f},{lat1:.6f};{lon2:.6f},{lat2:.6f}"
        params = {
            "overview": overview,
            "geometries": "geojson",
            "steps": "false",
        }
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()

            if data.get("code") == "Ok" and data.get("routes"):
                route_data = data["routes"][0]
                return {
                    "success": True,
                    "distance_m": round(route_data["distance"], 1),
                    "distance_km": round(route_data["distance"] / 1000.0, 3),
                    "duration_s": round(route_data["duration"], 1),
                    "duration_min": round(route_data["duration"] / 60.0, 2),
                    "geometry": route_data.get("geometry", {}),
                }
            return {"success": False, "error": data.get("code", "Unknown")}

        except Exception as e:
            logger.warning("Échec OSRM route entre (%s,%s) et (%s,%s) : %s", lat1, lon1, lat2, lon2, e)
            return {"success": False, "error": str(e)}

    def table(
        self,
        coords: List[Tuple[float, float]],
        annotations: str = "duration,distance",
    ) -> Dict[str, Any]:
        """
        Calcule la matrice complète des distances et/ou durées routières via OSRM Table API.
        
        Args:
            coords: Liste ordonnée de tuples (lat, lon) pour chaque point.
            annotations: Métriques demandées ('duration', 'distance' ou 'duration,distance').
            
        Returns:
            Dict contenant :
            - success: bool
            - distances: matrice 2D (mètres)
            - durations: matrice 2D (secondes)
            - error: str si échec
        """
        # OSRM attend l'ordre longitude,latitude séparés par des points-virgules
        coords_str = ";".join([f"{lon:.6f},{lat:.6f}" for lat, lon in coords])
        url = f"{self.base_url}/table/v1/driving/{coords_str}"
        params = {"annotations": annotations}

        try:
            resp = self.session.get(url, params=params, timeout=max(self.timeout, 45))
            resp.raise_for_status()
            data = resp.json()

            if data.get("code") == "Ok":
                distances = data.get("distances")
                durations = data.get("durations")

                return {
                    "success": True,
                    "distances": distances,
                    "durations": durations,
                    "sources": data.get("sources", []),
                    "destinations": data.get("destinations", []),
                }
            return {"success": False, "error": data.get("code", "Unknown")}

        except Exception as e:
            logger.warning("Échec OSRM Table API pour %d points : %s", len(coords), e)
            return {"success": False, "error": str(e)}

    def validate_points_accessibility(
        self, points: List[Dict[str, Any]], max_snap_distance_m: float = 40.0
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Valide l'accessibilité routière d'une liste de points.
        Sépare les points validés de ceux rejetés (trop éloignés de la route ou inaccessibles).
        """
        valid_points = []
        rejected_points = []

        for pt in points:
            lat = pt["latitude"]
            lon = pt["longitude"]
            snap_res = self.nearest(lat, lon)

            if snap_res["success"] and snap_res["distance_m"] <= max_snap_distance_m:
                pt_copy = dict(pt)
                pt_copy["osrm_snapped_lat"] = snap_res["snapped_lat"]
                pt_copy["osrm_snapped_lon"] = snap_res["snapped_lon"]
                pt_copy["osrm_snap_distance_m"] = snap_res["distance_m"]
                pt_copy["osrm_street_name"] = snap_res["street_name"]
                valid_points.append(pt_copy)
            else:
                rejected_points.append({
                    "point": pt,
                    "reason": f"Distance au réseau routier ({snap_res.get('distance_m')} m) > {max_snap_distance_m} m"
                    if snap_res["success"] else snap_res.get("error"),
                })
            time.sleep(0.05)  # Respect courtois des quotas publics OSRM

        return valid_points, rejected_points
