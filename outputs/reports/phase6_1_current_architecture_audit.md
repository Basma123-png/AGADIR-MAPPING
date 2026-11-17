# RAPPORT OFFICIEL — PHASE 6.1
## Document 1 : Audit Préalable de l'Architecture Existante (Phases 1 à 5)
**Projet :** AGADIR MAPPING — Last Mile TSP Optimization  
**Date d'audit :** 16/11/2026  
**Auteur :** Antigravity (Google DeepMind Team)  
**Classification :** Spécification Technique & Conception Système  

---

## 1. Objectif de l'Audit

Conformément aux directives de la Phase 6.1, aucune proposition d'architecture multi-agents ne peut être formulée sans une inspection préalable et exhaustive de la base de code réelle, des dépendances installées, des structures de données validées et des contraintes physiques du projet AGADIR MAPPING.

Le présent document dresse l'état des lieux rigoureux des Phases 1 à 5, identifie les points d'ancrage du futur système multi-agents et met en lumière les contraintes d'intégrité à respecter.

---

## 2. Inventaire de la Structure Réelle du Dépôt

L'inspection directe du système de fichiers révèle une organisation modulaire et strictement découplée :

```text
/Users/ouaarab/Documents/AGADIR MAPPING/
├── .env.example                 # Modèle de configuration des variables d'environnement
├── .gitignore                   # Exclusion Git (.venv, __pycache__, .env, etc.)
├── README.md                    # Documentation globale du projet
├── requirements.txt             # Dépendances Python déclarées et verrouillées
├── config/
│   ├── __init__.py
│   └── settings.py              # Constantes géographiques (BBOX, CRS), endpoints API, chemins
├── data/
│   ├── raw/
│   │   └── agadir_talborjt_raw.json           # Cache brut de l'extraction Overpass OSM
│   ├── processed/
│   │   ├── agadir_talborjt_all_pois.csv       # 243 POIs bruts extraits
│   │   ├── agadir_talborjt_all_pois.geojson   # Couche spatiale des 243 POIs
│   │   ├── delivery_points_40.csv             # 40 destinations validées + Dépôt #0 (certifié)
│   │   ├── delivery_points_40.geojson         # Couche spatiale officielle des 41 points
│   │   ├── cartesian_distance_matrix.csv      # Matrice euclidienne 41x41 (UTM 29N)
│   │   ├── distance_matrix.csv                # Matrice routière OSRM 41x41 (Mètres, certifiée)
│   │   ├── distance_matrix.json               # Métadonnées et matrice des distances
│   │   ├── duration_matrix.csv                # Matrice des durées OSRM 41x41 (Secondes)
│   │   └── duration_matrix.json               # Métadonnées et matrice des durées
│   └── results/
│       ├── distance_matrix.csv / .json        # Miroir certifié pour la recherche
│       ├── duration_matrix.csv / .json        # Miroir certifié pour la recherche
│       ├── tsp_results.csv                    # Banc d'essai comparatif de la Phase 4
│       ├── tsp_best_route.json                # Meilleure tournée Phase 4 (21 014,3 m)
│       ├── optuna_study.db                    # Base SQLite de l'optimisation bayésienne Phase 5
│       ├── optuna_trials.csv                  # Tableau des 50 essais Optuna
│       ├── optuna_best_params.json            # Meilleurs hyperparamètres découverts
│       └── tsp_optimized_route.json           # Tournée officielle optimisée Phase 5 (18 933,1 m)
├── outputs/
│   ├── figures/                               # Visualisations graphiques (PNG 300 DPI)
│   ├── maps/                                  # Cartes interactives Folium (HTML)
│   └── reports/                               # Rapports d'audit et de validation Markdown
├── scripts/
│   ├── run_phase1_extraction.py               # Exécutable Phase 1 (OSM Overpass)
│   ├── run_phase2_selection.py                # Exécutable Phase 2 (Sélection des 40 points)
│   ├── run_phase3_matrices.py                 # Exécutable Phase 3 (Matrices OSRM 41x41)
│   ├── run_phase4_tsp.py                      # Exécutable Phase 4 (Moteur GA et 2-opt)
│   └── run_phase5_optuna.py                   # Exécutable Phase 5 (Optimisation bayésienne)
├── src/
│   ├── agents/                                # Package réservé au Système Multi-Agents IA (Phase 6)
│   │   └── __init__.py
│   ├── data_collection/
│   │   ├── osm_collector.py                   # Client Overpass API robuste avec bascule multi-serveurs
│   │   └── destination_selector.py            # Sélecteur stratifié (39 urbains + 1 littoral + dépôt)
│   ├── genetic_algorithm/
│   │   ├── individual.py                      # Classe Individual ATSP (coût orienté exact)
│   │   ├── operators.py                       # Sélection, Croisements (OX, PMX), Mutations, 2-opt, Or-opt
│   │   ├── population.py                      # Gestionnaire de population et amorçage hybride
│   │   ├── engine.py                          # Moteur GA mémétique complet avec callback d'arrêt
│   │   ├── genetic_algorithm.py               # Façade d'exportation
│   │   └── tsp_solver.py                      # Banc d'essai comparatif (NN, 2-opt, GA, Memetic)
│   ├── geographic/
│   │   ├── projection.py                      # Convertisseur bidirectionnel WGS84 <-> UTM Zone 29N
│   │   └── spatial_processing.py              # Analyse spatiale, calcul de BBOX et centroïdes
│   ├── interface/                             # Package réservé à la GUI Tkinter (Phase 7)
│   │   └── __init__.py
│   ├── optimization/
│   │   ├── optuna_tuner.py                    # Tuner bayésien Optuna (TPE) multi-graines
│   │   └── __init__.py
│   ├── routing/
│   │   ├── osrm_client.py                     # Client HTTP OSRM (nearest, table, route)
│   │   └── distance_matrix.py                 # Constructeur et auditeur des matrices 41x41
│   └── visualization/
│       ├── candidates_map.py                  # Carte Folium des 40 candidats + dépôt
│       ├── control_map.py                     # Carte Folium de la BBOX d'Agadir
│       ├── matrix_visualization.py            # Heatmaps et distribution du détour (Matplotlib)
│       └── tsp_visualization.py               # Tracé interactif Folium (AntPath) et convergence
└── tests/                                     # Suite de 29 tests unitaires (100% passante)
```

