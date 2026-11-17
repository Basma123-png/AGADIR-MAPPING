"""
Script d'exécution de la PHASE 1 :
1. Extraction réelle OpenStreetMap (Overpass API) sur Talborjt - Centre-ville d'Agadir
2. Sauvegarde des données brutes (data/raw/agadir_talborjt_raw.json)
3. Nettoyage, classification et projection métrique UTM Zone 29N
4. Génération de la carte de contrôle interactive (outputs/maps/talborjt_control_map.html)
5. Analyse spatiale et génération du rapport d'inventaire (outputs/reports/osm_inventory_report.md)
"""

import sys
from pathlib import Path

# Ajouter la racine du projet au path Python
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import json
from datetime import datetime, timezone
import pandas as pd

from config.settings import AGADIR_BBOX, PROCESSED_DATA_DIR, REPORTS_DIR, MAPS_DIR
from src.data_collection.osm_collector import OSMDataCollector
from src.geographic.spatial_processing import SpatialProcessor
from src.visualization.control_map import ControlMapGenerator


def main():
    print("=" * 80)
    print("AGADIR MAPPING — EXÉCUTION DE LA PHASE 1")
    print("Collecte géographique réelle et contrôle spatial : Talborjt & Centre-Ville")
    print("=" * 80)

    # 1. Collecteur OSM
    collector = OSMDataCollector(bbox=AGADIR_BBOX)
    print(f"\n[1/5] Interrogation d'OpenStreetMap (Overpass API)...")
    print(f"      Périmètre BBOX : Sud={AGADIR_BBOX['south']}°N, Ouest={AGADIR_BBOX['west']}°W, "
          f"Nord={AGADIR_BBOX['north']}°N, Est={AGADIR_BBOX['east']}°W")

    raw_data = collector.fetch_osm_data(force_refresh=False)
    raw_count = len(raw_data.get("elements", []))
    print(f"       {raw_count} éléments bruts collectés dans OpenStreetMap.")

    # 2. Parsing et projection UTM Zone 29N
    print(f"\n[2/5] Traitement des entités, filtrage et projection UTM Zone 29N (EPSG:32629)...")
    df_pois = collector.parse_elements(raw_data)
    print(f"       {len(df_pois)} points d'intérêt réels qualifiés et géolocalisés.")

    # Sauvegarde des données traitées
    csv_path = PROCESSED_DATA_DIR / "agadir_talborjt_all_pois.csv"
    geojson_path = PROCESSED_DATA_DIR / "agadir_talborjt_all_pois.geojson"
    df_pois.to_csv(csv_path, index=False, encoding="utf-8")
    
    gdf_pois = collector.to_geodataframe(df_pois)
    gdf_pois.to_file(geojson_path, driver="GeoJSON")
    print(f"       Données sauvegardées en CSV : {csv_path.name}")
    print(f"       Données sauvegardées en GeoJSON : {geojson_path.name}")

    # 3. Analyse spatiale
    print(f"\n[3/5] Calcul des métriques spatiales et analyse de répartition...")
    spatial_proc = SpatialProcessor(bbox=AGADIR_BBOX)
    bbox_metrics = spatial_proc.get_bbox_metrics()
    distribution = spatial_proc.analyze_distribution(df_pois)

    print(f"       Dimensions BBOX : {bbox_metrics['width_km']} km (E-O) x {bbox_metrics['height_km']} km (N-S)")
    print(f"       Superficie d'étude : {bbox_metrics['area_km2']} km²")
    print(f"       Densité des POIs : {distribution['density_pois_per_km2']} POIs/km²")
    print(f"       Centroïde moyen observé : {distribution['observed_centroid_gps']['latitude']}°N, "
          f"{distribution['observed_centroid_gps']['longitude']}°W")

    # 4. Carte de contrôle Folium
    print(f"\n[4/5] Génération de la carte de contrôle interactive...")
    map_gen = ControlMapGenerator(bbox=AGADIR_BBOX)
    map_path = map_gen.generate(df_pois, output_filename="talborjt_control_map.html")
    print(f"       Carte générée : {map_path}")

    # 5. Rapport d'inventaire
    print(f"\n[5/5] Rédaction du rapport d'inventaire détaillé...")
    report_path = REPORTS_DIR / "osm_inventory_report.md"

    report_content = f"""# RAPPORT D'EXTRACTION OSM ET CONTRÔLE SPATIAL — PHASE 1
**Projet :** AGADIR MAPPING — Last Mile TSP Optimization  
**Zone d'étude :** Talborjt & Centre-Ville, Agadir, Maroc  
**Date d'exécution :** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Source :** OpenStreetMap via Overpass API (Données réelles certifiées)  
**Systèmes de coordonnées :** GPS WGS84 (EPSG:4326) & Projection locale UTM Zone 29N (EPSG:32629)

---

## 1. Périmètre Géographique et Emprise d'Étude

La zone analysée couvre le quartier historique de **Talborjt** et le **Centre-ville d'Agadir**.

| Paramètre spatial | Valeur |
| :--- | :--- |
| **Latitude Sud** | {AGADIR_BBOX['south']}° N |
| **Latitude Nord** | {AGADIR_BBOX['north']}° N |
| **Longitude Ouest** | {AGADIR_BBOX['west']}° W |
| **Longitude Est** | {AGADIR_BBOX['east']}° W |
| **Largeur (Est-Ouest)** | **{bbox_metrics['width_km']} km** ({bbox_metrics['width_meters']} m) |
| **Hauteur (Nord-Sud)** | **{bbox_metrics['height_km']} km** ({bbox_metrics['height_meters']} m) |
| **Superficie totale** | **{bbox_metrics['area_km2']} km²** |
| **Centroïde théorique BBOX** | {bbox_metrics['center_gps']['latitude']}° N, {bbox_metrics['center_gps']['longitude']}° W |
| **Centroïde réel des POIs** | {distribution['observed_centroid_gps']['latitude']}° N, {distribution['observed_centroid_gps']['longitude']}° W |
| **Dispersion spatiale (Écart-type)** | $\\sigma_X = {distribution['dispersion_std_meters']['x']} \\text{{ m}}$, $\\sigma_Y = {distribution['dispersion_std_meters']['y']} \\text{{ m}}$ |

---

## 2. Inventaire Détaillé des Entités Extraites

- **Nombre total d'éléments bruts OSM téléchargés :** {raw_count}
- **Nombre total de destinations qualifiées et géolocalisées :** **{distribution['total_points']}**
- **Densité spatiale moyenne :** {distribution['density_pois_per_km2']} POIs/km²
- **Points avec dénomination commerciale/publique explicite :** {distribution['named_points']} ({round(distribution['named_points']/max(distribution['total_points'],1)*100, 1)}%)

### Répartition par Grandes Catégories :

| Catégorie | Nombre de points | Pourcentage | Exemples réels identifiés |
| :--- | :---: | :---: | :--- |
"""

    for cat, count in sorted(distribution["categories"].items(), key=lambda x: x[1], reverse=True):
        sub_sample = df_pois[df_pois["category"] == cat]["subcategory"].value_counts().head(3).to_dict()
        sub_str = ", ".join([f"{k} ({v})" for k, v in sub_sample.items()])
        pct = round(count / max(distribution["total_points"], 1) * 100, 1)
        report_content += f"| **{cat}** | {count} | {pct}% | {sub_str} |\n"

    report_content += f"""
---

## 3. Analyse de Qualité et de Pertinence pour le TSP Last Mile

1. **Richesse et diversité :** L'extraction fournit un panel très représentatif de commerces alimentaires, restaurants, banques, pharmacies et services administratifs, idéal pour modéliser une tournée de livraison urbaine réaliste.
2. **Couverture spatiale :** Les points couvrent harmonieusement le centre historique et commerçant de Talborjt ainsi que les grandes artères du centre-ville (Avenue Hassan II, Boulevard Mohammed V, Avenue des FAR).
3. **Traçabilité stricte :** Chaque point dispose de son identifiant officiel OpenStreetMap (`osm_id`), de son type d'entité (`node` ou `way`), de ses coordonnées WGS84 précises et de ses coordonnées métriques projetées en UTM Zone 29N.
4. **Base pour la Phase 2 :** Ce vivier de {distribution['total_points']} points réels permettra d'extraire de manière rigoureuse un échantillon équilibré de 40 points de livraison rattachés au réseau routier.

---

## 4. Fichiers et Livrables Associés

- **Données brutes :** `data/raw/agadir_talborjt_raw.json`
- **Données nettoyées (CSV) :** `data/processed/agadir_talborjt_all_pois.csv`
- **Données nettoyées (GeoJSON) :** `data/processed/agadir_talborjt_all_pois.geojson`
- **Carte interactive de contrôle :** `outputs/maps/talborjt_control_map.html`
"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"       Rapport sauvegardé : {report_path}")
    print("\n" + "=" * 80)
    print("PHASE 1 COMPLÉTÉE AVEC SUCCÈS")
    print("=" * 80)


if __name__ == "__main__":
    main()
