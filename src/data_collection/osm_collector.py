"""
Module d'extraction de données géographiques réelles depuis OpenStreetMap via Overpass API.

Règles impératives :
- Extraction stricte de données réelles (aucun point GPS synthétique/inventé).
- Sauvegarde intégrale du fichier brut dans data/raw/agadir_talborjt_raw.json.
- Résilience réseau : gestion des timeouts, essais multiples et bascule sur des serveurs Overpass miroirs.
"""

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from config.settings import (
    AGADIR_BBOX,
    OVERPASS_ENDPOINTS,
    RAW_DATA_DIR,
    NETWORK_TIMEOUT,
    GPS_CRS,
)
from src.geographic.projection import GeoProjector

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class OSMDataCollector:
    """
    Collecteur de POIs et bâtiments réels depuis OpenStreetMap pour la zone de Talborjt - Centre-ville d'Agadir.
    """

    def __init__(self, bbox: Optional[Dict[str, float]] = None):
        self.bbox = bbox or AGADIR_BBOX
        self.projector = GeoProjector()
        self.raw_data_path = RAW_DATA_DIR / "agadir_talborjt_raw.json"

    def build_overpass_query(self) -> str:
        """
        Construit la requête Overpass QL ciblée sur Talborjt et Centre-ville d'Agadir.
        Extrait les commerces, équipements (amenity), bureaux, artisanats et bâtiments nommés/identifiés.
        """
        s, w, n, e = self.bbox["south"], self.bbox["west"], self.bbox["north"], self.bbox["east"]
        bbox_str = f"{s},{w},{n},{e}"

        query = f"""
        [out:json][timeout:35];
        (
          // 1. Commerces et magasins
          node["shop"]({bbox_str});
          way["shop"]({bbox_str});

          // 2. Équipements de proximité (restaurants, cafés, pharmacies, banques, etc.)
          node["amenity"]({bbox_str});
          way["amenity"]({bbox_str});

          // 3. Bureaux et services professionnels
          node["office"]({bbox_str});
          way["office"]({bbox_str});

          // 4. Artisanat et services
          node["craft"]({bbox_str});
          way["craft"]({bbox_str});

          // 5. Bâtiments nommés
          way["building"~"commercial|retail|residential"]["name"]({bbox_str});
        );
        out center;
        """
        return query.strip()

    def fetch_osm_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Interroge l'API Overpass pour collecter les données d'Agadir.
        Si les données brutes existent déjà en local et que force_refresh est False,
        utilise le cache local pour éviter des requêtes réseau inutiles.
        """
        if not force_refresh and self.raw_data_path.exists():
            logger.info("Données brutes trouvées en cache : %s", self.raw_data_path)
            with open(self.raw_data_path, "r", encoding="utf-8") as f:
                return json.load(f)

        query = self.build_overpass_query()
        logger.info("Lancement de la requête Overpass pour la BBOX: %s", self.bbox)

        headers = {
            "User-Agent": "AgadirMapping/1.0 (academic)",
            "Accept": "*/*",
        }

        last_error = None
        for endpoint in OVERPASS_ENDPOINTS:
            try:
                logger.info("Tentative de connexion à l'endpoint : %s", endpoint)
                try:
                    response = requests.get(
                        endpoint,
                        params={"data": query},
                        headers=headers,
                        timeout=NETWORK_TIMEOUT,
                    )
                    response.raise_for_status()
                except Exception as get_err:
                    logger.info("GET échoué sur %s (%s), tentative via POST...", endpoint, get_err)
                    response = requests.post(
                        endpoint,
                        data={"data": query},
                        headers=headers,
                        timeout=NETWORK_TIMEOUT,
                    )
                    response.raise_for_status()

                data = response.json()

                # Ajout de métadonnées d'extraction garantissant la traçabilité
                data["_extraction_metadata"] = {
                    "city": "Agadir",
                    "district": "Talborjt & Centre-ville",
                    "bbox": self.bbox,
                    "extracted_at": datetime.now(timezone.utc).isoformat(),
                    "source": endpoint,
                    "elements_count": len(data.get("elements", [])),
                }

                # Sauvegarde brute
                with open(self.raw_data_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                logger.info(
                    "Extraction réussie : %d éléments collectés et enregistrés dans %s",
                    len(data.get("elements", [])),
                    self.raw_data_path,
                )
                return data

            except Exception as e:
                logger.warning("Échec de l'endpoint %s : %s", endpoint, e)
                last_error = e
                time.sleep(1)

        raise RuntimeError(f"Impossible d'extraire les données OSM depuis Overpass : {last_error}")

    def parse_elements(self, raw_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Parse et normalise les éléments OpenStreetMap extraits.
        Calcule les coordonnées centroïdes pour les polygones/ways et projette en UTM Zone 29N.
        """
        elements = raw_data.get("elements", [])
        records = []

        for el in elements:
            el_type = el.get("type")
            tags = el.get("tags", {})
            if not tags:
                continue

            # Extraction des coordonnées géographiques
            lat, lon = None, None
            if el_type == "node":
                lat = el.get("lat")
                lon = el.get("lon")
            elif el_type in ("way", "relation"):
                center = el.get("center")
                if center:
                    lat = center.get("lat")
                    lon = center.get("lon")

            if lat is None or lon is None:
                continue

            # Vérification de l'appartenance à la BBOX
            if not (self.bbox["south"] <= lat <= self.bbox["north"] and self.bbox["west"] <= lon <= self.bbox["east"]):
                continue

            # Détermination de la catégorie et sous-catégorie
            category, subcategory = self._classify_element(tags)
            if not category:
                continue

            # Nommage propre
            name = tags.get("name")
            if not name:
                name_fr = tags.get("name:fr") or tags.get("name:ar") or tags.get("brand")
                if name_fr:
                    name = name_fr
                else:
                    name = f"{subcategory.capitalize()} (OSM #{el.get('id')})"

            # Adresse et rue
            street = tags.get("addr:street", "")
            housenumber = tags.get("addr:housenumber", "")

            # Projection métrique UTM Zone 29N
            try:
                x_utm, y_utm = self.projector.gps_to_utm(lat, lon)
            except Exception as e:
                logger.warning("Erreur de projection pour le point %s: %s", el.get("id"), e)
                continue

            records.append({
                "osm_id": el.get("id"),
                "osm_type": el_type,
                "name": name,
                "category": category,
                "subcategory": subcategory,
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
                "x_utm": round(x_utm, 2),
                "y_utm": round(y_utm, 2),
                "street": street,
                "housenumber": housenumber,
                "wheelchair": tags.get("wheelchair", ""),
                "opening_hours": tags.get("opening_hours", ""),
            })

        df = pd.DataFrame(records)
        if not df.empty:
            # Dédoublonnage sur identifiant OSM
            df = df.drop_duplicates(subset=["osm_id"]).reset_index(drop=True)
            logger.info("Parsed %d POIs valides et géolocalisés.", len(df))
        else:
            logger.warning("Aucun élément n'a pu être extrait avec les critères actuels.")

        return df

    def to_geodataframe(self, df: pd.DataFrame) -> gpd.GeoDataFrame:
        """
        Convertit le DataFrame en GeoDataFrame GeoPandas avec CRS EPSG:4326.
        """
        geometry = [Point(xy) for xy in zip(df["longitude"], df["latitude"])]
        gdf = gpd.GeoDataFrame(df, geometry=geometry, crs=GPS_CRS)
        return gdf

    @staticmethod
    def _classify_element(tags: Dict[str, str]) -> Tuple[Optional[str], str]:
        """
        Classe un élément OSM dans une taxonomie Last-Mile claire.
        """
        if "shop" in tags:
            return "Commerce & Magasin", tags["shop"]
        if "amenity" in tags:
            amenity = tags["amenity"]
            if amenity in ["restaurant", "cafe", "fast_food", "bar"]:
                return "Restauration & Cafés", amenity
            if amenity in ["pharmacy", "clinic", "hospital", "doctors"]:
                return "Santé & Pharmacie", amenity
            if amenity in ["bank", "atm", "bureau_de_change"]:
                return "Banque & Finance", amenity
            if amenity in ["post_office", "marketplace", "fuel"]:
                return "Services & Logistique", amenity
            return "Équipement Public", amenity
        if "office" in tags:
            return "Bureaux & Tertiaire", tags["office"]
        if "craft" in tags:
            return "Artisanat & Services", tags["craft"]
        if "building" in tags:
            return "Résidentiel & Bâtiment", tags["building"]
        return None, ""