---

## 3. Analyse des Technologies et Dépendances Réellement Installées

L'environnement virtuel actif `.venv` repose exclusivement sur l'interpréteur Framework Python 3.13 macOS :
`/Library/Frameworks/Python.framework/Versions/3.13/bin/python3`

### État de l'art des bibliothèques installées :

1. **Système d'Information Géographique & Réseau :**
   - `geopandas` (1.0.1) & `shapely` (2.0.7) : Manipulation vectorielle spatiale certifiée.
   - `pyproj` (3.7.1) : Projections géodésiques WGS84 (EPSG:4326) $\leftrightarrow$ UTM Zone 29N (EPSG:32629).
   - `folium` (0.19.4) : Rendu cartographique Leaflet/HTML interactif.
   - `requests` (2.34.2) : Client HTTP synchrone robuste avec gestion de sessions et timeouts.

2. **Calcul Numérique & Optimisation :**
   - `numpy` (2.2.3) & `pandas` (2.2.3) : Calcul vectoriel matriciel asymétrique 41x41 et gestion de DataFrames.
   - `scipy` (1.15.2) : Calculs statistiques avancés et distances.
   - `optuna` (5.1.0) : Optimisation bayésienne par TPE avec stockage persistant SQLite.

3. **Intelligence Artificielle & Gestion des Schémas :**
   - `google-genai` (3.3.0) : **SDK officiel moderne Google GenAI** pour l'interaction avec la famille de modèles Gemini (Interactions API / Decisions API).
   - `pydantic` (2.14.3) : Modélisation, sérialisation et validation stricte des schémas de données JSON.
   - `python-dotenv` (1.1.1) : Chargement sécurisé des secrets et clés d'API depuis les variables d'environnement.

4. **Tests et Qualité :**
   - `pytest` (9.2.0) & `pytest-cov` (7.1.0) : Framework d'automatisation des tests. 29 tests unitaires opérationnels et verts.

> [!TIP]
> **Constat technologique déterminant :** Toutes les dépendances clés nécessaires à la Phase 6 (`google-genai`, `pydantic v2`, `requests`, `python-dotenv`) sont **déjà installées et fonctionnelles** dans l'environnement virtuel. Aucune installation nouvelle n'est requise.

