"""
Module d'analyse spatiale et de traitement géographique pour la zone d'Agadir.

Fournit :
- Le calcul précis des dimensions réelles (km, surface) de la Bounding Box
- L'audit spatial de la répartition des points d'intérêt extraits
- L'évaluation de la dispersion géographique (plus proche voisin, centroïde)
- La conversion et sauvegarde en formats standards (GeoJSON, CSV)
"""

from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, box

from config.settings import AGADIR_BBOX, GPS_CRS, METRIC_CRS
from src.geographic.projection import GeoProjector


class SpatialProcessor:
    """
    Gestionnaire d'analyse et de traitements spatiaux pour AGADIR MAPPING.
    """

    def __init__(self, bbox: Dict[str, float] = None):
        self.bbox = bbox or AGADIR_BBOX
        self.projector = GeoProjector()

    def get_bbox_metrics(self) -> Dict[str, Any]:
        """
        Calcule les dimensions métriques exactes de la Bounding Box d'étude en utilisant UTM Zone 29N.
        """
        s, w = self.bbox["south"], self.bbox["west"]
        n, e = self.bbox["north"], self.bbox["east"]

        x_sw, y_sw = self.projector.gps_to_utm(s, w)
        x_se, y_se = self.projector.gps_to_utm(s, e)
        x_nw, y_nw = self.projector.gps_to_utm(n, w)
        x_ne, y_ne = self.projector.gps_to_utm(n, e)

        width_m = (abs(x_se - x_sw) + abs(x_ne - x_nw)) / 2.0
        height_m = (abs(y_nw - y_sw) + abs(y_ne - y_se)) / 2.0
        area_km2 = (width_m * height_m) / 1_000_000.0

        center_lat = (s + n) / 2.0
        center_lon = (w + e) / 2.0
        x_c, y_c = self.projector.gps_to_utm(center_lat, center_lon)

        return {
            "bbox_gps": self.bbox,
            "width_meters": round(width_m, 2),
            "height_meters": round(height_m, 2),
            "width_km": round(width_m / 1000.0, 3),
            "height_km": round(height_m / 1000.0, 3),
            "area_km2": round(area_km2, 3),
            "center_gps": {"latitude": round(center_lat, 6), "longitude": round(center_lon, 6)},
            "center_utm": {"x": round(x_c, 2), "y": round(y_c, 2)},
        }

    def analyze_distribution(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyse la qualité et la distribution spatiale des POIs extraits.
        """
        if df.empty:
            return {"count": 0, "status": "empty"}

        xs = df["x_utm"].values
        ys = df["y_utm"].values

        # Centroïde moyen observé
        mean_x = float(np.mean(xs))
        mean_y = float(np.mean(ys))
        mean_lat, mean_lon = self.projector.utm_to_gps(mean_x, mean_y)

        # Écarts-types spatiaux (dispersion autour du centre)
        std_x_m = float(np.std(xs))
        std_y_m = float(np.std(ys))

        # Répartition par catégorie
        category_counts = df["category"].value_counts().to_dict()

        # Éléments nommés vs sans nom
        has_real_name = df["name"].apply(lambda n: "OSM #" not in str(n)).sum()

        return {
            "total_points": len(df),
            "named_points": int(has_real_name),
            "unnamed_or_generic": int(len(df) - has_real_name),
            "categories": category_counts,
            "observed_centroid_gps": {"latitude": round(mean_lat, 6), "longitude": round(mean_lon, 6)},
            "observed_centroid_utm": {"x": round(mean_x, 2), "y": round(mean_y, 2)},
            "dispersion_std_meters": {"x": round(std_x_m, 2), "y": round(std_y_m, 2)},
            "density_pois_per_km2": round(len(df) / self.get_bbox_metrics()["area_km2"], 2),
        }

    def get_bbox_polygon_geojson(self) -> Dict[str, Any]:
        """
        Génère la géométrie GeoJSON de la Bounding Box.
        """
        b = box(self.bbox["west"], self.bbox["south"], self.bbox["east"], self.bbox["north"])
        gdf = gpd.GeoDataFrame(geometry=[b], crs=GPS_CRS)
        return gdf.__geo_interface__
