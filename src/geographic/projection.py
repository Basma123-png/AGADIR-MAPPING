"""
Module de gestion des projections géographiques et métriques pour Agadir.

Systèmes de référence utilisés :
- EPSG:4326 (WGS84) : Coordonnées angulaires GPS standards (latitude, longitude en degrés)
- EPSG:32629 (UTM Zone 29N) : Projection cartographique métrique conforme adaptée à Agadir.
  Permet de calculer avec une précision millimétrique les distances cartésiennes euclidiennes (en mètres et km).
"""

from typing import Tuple, Union, List
import math
import numpy as np
from pyproj import Transformer, CRS

from config.settings import GPS_CRS, METRIC_CRS


class GeoProjector:
    """
    Gestionnaire bidirectionnel de projection spatiale pour la zone d'Agadir.
    
    Transforme les coordonnées entre WGS84 (EPSG:4326) et UTM Zone 29N (EPSG:32629).
    """

    def __init__(self, source_crs: str = GPS_CRS, target_crs: str = METRIC_CRS):
        self.source_crs = source_crs
        self.target_crs = target_crs
        
        # always_xy=True assure que l'ordre est (longitude, latitude) / (easting, northing)
        self.transformer_to_metric = Transformer.from_crs(
            CRS(self.source_crs), CRS(self.target_crs), always_xy=True
        )
        self.transformer_to_gps = Transformer.from_crs(
            CRS(self.target_crs), CRS(self.source_crs), always_xy=True
        )

    def gps_to_utm(self, lat: float, lon: float) -> Tuple[float, float]:
        """
        Convertit des coordonnées GPS (lat, lon) en coordonnées UTM (X, Y) en mètres.

        Args:
            lat: Latitude en degrés décimaux (ex: 30.4215)
            lon: Longitude en degrés décimaux (ex: -9.5985)

        Returns:
            Tuple (x, y) en mètres dans UTM Zone 29N.
        """
        self._validate_agadir_gps(lat, lon)
        x, y = self.transformer_to_metric.transform(lon, lat)
        return float(x), float(y)

    def utm_to_gps(self, x: float, y: float) -> Tuple[float, float]:
        """
        Convertit des coordonnées UTM Zone 29N (X, Y) en GPS (lat, lon).

        Args:
            x: Coordonnée Est (Easting) en mètres
            y: Coordonnée Nord (Northing) en mètres

        Returns:
            Tuple (latitude, longitude) en degrés décimaux WGS84.
        """
        lon, lat = self.transformer_to_gps.transform(x, y)
        return float(lat), float(lon)

    def batch_gps_to_utm(
        self, lats: Union[List[float], np.ndarray], lons: Union[List[float], np.ndarray]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Conversion par lot d'un ensemble de coordonnées GPS vers UTM Zone 29N.
        """
        xs, ys = self.transformer_to_metric.transform(lons, lats)
        return np.array(xs, dtype=float), np.array(ys, dtype=float)

    @staticmethod
    def euclidean_distance_meters(x1: float, y1: float, x2: float, y2: float) -> float:
        """
        Calcule la distance euclidienne cartésienne en mètres entre deux points UTM.
        """
        return math.hypot(x2 - x1, y2 - y1)

    @staticmethod
    def euclidean_distance_km(x1: float, y1: float, x2: float, y2: float) -> float:
        """
        Calcule la distance euclidienne cartésienne en kilomètres entre deux points UTM.
        """
        return math.hypot(x2 - x1, y2 - y1) / 1000.0

    @staticmethod
    def _validate_agadir_gps(lat: float, lon: float) -> None:
        """
        Vérification de bon sens : s'assure que les coordonnées sont cohérentes avec la région d'Agadir.
        Agadir se situe approximativement entre 30.2°N et 30.6°N et -9.8°W et -9.4°W.
        """
        if not (29.5 <= lat <= 31.5):
            raise ValueError(f"Latitude hors de la zone d'Agadir / Souss-Massa: {lat}°N")
        if not (-10.5 <= lon <= -8.5):
            raise ValueError(f"Longitude hors de la zone d'Agadir / Souss-Massa: {lon}°W")
