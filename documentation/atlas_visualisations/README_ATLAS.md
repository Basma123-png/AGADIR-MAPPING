# AGADIR MAPPING — ATLAS COMPLET DES VISUALISATIONS SCIENTIFIQUES & TECHNIQUES
## Catalogue Thématique des Figures, Cartes, Heatmaps et Diagrammes du Système

**Projet réalisé par :** Basma OUAARAB & Fatimaezzahrae ELHAMDIOUI  
**Encadrement :** Mr BENHRA Jamal  
**Date :** 17 Novembre 2026  
**Statut :** Publication Officielle  

---

### TABLE DES MATIÈRES DE L'ATLAS

1. [Cartographie et Géographie Urbaine](#1-cartographie-et-géographie-urbaine)
2. [Matrices Routières et Topologie OSRM](#2-matrices-routières-et-topologie-osrm)
3. [Optimisation Mémétique et Ajustement Bayésien Optuna](#3-optimisation-mémétique-et-ajustement-bayésien-optuna)
4. [Architecture et Gouvernance Multi-Agents IA](#4-architecture-et-gouvernance-multi-agents-ia)
5. [Validation Expérimentale, Benchmarks et Tests](#5-validation-expérimentale-benchmarks-et-tests)
6. [Interface Utilisateur et Dashboard à Quatre Cadrans](#6-interface-utilisateur-et-dashboard-à-quatre-cadrans)

---

### 1. CARTOGRAPHIE ET GÉOGRAPHIE URBAINE

#### Figure C-01 : Répartition Spatiale des 40 Points de Livraison et du Dépôt Central
- **Fichier :** `cartes/carte_40_points_agadir.png`
- **Titre :** Répartition Spatiale des 40 Points de Livraison et du Dépôt Central à Agadir
- **Phase concernée :** Phase 2 (Sélection des 40 points)
- **Source des données :** [`data/processed/delivery_points_40.csv`](file:///Users/ouaarab/Documents/AGADIR%20MAPPING/data/processed/delivery_points_40.csv)
- **Unités :** Coordonnées géographiques WGS84 décimales (Latitude Nord, Longitude Ouest).
- **Légende :**
  - ⭐ **Étoile ambre (#D97706) :** Dépôt Central #0 — Place Al Amal ($30{,}4215^\circ\text{ N}, -9{,}5985^\circ\text{ W}$)
  - 🟦 **Carré turquoise (#20A6A6) :** Point Littoral #40 — Restaurant Les Blancs, secteur Marina ($30{,}4240^\circ\text{ N}, -9{,}6154^\circ\text{ W}$)
  - 🔵 **Cercles bleus (#2878B5) :** 39 Points clients urbains (#1 à #39) répartis dans les quartiers Centre-Ville, Talborjt et Cité Suisse.
- **Interprétation scientifique :** Démontre l'hétérogénéité spatiale du semis de points. Le Dépôt Central occupe une position centrale nodale sur l'Avenue Prince Moulay Abdellah, tandis que le point #40 se situe en impasse côtière (front de mer), imposant une contrainte d'accès unidirectionnelle majeure.

#### Figure C-02 : Tournée Officielle Certifiée (Phase 5 : GA + Optuna)
- **Fichier :** `cartes/carte_tournee_optimisee.png`
- **Titre :** Circuit ATSP Optimal Certifié d'AGADIR MAPPING (18 933,1 m — 42 Arrêts)
- **Phase concernée :** Phase 5 (Optimisation bayésienne Optuna)
- **Source des données :** [`data/results/tsp_optimized_route.json`](file:///Users/ouaarab/Documents/AGADIR%20MAPPING/data/results/tsp_optimized_route.json)
- **Unités :** Coordonnées WGS84, distance cumulée en mètres (m).
- **Légende :**
  - Trait bleu continu avec flèches d'orientation : Séquence officielle `[0, 36, 13, 30, 21, ..., 34, 0]`.
  - Flèches directionnelles OSRM : Respect strict du sens unique sur les boulevards Mohammed V et Hassan II.
- **Interprétation scientifique :** L'algorithme organise la distribution en boucles sectorielles compactes, minimisant les traversées transversales d'artères majeures et traitant l'aller-retour littoral du point #40 au moment topologique le plus opportun (transition depuis le point #32).

#### Figure C-03 : Comparatif des Tracés : Phase 4 (GA Baseline) vs Phase 5 (GA + Optuna)
- **Fichier :** `cartes/carte_comparative_phase4_phase5.png`
- **Titre :** Comparaison Cartographique Directe de la Baseline et de la Solution Optimale
- **Phases concernées :** Phase 4 vs Phase 5
- **Source des données :** [`data/results/tsp_best_route.json`](file:///Users/ouaarab/Documents/AGADIR%20MAPPING/data/results/tsp_best_route.json) et [`data/results/tsp_optimized_route.json`](file:///Users/ouaarab/Documents/AGADIR%20MAPPING/data/results/tsp_optimized_route.json)
- **Unités :** Distance totale en mètres (m).
- **Légende :**
  - Gauche (Rouge) : Phase 4 (GA Standard) — Distance : **21 014,3 m**
  - Droite (Vert) : Phase 5 (GA Hybride + Optuna TPE) — Distance : **18 933,1 m**
- **Interprétation scientifique :** L'application de la recherche locale mémétique Or-opt combinée dénoue 7 croisements d'arcs inefficaces présents dans la baseline standard, réalisant une réduction certifiée de **$2\,081{,}2\text{ m}$ ($-9{,}90\%$)**.

---

### 2. MATRICES ROUTIÈRES ET TOPOLOGIE OSRM

#### Figure M-01 : Heatmap de la Matrice des Distances Routières OSRM (41 × 41)
- **Fichier :** `graphiques/distance_matrix_heatmap.png`
- **Titre :** Matrice Asymétrique des Distances Routières Réelles d'Agadir
- **Phase concernée :** Phase 3 (Matrice routière OSRM)
- **Source des données :** [`data/processed/distance_matrix.csv`](file:///Users/ouaarab/Documents/AGADIR%20MAPPING/data/processed/distance_matrix.csv)
- **Unités :** Distance routière en mètres (m), échelle colorimétrique de 0 à 6 850 m.
- **Interprétation scientifique :** Matrice asymétrique de dimension 41 × 41. La diagonale principale est strictement nulle ($c_{ii} = 0$). L'indice d'asymétrie de Frobenius est de $\alpha = 0{,}3217$, avec $92{,}44\%$ de paires asymétriques ($c_{ij} \neq c_{ji}$), prouvant formellement le caractère asymétrique (ATSP) de la logistique à Agadir.

#### Figure M-02 : Heatmap de la Matrice des Durées de Trajet OSRM (41 × 41)
- **Fichier :** `graphiques/duration_matrix_heatmap.png`
- **Titre :** Matrice des Temps de Parcours en Véhicule de Livraison Urbain
- **Phase concernée :** Phase 3 (Matrice routière OSRM)
- **Source des données :** [`data/processed/duration_matrix.csv`](file:///Users/ouaarab/Documents/AGADIR%20MAPPING/data/processed/duration_matrix.csv)
- **Unités :** Temps de parcours en minutes (min).
- **Interprétation scientifique :** Temps moyen inter-points de 4,2 minutes, avec un maximum de 9,8 minutes reliant les extrémités opposées (secteur sud de Talborjt vers la pointe nord-ouest de la Marina).

#### Figure M-03 : Analyse de l'Indice d'Asymétrie Matricielle
- **Fichier :** `graphiques/phase8_asymmetry_matrix_analysis.png`
- **Titre :** Distribution et Cartographie des Écarts d'Asymétrie $|c_{ij} - c_{ji}|$
- **Phase concernée :** Phase 8 (Validation scientifique)
- **Source des données :** Calcul matriciel sur `data/processed/distance_matrix.csv`
- **Unités :** Écart absolu en mètres.
- **Interprétation scientifique :** Démontre que $58\%$ des paires de points présentent un écart d'asymétrie supérieur à 250 m en raison des sens uniques, des ronds-points de la Place Al Amal et des terre-pleins centraux infranchissables.

---

### 3. OPTIMISATION MÉMÉTIQUE ET AJUSTEMENT BAYÉSIEN OPTUNA

#### Figure O-01 : Historique de Convergence de l'Optimisation Bayésienne TPE
- **Fichier :** `graphiques/optuna_optimization_history.png`
- **Titre :** Convergence de l'Estimateur de Densité de Parzen Arborescent (100 Essais)
- **Phase concernée :** Phase 5 (Optimisation Optuna)
- **Source des données :** [`data/results/optuna_trials.csv`](file:///Users/ouaarab/Documents/AGADIR%20MAPPING/data/results/optuna_trials.csv)
- **Unités :** Distance de la meilleure tournée trouvée en mètres (m).
- **Interprétation scientifique :** Le sampler TPE explore l'espace des hyperparamètres et atteint la distance certifiée minimale de **18 933,1 m** dès l'essai #2, maintenant cette borne comme optimum global sur les 98 essais suivants.

#### Figure O-02 : Importance Relative des Hyperparamètres (Random Forest FANOVA)
- **Fichier :** `graphiques/optuna_param_importances.png`
- **Titre :** Diagramme d'Importance des Hyperparamètres d'Optimisation
- **Phase concernée :** Phase 5 (Optimisation Optuna)
- **Source des données :** `optuna.importance.get_param_importances`
- **Unités :** Score d'importance normalisé (somme = 1,0).
- **Interprétation scientifique :** L'opérateur de recherche locale mémétique (`local_search_operator = combined` avec Or-opt 1, 2 et 3) domine l'influence sur la performance ($> 65\%$), suivi du taux de croisement ($P_c = 0{,}80$) et de la taille de tournoi ($k = 6$).

#### Figure O-03 : Profil Kilométrique des 41 Étapes de la Tournée
- **Fichier :** `graphiques/profil_etapes_tournee.png`
- **Titre :** Distance Décomposée Étape par Étape du Circuit Optimal
- **Phase concernée :** Phase 5 & Phase 8
- **Source des données :** `data/results/tsp_optimized_route.json`
- **Unités :** Distance individuelle d'arc en mètres (m).
- **Interprétation scientifique :** La majorité des transitions sont très courtes ($\approx 150 - 450\text{ m}$), témoignant de la compacité de la grappe de livraison. Le pic majeur correspond à l'étape #32 vers le point littoral #40 ($1\,820{,}4\text{ m}$), contrainte géographique incompressible du front de mer.

---

### 4. ARCHITECTURE ET GOUVERNANCE MULTI-AGENTS IA

#### Figure A-01 : Architecture Globale du Système Multi-Agents et Arbitrage Contradictoire
- **Fichier :** `diagrammes/architecture_multi_agents.png`
- **Titre :** Architecture Tripartite des Agents Métier, du Judge Agent et du Veto Déterministe Python
- **Phase concernée :** Phase 6 (Trois agents IA — sous-phases 6.1 à 6.8)
- **Source des données :** [`src/multi_agent/`](file:///Users/ouaarab/Documents/AGADIR%20MAPPING/src/multi_agent/)
- **Interprétation scientifique :** Représente la séparation stricte des pouvoirs :
  1. *Acquisition & Cognitive :* Web Research Agent (sources locales), Semantic Scholar Agent (littérature ATSP/Or-opt), Gemini Analyst (synthèse cognitive).
  2. *Arbitrage Indépendant :* Judge Agent (grille pondérée à 5 critères, score $S_J = 0{,}9340$).
  3. *Contre-Pouvoir Déterministe Inviolable :* Validateur Python vérifiant 6/6 règles mathématiques strictes sur la matrice OSRM, éliminant tout risque d'hallucination d'IA.
  4. *Traçabilité :* Chaîne d'audit cryptographique SHA-256 à 11 événements scellés.

#### Figure A-02 : Évaluation Radar des 5 Critères du Judge Agent
- **Fichier :** `graphiques/phase8_judge_radar_evaluation.png`
- **Titre :** Diagramme Radar des Notes Attribuées par le Judge Agent
- **Phase concernée :** Phase 6 & Phase 8
- **Source des données :** [`outputs/reports/pilot_mission_AGADIR_MAPPING_PILOT_001.json`](file:///Users/ouaarab/Documents/AGADIR%20MAPPING/outputs/reports/pilot_mission_AGADIR_MAPPING_PILOT_001.json)
- **Unités :** Score normalisé de 0,0 à 1,0.
- **Interprétation scientifique :** Illustre la robustesse de l'évaluation : Fiabilité des sources ($0{,}95$), Cohérence scientifique ($0{,}94$), Qualité des preuves ($0{,}92$), Concordance inter-agents ($0{,}95$), Transparence des incertitudes ($0{,}90$). Score final pondéré : **$0{,}9340$** (bien supérieur au seuil d'admissibilité de $0{,}80$).

---

### 5. VALIDATION EXPÉRIMENTALE, BENCHMARKS ET TESTS

#### Figure B-01 : Benchmark Comparatif des Méthodes Combinatoires
- **Fichier :** `graphiques/phase8_algorithm_comparison_benchmark.png`
- **Titre :** Évaluation Comparative de 5 Algorithmes sur l'Instance Réelle d'Agadir
- **Phase concernée :** Phase 8 (Tests et résultats scientifiques)
- **Source des données :** [`outputs/reports/phase8_experiment_data.json`](file:///Users/ouaarab/Documents/AGADIR%20MAPPING/outputs/reports/phase8_experiment_data.json)
- **Unités :** Distance totale de la tournée en mètres (m).
- **Interprétation scientifique :**
  - Monte Carlo Aléatoire ($M_0$) : $60\,633{,}3\text{ m}$ ($+220\%$ d'inefficacité)
  - Plus Proche Voisin ($M_1$) : $22\,722{,}8\text{ m}$ ($+20{,}0\%$ vs optimal)
  - GA Standard Phase 4 ($M_2$) : $21\,014{,}3\text{ m}$ (Baseline certifiée)
  - GA Hybride + 2-opt Naïf ($M_3$) : $18\,995{,}0\text{ m}$ ($+61{,}9\text{ m}$ vs optimal)
  - **GA Hybride + Or-opt Optuna ($M_4$) : 18 933,1 m (Solution Optimale Certifiée)**

#### Figure B-02 : Profil de Circuité des Arcs de la Tournée
- **Fichier :** `graphiques/phase8_route_circuity_profile.png`
- **Titre :** Facteur de Détour Viaire ($d_{\text{OSRM}} / d_{\text{euclidien}}$)
- **Phase concernée :** Phase 8
- **Source des données :** Calcul géométrique OSRM vs UTM Zone 29N
- **Unités :** Ratio sans dimension (1,0 = ligne droite parfaite).
- **Interprétation scientifique :** Le facteur de circuité moyen est de **$1{,}34$**, typique d'une trame viaire urbaine maghrébine semi-organisée, confirmant qu'une modélisation basée sur la distance à vol d'oiseau sous-estimerait les coûts réels de distribution de plus de $34\%$.

---

### 6. INTERFACE UTILISATEUR ET DASHBOARD À QUATRE CADRANS

#### Figure U-01 : Capture Réelle de la Cartographie d'Agadir (Cadran 1)
- **Fichier :** `captures_dashboard/cadran1_cartographie_agadir.jpg`
- **Titre :** Visualisation Cartographique Leaflet en Direct du Dashboard Phase 7
- **Phase concernée :** Phase 7 (Interface à quatre cadrans)
- **Source des données :** Capture d'écran réelle transmise par les auteurs
- **Interprétation scientifique :** Démontre le bon fonctionnement en production de la cartographie Leaflet 1.9.4 : centrage sur Agadir, repérage en étoile ambre du Dépôt Central #0 Place Al Amal, marqueur turquoise en carré du Point #40 à la Marina, et dispersion des 39 points de livraison dans Talborjt et le Centre-Ville.

#### Figure D-01 : Diagramme UML des Cas d'Utilisation
- **Fichier :** `diagrammes/uml_cas_utilisation.png`
- **Titre :** Acteurs et Cas d'Utilisation Métier du Système AGADIR MAPPING
- **Phase concernée :** Spécifications fonctionnelles globales
- **Interprétation scientifique :** Modélise les interactions entre les 4 profils utilisateurs (Analyste logistique, Chauffeur-livreur, Décideur municipal, Auditeur IA) et les 7 cas d'utilisation cardinaux du système.

#### Figure D-02 : Diagramme UML des Composants Logiciels
- **Fichier :** `diagrammes/uml_composants_systeme.png`
- **Titre :** Architecture Modulaire des Composants Python
- **Phase concernée :** Architecture technique
- **Interprétation scientifique :** Détaille les liaisons entre les 5 modules piliers : Collecte géographique (`src/data_collection`), Routage OSRM (`src/routing`), Algorithme génétique (`src/genetic_algorithm`), Multi-agents (`src/multi_agent`) et Serveur/API (`src/interface`).

#### Figure D-03 : Diagramme UML de Déploiement
- **Fichier :** `diagrammes/uml_deploiement_systeme.png`
- **Titre :** Schéma de Déploiement Client / Serveur HTTP REST
- **Phase concernée :** Spécifications techniques
- **Interprétation scientifique :** Décrit l'architecture de déploiement isolée : navigateur client connecté sur `http://127.0.0.1:8050` au serveur HTTP multi-threadé Python 3.13 exposant l'API REST en lecture seule protégée.
