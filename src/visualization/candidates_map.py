"""
Générateur de la carte interactive des 40 candidats de livraison et du dépôt pour AGADIR MAPPING.

Fonctionnalités :
- Visualisation de la Bounding Box élargie vers l'Ouest (Marina & Corniche)
- Affichage du Dépôt (Place Al Amal) avec symbole distinctif
- Affichage des 39 destinations urbaines (Talborjt et Centre-ville) numérotées 1 à 39
- Affichage mis en valeur de la destination littorale (Point 40, Corniche / Marina)
- Visualisation du rattachement au réseau routier OSRM (lignes de projection et voies réelles)
- Vue satellite et fond OpenStreetMap avec contrôle des calques
"""

from pathlib import Path
from typing import Dict, Any, Optional
import folium
from folium import plugins
import pandas as pd

from config.settings import AGADIR_BBOX, MAPS_DIR

CATEGORY_COLORS = {
    "Dépôt Central": "#d9534f",                     # Rouge
    "Destination Littorale": "#008080",             # Cyan / Bleu canard marin
    "Commerce & Magasin": "#1f77b4",                # Bleu
    "Restauration & Cafés": "#ff7f0e",              # Orange
    "Santé & Pharmacie": "#2ca02c",                 # Vert
    "Banque & Finance": "#e377c2",                  # Rose / Magenta
    "Services & Logistique": "#9467bd",             # Violet
    "Bureaux & Tertiaire": "#8c564b",               # Marron
}

CATEGORY_ICONS = {
    "Dépôt Central": "star",
    "Destination Littorale": "anchor",
    "Commerce & Magasin": "shopping-cart",
    "Restauration & Cafés": "cutlery",
    "Santé & Pharmacie": "plus",
    "Banque & Finance": "usd",
    "Services & Logistique": "truck",
    "Bureaux & Tertiaire": "briefcase",
}


