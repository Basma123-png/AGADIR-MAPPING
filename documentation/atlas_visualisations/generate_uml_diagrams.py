#!/usr/bin/env python3
"""Génération des diagrammes UML et d'architecture pour le projet AGADIR MAPPING."""

from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DIAG_DIR = ROOT_DIR / "documentation" / "atlas_visualisations" / "diagrammes"

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial']


def generate_uml_use_cases():
    fig, ax = plt.subplots(figsize=(11, 7), dpi=300)
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#FFFFFF')
    ax.axis('off')

    # Boîte système
    system_box = patches.FancyBboxPatch((0.26, 0.05), 0.52, 0.88, boxstyle="round,pad=0.02",
                                        facecolor='#FFFFFF', edgecolor='#1E3A5F', linewidth=2)
    ax.add_patch(system_box)
    ax.text(0.52, 0.89, "Système AGADIR MAPPING (Phase 1 à 8)", fontsize=11, weight='bold', color='#1E3A5F', ha='center')

    # Acteurs
    actors = [
        ("Analyste\nLogistique", 0.08, 0.72),
        ("Chauffeur /\nLivreur", 0.08, 0.28),
        ("Décideur\nMunicipal", 0.92, 0.72),
        ("Auditeur IA /\nScientifique", 0.92, 0.28)
    ]
    for name, x, y in actors:
        # Tête
        circle = plt.Circle((x, y + 0.05), 0.025, color='#1E3A5F', fill=False, lw=1.5)
        ax.add_patch(circle)
        # Corps
        ax.plot([x, x], [y + 0.025, y - 0.03], color='#1E3A5F', lw=1.5)
        # Bras
        ax.plot([x - 0.025, x + 0.025], [y + 0.01, y + 0.01], color='#1E3A5F', lw=1.5)
        # Jambes
        ax.plot([x, x - 0.02], [y - 0.03, y - 0.07], color='#1E3A5F', lw=1.5)
        ax.plot([x, x + 0.02], [y - 0.03, y - 0.07], color='#1E3A5F', lw=1.5)
        ax.text(x, y - 0.11, name, fontsize=8, weight='bold', color='#1E3A5F', ha='center')

    # Cas d'utilisation (ellipses)
    use_cases = [
        ("UC-01 : Extraire & filtrer les POIs OSM", 0.52, 0.80, "#E0F2FE", "#0284C7"),
        ("UC-02 : Sélectionner 40 points & Dépôt #0", 0.52, 0.68, "#E0F2FE", "#0284C7"),
        ("UC-03 : Calculer matrices OSRM asymétriques", 0.52, 0.56, "#FEF3C7", "#D97706"),
        ("UC-04 : Optimiser la tournée (GA + Optuna TPE)", 0.52, 0.44, "#DCFCE7", "#16A34A"),
        ("UC-05 : Exécuter l'arbitrage multi-agents & Veto", 0.52, 0.32, "#F3E8FF", "#9333EA"),
        ("UC-06 : Visualiser le Dashboard 4 Cadrans", 0.52, 0.20, "#DBEAFE", "#2563EB"),
        ("UC-07 : Auditer la conformité SHA-256", 0.52, 0.08, "#FEE2E2", "#DC2626")
    ]
    for name, x, y, bg, border in use_cases:
        ellipse = patches.Ellipse((x, y), 0.44, 0.075, facecolor=bg, edgecolor=border, lw=1.4)
        ax.add_patch(ellipse)
        ax.text(x, y, name, fontsize=8, weight='bold', color='#1E293B', ha='center', va='center')

    # Lignes d'association
    # Analyste
    ax.plot([0.12, 0.30], [0.72, 0.80], color='#64748B', lw=1.2)
    ax.plot([0.12, 0.30], [0.72, 0.68], color='#64748B', lw=1.2)
    ax.plot([0.12, 0.30], [0.72, 0.56], color='#64748B', lw=1.2)
    ax.plot([0.12, 0.30], [0.72, 0.44], color='#64748B', lw=1.2)

    # Chauffeur
    ax.plot([0.12, 0.30], [0.28, 0.44], color='#64748B', lw=1.2)
    ax.plot([0.12, 0.30], [0.28, 0.20], color='#64748B', lw=1.2)

    # Décideur
    ax.plot([0.88, 0.74], [0.72, 0.44], color='#64748B', lw=1.2)
    ax.plot([0.88, 0.74], [0.72, 0.20], color='#64748B', lw=1.2)

    # Auditeur
    ax.plot([0.88, 0.74], [0.28, 0.32], color='#64748B', lw=1.2)
    ax.plot([0.88, 0.74], [0.28, 0.08], color='#64748B', lw=1.2)

    ax.set_title("AGADIR MAPPING — Diagramme UML des Cas d'Utilisation", fontsize=12, weight='bold', color='#1E3A5F', pad=15)
    out_path = DIAG_DIR / "uml_cas_utilisation.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"✓ Généré : {out_path}")


