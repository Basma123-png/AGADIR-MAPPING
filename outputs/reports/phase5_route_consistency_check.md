# RAPPORT OFFICIEL DE VÉRIFICATION DE COHÉRENCE — PHASE 5
## Audit de Concordance des Tournées ATSP et Recalcul Indépendant des 41 Arcs OSRM
**Projet :** AGADIR MAPPING — Last Mile TSP Optimization  
**Date d'audit :** 16/11/2026  
**Auteur :** Antigravity (Google DeepMind Team)  
**Document de Référence :** `phase5_route_consistency_check.md`  

---

## 1. Contexte et Objectifs de la Vérification

Ce contrôle fait suite à la validation algorithmique, statistique et géographique de la Phase 5. L'utilisateur a demandé d'effectuer un audit strict de concordance entre les différentes mentions de la tournée finale :
1. Comparer rigoureusement la tournée figurant dans `phase5_validation_report.md`, celle de `phase5_final_audit.md` et celle enregistrée dans `tsp_optimized_route.json`.
2. Identifier formellement la tournée officielle retenue comme résultat définitif.
3. Recalculer de façon indépendante les 41 arcs orientés à partir de la matrice originale `data/processed/distance_matrix.csv`.
4. Vérifier la conformité de l'ensemble des contraintes ATSP (départ et retour au dépôt #0, visite unique des 40 destinations, présence du point littoral #40, absence de doublons).
5. Confirmer l'intégrité absolue des fichiers de données.

---

## 2. Comparaison des Tournées dans les Fichiers du Projet

Une comparaison bit-à-bit et structurelle a été menée sur tous les fichiers générés en Phase 5 :

| Fichier Source | Emplacement Physique | Séquence Exacte Enregistrée | Longueur | Distance Associée |
| :--- | :--- | :--- | :---: | :---: |
| **`tsp_optimized_route.json`** | `data/results/` | `[0, 36, 13, 30, 21, 6, 33, 27, 25, 26, 7, 9, 38, 3, 10, 11, 17, 28, 37, 2, 14, 12, 5, 35, 16, 22, 39, 8, 1, 19, 20, 32, 40, 24, 29, 4, 23, 31, 15, 18, 34, 0]` | 42 arrêts | **18 933,1 m** |
| **`optuna_best_params.json`** | `data/results/` | `[0, 36, 13, 30, 21, 6, 33, 27, 25, 26, 7, 9, 38, 3, 10, 11, 17, 28, 37, 2, 14, 12, 5, 35, 16, 22, 39, 8, 1, 19, 20, 32, 40, 24, 29, 4, 23, 31, 15, 18, 34, 0]` | 42 arrêts | **18 933,1 m** |
| **`phase5_validation_report.md`** | `outputs/reports/` | `[0, 36, 13, 30, 21, 6, 33, 27, 25, 26, 7, 9, 38, 3, 10, 11, 17, 28, 37, 2, 14, 12, 5, 35, 16, 22, 39, 8, 1, 19, 20, 32, 40, 24, 29, 4, 23, 31, 15, 18, 34, 0]` | 42 arrêts | **18 933,1 m** |
| **`phase5_final_audit.md`** | `outputs/reports/` | `[0, 36, 13, 30, 21, 6, 33, 27, 25, 26, 7, 9, 38, 3, 10, 11, 17, 28, 37, 2, 14, 12, 5, 35, 16, 22, 39, 8, 1, 19, 20, 32, 40, 24, 29, 4, 23, 31, 15, 18, 34, 0]` | 42 arrêts | **18 933,1 m** |
| **`tsp_optimized_route_map.html`** | `outputs/maps/` | `[0, 36, 13, 30, 21, 6, 33, 27, 25, 26, 7, 9, 38, 3, 10, 11, 17, 28, 37, 2, 14, 12, 5, 35, 16, 22, 39, 8, 1, 19, 20, 32, 40, 24, 29, 4, 23, 31, 15, 18, 34, 0]` | 42 arrêts | **18 933,1 m** |

