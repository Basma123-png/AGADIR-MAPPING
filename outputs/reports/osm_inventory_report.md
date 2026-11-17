# RAPPORT D'EXTRACTION OSM ET CONTRÔLE SPATIAL — PHASE 1
**Projet :** AGADIR MAPPING — Last Mile TSP Optimization  
**Zone d'étude :** Talborjt & Centre-Ville, Agadir, Maroc  
**Date d'exécution :** 2026-11-16 20:24:17 UTC  
**Source :** OpenStreetMap via Overpass API (Données réelles certifiées)  
**Systèmes de coordonnées :** GPS WGS84 (EPSG:4326) & Projection locale UTM Zone 29N (EPSG:32629)

---

## 1. Périmètre Géographique et Emprise d'Étude

La zone analysée couvre le quartier historique de **Talborjt** et le **Centre-ville d'Agadir**.

| Paramètre spatial | Valeur |
| :--- | :--- |
| **Latitude Sud** | 30.415° N |
| **Latitude Nord** | 30.435° N |
| **Longitude Ouest** | -9.608° W |
| **Longitude Est** | -9.584° W |
| **Largeur (Est-Ouest)** | **2.305 km** (2304.88 m) |
| **Hauteur (Nord-Sud)** | **2.216 km** (2216.36 m) |
| **Superficie totale** | **5.108 km²** |
| **Centroïde théorique BBOX** | 30.425° N, -9.596° W |
| **Centroïde réel des POIs** | 30.422297° N, -9.596518° W |
| **Dispersion spatiale (Écart-type)** | $\sigma_X = 580.49 \text{ m}$, $\sigma_Y = 452.76 \text{ m}$ |

---

## 2. Inventaire Détaillé des Entités Extraites

- **Nombre total d'éléments bruts OSM téléchargés :** 418
- **Nombre total de destinations qualifiées et géolocalisées :** **413**
- **Densité spatiale moyenne :** 80.85 POIs/km²
- **Points avec dénomination commerciale/publique explicite :** 244 (59.1%)

### Répartition par Grandes Catégories :

| Catégorie | Nombre de points | Pourcentage | Exemples réels identifiés |
| :--- | :---: | :---: | :--- |
| **Équipement Public** | 158 | 38.3% | parking (94), school (13), fountain (11) |
| **Commerce & Magasin** | 74 | 17.9% | kiosk (15), supermarket (5), convenience (5) |
| **Restauration & Cafés** | 70 | 16.9% | restaurant (44), cafe (15), fast_food (9) |
| **Banque & Finance** | 34 | 8.2% | bank (28), atm (3), bureau_de_change (3) |
| **Santé & Pharmacie** | 33 | 8.0% | pharmacy (24), doctors (4), hospital (4) |
| **Bureaux & Tertiaire** | 27 | 6.5% | government (20), diplomatic (3), architect (1) |
| **Services & Logistique** | 12 | 2.9% | fuel (6), post_office (4), marketplace (2) |
| **Artisanat & Services** | 3 | 0.7% | shoemaker (1), electrician (1), watchmaker (1) |
| **Résidentiel & Bâtiment** | 2 | 0.5% | residential (1), retail (1) |

---

## 3. Analyse de Qualité et de Pertinence pour le TSP Last Mile

1. **Richesse et diversité :** L'extraction fournit un panel très représentatif de commerces alimentaires, restaurants, banques, pharmacies et services administratifs, idéal pour modéliser une tournée de livraison urbaine réaliste.
2. **Couverture spatiale :** Les points couvrent harmonieusement le centre historique et commerçant de Talborjt ainsi que les grandes artères du centre-ville (Avenue Hassan II, Boulevard Mohammed V, Avenue des FAR).
3. **Traçabilité stricte :** Chaque point dispose de son identifiant officiel OpenStreetMap (`osm_id`), de son type d'entité (`node` ou `way`), de ses coordonnées WGS84 précises et de ses coordonnées métriques projetées en UTM Zone 29N.
4. **Base pour la Phase 2 :** Ce vivier de 413 points réels permettra d'extraire de manière rigoureuse un échantillon équilibré de 40 points de livraison rattachés au réseau routier.

---

## 4. Fichiers et Livrables Associés

- **Données brutes :** `data/raw/agadir_talborjt_raw.json`
- **Données nettoyées (CSV) :** `data/processed/agadir_talborjt_all_pois.csv`
- **Données nettoyées (GeoJSON) :** `data/processed/agadir_talborjt_all_pois.geojson`
- **Carte interactive de contrôle :** `outputs/maps/talborjt_control_map.html`