---

## 4. Données et Artefacts Protégés (Sanctuarisation des Acquis)

Les modules de la Phase 6 devront opérer en **lecture seule stricte** sur les acquis fondamentaux :

1. **La Tournée Officielle de Référence (Phase 5) :**
   $$\pi_{\text{official}} = [0, 36, 13, 30, 21, 6, 33, 27, 25, 26, 7, 9, 38, 3, 10, 11, 17, 28, 37, 2, 14, 12, 5, 35, 16, 22, 39, 8, 1, 19, 20, 32, 40, 24, 29, 4, 23, 31, 15, 18, 34, 0]$$
   - Distance officielle certifiée : **`18 933,1 mètres`** (`18,9331 km`).
   - Dépôt Central : Point #0 (*Place Al Amal*).
   - Destination Littorale : Point #40 (*Restaurant Les Blancs — Corniche / Marina*), visité à l'étape #32.
   - Nombre de points visités : 40 destinations uniques + 1 départ + 1 retour = 42 arrêts.

2. **Les Données Géographiques et Topologiques :**
   - `delivery_points_40.csv` et `delivery_points_40.geojson` : Coordonnées réelles issues d'OpenStreetMap.
   - `distance_matrix.csv` et `duration_matrix.csv` : Matrices asymétriques 41x41 issues du graphe routier OSRM réel.
   - **Interdiction absolue :** Aucun agent IA ne possède de droit d'écriture sur ces fichiers.

---

## 5. Points d'Intégration pour le Système Multi-Agents

Le système multi-agents viendra s'insérer naturellement dans l'architecture sans perturber le cœur algorithmique :

1. **Emplacement de code dédié :** Le dossier [`src/agents/`](file:///Users/ouaarab/Documents/AGADIR%20MAPPING/src/agents/) accueillera l'ensemble des modules agents, orchestrateur, et validateurs.
2. **Interface avec le moteur TSP existant :**
   - Les agents de recherche (Web, Semantic Scholar) collectent des articles et méthodes académiques (ex: LKH-3, ALNS, Genetic Edge Recombination).
   - L'agent Analyste (Gemini) propose des améliorations potentielles.
   - Le Validateur Déterministe Python vérifie mathématiquement toute hypothèse sur la matrice OSRM brute 41x41 via les modules existants (`src/genetic_algorithm/individual.py` et `src/routing/distance_matrix.py`).
   - L'agent Juge arbitre de manière probatoire sans jamais faire confiance aveuglément aux hallucinations textuelles.
3. **Persistance et Traçabilité :**
   - Les journaux de mission et les rapports d'arbitrage seront stockés dans `data/agents_output/` et `outputs/reports/`.

---

## 6. Analyse des Risques Techniques et de Compatibilité

| Risque Identifié | Gravité | Probabilité | Stratégie d'Atténuation Prévue |
| :--- | :---: | :---: | :--- |
| **Sandbox macOS & Réseau** | Moyenne | Moyenne | Prévoir un mode dégradé hors-ligne avec cache local des requêtes web/scientifiques pour les tests locaux. |
| **Indisponibilité API Gemini** | Élevée | Faible | Architecture configurable permettant le choix dynamique du modèle (`gemini-2.5-flash`, `gemini-2.5-pro`) ou fallback mock. |
| **Quotas Semantic Scholar** | Moyenne | Élevée | Limitation stricte des requêtes (1 req/sec), pagination contrôlée, mise en cache SQLite locale des articles indexés. |
| **Injections de Prompt Web** | Élevée | Moyenne | Sanitisation stricte des textes scrapés et balisage XML étanche interdisant l'exécution d'instructions arbitraires. |
| **Altération des fichiers de référence** | Critique | Faible | Contrôle d'accès strict en lecture seule et vérification par hachage SHA-256 dans le Validateur Déterministe. |

---

## 7. Conclusion de l'Audit Préalable

L'architecture actuelle d'AGADIR MAPPING est saine, hautement modulaire et parfaitement pourvue en dépendances technologiques de premier plan. La conception de la Phase 6 peut s'appuyer sur un socle robuste et sécurisé.
