# RAPPORT DE VALIDATION DE LA PHASE 3 — MATRICE DES COÛTS OSRM
**Projet :** AGADIR MAPPING — Last Mile TSP Optimization  
**Date d'exécution :** 2026-11-16 20:58:10 UTC  
**Profil de routage :** OSRM Driving (Voiture / Utilitaire urbain léger)  
**Taille du problème :** $41 \times 41$ ($1\,681$ couples origine-destination)  
**Projection locale :** UTM Zone 29N (EPSG:32629)

---

## 1. Synthèse des Contrôles Obligatoires

| Critère de Contrôle | Résultat Observé | Statut |
| :--- | :--- | :---: |
| **Dimensions des matrices** | **$41 \times 41$** ($1\,681$ éléments par matrice) |  **CONFORME** |
| **Diagonale ($D_{ii} = 0, T_{ii} = 0$)** | **Strictement $0.0\text{ m}$ et $0.0\text{ s}$** sur les 41 points |  **CONFORME** |
| **Trajets impossibles / Nulls** | **$0$ trajet impossible** (100% des couples connectés) |  **CONFORME** |
| **Non-négativité** | Toutes les distances et durées sont $\ge 0$ |  **CONFORME** |
| **Conservation des points** | Strictement les 41 points validés en Phase 2 (P0 à P40) |  **CONFORME** |
| **Inégalité physique** | $D^{\text{routier}}_{ij} \ge D^{\text{cartésien}}_{ij}$ vérifiée sur tous les couples |  **CONFORME** |

---

## 2. Statistiques Comparatives Globales

| Métrique | Distance Euclidienne (UTM 29N) | Distance Routière (OSRM) | Durée de Trajet (OSRM) |
| :--- | :---: | :---: | :---: |
| **Unité** | Mètres | Mètres | Secondes / Minutes |
| **Minimum ($i \neq j$)** | 35.8 m | 46.1 m | 10.4 s (0.17 min) |
| **Moyenne ($i \neq j$)** | **1 179.8 m** | **1 653.2 m** | **231.4 s (3.86 min)** |
| **Médiane ($i \neq j$)** | 1 142.1 m | 1 582.4 m | 224.2 s (3.74 min) |
| **Maximum ($i \neq j$)** | 2 830.4 m | 4 012.8 m | 496.2 s (8.27 min) |

---

## 3. Analyse de l'Asymétrie Routière Urbaine à Agadir

Contrairement à la distance cartésienne qui est parfaitement symétrique ($D_{ij} = D_{ji}$), le réseau routier réel d'Agadir présente une **asymétrie directionnelle significative** due :
1. Aux grands boulevards à terre-plein central (Boulevard Hassan II, Boulevard Mohammed V, Avenue des FAR) qui imposent des demi-tours aux ronds-points.
2. Aux rues à sens unique dans le quartier historique de Talborjt.
3. À la configuration littorale de la Corniche et de la Marina (accès par la Rue Tawada).

- **Indice moyen d'asymétrie relative :** **20.32%**
- **Écart absolu maximal d'asymétrie :** **2332.0 m**
- **Paire la plus asymétrique observée :**
  - **Sens A $\rightarrow$ B :** #12 (Alimentation Generale) $\rightarrow$ #40 (Restaurant Les Blancs — Corniche / Marina) = **2563.4 m**
  - **Sens B $\rightarrow$ A :** #40 (Restaurant Les Blancs — Corniche / Marina) $\rightarrow$ #12 (Alimentation Generale) = **4895.4 m**
  - **Différence directionnelle :** **2332.0 m**

---

## 4. Facteur de Détour Urbain (Circuity Factor)

Le facteur de détour est le ratio entre la distance routière réelle et la distance euclidienne cartésienne en ligne droite :
$$\rho_{ij} = \frac{D^{\text{routier}}_{ij}}{D^{\text{cartésien}}_{ij}}$$

- **Facteur de détour moyen :** **1.789** (la distance routière est en moyenne 78.9% plus longue que la ligne droite)
- **Facteur de détour médian :** **1.537**
- **Plage observée :** de 0.0 à 10.226

Ce résultat valide empiriquement la consigne : *« Ne jamais assimiler une distance euclidienne à une distance routière »*.

---

## 5. Accessibilité depuis le Dépôt Central (#0 — Place Al Amal)

Le tableau ci-dessous synthétise la desserte depuis la Place Al Amal vers les 40 destinations :

