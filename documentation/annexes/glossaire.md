# AGADIR MAPPING — GLOSSAIRE SCIENTIFIQUE ET TECHNIQUE
## Définitions Terminologiques Bilingues (Français / Anglais)

**Projet :** AGADIR MAPPING — Système Intelligent d'Optimisation Logistique Urbaine  
**Auteurs :** Basma OUAARAB & Fatimaezzahrae ELHAMDIOUI  
**Encadrant :** Mr BENHRA Jamal  
**Date :** 17 Novembre 2026  

---

### A

- **API REST (Representational State Transfer API) :**  
  Interface de communication logicielle reposant sur le protocole HTTP. Dans AGADIR MAPPING, l'API REST exposée par le serveur HTTP de la Phase 7 fonctionne en lecture seule (`GET`) pour protéger l'intégrité des 4 fichiers certifiés contre toute altération.
- **Asymétrie Topologique / Asymétrie Routière :**  
  Propriété d'un réseau viaire où la distance et/ou la durée de parcours entre un point $i$ et un point $j$ diffère de celle entre $j$ et $i$ ($d(i, j) \neq d(j, i)$). À Agadir, cette asymétrie atteint $\alpha = 0{,}3217$ (Frobenius) avec $92{,}44\%$ d'arcs asymétriques en raison des sens uniques et ronds-points.
- **ATSP (Asymmetric Traveling Salesperson Problem / Problème du Voyageur de Commerce Asymétrique) :**  
  Problème d'optimisation combinatoire NP-difficile consistant à déterminer le plus court circuit hamiltonien fermé visitant exactement une fois chaque client à partir d'un dépôt central, lorsque la matrice des coûts est asymétrique ($C \neq C^T$).
- **Audit Cryptographique SHA-256 :**  
  Mécanisme d'enregistrement séquentiel inviolable où chaque événement du système multi-agents est scellé dans une chaîne de blocs de condensats SHA-256, chaque événement intégrant le hash du bloc précédent ($H_k = \text{SHA256}(H_{k-1} + E_k)$).

### B

- **Baseline (Ligne de Base / Solution de Référence) :**  
  Solution algorithmique initiale servant de point de comparaison étalon. Dans AGADIR MAPPING, la baseline officielle est la tournée de la Phase 4 obtenue par algorithme génétique standard ($21\,014{,}3\text{ m}$).
- **Bayesian Optimization (Optimisation Bayésienne) :**  
  Méthode séquentielle d'optimisation de fonctions boîtes noires coûteuses reposant sur un modèle probabiliste a priori mis à jour par les observations passées. Implémentée via Optuna et l'algorithme TPE.

### C

- **Cartographie Numérique (Digital Cartography) :**  
  Représentation spatiale informatisée d'un territoire géographique. Réalisée dans le projet via OpenStreetMap (données brutes) et Leaflet 1.9.4 (rendu interactif web).
- **Circuity Factor (Facteur de Circuité ou Indice de Détour) :**  
  Rapport sans dimension entre la distance de parcours réelle sur réseau routier ($d_{\text{OSRM}}$) et la distance euclidienne à vol d'oiseau ($d_{\text{euclidien}}$) : $CF_{ij} = d_{\text{OSRM}}(i, j) / d_{\text{euclidien}}(i, j)$. Sur la tournée officielle d'Agadir, la moyenne est de $1{,}34$.
- **Contre-Pouvoir Déterministe (Deterministic Counterweight) :**  
  Principe de gouvernance logicielle dans lequel une règle mathématique ou un validateur impératif Python non négociable a le pouvoir de veto absolu sur les propositions générées par des modèles probabilistes ou des agents IA (LLM).
- **Crossover OX (Order Crossover / Croisement par Ordre) :**  
  Opérateur génétique de recombinaison pour permutations préservant l'ordre relatif des sous-chaînes de gènes parentaux sans introduire de doublons ni d'omissions.

### D

- **Dépôt Central (Central Depot / Logistics Hub) :**  
  Nœud logistique central d'où partent et où reviennent obligatoirement les véhicules de livraison. Dans AGADIR MAPPING, le Dépôt Central correspond au point #0 situé sur la Place Al Amal ($30{,}4215^\circ\text{ N}, -9{,}5985^\circ\text{ W}$).
- **Deterministic Validator (Validateur Déterministe Python) :**  
  Module Python souverain vérifiant six règles topologiques inviolables sur la matrice OSRM avant d'autoriser toute validation de proposition d'itinéraire.

### E

- **EPSG:4326 (WGS84) :**  
  Système géodésique mondial exprimant les coordonnées sous forme angulaire (latitude et longitude décimales en degrés).
- **EPSG:32629 (UTM Zone 29N) :**  
  Projection cartographique conforme cylindrique transverse universelle de Mercator projetant la ville d'Agadir sur un repère métrique cartésien plat ($X, Y$ en mètres).

### F

