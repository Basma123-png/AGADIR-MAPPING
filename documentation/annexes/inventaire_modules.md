# AGADIR MAPPING — INVENTAIRE TECHNIQUE EXHAUSTIF DES MODULES ET SCRIPTS
## Dictionnaire des Composants Logiciels, Classes, Fonctions et Tests Associés

**Projet :** AGADIR MAPPING — Système Intelligent d'Optimisation Logistique Urbaine  
**Auteurs :** Basma OUAARAB & Fatimaezzahrae ELHAMDIOUI  
**Encadrant :** Mr BENHRA Jamal  
**Date :** 17 Novembre 2026  

---

### 1. TABLEAU DE CORRESPONDANCE GLOBAL

| Module / Script | Rôle Métier Principal | Classes Clés | Tests Associés |
| :--- | :--- | :--- | :--- |
| `src/data_collection/osm_collector.py` | Extraction OSM Overpass | `OSMCollector` | `tests/test_osm_collector.py` |
| `src/data_collection/destination_selector.py`| Sélection des 40 points + Dépôt | `DestinationSelector` | `tests/test_destination_selector.py` |
| `src/geographic/projection.py` | Projections WGS84 / UTM Zone 29N | `SpatialProjector` | `tests/test_projections.py` |
| `src/geographic/spatial_processing.py` | Nettoyage géométrique & filtrage | `SpatialProcessor` | `tests/test_spatial_processing.py` |
| `src/routing/osrm_client.py` | Client HTTP OSRM (Table & Route) | `OSRMClient` | `tests/test_osrm_client.py` |
| `src/routing/distance_matrix.py` | Calcul matrices distances/durées | `DistanceMatrixBuilder` | `tests/test_distance_matrix.py` |
| `src/genetic_algorithm/individual.py` | Représentation d'une tournée | `Individual` | `tests/test_genetic_algorithm.py` |
| `src/genetic_algorithm/population.py` | Gestion de population de tournées| `Population` | `tests/test_genetic_algorithm.py` |
| `src/genetic_algorithm/operators.py` | Croisement OX, mutation inversion | `GeneticOperators` | `tests/test_genetic_algorithm.py` |
| `src/genetic_algorithm/engine.py` | Moteur d'évolution génétique | `GeneticEngine` | `tests/test_genetic_algorithm.py` |
| `src/genetic_algorithm/tsp_solver.py` | Résolveur ATSP haut niveau | `TSPSolver` | `tests/test_genetic_algorithm.py` |
| `src/optimization/optuna_tuner.py` | Tuner bayésien TPE & Or-opt | `OptunaTSPTuner` | `tests/test_optuna_tuner.py` |
| `src/multi_agent/schemas.py` | Modèles de données Pydantic | `MissionProposal`, etc. | `tests/multi_agent/test_schemas.py` |
| `src/multi_agent/config.py` | Configuration système multi-agents | `MultiAgentConfig` | `tests/multi_agent/test_config.py` |
| `src/multi_agent/cache.py` | Cache persistant SQLite | `AgentCache` | `tests/multi_agent/test_cache.py` |
| `src/multi_agent/budget_manager.py` | Gestionnaire budgétaire & kill-switch| `BudgetManager` | `tests/multi_agent/test_budget_manager.py` |
| `src/multi_agent/audit_logger.py` | Journal d'audit cryptographique | `AuditLogger` | `tests/multi_agent/test_audit_logger.py` |
| `src/multi_agent/security.py` | Nettoyage & détection d'injections | `SecurityValidator` | `tests/multi_agent/test_security.py` |
| `src/multi_agent/base_provider.py` | Classe abstraite LLM | `BaseLLMProvider` | `tests/multi_agent/test_gemini_provider.py` |
| `src/multi_agent/gemini_provider.py` | Connecteur Google Gemini Flash | `GeminiProvider` | `tests/multi_agent/test_gemini_provider.py` |
| `src/multi_agent/agents/web_research.py`| Agent de recherche web locale | `WebResearchAgent` | `tests/multi_agent/test_web_research.py` |
| `src/multi_agent/agents/scholar_research.py`| Agent de littérature académique | `ScholarResearchAgent` | `tests/multi_agent/test_scholar_research.py`|
| `src/multi_agent/agents/gemini_analyst.py`| Agent d'analyse cognitive | `GeminiAnalystAgent` | `tests/multi_agent/test_gemini_analyst.py` |
| `src/multi_agent/agents/judge.py` | Arbitre contradictoire & Veto | `JudgeAgent`, `VetoValidator`| `tests/multi_agent/test_judge.py` |
| `src/multi_agent/orchestrator.py` | Orchestrateur central State Machine| `MultiAgentOrchestrator`| `tests/multi_agent/test_orchestrator.py` |
| `src/interface/api_service.py` | Service de données du dashboard | `DashboardDataService` | `tests/test_phase7_dashboard.py` |
| `src/interface/server.py` | Serveur HTTP multi-threadé | `DashboardRequestHandler` | `tests/test_phase7_dashboard.py` |
| `src/visualization/candidates_map.py` | Cartographie interactive Folium | `CandidatesVisualizer` | `tests/test_destination_selector.py` |
| `src/visualization/control_map.py` | Cartes de contrôle spatial | `ControlMapBuilder` | `tests/test_osm_collector.py` |
| `src/visualization/matrix_visualization.py`| Heatmaps matricielles | `MatrixVisualizer` | `tests/test_distance_matrix.py` |
| `src/visualization/tsp_visualization.py`| Tracé des tournées TSP | `TSPVisualizer` | `tests/test_genetic_algorithm.py` |
| `scripts/run_phase1_extraction.py` | Lancement de la Phase 1 | `main()` | Intégration Phase 1 |
| `scripts/run_phase2_selection.py` | Lancement de la Phase 2 | `main()` | Intégration Phase 2 |
| `scripts/run_phase3_matrices.py` | Lancement de la Phase 3 | `main()` | Intégration Phase 3 |
| `scripts/run_phase4_tsp.py` | Lancement de la Phase 4 | `main()` | Intégration Phase 4 |
| `scripts/run_phase5_optuna.py` | Lancement de la Phase 5 | `main()` | Intégration Phase 5 |
| `scripts/run_phase6_pilot_mission.py`| Lancement de la Phase 6 (Pilote) | `main()` | Intégration Phase 6 |
| `scripts/run_phase7_dashboard.py` | Lancement du Dashboard Phase 7 | `main()`, `--check-only` | `tests/test_phase7_dashboard.py` |
| `scripts/run_phase8_experiments.py`| Campagne expérimentale Phase 8 | `main()` | `tests/test_phase8_scientific_validation.py`|

