"""
AGADIR MAPPING — Configuration globale et paramètres spatiaux.

Ce module centralise :
- L'emprise géographique de référence (Bounding Box pour Talborjt et Centre-ville d'Agadir)
- Les systèmes de projection (WGS84 EPSG:4326 et UTM Zone 29N EPSG:32629)
- Les URLs et endpoints des services externes (Overpass API, OSRM, Gemini)
- Les chemins d'accès aux répertoires de données et résultats
- Les paramètres de l'algorithme génétique et d'optimisation
"""

import os
from pathlib import Path
from typing import Dict, Any, List

# ------------------------------------------------------------------------------
# 1. Chemins du projet
# ------------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
RESULTS_DATA_DIR = DATA_DIR / "results"

OUTPUTS_DIR = BASE_DIR / "outputs"
MAPS_DIR = OUTPUTS_DIR / "maps"
FIGURES_DIR = OUTPUTS_DIR / "figures"
REPORTS_DIR = OUTPUTS_DIR / "reports"

# Création automatique des répertoires requis
for d in [RAW_DATA_DIR, PROCESSED_DATA_DIR, RESULTS_DATA_DIR, MAPS_DIR, FIGURES_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------------------
# 2. Systèmes de Coordonnées de Référence (CRS)
# ------------------------------------------------------------------------------
GPS_CRS = "EPSG:4326"       # Coordonnées géographiques WGS84 (Lat/Lon)
METRIC_CRS = "EPSG:32629"   # UTM Zone 29N adapté à Agadir (Mètres)

# ------------------------------------------------------------------------------
# 3. Zone Géographique : Talborjt & Centre-Ville d'Agadir
# ------------------------------------------------------------------------------
# Bounding Box d'étude élargie (South, West, North, East)
# Englobe Talborjt, le Centre-ville et la Corniche / Marina d'Agadir à l'Ouest.
AGADIR_BBOX: Dict[str, float] = {
    "south": 30.4150,  # Limite sud (Avenue Hassan II / Bd Mohammed V)
    "west": -9.6180,   # Limite ouest élargie (Corniche d'Agadir, Port de Plaisance & Marina)
    "north": 30.4350,  # Limite nord (Nouveau Talborjt / piémont Casbah Oufella)
    "east": -9.5840,   # Limite est (Avenue Moulay Abdellah / Cité Suisse)
}

# Coordonnées du Dépôt par défaut (Place Al Amal / Centre logistique urbain)
DEFAULT_DEPOT_GPS = {
    "name": "Dépôt Central — Place Al Amal",
    "latitude": 30.4215,
    "longitude": -9.5985,
    "category": "Dépôt Logistique",
}

# Destination littorale obligatoire sur la Corniche / Marina d'Agadir
COASTAL_DESTINATION_GPS = {
    "name": "Restaurant Les Blancs — Corniche / Marina",
    "latitude": 30.423998,
    "longitude": -9.615366,
    "osm_id": 5525615990,
    "osm_type": "node",
    "category": "Destination Littorale",
    "subcategory": "restaurant_corniche",
    "street": "Rue Tawada (Boulevard de la Corniche)",
}

# ------------------------------------------------------------------------------
# 4. Endpoints API et Réseau
# ------------------------------------------------------------------------------
OVERPASS_ENDPOINTS: List[str] = [
    os.getenv("OVERPASS_ENDPOINT", "https://overpass.openstreetmap.fr/api/interpreter"),
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

# Service OSRM de routage routier (par défaut serveur public OpenStreetMap)
OSRM_BASE_URL = os.getenv("OSRM_BASE_URL", "https://router.project-osrm.org")

# Timeout réseau en secondes
NETWORK_TIMEOUT = 30

# ------------------------------------------------------------------------------
# 5. Constantes TSP et Algorithme Génétique
# ------------------------------------------------------------------------------
TARGET_DELIVERY_POINTS = 40

GA_DEFAULT_PARAMS: Dict[str, Any] = {
    "population_size": 50,
    "mutation_rate": 0.05,
    "crossover_rate": 0.8,
    "selection_method": "tournament",  # 'roulette' ou 'tournament'
    "tournament_size": 3,
    "crossover_operator": "ox",         # Order Crossover (OX) ou PMX
    "mutation_operator": "inversion",   # 2-opt inversion ou swap
    "elite_size": 2,
    "max_generations": 500,
    "seed": 42,
}
