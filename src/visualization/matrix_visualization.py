"""
Module de visualisation graphique et cartographique des matrices de distances et de durées OSRM.

Produit :
- outputs/figures/distance_matrix_heatmap.png : Heatmaps de la distance routière et de l'asymétrie
- outputs/figures/circuity_distribution.png : Distribution du facteur de détour (Routier vs Euclidien)
- outputs/maps/depot_accessibility_map.html : Carte Folium des isochrones et distances depuis le Dépôt
"""

from pathlib import Path
from typing import Dict, Any, List
import folium
from folium import plugins
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config.settings import FIGURES_DIR, MAPS_DIR, AGADIR_BBOX


class MatrixVisualizer:
    """
    Générateur de graphiques Matplotlib et de cartes Folium d'analyse de la matrice de coûts.
    """

    @staticmethod
    def plot_matrix_heatmaps(
        dist_matrix_m: np.ndarray,
        df_points: pd.DataFrame,
        output_filename: str = "distance_matrix_heatmap.png",
    ) -> Path:
        """
        Génère une figure à deux panneaux :
        1. Matrice des distances routières (km)
        2. Matrice d'asymétrie routière |D_ij - D_ji| (mètres)
        """
        n = len(df_points)
        dist_km = dist_matrix_m / 1000.0
        asym_m = np.abs(dist_matrix_m - dist_matrix_m.T)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8), dpi=150)

        # Panneau 1 : Distances routières
        im1 = ax1.imshow(dist_km, cmap="viridis", origin="upper")
        ax1.set_title("Matrice des Distances Routières OSRM (km)", fontsize=13, fontweight="bold", pad=12)
        ax1.set_xlabel("Destination (Point ID)", fontsize=11)
        ax1.set_ylabel("Origine (Point ID)", fontsize=11)
        fig.colorbar(im1, ax=ax1, fraction=0.046, pad=0.04, label="Distance (km)")

        # Repères sur axes
        ticks = list(range(0, n, 5))
        if (n - 1) not in ticks:
            ticks.append(n - 1)
        ax1.set_xticks(ticks)
        ax1.set_yticks(ticks)
        ax1.set_xticklabels([f"P{t}" for t in ticks])
        ax1.set_yticklabels([f"P{t}" for t in ticks])

        # Surligner P0 (Dépôt) et P40 (Littoral)
        ax1.axhline(0, color="red", linestyle="--", alpha=0.5, linewidth=1)
        ax1.axvline(0, color="red", linestyle="--", alpha=0.5, linewidth=1)
        ax1.axhline(n - 1, color="cyan", linestyle="--", alpha=0.5, linewidth=1)
        ax1.axvline(n - 1, color="cyan", linestyle="--", alpha=0.5, linewidth=1)

        # Panneau 2 : Asymétrie routière
        im2 = ax2.imshow(asym_m, cmap="magma", origin="upper")
        ax2.set_title("Matrice d'Asymétrie Routière : |D_ij - D_ji| (mètres)", fontsize=13, fontweight="bold", pad=12)
        ax2.set_xlabel("Destination (Point ID)", fontsize=11)
        ax2.set_ylabel("Origine (Point ID)", fontsize=11)
        fig.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04, label="Différence absolue (mètres)")

        ax2.set_xticks(ticks)
        ax2.set_yticks(ticks)
        ax2.set_xticklabels([f"P{t}" for t in ticks])
        ax2.set_yticklabels([f"P{t}" for t in ticks])

        plt.tight_layout()
        output_path = FIGURES_DIR / output_filename
        fig.savefig(output_path, bbox_inches="tight")
        plt.close(fig)
        return output_path

    @staticmethod
    def plot_circuity_distribution(
        dist_matrix_m: np.ndarray,
        cart_matrix_m: np.ndarray,
        output_filename: str = "circuity_distribution.png",
    ) -> Path:
        """
        Histogramme du ratio de détour (Circuity Factor = Distance Routière / Distance Euclidienne).
        """
        n = dist_matrix_m.shape[0]
        off_diag = ~np.eye(n, dtype=bool)

        d_road = dist_matrix_m[off_diag]
        d_cart = cart_matrix_m[off_diag]

        with np.errstate(divide="ignore", invalid="ignore"):
            ratios = np.where(d_cart > 0, d_road / d_cart, 1.0)

        # Filtrer valeurs extrêmes pour affichage
        ratios_clean = ratios[(ratios >= 1.0) & (ratios <= 3.5)]

        fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
        mean_ratio = float(np.mean(ratios_clean))
        median_ratio = float(np.median(ratios_clean))

        n_bins, bins, patches = ax.hist(
            ratios_clean, bins=35, color="#2b5c8f", edgecolor="white", alpha=0.85, density=True
        )

        ax.axvline(1.0, color="gray", linestyle=":", linewidth=2, label="Ligne droite théorique (Ratio = 1.0)")
        ax.axvline(mean_ratio, color="crimson", linestyle="--", linewidth=2, label=f"Moyenne observée = {mean_ratio:.2f}")
        ax.axvline(median_ratio, color="darkorange", linestyle="-", linewidth=2, label=f"Médiane observée = {median_ratio:.2f}")

        ax.set_title("Distribution du Facteur de Détour Urbain à Agadir (Distance OSRM / Distance Euclidienne UTM)", fontsize=12, fontweight="bold", pad=12)
        ax.set_xlabel("Ratio de détour (Circuity Factor)", fontsize=11)
        ax.set_ylabel("Densité de fréquence", fontsize=11)
        ax.legend(loc="upper right", frameon=True)
        ax.grid(True, linestyle="--", alpha=0.5)

        plt.tight_layout()
        output_path = FIGURES_DIR / output_filename
        fig.savefig(output_path, bbox_inches="tight")
        plt.close(fig)
        return output_path

    @staticmethod
    def generate_depot_accessibility_map(
        df_points: pd.DataFrame,
        dist_matrix_m: np.ndarray,
        dur_matrix_s: np.ndarray,
        output_filename: str = "depot_accessibility_map.html",
    ) -> Path:
        """
        Carte Folium montrant le Dépôt (Point 0) et les rayons d'accessibilité vers les 40 destinations.
        """
        depot = df_points.iloc[0]
        m = folium.Map(
            location=[depot["latitude"], depot["longitude"]],
            zoom_start=14,
            tiles="OpenStreetMap",
            control_scale=True,
        )

        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri",
            name="Vue Satellite (Esri)",
        ).add_to(m)

        # Marqueur Dépôt
        depot_group = folium.FeatureGroup(name="Dépôt Central (Place Al Amal)", show=True)
        folium.Marker(
            location=[depot["latitude"], depot["longitude"]],
            tooltip="<b>POINT #0 (DÉPÔT CENTRAL) : Place Al Amal</b>",
            popup=f"<b>DÉPÔT CENTRAL</b><br>Place Al Amal, Agadir<br>Lat: {depot['latitude']}°N | Lon: {depot['longitude']}°W",
            icon=folium.Icon(color="red", icon="star", prefix="fa"),
        ).add_to(depot_group)
        depot_group.add_to(m)

        # Rayons et marqueurs vers les 40 destinations
        rays_group = folium.FeatureGroup(name="Rayons de desserte depuis le Dépôt", show=True)
        dest_group = folium.FeatureGroup(name="Les 40 Destinations", show=True)

        for j in range(1, len(df_points)):
            row = df_points.iloc[j]
            pid = int(row["point_id"])
            dist_km = round(dist_matrix_m[0, j] / 1000.0, 2)
            dur_min = round(dur_matrix_s[0, j] / 60.0, 1)

            # Couleur selon la durée de trajet
            if dur_min <= 2.0:
                color = "#2ca02c"  # Vert rapide (< 2 min)
            elif dur_min <= 3.5:
                color = "#ff7f0e"  # Orange modéré (2-3.5 min)
            else:
                color = "#d62728"  # Rouge / plus lointain (> 3.5 min)

            # Rayon direct
            folium.PolyLine(
                locations=[[depot["latitude"], depot["longitude"]], [row["latitude"], row["longitude"]]],
                color=color,
                weight=1.5,
                opacity=0.6,
                dash_array="4, 4",
                tooltip=f"Vers #{pid} : {dist_km} km | {dur_min} min",
            ).add_to(rays_group)

            # Marqueur
            is_coast = bool(row.get("is_coastal", False))
            icon_name = "anchor" if is_coast else "map-marker"
            marker_color = "darkblue" if is_coast else "blue"

            folium.Marker(
                location=[row["latitude"], row["longitude"]],
                tooltip=f"<b>#{pid}</b> : {row['name']} ({dist_km} km, {dur_min} min)",
                popup=(
                    f"<b>Point #{pid} — {row['point_type']}</b><br>"
                    f"<b>{row['name']}</b><br>"
                    f"Quartier : {row['district']}<br>"
                    f"Catégorie : {row['category']}<br>"
                    f"Distance OSRM : <b>{dist_km} km</b><br>"
                    f"Durée OSRM : <b>{dur_min} min</b>"
                ),
                icon=folium.Icon(color=marker_color, icon=icon_name, prefix="fa"),
            ).add_to(dest_group)

        rays_group.add_to(m)
        dest_group.add_to(m)

        folium.LayerControl(collapsed=False).add_to(m)
        plugins.MiniMap(toggle_display=True).add_to(m)
        plugins.Fullscreen(position="topleft").add_to(m)

        output_path = MAPS_DIR / output_filename
        m.save(str(output_path))
        return output_path