---

### 2. DÉTAIL DES RESPONSABILITÉS PAR MODULE

#### 2.1. Module de Collecte Géographique (`src/data_collection/`)
- **`osm_collector.py` :**
  - *Classe `OSMCollector` :* Construit les requêtes Overpass QL avec bounding box stricte sur Agadir Talborjt. Filtre les nœuds et polygones selon les balises `amenity`, `shop`, `tourism`. Exclut formellement les objets sans nom ou doublons spatiaux.
  - *Sorties :* `data/raw/agadir_talborjt_raw.json` et `data/processed/agadir_talborjt_all_pois.csv`.
- **`destination_selector.py` :**
  - *Classe `DestinationSelector` :* Échantillonne 40 points de livraison représentatifs selon des quotas par quartier et catégorie d'activité. Force l'insertion du Point Littoral #40 (*Restaurant Les Blancs*) et du Dépôt Central #0 (*Place Al Amal*).

#### 2.2. Module de Traitement Spatial (`src/geographic/`)
- **`projection.py` :**
  - *Classe `SpatialProjector` :* Convertit les coordonnées angulaires WGS84 (EPSG:4326) en coordonnées métriques cartésiennes planes UTM Zone 29N (EPSG:32629) via `pyproj`.
- **`spatial_processing.py` :**
  - *Classe `SpatialProcessor` :* Calcule les distances euclidiennes cartésiennes, vérifie l'absence de points aberrants et contrôle les contraintes de non-immersion marine.

#### 2.3. Module de Routage et Matrices (`src/routing/`)
- **`osrm_client.py` :**
  - *Classe `OSRMClient` :* Émet des requêtes HTTP vers le moteur OSRM (`/table/v1/driving/` et `/route/v1/driving/`). Gère les retries exponentiels et le recalage (snapping) des points sur le graphe routier.
- **`distance_matrix.py` :**
  - *Classe `DistanceMatrixBuilder` :* Assemble et normalise la matrice carrée 41 × 41 des distances (en mètres) et des durées (en secondes). Calcule les indices d'asymétrie matricielle de Frobenius.

#### 2.4. Métaheuristique Mémétique et Optimisation (`src/genetic_algorithm/` et `src/optimization/`)
- **`individual.py`, `population.py`, `operators.py`, `engine.py`, `tsp_solver.py` :**
  - Implémentent le cycle de vie de l'algorithme génétique pour l'ATSP : population d'individus à permutation fermée débutant et finissant par 0, croisement Order Crossover (OX) à 2 points de coupure, mutation par inversion de segment, sélection par tournoi de taille $k=6$, initialisation hybride combinant plus proche voisin et aléatoire.
- **`optuna_tuner.py` :**
  - *Classe `OptunaTSPTuner` :* Orchestre l'optimisation bayésienne des hyperparamètres par TPE sur 100 trials. Intègre la recherche locale intensive Or-opt (relocalisation sans inversion de chaînes de 1, 2 ou 3 nœuds) permettant d'atteindre l'optimum certifié de **18 933,1 m**.

#### 2.5. Système Multi-Agents et Gouvernance IA (`src/multi_agent/`)
- **`schemas.py` :** Modèles de validation de données Pydantic v2 garantissant le typage strict des requêtes, thèses, verdicts et journaux d'audit.
- **`budget_manager.py` :** Surveillance en temps réel des coûts d'inférence LLM avec seuil d'alerte précoce à 0,10 $ et Kill-Switch matériel inviolable à 0,50 $.
- **`audit_logger.py` :** Enregistrement cryptographique séquentiel garantissant la non-répudiation des décisions multi-agents par chaînage de hachages SHA-256 scellés.
- **`agents/web_research.py` :** Collecte automatisée et filtrage de confiance d'extraits d'urbanisme sur Agadir.
- **`agents/scholar_research.py` :** Recherche bibliographique et extraction de résumés d'articles scientifiques validés par DOI.
- **`agents/gemini_analyst.py` :** Synthèse cognitive et formalisation d'hypothèses sur le modèle Gemini 3 Flash.
- **`agents/judge.py` :** Arbitrage contradictoire selon la grille officielle à 5 critères pondérés (score 0,9340) et application du **Veto Déterministe Python** vérifiant 6/6 règles mathématiques strictes sur la matrice OSRM.

#### 2.6. Visualisation et Interface (`src/visualization/` et `src/interface/`)
- **`server.py` & `api_service.py` :** Serveur HTTP multi-threadé servant l'application Single Page et exposant l'API REST en lecture seule stricte (protection contre toute injection ou écriture non autorisée).
- **Interface Web à Quatre Cadrans (`src/interface/static/`) :** Application moderne en thème clair urbain articulant en temps réel la cartographie Leaflet, le pas-à-pas de la tournée, le panneau multi-agents et les six visualisations scientifiques (Chart.js et Canvas natif).