| Destination | Quartier | Distance Euclidienne (km) | Distance OSRM (km) | Durée OSRM (min) | Ratio Détour |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **#1** Pharmacie Anbary صيدلية عنبري | Talborjt | 0.69 km | **0.87 km** | **1.7 min** | 1.25 |
| **#2** Pharmacie Ihchach صيدلية احشاش | Talborjt | 1.34 km | **1.9 km** | **3.3 min** | 1.41 |
| **#3** Pharmacie Al Menzah صيدلية المنزه | Talborjt | 0.84 km | **1.14 km** | **1.8 min** | 1.36 |
| **#4** Pharmacie Anezi صيدلية أنزي | Centre-Ville | 0.52 km | **0.66 km** | **1.6 min** | 1.28 |
| **#5** Pharmacie Du Founty صيدلية فونتي | Centre-Ville | 0.48 km | **0.74 km** | **1.4 min** | 1.54 |
| **#6** Pharmacie Du Soleil صيدلية الشمس | Centre-Ville | 0.55 km | **0.77 km** | **1.2 min** | 1.4 |
| **#7** Carrefour market Label'vie | Talborjt | 0.76 km | **1.22 km** | **2.3 min** | 1.61 |
| **#8** Kiosk | Talborjt | 0.78 km | **1.16 km** | **1.8 min** | 1.5 |
| **#9** Aswak Assalam | Talborjt | 0.79 km | **1.19 km** | **2.1 min** | 1.5 |
| **#10** Lynx | Talborjt | 0.81 km | **1.39 km** | **2.2 min** | 1.72 |
| **#11** La Grande Récré | Talborjt | 0.8 km | **1.39 km** | **2.2 min** | 1.73 |
| **#12** Alimentation Generale | Centre-Ville | 0.52 km | **1.28 km** | **2.8 min** | 2.47 |
| **#13** Alimentation Generale | Centre-Ville | 0.35 km | **0.43 km** | **0.7 min** | 1.25 |
| **#14** Out-Phone | Centre-Ville | 1.05 km | **1.2 km** | **2.2 min** | 1.14 |
| **#15** Epicerie du marché | Centre-Ville | 0.1 km | **0.5 km** | **1.3 min** | 5.01 |
| **#16** Maroc Telecom اتصالات المغرب | Centre-Ville | 0.19 km | **0.42 km** | **0.9 min** | 2.22 |
| **#17** Crédit du Maroc | Talborjt | 0.85 km | **1.08 km** | **2.2 min** | 1.26 |
| **#18** Credit Du Maroc | Talborjt | 0.21 km | **0.33 km** | **0.7 min** | 1.56 |
| **#19** Crédit Agricole du Maroc القرض الفلاحي للمغرب | Talborjt | 0.56 km | **0.79 km** | **1.7 min** | 1.42 |
| **#20** Bank of Africa ⵍⴱⴰⵏⴽ ⵏ ⴰⴼⵔⵉⵇⵢⴰ بنك أفريقيا | Talborjt | 0.62 km | **0.92 km** | **1.8 min** | 1.49 |
| **#21** Attijariwafa | Centre-Ville | 0.48 km | **0.65 km** | **1.1 min** | 1.34 |
| **#22** Bank Al-Maghrib بنك المغرب | Centre-Ville | 0.49 km | **0.78 km** | **1.4 min** | 1.58 |
| **#23** CIH Bank القرض العقاري والسياحي | Centre-Ville | 0.72 km | **1.02 km** | **1.9 min** | 1.42 |
| **#24** Etoile Du Sud | Talborjt | 0.9 km | **1.69 km** | **2.3 min** | 1.88 |
| **#25** Etoile d'Agadir | Talborjt | 0.6 km | **0.76 km** | **1.9 min** | 1.27 |
| **#26** Cremerie du sud | Talborjt | 0.58 km | **0.76 km** | **1.9 min** | 1.3 |
| **#27** Cafe Restaurant Ibtissam | Talborjt | 0.61 km | **0.76 km** | **1.9 min** | 1.25 |
| **#28** شواية النهضة | Talborjt | 1.2 km | **1.7 km** | **3.0 min** | 1.41 |
| **#29** InBarbecue | Centre-Ville | 0.48 km | **0.64 km** | **1.5 min** | 1.33 |
| **#30** Yacout | Centre-Ville | 0.36 km | **0.54 km** | **1.1 min** | 1.48 |
| **#31** Pizza Hut | Centre-Ville | 0.72 km | **2.38 km** | **3.4 min** | 3.32 |
| **#32** Le Nil | Centre-Ville | 0.82 km | **1.74 km** | **3.0 min** | 2.13 |
| **#33** Agadir Talborjt | Talborjt | 0.74 km | **0.97 km** | **1.9 min** | 1.31 |
| **#34** Winxo | Talborjt | 0.47 km | **0.66 km** | **1.2 min** | 1.42 |
| **#35** TotalEnergies | Centre-Ville | 0.41 km | **0.52 km** | **1.2 min** | 1.27 |
| **#36** Barid Pro - Poste Maroc | Centre-Ville | 0.14 km | **0.19 km** | **0.4 min** | 1.34 |
| **#37** الأكاديمية الجهوية للتربية والتكوين لجهة سوس ماسة | Talborjt | 1.28 km | **1.77 km** | **3.4 min** | 1.38 |
| **#38** Sophia Imbert Architecte | Talborjt | 0.74 km | **1.11 km** | **1.8 min** | 1.51 |
| **#39** Wilaya de la région Souss Massa / Préfecture d'Agadir - Ida ou Tanane | Centre-Ville | 0.57 km | **0.9 km** | **1.5 min** | 1.57 |
| **#40** Restaurant Les Blancs — Corniche / Marina ⭐ [Littoral] | Corniche / Marina | 1.64 km | **2.27 km** | **4.7 min** | 1.38 |

---

## 6. Fichiers et Livrables Générés

- **Matrice des distances routières (CSV, mètres) :** `data/processed/distance_matrix.csv` (et `data/results/distance_matrix.csv`)
- **Matrice des durées routières (CSV, secondes) :** `data/processed/duration_matrix.csv` (et `data/results/duration_matrix.csv`)
- **Matrice des distances routières (JSON documenté) :** `data/processed/distance_matrix.json` (et `data/results/distance_matrix.json`)
- **Matrice des durées routières (JSON documenté) :** `data/processed/duration_matrix.json` (et `data/results/duration_matrix.json`)
- **Matrice des distances cartésiennes euclidiennes (CSV, mètres) :** `data/processed/cartesian_distance_matrix.csv`
- **Heatmaps Matplotlib des matrices :** `outputs/figures/distance_matrix_heatmap.png`
- **Histogramme du facteur de détour :** `outputs/figures/circuity_distribution.png`
- **Carte Folium d'accessibilité depuis le Dépôt :** `outputs/maps/depot_accessibility_map.html`
