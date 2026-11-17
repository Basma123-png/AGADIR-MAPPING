# AGADIR MAPPING — Last Mile TSP Optimization

## Description du Projet

**AGADIR MAPPING** est une application d'optimisation combinatoire et d'aide à la décision spatiale dédiée à la logistique du dernier kilomètre (*Last Mile Delivery*) dans la ville d'**Agadir, Maroc**.

L'application aborde le problème du voyageur de commerce (**TSP — Travelling Salesperson Problem**) en comparant la distance cartésienne euclidienne (projetée en **UTM Zone 29N / EPSG:32629**) à la distance réelle sur le réseau routier urbain calculée via l'API **OSRM** (Open Source Routing Machine).

Le quartier d'étude initial est **Talborjt – Centre-ville d'Agadir**.

---

## Architecture de l'Application

L'interface graphique est structurée en **quatre cadrans interactifs** :
1. **Cadran 1 — Paramétrage et Lancement :** Configuration de l'algorithme génétique (Manuel, Optuna ou Multi-Agents IA avec Google Gemini), commandes et journaux d'exécution.
2. **Cadran 2 — Métriques et Convergence :** Indicateurs de performance (distances initiale et finale, gain %, temps de calcul) et graphiques Matplotlib temps réel (fitness et distance).
3. **Cadran 3 — Plan TSP Cartésien :** Projection métrique XY locale en UTM 29N (exprimée en km) illustrant le dépôt et le parcours optimisé.
4. **Cadran 4 — Carte Réelle OSRM :** Visualisation interactive Leaflet/Folium montrant le véritable tracé routier empruntant les rues d'Agadir.

---

## Installation et Environnement

Le projet s'appuie sur Python 3.13 (Python Framework natif macOS avec support Tkinter 8.6).

```bash
# 1. Cloner ou ouvrir le projet
cd "AGADIR MAPPING"

# 2. Activer l'environnement virtuel
source .venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
cp .env.example .env
# Renseigner votre clé GEMINI_API_KEY dans .env
```

---

## Structure du Répertoire

```text
AGADIR MAPPING/
├── main.py                          # Point d'entrée principal
├── requirements.txt                 # Dépendances du projet
├── config/
│   └── settings.py                  # Constantes spatiales et paramètres généraux
├── data/
│   ├── raw/                         # Données brutes Overpass API
│   ├── processed/                   # POIs qualifiés (CSV, GeoJSON)
│   └── results/                     # Résultats et matrices de coûts
├── src/
│   ├── data_collection/             # Extraction Overpass OSM
│   ├── geographic/                  # Projections (EPSG:4326 <-> EPSG:32629) et métriques
│   ├── routing/                     # Client OSRM (matrices et géométries)
│   ├── genetic_algorithm/           # Moteur GA pour le TSP
│   ├── optimization/                # Optimiseur Optuna
│   ├── agents/                      # Système multi-agents (Web, Sémantique, Arbitre)
│   ├── visualization/               # Cartographie Folium et figures Matplotlib
│   └── interface/                   # IHM Tkinter à quatre cadrans
├── tests/                           # Tests unitaires automatisés
├── outputs/
│   ├── maps/                        # Cartes interactives générées
│   ├── figures/                     # Graphiques PNG
│   └── reports/                     # Rapports d'expérimentation
└── scripts/                         # Scripts de traitement par phase
```

---

## Méthodologie par Phases

- **Phase 1 :** Environnement, architecture et collecte géographique réelle OSM à Talborjt.
- **Phase 2 :** Sélection et validation des 40 points de livraison représentatifs.
- **Phase 3 :** Construction de la matrice des distances et intégration OSRM.
- **Phase 4 :** Moteur d'algorithme génétique TSP (OX, PMX, 2-opt, élitisme).
- **Phase 5 :** Réglage automatique des hyperparamètres avec Optuna.
- **Phase 6 :** Architecture multi-agents (Web, Sémantique, Arbitre avec Gemini).
- **Phase 7 :** Interface graphique interactive à quatre cadrans (Dash / Plotly / Leaflet).
- **Phase 8 :** Intégration globale, validation scientifique et benchmark comparatif.

---

## Lancement de l'Application

### Dashboard Interactif à Quatre Cadrans (Recommandé)
```bash
python scripts/run_phase7_dashboard.py --port 8050
```
Accéder ensuite à l'application dans votre navigateur : `http://127.0.0.1:8050`.

### Validation et Tests
```bash
# Vérification de l'intégrité des fichiers protégés
python scripts/run_phase7_dashboard.py --check-only

# Exécution des 197 tests unitaires et d'intégration
pytest tests/
```

---

## Équipe et Encadrement

- **Projet Réalisé par :**
  - **Basma OUAARAB**
  - **Fatimaezzahrae ELHAMDIOUI**
- **Sous l'Encadrement de :**
  - **Mr BENHRA Jamal** — Enseignant-Chercheur

