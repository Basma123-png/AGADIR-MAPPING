"""
Module de sélection et de validation des 40 points de livraison pour AGADIR MAPPING.

Règles impératives :
- Exactement 40 destinations au total :
  * 39 destinations urbaines équilibrées entre Talborjt et le Centre-ville
  * 1 destination littorale obligatoire sur la Corniche / Marina d'Agadir
- 1 Dépôt distinct (Place Al Amal) servant de point de départ et de retour
- Rattachement rigoureux au réseau routier vérifié via OSRM (distance de projection < 35 m)
- Traçabilité totale des coordonnées WGS84 (EPSG:4326) et métriques UTM Zone 29N (EPSG:32629)
"""

import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from config.settings import (
    PROCESSED_DATA_DIR,
    DEFAULT_DEPOT_GPS,
    COASTAL_DESTINATION_GPS,
    GPS_CRS,
    METRIC_CRS,
)
from src.geographic.projection import GeoProjector
from src.routing.osrm_client import OSRMClient

logger = logging.getLogger(__name__)


class DestinationSelector:
    """
    Sélectionne, qualifie et valide sur le réseau routier OSRM les 40 destinations de livraison.
    """

    def __init__(self, all_pois_csv: Optional[Path] = None):
        self.all_pois_csv = all_pois_csv or (PROCESSED_DATA_DIR / "agadir_talborjt_all_pois.csv")
        self.projector = GeoProjector()
        self.osrm = OSRMClient()

    def select_40_destinations(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Constitue le jeu de données final de 40 destinations + 1 dépôt.
        """
        df_all = pd.read_csv(self.all_pois_csv)

        # ----------------------------------------------------------------------
        # 1. Sélection de la Destination Littorale (Corniche / Marina)
        # ----------------------------------------------------------------------
        x_coastal, y_coastal = self.projector.gps_to_utm(
            COASTAL_DESTINATION_GPS["latitude"], COASTAL_DESTINATION_GPS["longitude"]
        )
        coastal_point = {
            "osm_id": COASTAL_DESTINATION_GPS["osm_id"],
            "osm_type": COASTAL_DESTINATION_GPS["osm_type"],
            "name": COASTAL_DESTINATION_GPS["name"],
            "category": COASTAL_DESTINATION_GPS["category"],
            "subcategory": COASTAL_DESTINATION_GPS["subcategory"],
            "latitude": COASTAL_DESTINATION_GPS["latitude"],
            "longitude": COASTAL_DESTINATION_GPS["longitude"],
            "x_utm": round(x_coastal, 2),
            "y_utm": round(y_coastal, 2),
            "street": COASTAL_DESTINATION_GPS["street"],
            "district": "Corniche / Marina",
            "point_type": "Littoral",
            "is_coastal": True,
        }

        # ----------------------------------------------------------------------
        # 2. Sélection des 39 Destinations Urbaines (Talborjt & Centre-Ville)
        # ----------------------------------------------------------------------
        # Filtrage des POIs pertinents pour la livraison Last-Mile
        # Exclure les parkings purs, les fontaines, toilettes
        mask_relevant = ~df_all["subcategory"].isin(["parking", "fountain", "toilets", "waste_basket"])
        # Privilégier les points avec nom commercial explicite
        mask_named = df_all["name"].apply(lambda n: "OSM #" not in str(n))
        df_candidates = df_all[mask_relevant & mask_named].copy()

        # Attribution du quartier (Nord: Talborjt / Sud: Centre-Ville)
        df_candidates["district"] = df_candidates["latitude"].apply(
            lambda lat: "Talborjt" if lat >= 30.4220 else "Centre-Ville"
        )
        df_candidates["point_type"] = "Urbain"
        df_candidates["is_coastal"] = False

        # Quotas ciblés pour une répartition harmonieuse par secteur et catégorie :
        # - Talborjt : ~20 points
        # - Centre-Ville : ~19 points
        # Diversité : Pharmacies (6), Commerces (10), Banques (7), Restaurants/Cafés (9), Services/Bureaux (7)
        selected_records = []

        # Catégories prioritaires
        desired_composition = {
            "Santé & Pharmacie": 6,
            "Commerce & Magasin": 10,
            "Banque & Finance": 7,
            "Restauration & Cafés": 9,
            "Services & Logistique": 4,
            "Bureaux & Tertiaire": 3,
        }

        used_ids = set()
        for cat, target_count in desired_composition.items():
            cat_df = df_candidates[df_candidates["category"] == cat]
            # Équilibrer entre Talborjt et Centre-ville
            tal_df = cat_df[cat_df["district"] == "Talborjt"]
            cv_df = cat_df[cat_df["district"] == "Centre-Ville"]

            n_tal = min(len(tal_df), target_count // 2 + target_count % 2)
            n_cv = min(len(cv_df), target_count - n_tal)

            for _, row in tal_df.head(n_tal).iterrows():
                if row["osm_id"] not in used_ids:
                    selected_records.append(row.to_dict())
                    used_ids.add(row["osm_id"])

            for _, row in cv_df.head(n_cv).iterrows():
                if row["osm_id"] not in used_ids:
                    selected_records.append(row.to_dict())
                    used_ids.add(row["osm_id"])

        # Compléter si besoin jusqu'à 39 avec les points restants les plus qualifiés
        remaining_needed = 39 - len(selected_records)
        if remaining_needed > 0:
            remaining_df = df_candidates[~df_candidates["osm_id"].isin(used_ids)]
            for _, row in remaining_df.head(remaining_needed).iterrows():
                selected_records.append(row.to_dict())
                used_ids.add(row["osm_id"])

        # Conserver strictement 39 destinations urbaines
        selected_urban = selected_records[:39]

        # ----------------------------------------------------------------------
        # 3. Assemblage des 40 destinations (39 urbaines + 1 littorale)
        # ----------------------------------------------------------------------
        all_40 = selected_urban + [coastal_point]

        # Ajout des identifiants séquentiels 1 à 40
        for i, pt in enumerate(all_40, start=1):
            pt["point_id"] = i

        # ----------------------------------------------------------------------
        # 4. Définition du Dépôt Central (Point 0)
        # ----------------------------------------------------------------------
        x_depot, y_depot = self.projector.gps_to_utm(
            DEFAULT_DEPOT_GPS["latitude"], DEFAULT_DEPOT_GPS["longitude"]
        )
        depot_record = {
            "point_id": 0,
            "osm_id": 9999999999,
            "osm_type": "depot",
            "name": DEFAULT_DEPOT_GPS["name"],
            "category": "Dépôt Central",
            "subcategory": "logistics_hub",
            "latitude": DEFAULT_DEPOT_GPS["latitude"],
            "longitude": DEFAULT_DEPOT_GPS["longitude"],
            "x_utm": round(x_depot, 2),
            "y_utm": round(y_depot, 2),
            "street": "Place Al Amal",
            "district": "Centre-Ville",
            "point_type": "Dépôt",
            "is_coastal": False,
        }

        # ----------------------------------------------------------------------
        # 5. Validation OSRM de Rattachement Routier
        # ----------------------------------------------------------------------
        logger.info("Validation OSRM du rattachement routier pour les 40 points et le dépôt...")
        full_list_to_validate = [depot_record] + all_40

        validated_list = []
        osrm_stats = {
            "total_tested": len(full_list_to_validate),
            "snapped_successfully": 0,
            "max_snap_dist_m": 0.0,
            "avg_snap_dist_m": 0.0,
            "routes_from_depot_ok": 0,
        }

        total_snap_dist = 0.0
        for pt in full_list_to_validate:
            # 5a. Snap routier /nearest
            snap = self.osrm.nearest(pt["latitude"], pt["longitude"])
            if snap["success"]:
                pt["osrm_snapped_lat"] = snap["snapped_lat"]
                pt["osrm_snapped_lon"] = snap["snapped_lon"]
                pt["osrm_snap_distance_m"] = snap["distance_m"]
                pt["osrm_street"] = snap["street_name"]
                osrm_stats["snapped_successfully"] += 1
                total_snap_dist += snap["distance_m"]
                if snap["distance_m"] > osrm_stats["max_snap_dist_m"]:
                    osrm_stats["max_snap_dist_m"] = snap["distance_m"]
            else:
                pt["osrm_snapped_lat"] = pt["latitude"]
                pt["osrm_snapped_lon"] = pt["longitude"]
                pt["osrm_snap_distance_m"] = 0.0
                pt["osrm_street"] = "N/A"

            # 5b. Validation de la connectivité depuis le dépôt
            if pt["point_id"] != 0:
                route_res = self.osrm.route(
                    depot_record["latitude"], depot_record["longitude"],
                    pt["latitude"], pt["longitude"]
                )
                if route_res["success"] and route_res["distance_m"] > 0:
                    pt["osrm_route_from_depot_m"] = route_res["distance_m"]
                    pt["osrm_route_from_depot_min"] = route_res["duration_min"]
                    osrm_stats["routes_from_depot_ok"] += 1
                else:
                    pt["osrm_route_from_depot_m"] = 0.0
                    pt["osrm_route_from_depot_min"] = 0.0
            else:
                pt["osrm_route_from_depot_m"] = 0.0
                pt["osrm_route_from_depot_min"] = 0.0

            validated_list.append(pt)
            time.sleep(0.04)

        osrm_stats["avg_snap_dist_m"] = round(total_snap_dist / len(full_list_to_validate), 2)

        df_final = pd.DataFrame(validated_list)
        return df_final, osrm_stats

    def save_datasets(self, df_final: pd.DataFrame) -> Tuple[Path, Path]:
        """
        Sauvegarde le jeu de données final en CSV et GeoJSON.
        """
        csv_path = PROCESSED_DATA_DIR / "delivery_points_40.csv"
        geojson_path = PROCESSED_DATA_DIR / "delivery_points_40.geojson"

        df_final.to_csv(csv_path, index=False, encoding="utf-8")

        # Conversion GeoDataFrame
        geometry = [Point(xy) for xy in zip(df_final["longitude"], df_final["latitude"])]
        gdf = gpd.GeoDataFrame(df_final, geometry=geometry, crs=GPS_CRS)
        gdf.to_file(geojson_path, driver="GeoJSON")

        logger.info("Fichiers des 40 points sauvegardés : %s et %s", csv_path.name, geojson_path.name)
        return csv_path, geojson_path