- **Frobenius Asymmetry Index (Indice d'Asymétrie de Frobenius) :**  
  Indicateur matriciel normalisé mesurant le degré d'asymétrie d'une matrice carrée de distance $C$ : $\alpha = \|C - C^T\|_F / \|C\|_F$. Pour Agadir, $\alpha = 0{,}3217$.

### G

- **GA (Genetic Algorithm / Algorithme Génétique) :**  
  Métaheuristique stochastique inspirée de la théorie de l'évolution biologique (sélection, croisement, mutation) pour explorer l'espace combinatoire des permutations.
- **Gemini 3 Flash :**  
  Modèle de langage multimodal de Google DeepMind utilisé par le Gemini Analyst Agent pour la synthèse cognitive d'extraits d'urbanisme et d'articles scientifiques.

### H

- **Hamiltonian Cycle (Circuit Hamiltonien) :**  
  Cycle fermé passant exactement une fois par chaque sommet d'un graphe. Une tournée TSP valide est un circuit hamiltonien débutant et s'achevant au dépôt.
- **Heatmap (Carte de Chaleur Matricielle) :**  
  Représentation graphique bidimensionnelle d'une matrice où les valeurs scalaires sont traduites par un gradient de couleurs.

### J

- **Judge Agent (Agent Arbitre Contradictoire) :**  
  Composant IA autonome évaluant les hypothèses du Gemini Analyst selon une grille officielle pondérée à 5 critères (Fiabilité 25%, Cohérence 25%, Preuves 20%, Concordance 15%, Incertitudes 15%). Score obtenu : $0{,}9340 / 1{,}0000$.

### K

- **Kill-Switch Budgétaire (Budget Kill-Switch) :**  
  Mécanisme d'arrêt d'urgence logiciel interrompant automatiquement tout appel API externe dès que la dépense cumulée atteint le plafond dur préétabli ($0{,}50\text{ USD}$).

### L

- **Last-Mile Delivery (Livraison du Dernier Kilomètre) :**  
  Dernier segment de la chaîne logistique acheminant la marchandise depuis un dépôt ou hub central jusqu'au destinataire final urbain. Représente jusqu'à $40\%$ à $50\%$ du coût total de distribution.

### M

- **Memetic Algorithm (Algorithme Mémétique) :**  
  Extension hybride des algorithmes génétiques combinant l'exploration globale de l'espace par recombinaison de population avec une recherche locale intensive (exploitation individuelle) comme Or-opt.

### O

- **Optuna :**  
  Framework logiciel d'optimisation d'hyperparamètres de pointe reposant sur l'échantillonnage bayésien TPE et des mécanismes d'élagage dynamique.
- **Or-opt :**  
  Opérateur de recherche locale pour le TSP/ATSP consistant à désinsérer une sous-chaîne consécutive de 1, 2 ou 3 sommets pour la réinsérer au meilleur emplacement possible de la tournée sans inverser l'orientation des arcs.
- **OSM (OpenStreetMap) :**  
  Projet collaboratif de cartographie mondiale libre fournissant la topologie viaire et les points d'intérêt bruts.
- **OSRM (Open Source Routing Machine) :**  
  Moteur de routage haute performance calculant les plus courts chemins et matrices de distance sur réseau routier OpenStreetMap réel avec profil automobile (`car`).

### P

- **Parzen-Tree Estimator (TPE / Estimateur de Densité de Parzen Arborescent) :**  
  Algorithme d'optimisation bayésienne modélisant séparément la probabilité des bons et mauvais hyperparamètres par des mélanges de noyaux gaussiens pour guider l'échantillonnage vers l'optimum.
- **POI (Point of Interest / Point d'Intérêt) :**  
  Lieu géolocalisé remarquable (pharmacie, banque, restaurant, commerce) extrait d'OSM et qualifié comme destination logistique.

### S

- **SDAU (Schéma Directeur d'Aménagement Urbain) :**  
  Document d'urbanisme réglementaire fixant les orientations stratégiques d'aménagement de l'agglomération d'Agadir et les plans de circulation viaire.
- **Semantic Scholar :**  
  Moteur de recherche scientifique et base de données académique exploitée par l'agent Semantic Scholar pour acquérir des publications évaluées par les pairs indexées par DOI.

### T

- **Tournoi de Sélection (Tournament Selection) :**  
  Opérateur de sélection génétique choisissant au hasard $k$ individus de la population et retenant le plus apte. Dans AGADIR MAPPING, $k = 6$.
- **TSP (Traveling Salesperson Problem / Problème du Voyageur de Commerce) :**  
  Formulation classique du problème d'optimisation de tournée fermée. Lorsque les distances sont symétriques ($d_{ij} = d_{ji}$), il s'agit du TSP symétrique standard.

### V

- **Veto Python :**  
  Voir *Contre-Pouvoir Déterministe*.
- **VRP (Vehicle Routing Problem / Problème de Tournées de Véhicules) :**  
  Généralisation du TSP à une flotte de plusieurs véhicules sous contraintes de capacités, fenêtres temporelles ou dépôts multiples.
