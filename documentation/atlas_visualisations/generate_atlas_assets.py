#!/usr/bin/env python3
"""
Génération des actifs cartographiques, graphiques et diagrammes pour l'Atlas des Visualisations.
Projet AGADIR MAPPING.
"""

import json
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd

# Configuration matplotlib haute résolution
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#CBD5E1'
plt.rcParams['axes.linewidth'] = 0.8

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ATLAS_DIR = ROOT_DIR / "documentation" / "atlas_visualisations"
CARTES_DIR = ATLAS_DIR / "cartes"
GRAPHIQUES_DIR = ATLAS_DIR / "graphiques"
DIAGRAMMES_DIR = ATLAS_DIR / "diagrammes"
CAPTURES_DIR = ATLAS_DIR / "captures_dashboard"

POINTS_CSV = ROOT_DIR / "data" / "processed" / "delivery_points_40.csv"
DIST_CSV = ROOT_DIR / "data" / "processed" / "distance_matrix.csv"
DUR_CSV = ROOT_DIR / "data" / "processed" / "duration_matrix.csv"
TSP_OPT_JSON = ROOT_DIR / "data" / "results" / "tsp_optimized_route.json"
TSP_BASE_JSON = ROOT_DIR / "data" / "results" / "tsp_best_route.json"


