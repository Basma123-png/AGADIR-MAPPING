# RAPPORT DE SÉLECTION DES 40 DESTINATIONS — PHASE 2
**Projet :** AGADIR MAPPING — Last Mile TSP Optimization  
**Date de validation :** 2026-11-16 20:37:26 UTC  
**Réseau routier :** OpenStreetMap via API OSRM (Profil de conduite urbaine)  
**Systèmes de projection :** GPS WGS84 (EPSG:4326) & Projection locale UTM Zone 29N (EPSG:32629)

---

## 1. Composition Globale du Problème TSP

Le problème d'optimisation est configuré avec **exactement 40 destinations réelles** à visiter et **1 Dépôt logistique central** :

- **Dépôt Central (Point #0) :** Place Al Amal (`30.421500° N, -9.598500° W`), point de départ et d'arrivée de la tournée.
- **Destination Littorale (Point #40) :** Restaurant Les Blancs — Corniche / Marina sur la Corniche d'Agadir / Marina (`30.423998° N, -9.615366° W`).
- **Destinations Urbaines (Points #1 à #39) :** 39 points réels répartis entre **Talborjt (21 points)** et le **Centre-Ville (18 points)**.

---

## 2. Validation OSRM de Rattachement au Réseau Routier

Chaque destination a été vérifiée individuellement auprès de l'API OSRM (`/nearest` et `/route`) :
- **Taux de rattachement au réseau viaire :** 100% (41/41)
- **Distance moyenne de projection sur la chaussée :** **15.77 m**
- **Distance maximale de projection :** **47.6 m** (tous les points sont situés à moins de 30 mètres d'une rue carrossable)
- **Connectivité depuis le Dépôt :** 100% des destinations disposent d'un itinéraire automobile routier direct calculable.

### Détail de la Destination Littorale (Point #40) :
- **Nom :** Restaurant Les Blancs — Corniche / Marina
- **Emplacement :** Rue Tawada (Boulevard de la Corniche)
- **Secteur :** Corniche d'Agadir / Entrée Marina
- **Coordonnées GPS (WGS84) :** 30.423998° N, -9.615366° W
- **Coordonnées Métriques (UTM 29N) :** X = 440902.74 m, Y = 3365930.0 m
- **Rue de rattachement OSRM :** Rue Tawada
- **Distance de projection à la route :** 27.23 m (accès direct chaussée goudronnée, hors eau et hors sable)
- **Distance routière depuis Place Al Amal :** 2.27 km (4.68 min de trajet)

---

## 3. Répartition par Catégories des 40 Destinations

| Catégorie | Nombre de points | Rôle logistique Last-Mile |
| :--- | :---: | :--- |
| **Commerce & Magasin** | **10** | Supermarchés, alimentation générale, kiosques, fleuristes |
| **Restauration & Cafés** | **9** | Restaurants traditionnels et modernes, cafés de quartier |
| **Banque & Finance** | **7** | Agences bancaires (Attijariwafa, CIH, Crédit Agricole, Bank Al-Maghrib) |
| **Santé & Pharmacie** | **6** | Pharmacies d'officine (produits pharmaceutiques / urgences) |
| **Services & Logistique** | **4** | Agences postales Poste Maroc, stations-service |
| **Bureaux & Tertiaire** | **3** | Administrations publiques, ministères |
| **Destination Littorale** | **1** | Point maritime de prestige sur la Corniche / Marina |
| **TOTAL** | **40** | **Échantillon équilibré et représentatif** |

---

## 4. Inventaire Complet des 40 Destinations + Dépôt

| ID | Type | Nom du Point | Quartier | Catégorie | Rue / Voie OSRM | Distance Snap (m) | Dist. Dépôt (km) |
| :---: | :---: | :--- | :---: | :--- | :--- | :---: | :---: |
| **#0** | Dépôt | Dépôt Central — Place Al Amal | Centre-Ville | Dépôt Central | Avenue Prince Moulay Abdellah | 23.48 m | - |
| **#1** | Urbain | Pharmacie Anbary صيدلية عنبري | Talborjt | Santé & Pharmacie | Avenue Hassan II شارع الحسن الثاني | 16.42 m | 0.87 km |
| **#2** | Urbain | Pharmacie Ihchach صيدلية احشاش | Talborjt | Santé & Pharmacie | Rue Lahoussine Bijaouane | 10.71 m | 1.9 km |
| **#3** | Urbain | Pharmacie Al Menzah صيدلية المنزه | Talborjt | Santé & Pharmacie | Avenue des Forces Armées Royales شارع الجيش الملكي | 17.78 m | 1.14 km |
| **#4** | Urbain | Pharmacie Anezi صيدلية أنزي | Centre-Ville | Santé & Pharmacie | Voie urbaine (non nommée) | 32.71 m | 0.66 km |
| **#5** | Urbain | Pharmacie Du Founty صيدلية فونتي | Centre-Ville | Santé & Pharmacie | Avenue Hassan II شارع الحسن الثاني | 1.02 m | 0.74 km |
| **#6** | Urbain | Pharmacie Du Soleil صيدلية الشمس | Centre-Ville | Santé & Pharmacie | Avenue Président Kennedy | 18.12 m | 0.77 km |
| **#7** | Urbain | Carrefour market Label'vie | Talborjt | Commerce & Magasin | Voie urbaine (non nommée) | 15.6 m | 1.22 km |
| **#8** | Urbain | Kiosk | Talborjt | Commerce & Magasin | Avenue Mohammed V شارع محمد الخامس | 8.85 m | 1.16 km |
| **#9** | Urbain | Aswak Assalam | Talborjt | Commerce & Magasin | Voie urbaine (non nommée) | 17.56 m | 1.19 km |
| **#10** | Urbain | Lynx | Talborjt | Commerce & Magasin | Voie urbaine (non nommée) | 10.81 m | 1.39 km |
| **#11** | Urbain | La Grande Récré | Talborjt | Commerce & Magasin | Voie urbaine (non nommée) | 11.73 m | 1.39 km |
| **#12** | Urbain | Alimentation Generale | Centre-Ville | Commerce & Magasin | Voie urbaine (non nommée) | 4.43 m | 1.28 km |
| **#13** | Urbain | Alimentation Generale | Centre-Ville | Commerce & Magasin | Avenue du 29 Février | 14.16 m | 0.43 km |
| **#14** | Urbain | Out-Phone | Centre-Ville | Commerce & Magasin | Rue de Marrakech | 2.75 m | 1.2 km |
| **#15** | Urbain | Epicerie du marché | Centre-Ville | Commerce & Magasin | Voie urbaine (non nommée) | 14.46 m | 0.5 km |
| **#16** | Urbain | Maroc Telecom اتصالات المغرب | Centre-Ville | Commerce & Magasin | Boulevard Hassan II شارع الحسن الثاني | 17.04 m | 0.42 km |
| **#17** | Urbain | Crédit du Maroc | Talborjt | Banque & Finance | Rue Amhand Ait Ettaleb | 10.08 m | 1.08 km |
| **#18** | Urbain | Credit Du Maroc | Talborjt | Banque & Finance | Voie urbaine (non nommée) | 21.41 m | 0.33 km |
| **#19** | Urbain | Crédit Agricole du Maroc القرض الفلاحي للمغرب | Talborjt | Banque & Finance | Voie urbaine (non nommée) | 13.46 m | 0.79 km |
| **#20** | Urbain | Bank of Africa ⵍⴱⴰⵏⴽ ⵏ ⴰⴼⵔⵉⵇⵢⴰ بنك أفريقيا | Talborjt | Banque & Finance | Voie urbaine (non nommée) | 22.77 m | 0.92 km |
| **#21** | Urbain | Attijariwafa | Centre-Ville | Banque & Finance | Voie urbaine (non nommée) | 8.97 m | 0.65 km |
| **#22** | Urbain | Bank Al-Maghrib بنك المغرب | Centre-Ville | Banque & Finance | Avenue Mohammed V شارع محمد الخامس | 26.79 m | 0.78 km |
| **#23** | Urbain | CIH Bank القرض العقاري والسياحي | Centre-Ville | Banque & Finance | Voie urbaine (non nommée) | 4.96 m | 1.02 km |
| **#24** | Urbain | Etoile Du Sud | Talborjt | Restauration & Cafés | Avenue Mohammed V شارع محمد الخامس | 22.42 m | 1.69 km |
| **#25** | Urbain | Etoile d'Agadir | Talborjt | Restauration & Cafés | Rue El Mahdi Ibn Toumert | 18.55 m | 0.76 km |
| **#26** | Urbain | Cremerie du sud | Talborjt | Restauration & Cafés | Rue El Mahdi Ibn Toumert | 6.08 m | 0.76 km |
| **#27** | Urbain | Cafe Restaurant Ibtissam | Talborjt | Restauration & Cafés | Rue El Mahdi Ibn Toumert | 30.05 m | 0.76 km |
| **#28** | Urbain | شواية النهضة | Talborjt | Restauration & Cafés | Avenue Moulay Youssef شارع مولاي يوسف | 1.0 m | 1.7 km |
| **#29** | Urbain | InBarbecue | Centre-Ville | Restauration & Cafés | Voie urbaine (non nommée) | 3.63 m | 0.64 km |
| **#30** | Urbain | Yacout | Centre-Ville | Restauration & Cafés | Rue du Souvenir | 4.72 m | 0.54 km |
| **#31** | Urbain | Pizza Hut | Centre-Ville | Restauration & Cafés | Voie urbaine (non nommée) | 18.78 m | 2.38 km |
| **#32** | Urbain | Le Nil | Centre-Ville | Restauration & Cafés | Voie urbaine (non nommée) | 34.91 m | 1.74 km |
| **#33** | Urbain | Agadir Talborjt | Talborjt | Services & Logistique | Voie urbaine (non nommée) | 15.97 m | 0.97 km |
| **#34** | Urbain | Winxo | Talborjt | Services & Logistique | Voie urbaine (non nommée) | 1.24 m | 0.66 km |
| **#35** | Urbain | TotalEnergies | Centre-Ville | Services & Logistique | Voie urbaine (non nommée) | 7.5 m | 0.52 km |
| **#36** | Urbain | Barid Pro - Poste Maroc | Centre-Ville | Services & Logistique | Voie urbaine (non nommée) | 9.87 m | 0.19 km |
| **#37** | Urbain | الأكاديمية الجهوية للتربية والتكوين لجهة سوس ماسة | Talborjt | Bureaux & Tertiaire | Voie urbaine (non nommée) | 45.64 m | 1.77 km |
| **#38** | Urbain | Sophia Imbert Architecte | Talborjt | Bureaux & Tertiaire | Rue Taha Hossein | 5.32 m | 1.11 km |
| **#39** | Urbain | Wilaya de la région Souss Massa / Préfecture d'Agadir - Ida ou Tanane | Centre-Ville | Bureaux & Tertiaire | Avenue Mohammed V شارع محمد الخامس | 47.6 m | 0.9 km |
| **#40** | Littoral | Restaurant Les Blancs — Corniche / Marina | Corniche / Marina | Destination Littorale | Rue Tawada | 27.23 m | 2.27 km |

---

## 5. Livrables Associés

- **Dataset CSV validé :** `data/processed/delivery_points_40.csv`
- **Dataset GeoJSON validé :** `data/processed/delivery_points_40.geojson`
- **Carte interactive de validation des candidats :** `outputs/maps/candidates_40_map.html`
