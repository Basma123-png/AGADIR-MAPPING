"""
Générateur de la carte de contrôle interactive pour la zone Talborjt & Centre-ville d'Agadir.

Objectifs :
1. Visualiser avec précision les limites géographiques de la Bounding Box d'étude.
2. Représenter spatialement tous les éléments réels extraits d'OpenStreetMap.
3. Permettre la vérification visuelle de la répartition spatiale et de la qualité des données
   avant toute sélection des 40 points de livraison.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import folium
from folium import plugins
import pandas as pd

from config.settings import AGADIR_BBOX, MAPS_DIR, DEFAULT_DEPOT_GPS


CATEGORY_COLORS = {
    "Commerce & Magasin": "#1f77b4",       # Bleu
    "Restauration & Cafés": "#ff7f0e",     # Orange
    "Santé & Pharmacie": "#2ca02c",        # Vert
    "Banque & Finance": "#d62728",         # Rouge
    "Services & Logistique": "#9467bd",    # Violet
    "Bureaux & Tertiaire": "#8c564b",      # Marron
    "Artisanat & Services": "#e377c2",     # Rose
    "Résidentiel & Bâtiment": "#7f7f7f",   # Gris
    "Équipement Public": "#bcbd22",        # Jaune-vert
}

CATEGORY_ICONS = {
    "Commerce & Magasin": "shopping-cart",
    "Restauration & Cafés": "cutlery",
    "Santé & Pharmacie": "plus-sign",
    "Banque & Finance": "usd",
    "Services & Logistique": "envelope",
    "Bureaux & Tertiaire": "briefcase",
    "Artisanat & Services": "wrench",
    "Résidentiel & Bâtiment": "home",
    "Équipement Public": "info-sign",
}


class ControlMapGenerator:
    """
    Générateur de carte Folium de contrôle et de validation pour Agadir.
    """

    def __init__(self, bbox: Optional[Dict[str, float]] = None):
        self.bbox = bbox or AGADIR_BBOX

    def generate(self, df_pois: pd.DataFrame, output_filename: str = "talborjt_control_map.html") -> Path:
        """
        Génère la carte HTML interactive de contrôle.
        """
        center_lat = (self.bbox["south"] + self.bbox["north"]) / 2.0
        center_lon = (self.bbox["west"] + self.bbox["east"]) / 2.0

        # Création de la carte Folium de base avec OpenStreetMap
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=15,
            tiles="OpenStreetMap",
            control_scale=True,
        )

        # Fond satellite Esri gratuit sans clé pour une vue aérienne du tissu urbain
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri",
            name="Vue Satellite (Esri)",
        ).add_to(m)

        # ----------------------------------------------------------------------
        # 1. Tracé de la Bounding Box d'étude et Marqueurs des 4 Coins
        # ----------------------------------------------------------------------
        bbox_bounds = [
            [self.bbox["south"], self.bbox["west"]],
            [self.bbox["north"], self.bbox["east"]],
        ]
        
        bbox_group = folium.FeatureGroup(name="Périmètre d'étude (Bounding Box)", show=True)
        folium.Rectangle(
            bounds=bbox_bounds,
            color="#d9534f",
            weight=3,
            fill=True,
            fill_color="#f0ad4e",
            fill_opacity=0.08,
            dash_array="6, 6",
            tooltip=(
                f"<b>Périmètre d'étude Talborjt - Centre-Ville</b><br>"
                f"Sud: {self.bbox['south']}°N | Nord: {self.bbox['north']}°N<br>"
                f"Ouest: {self.bbox['west']}°W | Est: {self.bbox['east']}°W"
            ),
        ).add_to(bbox_group)

        # Repères visuels sur les 4 coins du périmètre
        corners = [
            ("Coin Nord-Ouest", self.bbox["north"], self.bbox["west"]),
            ("Coin Nord-Est", self.bbox["north"], self.bbox["east"]),
            ("Coin Sud-Ouest", self.bbox["south"], self.bbox["west"]),
            ("Coin Sud-Est", self.bbox["south"], self.bbox["east"]),
        ]
        for c_name, c_lat, c_lon in corners:
            folium.CircleMarker(
                location=[c_lat, c_lon],
                radius=6,
                color="#b30000",
                fill=True,
                fill_color="#ff4d4d",
                fill_opacity=0.9,
                weight=2,
                tooltip=f"<b>{c_name}</b> : {c_lat}°N, {c_lon}°W",
                popup=folium.Popup(f"<b>{c_name}</b><br>Lat: {c_lat}°N<br>Lon: {c_lon}°W", max_width=200),
            ).add_to(bbox_group)

        # Repères des deux secteurs majeurs (Talborjt et Centre-ville)
        districts_group = folium.FeatureGroup(name="Secteurs clés (Talborjt / Centre-ville)", show=True)
        folium.Marker(
            location=[30.4260, -9.5930],
            tooltip="<b>Secteur : Nouveau Talborjt</b>",
            icon=folium.Icon(color="blue", icon="bookmark", prefix="fa"),
        ).add_to(districts_group)
        folium.Marker(
            location=[30.4190, -9.6015],
            tooltip="<b>Secteur : Centre-Ville (Av. Hassan II / Bd Mohammed V)</b>",
            icon=folium.Icon(color="purple", icon="building", prefix="fa"),
        ).add_to(districts_group)
        districts_group.add_to(m)

        bbox_group.add_to(m)

        # ----------------------------------------------------------------------
        # 2. Dépôt Central proposé
        # ----------------------------------------------------------------------
        depot_group = folium.FeatureGroup(name="Dépôt Central proposé", show=True)
        folium.Marker(
            location=[DEFAULT_DEPOT_GPS["latitude"], DEFAULT_DEPOT_GPS["longitude"]],
            tooltip=f"<b>DÉPÔT</b> : {DEFAULT_DEPOT_GPS['name']}",
            popup=folium.Popup(
                f"<div style='font-family: Arial; font-size: 13px;'>"
                f"<h4 style='color: #d9534f; margin: 0;'>{DEFAULT_DEPOT_GPS['name']}</h4>"
                f"<p><b>Lat / Lon :</b> {DEFAULT_DEPOT_GPS['latitude']} / {DEFAULT_DEPOT_GPS['longitude']}</p>"
                f"<p>Point de départ et de retour pour la tournée TSP Last Mile.</p>"
                f"</div>",
                max_width=300,
            ),
            icon=folium.Icon(color="red", icon="star", prefix="fa"),
        ).add_to(depot_group)
        depot_group.add_to(m)

        # ----------------------------------------------------------------------
        # 3. Représentation des POIs par catégorie avec groupes activables
        # ----------------------------------------------------------------------
        categories = df_pois["category"].unique() if not df_pois.empty else []
        for cat in sorted(categories):
            cat_df = df_pois[df_pois["category"] == cat]
            cat_group = folium.FeatureGroup(name=f"{cat} ({len(cat_df)})", show=True)
            color = CATEGORY_COLORS.get(cat, "#333333")
            icon_name = CATEGORY_ICONS.get(cat, "info-sign")

            for _, row in cat_df.iterrows():
                popup_html = f"""
                <div style="font-family: Arial, sans-serif; font-size: 12px; min-width: 200px;">
                    <b style="color: {color}; font-size: 13px;">{row['name']}</b><br>
                    <hr style="margin: 4px 0;">
                    <b>Catégorie :</b> {row['category']}<br>
                    <b>Type :</b> {row['subcategory']}<br>
                    <b>OSM ID :</b> #{row['osm_id']} ({row['osm_type']})<br>
                    <b>GPS (WGS84) :</b> {row['latitude']}, {row['longitude']}<br>
                    <b>Métrique (UTM 29N) :</b> X={row['x_utm']}m, Y={row['y_utm']}m<br>
                    {"<b>Rue :</b> " + str(row['street']) + "<br>" if pd.notna(row['street']) and row['street'] else ""}
                </div>
                """
                folium.CircleMarker(
                    location=[row["latitude"], row["longitude"]],
                    radius=5,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.85,
                    weight=1.5,
                    tooltip=f"<b>{row['name']}</b> ({row['subcategory']})",
                    popup=folium.Popup(popup_html, max_width=320),
                ).add_to(cat_group)

            cat_group.add_to(m)

        # ----------------------------------------------------------------------
        # 4. Plugins utiles
        # ----------------------------------------------------------------------
        folium.LayerControl(collapsed=False).add_to(m)
        plugins.MiniMap(toggle_display=True).add_to(m)
        plugins.MeasureControl(position="topleft", primary_length_unit="kilometers").add_to(m)
        plugins.Fullscreen(position="topleft").add_to(m)

        output_path = MAPS_DIR / output_filename
        m.save(str(output_path))
        return output_path