### Explication de l'Éventuelle Divergence dans le Message de Chat Précédent :
Dans le corps de la réponse textuelle précédente, au niveau de la section descriptive *« PARTIE 5 — Séquence de la Tournée Optimale Découverte »*, une séquence textuelle erronée a été affichée :  
`[0, 36, 35, 5, 13, 30, 21, 6, 33, 27, 25, 26, 7, 9, 38, 3, 10, 11, 17, 28, 37, 2, 14, 12, 15, 18, 16, 22, 39, 8, 1, 40, 19, 20, 24, 29, 4, 23, 31, 32, 34, 0]`

- Cette séquence textuelle résultait d'une **erreur de copier-coller manuelle** lors de la rédaction du message de chat : elle reprenait l'ordre de la Phase 4 en y insérant maladroitement le point #40. Calculée sur la matrice, cette séquence erronée donnait $22\,094,7\text{ m}$.
- En revanche, **aucun fichier sur le disque n'a jamais contenu cette séquence erronée**.
- Le fichier officiel [`data/results/tsp_optimized_route.json`](file:///Users/ouaarab/Documents/AGADIR%20MAPPING/data/results/tsp_optimized_route.json), la base SQLite [`optuna_study.db`](file:///Users/ouaarab/Documents/AGADIR%20MAPPING/data/results/optuna_study.db), la carte interactive [`tsp_optimized_route_map.html`](file:///Users/ouaarab/Documents/AGADIR%20MAPPING/outputs/maps/tsp_optimized_route_map.html), ainsi que les rapports [`phase5_validation_report.md`](file:///Users/ouaarab/Documents/AGADIR%20MAPPING/outputs/reports/phase5_validation_report.md) et [`phase5_final_audit.md`](file:///Users/ouaarab/Documents/AGADIR%20MAPPING/outputs/reports/phase5_final_audit.md) contiennent **strictement et à 100 % la même tournée officielle de 18 933,1 m**.

---

## 3. Tournée Officielle Retenue

La tournée officielle définitive de la Phase 5 est :
```text
[0, 36, 13, 30, 21, 6, 33, 27, 25, 26, 7, 9, 38, 3, 10, 11, 17, 28, 37, 2, 14, 12, 5, 35, 16, 22, 39, 8, 1, 19, 20, 32, 40, 24, 29, 4, 23, 31, 15, 18, 34, 0]
```

- **Départ :** Point #0 — *Place Al Amal* (Dépôt Central)
- **40 livraisons intermédiaires :** Points #1 à #40 visités exactement une fois.
- **Destination Littorale (#40 — *Restaurant Les Blancs*) :** Étape **#32** (directement reliée entre #32 *Le Nil* et #24 *Etoile Du Sud*).
- **Arrivée :** Point #0 — *Place Al Amal* (Dépôt Central).
- **Nombre total d'arrêts :** 42 étapes.

---

## 4. Recalcul Indépendant des 41 Arcs Orientés sur `distance_matrix.csv`

Le recalcul indépendant des 41 arcs orientés a été exécuté sur la matrice originale [`data/processed/distance_matrix.csv`](file:///Users/ouaarab/Documents/AGADIR%20MAPPING/data/processed/distance_matrix.csv) sans utiliser aucune variable en cache :

| N° Arc | Nœud Début | Nœud Fin | Établissement Début | Établissement Fin | Quartier Fin | Distance OSRM (m) | Distance Cumulée (m) |
| :---: | :---: | :---: | :--- | :--- | :--- | :---: | :---: |
| **1** | #0 | #36 | Dépôt Central — Place Al Amal | Barid Pro - Poste Maroc | Centre-Ville | 190,5 m | 190,5 m |
| **2** | #36 | #13 | Barid Pro - Poste Maroc | Alimentation Generale | Talborjt | 405,9 m | 596,4 m |
| **3** | #13 | #30 | Alimentation Generale | Yacout | Talborjt | 107,7 m | 704,1 m |
| **4** | #30 | #21 | Yacout | Attijariwafa bank | Talborjt | 184,3 m | 888,4 m |
| **5** | #21 | #6 | Attijariwafa bank | Pharmacie Du Soleil | Talborjt | 151,4 m | 1 039,8 m |
| **6** | #6 | #33 | Pharmacie Du Soleil | Agadir Talborjt | Talborjt | 390,0 m | 1 429,8 m |
| **7** | #33 | #27 | Agadir Talborjt | Cafe Restaurant Ibn Toumart | Talborjt | 291,9 m | 1 721,7 m |
| **8** | #27 | #25 | Cafe Restaurant Ibn Toumart | Etoile d'Agadir | Talborjt | 0,9 m | 1 722,6 m |
| **9** | #25 | #26 | Etoile d'Agadir | Cremerie du sud | Talborjt | 0,0 m | 1 722,6 m |
| **10** | #26 | #7 | Cremerie du sud | Carrefour market Luccus | Talborjt | 261,2 m | 1 983,8 m |
| **11** | #7 | #9 | Carrefour market Luccus | Aswak Assalam | Talborjt | 36,4 m | 2 020,2 m |
| **12** | #9 | #38 | Aswak Assalam | Sophia Imbert Architecte | Talborjt | 125,3 m | 2 145,5 m |
| **13** | #38 | #3 | Sophia Imbert Architecte | Pharmacie Al Menzah | Talborjt | 123,1 m | 2 268,6 m |
| **14** | #3 | #10 | Pharmacie Al Menzah | Lynx | Talborjt | 244,8 m | 2 513,4 m |
| **15** | #10 | #11 | Lynx | La Grande Récré | Talborjt | 3,7 m | 2 517,1 m |
| **16** | #11 | #17 | La Grande Récré | Crédit du Maroc (Talborjt) | Talborjt | 346,7 m | 2 863,8 m |
| **17** | #17 | #28 | Crédit du Maroc (Talborjt) | شواية النهضة | Talborjt | 906,3 m | 3 770,1 m |
| **18** | #28 | #37 | شواية النهضة | الأكاديمية الجهوية للتربية | Talborjt | 67,4 m | 3 837,5 m |
| **19** | #37 | #2 | الأكاديمية الجهوية للتربية | Pharmacie Ihchach | Talborjt | 586,8 m | 4 424,3 m |
| **20** | #2 | #14 | Pharmacie Ihchach | Out-Phone | Centre-Ville | 1 292,3 m | 5 716,6 m |
| **21** | #14 | #12 | Out-Phone | Alimentation Generale | Centre-Ville | 1 159,4 m | 6 876,0 m |
| **22** | #12 | #5 | Alimentation Generale | Pharmacie Du Founti | Centre-Ville | 203,4 m | 7 079,4 m |
| **23** | #5 | #35 | Pharmacie Du Founti | TotalEnergies | Centre-Ville | 102,4 m | 7 181,8 m |
| **24** | #35 | #16 | TotalEnergies | Maroc Telecom | Centre-Ville | 564,4 m | 7 746,2 m |
| **25** | #16 | #22 | Maroc Telecom | Bank Al-Maghrib | Centre-Ville | 388,4 m | 8 134,6 m |
| **26** | #22 | #39 | Bank Al-Maghrib | Wilaya Souss Massa | Centre-Ville | 121,0 m | 8 255,6 m |
| **27** | #39 | #8 | Wilaya Souss Massa | Kiosk | Talborjt | 263,1 m | 8 518,7 m |
| **28** | #8 | #1 | Kiosk | Pharmacie Anbary | Talborjt | 304,0 m | 8 822,7 m |
| **29** | #1 | #19 | Pharmacie Anbary | Crédit Agricole du Maroc | Talborjt | 144,6 m | 8 967,3 m |
| **30** | #19 | #20 | Crédit Agricole du Maroc | Bank of Africa | Talborjt | 333,0 m | 9 300,3 m |
| **31** | #20 | #32 | Bank of Africa | Le Nil | Centre-Ville | 873,2 m | 10 173,5 m |
| **32** | #32 | #40 | Le Nil | **Restaurant Les Blancs [LITTORAL]** | **Corniche / Marina** | **1 575,5 m** | **11 749,0 m** |
| **33** | #40 | #24 | **Restaurant Les Blancs [LITTORAL]** | Etoile Du Sud | Talborjt | 1 783,3 m | 13 532,3 m |
| **34** | #24 | #29 | Etoile Du Sud | InBarbecue | Centre-Ville | 962,9 m | 14 495,2 m |
| **35** | #29 | #4 | InBarbecue | Pharmacie Anezi | Centre-Ville | 21,1 m | 14 516,3 m |
| **36** | #4 | #23 | Pharmacie Anezi | CIH Bank | Centre-Ville | 377,8 m | 14 894,1 m |
| **37** | #23 | #31 | CIH Bank | Pizza Hut | Centre-Ville | 1 517,8 m | 16 411,9 m |
| **38** | #31 | #15 | Pizza Hut | Epicerie du marché | Centre-Ville | 1 185,7 m | 17 597,6 m |
| **39** | #15 | #18 | Epicerie du marché | Credit Du Maroc (Centre-Ville) | Centre-Ville | 230,5 m | 17 828,1 m |
| **40** | #18 | #34 | Credit Du Maroc (Centre-Ville) | Winxo | Talborjt | 476,9 m | 18 305,0 m |
| **41** | #34 | #0 | Winxo | Dépôt Central — Place Al Amal | Centre-Ville | 628,1 m | **18 933,1 m** |

### Résultats du Recalcul Indépendant :
- **Somme mathématique exacte des 41 arcs :** **`18 933,1000 m`** (`18,9331 km`).
- **Distance enregistrée en métadonnées :** **`18 933,1000 m`**.
- **Écart absolu :** **`0,0000 m`** (précision au centième de millimètre).
- **Gain confirmé vs Phase 4 (21 014,3 m) :** **`-2 081,2 m`** (réduction de **`-9,90 %`**).

---

## 5. Vérification Stricte des Contraintes ATSP

1. **Point de départ et de retour :**
   - L'étape #0 est le Dépôt Central #0 (Place Al Amal, `30.421500, -9.598500`).
   - L'étape #41 est le retour au Dépôt Central #0.
   - La boucle fermée est strictement respectée.

2. **Couverture des destinations intermédiaires :**
   - Nombre de points intermédiaires : exactement **40**.
   - Ensemble des nœuds visités : $\bigcup_{k=1}^{40} \{\pi_k\} = \{1, 2, 3, \dots, 40\}$.
   - **Doublons :** 0.
   - **Omissions :** 0.

3. **Intégration du point littoral #40 :**
   - Le point #40 (*Restaurant Les Blancs*, Corniche / Marina) est visité à l'étape #32.
   - Arc entrant : #32 (*Le Nil*) $\to$ #40 : `1 575,5 m`.
   - Arc sortant : #40 $\to$ #24 (*Etoile Du Sud*) : `1 783,3 m`.
   - Cet ordonnancement assure une liaison littorale fluide sans aller-retour parasite vers le centre-ville.

---

## 6. Confirmation de l'Intégrité des Fichiers Sources

Conformément aux restrictions impératives :
- **Optuna n'a pas été relancé.**
- **L'algorithme génétique n'a pas été relancé.**
- **Les hyperparamètres optimaux n'ont pas été modifiés.**
- **La matrice `distance_matrix.csv` (41x41) n'a subi aucune modification.**
- **Le fichier `delivery_points_40.csv` et son GeoJSON n'ont subi aucune modification.**
- **La tournée officielle enregistrée n'a pas été remplacée.**
- **Aucune tâche de la Phase 6 n'a été commencée.**

---

## 7. Conclusion

L'audit de cohérence confirme que tous les artefacts de la Phase 5 (`tsp_optimized_route.json`, `optuna_best_params.json`, `tsp_optimized_route_map.html`, `phase5_validation_report.md` et `phase5_final_audit.md`) sont en **parfaite concordance mutuelle** et reposent sur la même tournée officielle de **18 933,1 m**.

Le travail est suspendu dans l'attente de votre autorisation explicite pour entamer la **PHASE 6**.