def generate_carte_points():
    """Génère la carte thématique des 41 points d'Agadir."""
    df = pd.read_csv(POINTS_CSV)
    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#FFFFFF')

    # Catégories de points
    depot = df[df['point_id'] == 0].iloc[0]
    coastal = df[df['point_id'] == 40].iloc[0]
    clients = df[(df['point_id'] != 0) & (df['point_id'] != 40)]

    # Tracé des clients
    ax.scatter(clients['longitude'], clients['latitude'], c='#2878B5', s=80, edgecolors='#FFFFFF', linewidth=1.2, zorder=4, label='Clients Urbains (39)')
    for _, r in clients.iterrows():
        ax.annotate(str(int(r['point_id'])), (r['longitude'], r['latitude']), fontsize=7, color='#FFFFFF', ha='center', va='center', weight='bold', zorder=5)

    # Point littoral #40
    ax.scatter(coastal['longitude'], coastal['latitude'], c='#20A6A6', s=160, marker='s', edgecolors='#FFFFFF', linewidth=1.5, zorder=6, label='Point Littoral #40 (Restaurant Les Blancs)')
    ax.annotate("40", (coastal['longitude'], coastal['latitude']), fontsize=8, color='#FFFFFF', ha='center', va='center', weight='bold', zorder=7)

    # Dépôt #0
    ax.scatter(depot['longitude'], depot['latitude'], c='#D97706', s=200, marker='*', edgecolors='#FFFFFF', linewidth=1.5, zorder=8, label='Dépôt Central #0 (Place Al Amal)')
    ax.annotate("0", (depot['longitude'], depot['latitude']), fontsize=8, color='#FFFFFF', ha='center', va='center', weight='bold', zorder=9)

    ax.set_title("AGADIR MAPPING — Répartition Spatiale des 40 Points de Livraison et du Dépôt Central", fontsize=12, weight='bold', color='#1E3A5F', pad=15)
    ax.set_xlabel("Longitude WGS84 (°)", fontsize=10, color='#475569')
    ax.set_ylabel("Latitude WGS84 (°)", fontsize=10, color='#475569')
    ax.grid(True, linestyle='--', alpha=0.5, color='#CBD5E1')
    ax.legend(loc='lower left', frameon=True, facecolor='#FFFFFF', edgecolor='#CBD5E1', fontsize=9)

    # Note cartographique
    ax.text(0.99, 0.01, "Source : OpenStreetMap & data/processed/delivery_points_40.csv\nProjection : WGS84 (EPSG:4326) / UTM Zone 29N (EPSG:32629)",
            transform=ax.transAxes, fontsize=8, color='#64748B', ha='right', va='bottom',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#FFFFFF', edgecolor='#E2E8F0', alpha=0.9))

    out_path = CARTES_DIR / "carte_40_points_agadir.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"✓ Généré : {out_path}")


def generate_carte_tournee():
    """Génère la carte du circuit optimal officiel certifié (18 933.1 m, 42 arrêts)."""
    df = pd.read_csv(POINTS_CSV).set_index('point_id')
    with open(TSP_OPT_JSON, 'r') as f:
        data = json.load(f)
    tour = data['tour']

    fig, ax = plt.subplots(figsize=(11, 8.5), dpi=300)
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#FFFFFF')

    # Tracé de la tournée
    lons = [df.loc[pid, 'longitude'] for pid in tour]
    lats = [df.loc[pid, 'latitude'] for pid in tour]

    # Tracé des arcs avec flèches
    ax.plot(lons, lats, color='#2878B5', linestyle='-', linewidth=1.8, alpha=0.85, zorder=2, label='Circuit Optimal ATSP (18 933,1 m)')

    # Flèches de direction
    for i in range(len(tour) - 1):
        x1, y1 = lons[i], lats[i]
        x2, y2 = lons[i+1], lats[i+1]
        dx, dy = (x2 - x1) * 0.5, (y2 - y1) * 0.5
        ax.annotate('', xy=(x1 + dx, y1 + dy), xytext=(x1 + dx*0.9, y1 + dy*0.9),
                    arrowprops=dict(arrowstyle="->", color='#1E3A5F', lw=1.2), zorder=3)

    # Nœuds
    for idx, pid in enumerate(tour[:-1]):
        lon = df.loc[pid, 'longitude']
        lat = df.loc[pid, 'latitude']
        if pid == 0:
            c = '#D97706'
            s = 180
            marker = '*'
        elif pid == 40:
            c = '#20A6A6'
            s = 140
            marker = 's'
        else:
            c = '#1E3A5F'
            s = 70
            marker = 'o'
        ax.scatter(lon, lat, c=c, s=s, marker=marker, edgecolors='#FFFFFF', linewidth=1.2, zorder=4)

    # Mise en évidence du cul-de-sac littoral #40
    p40_lon, p40_lat = df.loc[40, 'longitude'], df.loc[40, 'latitude']
    ax.annotate("Cul-de-sac Littoral\nPoint #40 (Restaurant Les Blancs)\nAccès unique via Corniche",
                xy=(p40_lon, p40_lat), xytext=(p40_lon - 0.006, p40_lat + 0.003),
                arrowprops=dict(facecolor='#20A6A6', edgecolor='#1E3A5F', arrowstyle='->', lw=1.5),
                fontsize=8, weight='bold', color='#1E3A5F',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#E0F2FE', edgecolor='#20A6A6', alpha=0.9))

    # Dépôt #0
    p0_lon, p0_lat = df.loc[0, 'longitude'], df.loc[0, 'latitude']
    ax.annotate("Dépôt Central #0 (Place Al Amal)\nDépart & Arrivée stricts",
                xy=(p0_lon, p0_lat), xytext=(p0_lon + 0.003, p0_lat - 0.004),
                arrowprops=dict(facecolor='#D97706', edgecolor='#1E3A5F', arrowstyle='->', lw=1.5),
                fontsize=8, weight='bold', color='#1E3A5F',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#FEF3C7', edgecolor='#D97706', alpha=0.9))

    ax.set_title("AGADIR MAPPING — Tournée Officielle Certifiée (Phase 5 : GA + Optuna)\nDistance : 18 933,1 m | Arrêts : 42 | Gain Net : -2 081,2 m (-9,90%)",
                 fontsize=12, weight='bold', color='#1E3A5F', pad=15)
    ax.set_xlabel("Longitude WGS84 (°)", fontsize=10, color='#475569')
    ax.set_ylabel("Latitude WGS84 (°)", fontsize=10, color='#475569')
    ax.grid(True, linestyle='--', alpha=0.5, color='#CBD5E1')
    ax.legend(loc='lower left', frameon=True, facecolor='#FFFFFF', edgecolor='#CBD5E1', fontsize=9)

    out_path = CARTES_DIR / "carte_tournee_optimisee.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"✓ Généré : {out_path}")


def generate_carte_comparative():
    """Génère la comparaison cartographique Phase 4 (21 014.3 m) vs Phase 5 (18 933.1 m)."""
    df = pd.read_csv(POINTS_CSV).set_index('point_id')
    with open(TSP_OPT_JSON, 'r') as f:
        t_opt = json.load(f)['tour']
    with open(TSP_BASE_JSON, 'r') as f:
        t_base = json.load(f)['tour']

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7), dpi=300)
    fig.patch.set_facecolor('#F8FAFC')

    for ax, tour, dist, title, col in [
        (ax1, t_base, "21 014,3 m", "Phase 4 : GA Standard (Baseline)", "#DC2626"),
        (ax2, t_opt, "18 933,1 m", "Phase 5 : GA + Optuna (Optimale)", "#32936F")
    ]:
        ax.set_facecolor('#FFFFFF')
        lons = [df.loc[pid, 'longitude'] for pid in tour]
        lats = [df.loc[pid, 'latitude'] for pid in tour]
        ax.plot(lons, lats, color=col, linewidth=1.6, alpha=0.85, zorder=2)
        ax.scatter(lons, lats, c='#1E3A5F', s=40, edgecolors='#FFFFFF', zorder=3)
        ax.scatter(df.loc[0, 'longitude'], df.loc[0, 'latitude'], c='#D97706', s=160, marker='*', zorder=4)
        ax.scatter(df.loc[40, 'longitude'], df.loc[40, 'latitude'], c='#20A6A6', s=100, marker='s', zorder=4)

        ax.set_title(f"{title}\nDistance Totale : {dist}", fontsize=11, weight='bold', color='#1E3A5F')
        ax.set_xlabel("Longitude (°)", fontsize=9, color='#475569')
        ax.set_ylabel("Latitude (°)", fontsize=9, color='#475569')
        ax.grid(True, linestyle='--', alpha=0.4, color='#CBD5E1')

    fig.suptitle("AGADIR MAPPING — Comparaison des Tracés de Tournée : Gain de 2 081,2 m (-9,90%)",
                 fontsize=13, weight='bold', color='#1E3A5F', y=0.98)
    out_path = CARTES_DIR / "carte_comparative_phase4_phase5.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"✓ Généré : {out_path}")


def generate_heatmap_duration():
    """Génère la heatmap de la matrice des durées OSRM (41x41)."""
    df = pd.read_csv(DUR_CSV, index_col=0) / 60.0  # Conversion en minutes
    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#FFFFFF')

    im = ax.imshow(df.values, cmap='YlGnBu', aspect='auto')
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Durée Routière OSRM (minutes)", fontsize=10, color='#1E3A5F')

    ax.set_title("AGADIR MAPPING — Matrice Routière OSRM des Durées de Trajet (41 × 41)\n(Moyenne : 4,2 min | Max : 9,8 min)",
                 fontsize=12, weight='bold', color='#1E3A5F', pad=15)
    ax.set_xlabel("ID Point Destination (#0 à #40)", fontsize=10, color='#475569')
    ax.set_ylabel("ID Point Origine (#0 à #40)", fontsize=10, color='#475569')

    # Repères Dépôt #0 et Littoral #40
    ax.axhline(0, color='#D97706', linewidth=1, linestyle='--')
    ax.axvline(0, color='#D97706', linewidth=1, linestyle='--')
    ax.axhline(40, color='#20A6A6', linewidth=1, linestyle='--')
    ax.axvline(40, color='#20A6A6', linewidth=1, linestyle='--')

    out_path = GRAPHIQUES_DIR / "duration_matrix_heatmap.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"✓ Généré : {out_path}")


def generate_profil_etapes():
    """Génère le profil kilométrique des 41 étapes de la tournée."""
    with open(TSP_OPT_JSON, 'r') as f:
        steps = json.load(f)['steps']

    fig, ax = plt.subplots(figsize=(12, 5), dpi=300)
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#FFFFFF')

    step_nums = [s['step'] for s in steps]
    leg_dists = [s['leg_distance_m'] for s in steps]
    colors = ['#20A6A6' if s['to_point_id'] == 40 else '#2878B5' for s in steps]

    bars = ax.bar(step_nums, leg_dists, color=colors, width=0.7, edgecolor='#FFFFFF', linewidth=0.5, zorder=3)
    ax.axhline(np.mean(leg_dists), color='#D97706', linestyle='--', linewidth=1.5, zorder=4, label=f'Distance Moyenne : {np.mean(leg_dists):.1f} m')

    # Annotation de l'étape vers le point littoral #40
    step_40_idx = [i for i, s in enumerate(steps) if s['to_point_id'] == 40][0]
    ax.annotate(f"Étape #32 ➔ #40 (Littoral)\nMax : {leg_dists[step_40_idx]:.1f} m",
                xy=(step_nums[step_40_idx], leg_dists[step_40_idx]),
                xytext=(step_nums[step_40_idx] - 4, leg_dists[step_40_idx] + 200),
                arrowprops=dict(facecolor='#20A6A6', edgecolor='#1E3A5F', arrowstyle='->', lw=1.2),
                fontsize=8, weight='bold', color='#1E3A5F',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#E0F2FE', edgecolor='#20A6A6', alpha=0.9))

    ax.set_title("AGADIR MAPPING — Profil des Distances Routières des 41 Étapes de la Tournée Optimale", fontsize=11, weight='bold', color='#1E3A5F', pad=12)
    ax.set_xlabel("Numéro d'Étape de la Tournée (1 à 41)", fontsize=9, color='#475569')
    ax.set_ylabel("Distance de l'Étape (mètres)", fontsize=9, color='#475569')
    ax.set_xlim(0, 42)
    ax.set_ylim(0, 2200)
    ax.grid(True, linestyle='--', alpha=0.4, color='#CBD5E1', zorder=1)
    ax.legend(loc='upper left', frameon=True, facecolor='#FFFFFF', edgecolor='#CBD5E1', fontsize=9)

    out_path = GRAPHIQUES_DIR / "profil_etapes_tournee.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"✓ Généré : {out_path}")


def generate_diagramme_multi_agents():
    """Génère le schéma d'architecture et de gouvernance multi-agents."""
    fig, ax = plt.subplots(figsize=(12, 7), dpi=300)
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#FFFFFF')
    ax.axis('off')

    # Boîtes des 3 agents métier
    agents = [
        ("Agent 1 : Web Research", "Acquisition de sources d'urbanisme\n(3 sources : agadir-urbanisme.ma,\ninforms.org, agadir-port-marina.ma)", 0.05, 0.65, "#E0F2FE", "#0284C7"),
        ("Agent 2 : Semantic Scholar", "Littérature scientifique ATSP & Or-opt\n(3 articles indexés DOI :\nCOR 2022, EJOR 2018, JoH 2020)", 0.05, 0.38, "#E0E7FF", "#4F46E5"),
        ("Agent 3 : Gemini Analyst", "Synthèse cognitive LLM Flash\n(Formulation d'hypothèses, analyse\ndes contraintes d'asymétrie urbaine)", 0.05, 0.10, "#F3E8FF", "#9333EA")
    ]

    for title, desc, x, y, bg, border in agents:
        rect = patches.FancyBboxPatch((x, y), 0.28, 0.20, boxstyle="round,pad=0.02,rounding_size=0.03",
                                      facecolor=bg, edgecolor=border, linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + 0.14, y + 0.16, title, fontsize=9.5, weight='bold', color=border, ha='center')
        ax.text(x + 0.14, y + 0.07, desc, fontsize=7.5, color='#334155', ha='center', va='center')

    # Boîte Orchestrateur Central
    orch = patches.FancyBboxPatch((0.40, 0.38), 0.22, 0.22, boxstyle="round,pad=0.02,rounding_size=0.03",
                                  facecolor='#FEF3C7', edgecolor='#D97706', linewidth=2)
    ax.add_patch(orch)
    ax.text(0.51, 0.54, "Orchestrateur Central\n(Workflow State Machine)", fontsize=9.5, weight='bold', color='#D97706', ha='center')
    ax.text(0.51, 0.44, "• Budget Manager ($0,00619)\n• Cache Local SQLite\n• Sécurité & Ingestion Stricte", fontsize=7.5, color='#78350F', ha='center')

    # Boîte Judge Agent
    judge = patches.FancyBboxPatch((0.70, 0.55), 0.26, 0.30, boxstyle="round,pad=0.02,rounding_size=0.03",
                                   facecolor='#ECFDF5', edgecolor='#059669', linewidth=2)
    ax.add_patch(judge)
    ax.text(0.83, 0.80, "Judge Agent (Arbitre)\nArbitrage Contradictoire", fontsize=10, weight='bold', color='#059669', ha='center')
    ax.text(0.83, 0.67, "Score Pondéré : 0,9340 / 1,00\n1. Fiabilité sources (25%) : 0,95\n2. Cohérence scient. (25%) : 0,94\n3. Preuves solides (20%) : 0,92\n4. Concordance (15%) : 0,95\n5. Incertitudes (15%) : 0,90\n➔ Verdict : ACCEPTÉ",
            fontsize=7.5, color='#065F46', ha='center', va='center')

    # Boîte Veto Déterministe Python
    veto = patches.FancyBboxPatch((0.70, 0.12), 0.26, 0.30, boxstyle="round,pad=0.02,rounding_size=0.03",
                                  facecolor='#FEF2F2', edgecolor='#DC2626', linewidth=2)
    ax.add_patch(veto)
    ax.text(0.83, 0.37, "Veto Déterministe Python\n(Contre-Pouvoir Inviolable)", fontsize=10, weight='bold', color='#DC2626', ha='center')
    ax.text(0.83, 0.24, "6 / 6 Règles Validées sur OSRM\n• Départ strict Dépôt #0\n• Arrivée stricte Dépôt #0\n• Inclusion Point Littoral #40\n• Exactement 42 arrêts\n• 40 clients uniques (0 doublon)\n• Distance certifiée : 18 933,1 m",
            fontsize=7.5, color='#991B1B', ha='center', va='center')

    # Flèches de flux
    ax.annotate('', xy=(0.40, 0.50), xytext=(0.33, 0.75), arrowprops=dict(arrowstyle="->", color='#64748B', lw=1.5))
    ax.annotate('', xy=(0.40, 0.49), xytext=(0.33, 0.48), arrowprops=dict(arrowstyle="->", color='#64748B', lw=1.5))
    ax.annotate('', xy=(0.40, 0.48), xytext=(0.33, 0.20), arrowprops=dict(arrowstyle="->", color='#64748B', lw=1.5))
    ax.annotate('', xy=(0.70, 0.70), xytext=(0.62, 0.55), arrowprops=dict(arrowstyle="->", color='#059669', lw=1.8))
    ax.annotate('', xy=(0.70, 0.27), xytext=(0.62, 0.45), arrowprops=dict(arrowstyle="->", color='#DC2626', lw=1.8))

    # Journal d'audit scellé en bas
    ax.text(0.50, 0.03, "🔒 Journal d'Audit Cryptographique SHA-256 (11 événements scellés, empreinte cd368bf4e7ef...)",
            fontsize=9, weight='bold', color='#1E3A5F', ha='center',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#F1F5F9', edgecolor='#94A3B8'))

    ax.set_title("AGADIR MAPPING — Architecture Complète du Système Multi-Agents et de la Gouvernance Contradictoire",
                 fontsize=12, weight='bold', color='#1E3A5F', pad=15)

    out_path = DIAGRAMMES_DIR / "architecture_multi_agents.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"✓ Généré : {out_path}")


def generate_cycle_de_vie_donnees():
    """Génère le diagramme du cycle de vie des données à travers les 8 phases."""
    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#FFFFFF')
    ax.axis('off')

    phases = [
        ("P1: OSM", "Overpass API\n269 nœuds bruts\n167 POIs filtrés", "#0284C7"),
        ("P2: 40 Points", "delivery_points_40.csv\nUTM Zone 29N\nDépôt #0 + Littoral #40", "#0D9488"),
        ("P3: OSRM", "Matrice 41×41\nDistances (m) & Durées (s)\nAsymétrie alpha = 0.3217", "#D97706"),
        ("P4: GA ATSP", "Croisement OX + Inversion\nBaseline certifiée\n21 014,3 m", "#E11D48"),
        ("P5: Optuna", "Or-opt combiné (1,2,3)\n100 trials, 10 graines\n18 933,1 m (-9,90%)", "#059669"),
        ("P6: Multi-Agents", "3 Agents + Judge (0.934)\nVeto Python 6/6 règles\nAudit SHA-256", "#7C3AED"),
        ("P7: Dashboard", "Interface 4 Cadrans\nLeaflet + Tournée + IA\n6 Graphiques scientifiques", "#2563EB"),
        ("P8: Validation", "197 tests automatisés (100%)\nRapport reproductibilité\nClôture certifiée", "#047857")
    ]

    for i, (title, desc, color) in enumerate(phases):
        x = 0.02 + i * 0.122
        y = 0.35
        rect = patches.FancyBboxPatch((x, y), 0.105, 0.35, boxstyle="round,pad=0.015,rounding_size=0.02",
                                      facecolor='#FFFFFF', edgecolor=color, linewidth=1.8)
        ax.add_patch(rect)
        ax.text(x + 0.052, y + 0.28, title, fontsize=9, weight='bold', color=color, ha='center')
        ax.text(x + 0.052, y + 0.13, desc, fontsize=7, color='#334155', ha='center', va='center')

        if i < len(phases) - 1:
            ax.annotate('', xy=(x + 0.122, y + 0.175), xytext=(x + 0.105, y + 0.175),
                        arrowprops=dict(arrowstyle="->", color='#64748B', lw=1.5))

    ax.set_title("AGADIR MAPPING — Cycle de Vie Global des Données et Enchaînement des 8 Grandes Phases",
                 fontsize=12, weight='bold', color='#1E3A5F', pad=15)

    out_path = DIAGRAMMES_DIR / "cycle_de_vie_donnees.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"✓ Généré : {out_path}")


if __name__ == "__main__":
    generate_carte_points()
    generate_carte_tournee()
    generate_carte_comparative()
    generate_heatmap_duration()
    generate_profil_etapes()
    generate_diagramme_multi_agents()
    generate_cycle_de_vie_donnees()
    print("\n✓ Tous les actifs de l'Atlas ont été générés avec succès.")