def generate_uml_components():
    fig, ax = plt.subplots(figsize=(11, 7), dpi=300)
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#FFFFFF')
    ax.axis('off')

    components = [
        ("Module Géographique\n(src/data_collection,\nsrc/geographic)", 0.05, 0.60, "#E0F2FE", "#0284C7"),
        ("Module de Routage\n(src/routing/\nosrm_client, distance_matrix)", 0.38, 0.60, "#FEF3C7", "#D97706"),
        ("Moteur Mémétique ATSP\n(src/genetic_algorithm,\nsrc/optimization)", 0.71, 0.60, "#DCFCE7", "#16A34A"),
        ("Socle Multi-Agents\n(src/multi_agent/\nagents, orchestrator, judge)", 0.20, 0.15, "#F3E8FF", "#9333EA"),
        ("Interface 4 Cadrans\n(src/interface/\nserver, api_service, static/)", 0.60, 0.15, "#DBEAFE", "#2563EB")
    ]

    for title, x, y, bg, border in components:
        rect = patches.FancyBboxPatch((x, y), 0.24, 0.24, boxstyle="round,pad=0.02",
                                      facecolor=bg, edgecolor=border, lw=1.8)
        ax.add_patch(rect)
        ax.text(x + 0.12, y + 0.12, title, fontsize=9, weight='bold', color='#1E293B', ha='center', va='center')

    # Liaisons
    ax.annotate('', xy=(0.38, 0.72), xytext=(0.29, 0.72), arrowprops=dict(arrowstyle="->", color='#64748B', lw=1.5))
    ax.annotate('', xy=(0.71, 0.72), xytext=(0.62, 0.72), arrowprops=dict(arrowstyle="->", color='#64748B', lw=1.5))
    ax.annotate('', xy=(0.32, 0.39), xytext=(0.50, 0.60), arrowprops=dict(arrowstyle="->", color='#64748B', lw=1.5))
    ax.annotate('', xy=(0.72, 0.39), xytext=(0.72, 0.60), arrowprops=dict(arrowstyle="->", color='#64748B', lw=1.5))
    ax.annotate('', xy=(0.60, 0.27), xytext=(0.44, 0.27), arrowprops=dict(arrowstyle="->", color='#64748B', lw=1.5))

    ax.set_title("AGADIR MAPPING — Diagramme UML des Composants Logiciels", fontsize=12, weight='bold', color='#1E3A5F', pad=15)
    out_path = DIAG_DIR / "uml_composants_systeme.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"✓ Généré : {out_path}")


def generate_uml_deployment():
    fig, ax = plt.subplots(figsize=(11, 6), dpi=300)
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#FFFFFF')
    ax.axis('off')

    nodes = [
        ("Nœud Client (Poste Utilisateur / Décideur)\nNavigateur Web Moderne (Chrome, Firefox, Safari)\n• Single Page App (HTML5 / CSS3 Thème Clair)\n• Cartographie Leaflet 1.9.4\n• Moteur Graphique Chart.js 4.4.2 & Canvas", 0.05, 0.30, "#E0F2FE", "#0284C7"),
        ("Nœud Serveur d'Application (AGADIR MAPPING Host)\nEnvironnement Python 3.11 - 3.13\n• Serveur HTTP Multi-threadé (src/interface/server.py)\n• API REST Lecture Seule (port 8050)\n• Moteur Algorithmique ATSP & Or-opt\n• Orchestrateur Multi-Agents & Veto Python\n• Système de fichiers scellé SHA-256", 0.55, 0.30, "#FEF3C7", "#D97706")
    ]

    for title, x, y, bg, border in nodes:
        rect = patches.FancyBboxPatch((x, y), 0.40, 0.45, boxstyle="round,pad=0.03",
                                      facecolor=bg, edgecolor=border, lw=2)
        ax.add_patch(rect)
        ax.text(x + 0.20, y + 0.22, title, fontsize=8.5, color='#1E293B', ha='center', va='center')

    # Connexion HTTP/REST
    ax.annotate('', xy=(0.55, 0.52), xytext=(0.45, 0.52),
                arrowprops=dict(arrowstyle="<->", color='#2563EB', lw=2))
    ax.text(0.50, 0.55, "Protocole HTTP / REST (JSON)\nhttp://127.0.0.1:8050", fontsize=8, weight='bold', color='#2563EB', ha='center')

    ax.set_title("AGADIR MAPPING — Diagramme UML de Déploiement", fontsize=12, weight='bold', color='#1E3A5F', pad=15)
    out_path = DIAG_DIR / "uml_deploiement_systeme.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"✓ Généré : {out_path}")


if __name__ == "__main__":
    generate_uml_use_cases()
    generate_uml_components()
    generate_uml_deployment()
    print("✓ Diagrammes UML générés avec succès.")