class CandidatesMapGenerator:
    """
    Générateur de carte Folium des 40 destinations candidates pour validation avant TSP.
    """

    def __init__(self, bbox: Optional[Dict[str, float]] = None):
        self.bbox = bbox or AGADIR_BBOX

    def generate(self, df_points: pd.DataFrame, output_filename: str = "candidates_40_map.html") -> Path:
        """
        Génère la carte interactive HTML des 40 points et du dépôt.
        """
        center_lat = (self.bbox["south"] + self.bbox["north"]) / 2.0
        center_lon = (self.bbox["west"] + self.bbox["east"]) / 2.0

        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=14,
            tiles="OpenStreetMap",
            control_scale=True,
        )

        # Fond satellite Esri
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri",
            name="Vue Satellite (Esri)",
        ).add_to(m)

        # ----------------------------------------------------------------------
        # 1. Bounding Box élargie à la Marina
        # ----------------------------------------------------------------------
        bbox_bounds = [
            [self.bbox["south"], self.bbox["west"]],
            [self.bbox["north"], self.bbox["east"]],
        ]
        bbox_group = folium.FeatureGroup(name="Périmètre BBOX Élargi (Corniche comprise)", show=True)
        folium.Rectangle(
            bounds=bbox_bounds,
            color="#d9534f",
            weight=3,
            fill=True,
            fill_color="#f0ad4e",
            fill_opacity=0.06,
            dash_array="5, 5",
            tooltip=f"<b>Périmètre global d'étude</b><br>Ouest: {self.bbox['west']}°W (Marina incluse)",
        ).add_to(bbox_group)
        bbox_group.add_to(m)

        # ----------------------------------------------------------------------
        # 2. Lignes de projection OSRM (Rattachement routier)
        # ----------------------------------------------------------------------
        snapping_group = folium.FeatureGroup(name="Rattachement au réseau routier (OSRM)", show=True)
        for _, row in df_points.iterrows():
            if pd.notna(row.get("osrm_snapped_lat")) and row.get("osrm_snap_distance_m", 0) > 0:
                p_orig = [row["latitude"], row["longitude"]]
                p_snap = [row["osrm_snapped_lat"], row["osrm_snapped_lon"]]
                folium.PolyLine(
                    locations=[p_orig, p_snap],
                    color="#555555",
                    weight=1.5,
                    dash_array="3, 3",
                    opacity=0.8,
                    tooltip=f"Snap OSRM : {row['osrm_snap_distance_m']} m vers {row.get('osrm_street', '')}",
                ).add_to(snapping_group)
        snapping_group.add_to(m)

        # ----------------------------------------------------------------------
        # 3. Marqueurs des 40 destinations et du dépôt
        # ----------------------------------------------------------------------
        # Groupes par type
        depot_group = folium.FeatureGroup(name="Dépôt Logistique (Place Al Amal)", show=True)
        coastal_group = folium.FeatureGroup(name="Destination Littorale (Corniche / Marina)", show=True)
        urban_group = folium.FeatureGroup(name="Destinations Urbaines (Talborjt & Centre)", show=True)

        for _, row in df_points.iterrows():
            pid = int(row["point_id"])
            cat = row["category"]
            color = CATEGORY_COLORS.get(cat, "#333333")
            icon_name = CATEGORY_ICONS.get(cat, "info-sign")

            popup_html = f"""
            <div style="font-family: Arial, sans-serif; font-size: 12px; min-width: 240px;">
                <div style="background-color: {color}; color: white; padding: 4px 8px; border-radius: 3px; font-weight: bold;">
                    Point #{pid} — {row['point_type']}
                </div>
                <h4 style="margin: 6px 0 4px 0; color: #222;">{row['name']}</h4>
                <b>Quartier :</b> {row.get('district', '')}<br>
                <b>Catégorie :</b> {cat} ({row.get('subcategory', '')})<br>
                <b>OSM ID :</b> #{row.get('osm_id', 'N/A')}<br>
                <hr style="margin: 5px 0;">
                <b>Coordonnées GPS (WGS84) :</b><br>
                Lat: {row['latitude']}°N | Lon: {row['longitude']}°W<br>
                <b>Coordonnées Métriques (UTM 29N) :</b><br>
                X: {row['x_utm']} m | Y: {row['y_utm']} m<br>
                <hr style="margin: 5px 0;">
                <b>Rattachement routier OSRM :</b><br>
                Rue: <i>{row.get('osrm_street', 'N/A')}</i><br>
                Distance à la route: <b>{row.get('osrm_snap_distance_m', 'N/A')} m</b><br>
                {"<b>Trajet depuis le dépôt :</b> " + str(round(row.get('osrm_route_from_depot_m', 0)/1000, 2)) + " km (" + str(row.get('osrm_route_from_depot_min', '')) + " min)<br>" if pid != 0 else ""}
            </div>
            """

            # Dépôt (Point 0)
            if pid == 0:
                folium.Marker(
                    location=[row["latitude"], row["longitude"]],
                    tooltip=f"<b>POINT #0 (DÉPÔT)</b> : {row['name']}",
                    popup=folium.Popup(popup_html, max_width=320),
                    icon=folium.Icon(color="red", icon="star", prefix="fa"),
                ).add_to(depot_group)

            # Destination Littorale (Point 40)
            elif row.get("is_coastal", False) or row.get("point_type") == "Littoral":
                # Marqueur distinctif avec couronne pulsée / cercle accentué
                folium.CircleMarker(
                    location=[row["latitude"], row["longitude"]],
                    radius=12,
                    color="#008080",
                    fill=True,
                    fill_color="#00ffff",
                    fill_opacity=0.4,
                    weight=3,
                ).add_to(coastal_group)
                folium.Marker(
                    location=[row["latitude"], row["longitude"]],
                    tooltip=f"<b>POINT #{pid} [LITTORAL]</b> : {row['name']}",
                    popup=folium.Popup(popup_html, max_width=320),
                    icon=folium.Icon(color="darkblue", icon="anchor", prefix="fa"),
                ).add_to(coastal_group)

            # Destinations Urbaines (1 à 39)
            else:
                # Badge numéroté
                folium.CircleMarker(
                    location=[row["latitude"], row["longitude"]],
                    radius=8,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.85,
                    weight=1.5,
                    tooltip=f"<b>#{pid}</b> : {row['name']} ({cat})",
                    popup=folium.Popup(popup_html, max_width=320),
                ).add_to(urban_group)

        depot_group.add_to(m)
        coastal_group.add_to(m)
        urban_group.add_to(m)

        # ----------------------------------------------------------------------
        # 4. Contrôles et plugins Folium
        # ----------------------------------------------------------------------
        folium.LayerControl(collapsed=False).add_to(m)
        plugins.MiniMap(toggle_display=True).add_to(m)
        plugins.MeasureControl(position="topleft", primary_length_unit="kilometers").add_to(m)
        plugins.Fullscreen(position="topleft").add_to(m)

        output_path = MAPS_DIR / output_filename
        m.save(str(output_path))
        return output_path
