"""
Visualisations cartographiques et graphiques pour les résultats TSP de la PHASE 4.

Produit :
- outputs/figures/tsp_convergence.png : Courbes de convergence (Distance et Fitness par génération)
- outputs/maps/tsp_route_map.html : Carte interactive Folium de la tournée TSP optimisée
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import folium
from folium import plugins
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config.settings import FIGURES_DIR, MAPS_DIR, AGADIR_BBOX


class TSPVisualizer:
    """
    Générateur de graphiques Matplotlib et de cartes Folium pour la tournée TSP.
    """

    @staticmethod
    def plot_convergence(
        history: Dict[str, List[float]],
        method_name: str = "Algorithme Génétique",
        output_filename: str = "tsp_convergence.png",
    ) -> Path:
        """
        Trace les courbes d'évolution de la distance et de la fitness au fil des générations.
        """
        gens = history["generation"]
        best_dists = [d / 1000.0 for d in history["best_distance"]]  # km
        avg_dists = [d / 1000.0 for d in history["avg_distance"]]    # km
        best_fitness = history["best_fitness"]

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), dpi=150, sharex=True)

        # 1. Courbe de distance
        ax1.plot(gens, avg_dists, color="#888888", linestyle="--", linewidth=1.5, label="Distance moyenne de la population")
        ax1.plot(gens, best_dists, color="#0055aa", linewidth=2.5, label="Meilleure distance (Élite)")

        d_init = best_dists[0]
        d_final = best_dists[-1]
        gain_pct = ((d_init - d_final) / d_init) * 100.0

        ax1.set_title(
            f"Convergence de l'Algorithme Génétique — {method_name}\n"
            f"Distance Initiale: {d_init:.2f} km | Distance Optimale: {d_final:.2f} km | Gain: -{gain_pct:.1f}%",
            fontsize=13,
            fontweight="bold",
            pad=12,
        )
        ax1.set_ylabel("Distance Routière Totale (km)", fontsize=11)
        ax1.grid(True, linestyle="--", alpha=0.5)
        ax1.legend(loc="upper right", frameon=True)

        # Annotation point final
        ax1.scatter([gens[-1]], [d_final], color="crimson", s=80, zorder=5)
        ax1.annotate(
            f"Optimum: {d_final:.2f} km",
            xy=(gens[-1], d_final),
            xytext=(gens[-1] - len(gens) * 0.25, d_final + (d_init - d_final) * 0.15),
            arrowprops=dict(facecolor="crimson", arrowstyle="->", lw=1.5),
            fontsize=10,
            fontweight="bold",
            color="crimson",
        )

        # 2. Courbe de fitness
        scaled_fitness = [f * 1e6 for f in best_fitness]
        ax2.plot(gens, scaled_fitness, color="#2ca02c", linewidth=2.5, label="Meilleure Fitness (× 10⁶)")
        ax2.set_xlabel("Nombre de Générations", fontsize=11)
        ax2.set_ylabel("Fitness (1 / Distance)", fontsize=11)
        ax2.grid(True, linestyle="--", alpha=0.5)
        ax2.legend(loc="lower right", frameon=True)

        plt.tight_layout()
        output_path = FIGURES_DIR / output_filename
        fig.savefig(output_path, bbox_inches="tight")
        plt.close(fig)
        return output_path

    @staticmethod
    def generate_route_map(
        route_steps: List[Dict[str, Any]],
        output_filename: str = "tsp_route_map.html",
        bbox: Optional[Dict[str, float]] = None,
    ) -> Path:
        """
        Génère la carte interactive Folium représentant la tournée complète dans l'ordre de visite.
        """
        center_lat = sum(s["latitude"] for s in route_steps) / len(route_steps)
        center_lon = sum(s["longitude"] for s in route_steps) / len(route_steps)

        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=14,
            tiles="OpenStreetMap",
            control_scale=True,
        )

        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri",
            name="Vue Satellite (Esri)",
        ).add_to(m)

        # Tracé de la tournée
        route_coords = [[s["latitude"], s["longitude"]] for s in route_steps]

        tour_group = folium.FeatureGroup(name="Trajet de la Tournée TSP", show=True)
        folium.PolyLine(
            locations=route_coords,
            color="#0055aa",
            weight=4,
            opacity=0.85,
            tooltip="Itinéraire de livraison TSP optimisé",
        ).add_to(tour_group)

        # Ligne animée pour matérialiser le sens de circulation
        plugins.AntPath(
            locations=route_coords,
            color="#0055aa",
            pulse_color="#ffffff",
            weight=3,
            opacity=0.7,
            delay=1000,
        ).add_to(tour_group)
        tour_group.add_to(m)

        # Marqueurs des étapes
        stops_group = folium.FeatureGroup(name="Étapes de livraison (Ordre de visite)", show=True)

        for step in route_steps:
            seq = step["sequence_order"]
            pid = step["point_id"]
            name = step["name"]
            is_coast = step.get("is_coastal", False)

            # Contenu Popup
            popup_html = f"""
            <div style="font-family: Arial, sans-serif; font-size: 12px; min-width: 220px;">
                <div style="background-color: {'#d9534f' if pid==0 else ('#008080' if is_coast else '#1f77b4')}; color: white; padding: 4px; border-radius: 3px; font-weight: bold;">
                    Arrêt #{seq} {'(DÉPÔT)' if pid==0 else ('[LITTORAL]' if is_coast else '')}
                </div>
                <h4 style="margin: 6px 0 3px 0;">{name}</h4>
                <b>Point ID :</b> #{pid}<br>
                <b>Quartier :</b> {step['district']}<br>
                <b>Catégorie :</b> {step['category']}<br>
                <b>Étape précédente :</b> {step['leg_distance_m']:.0f} m ({step['leg_distance_km']:.2f} km)<br>
                <b>Distance cumulée :</b> <b>{step['cumulative_distance_km']:.2f} km</b>
            </div>
            """

            # Dépôt (Départ / Arrivée)
            if pid == 0 and seq == 0:
                folium.Marker(
                    location=[step["latitude"], step["longitude"]],
                    tooltip=f"<b>DÉPÔT CENTRAL (DÉPART & RETOUR)</b> : {name}",
                    popup=folium.Popup(popup_html, max_width=300),
                    icon=folium.Icon(color="red", icon="star", prefix="fa"),
                ).add_to(stops_group)

            elif pid == 0 and seq == len(route_steps) - 1:
                # Retour au dépôt (déjà marqué à l'origine)
                pass

            # Destination Littorale (Point #40)
            elif is_coast:
                folium.CircleMarker(
                    location=[step["latitude"], step["longitude"]],
                    radius=12,
                    color="#008080",
                    fill=True,
                    fill_color="#00ffff",
                    fill_opacity=0.6,
                    weight=3,
                ).add_to(stops_group)
                folium.Marker(
                    location=[step["latitude"], step["longitude"]],
                    tooltip=f"<b>Arrêt #{seq} [LITTORAL]</b> : {name}",
                    popup=folium.Popup(popup_html, max_width=300),
                    icon=folium.Icon(color="darkblue", icon="anchor", prefix="fa"),
                ).add_to(stops_group)

            # Destinations Urbaines
            else:
                folium.CircleMarker(
                    location=[step["latitude"], step["longitude"]],
                    radius=7,
                    color="#1f77b4",
                    fill=True,
                    fill_color="#1f77b4",
                    fill_opacity=0.85,
                    weight=1.5,
                    tooltip=f"<b>Arrêt #{seq}</b> : {name}",
                    popup=folium.Popup(popup_html, max_width=300),
                ).add_to(stops_group)

        stops_group.add_to(m)

        folium.LayerControl(collapsed=False).add_to(m)
        plugins.MiniMap(toggle_display=True).add_to(m)
        plugins.Fullscreen(position="topleft").add_to(m)

        output_path = MAPS_DIR / output_filename
        m.save(str(output_path))
        return output_path
