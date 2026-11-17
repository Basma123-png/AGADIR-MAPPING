# AGADIR MAPPING — PROTOCOLE EXPÉRIMENTAL ET CADRE MÉTHODOLOGIQUE (PHASE 8)
## Évaluation Scientifique, Reproductibilité et Validation Expérimentale du Système

---

### 1. CONTEXTE ET OBJECTIF SCIENTIFIQUE
Le projet **AGADIR MAPPING** arrive à sa phase d'évaluation scientifique finale (**Phase 8**).  
L'objectif est d'asseoir la validité scientifique, la reproductibilité expérimentale et la pertinence opérationnelle des résultats obtenus à travers les Phases 1 à 7.

Ce protocole formalise la démarche méthodologique, énonce les hypothèses à tester, définit les métriques quantitatives, les variables contrôlées et les critères d'acceptation statistique nécessaires à la publication des résultats.

---

### 2. FORMULATION MATHÉMATIQUE DU PROBLÈME (ATSP URBAIN)

#### 2.1. Définition du Graphe Orienté
Soit $G = (V, A)$ un graphe orienté complet où :
- $V = \{0, 1, 2, \dots, n\}$ est l'ensemble des sommets avec $n = 40$ clients (soit $|V| = 41$).
- Le sommet $0$ représente le **Dépôt Central (Place Al Amal)**.
- Le sous-ensemble $V_C = \{1, 2, \dots, 40\}$ représente les 40 destinations clientes, dont le point singulier $40 \in V_C$ (**Restaurant Les Blancs**, impasse côtière).
- $A = \{(i, j) \mid i, j \in V, i \neq j\}$ est l'ensemble des arcs orientés ($|A| = 41 \times 40 = 1\,640$ arcs).

#### 2.2. Matrice de Coûts Asymétrique
À chaque arc $(i, j) \in A$ est associé un coût de distance routière réelle $c_{ij} = d_{\text{OSRM}}(i, j) \ge 0$, issu du réseau viaire réel d'Agadir calculé en Phase 3.  
En raison de la topologie urbaine (chaussées séparées des Boulevards Mohammed V et Hassan II, sens interdits, giratoires), la matrice est intrinsèquement asymétrique :
$$\exists (i, j) \in A \quad \text{tel que} \quad c_{ij} \neq c_{ji}$$

#### 2.3. Fonction Objectif
Soit $x_{ij} \in \{0, 1\}$ la variable de décision indiquant si l'arc $(i, j)$ est emprunté dans la tournée. Le problème ATSP s'énonce :
$$\min \quad Z = \sum_{i \in V} \sum_{j \in V, j \neq i} c_{ij} \, x_{ij}$$

Sous les contraintes de degré et d'élimination des sous-tours (Miller-Tucker-Zemlin / DFJ) :
$$\sum_{j \in V, j \neq i} x_{ij} = 1 \quad \forall i \in V \quad \text{(exactement un arc sortant)}$$
$$\sum_{i \in V, i \neq j} x_{ij} = 1 \quad \forall j \in V \quad \text{(exactement un arc entrant)}$$
$$\sum_{i \in S} \sum_{j \in S, j \neq i} x_{ij} \le |S| - 1 \quad \forall S \subset V, \, 2 \le |S| \le |V| - 1 \quad \text{(élimination des sous-tours)}$$

---

### 3. HYPOTHÈSES SCIENTIFIQUES DE RECHERCHE

- **Hypothèse $H_1$ (Optimisation Combinatoire & Réglage Bayésien) :**  
  *Le réglage fin des hyperparamètres par optimisation bayésienne TPE (Optuna) combiné à un opérateur de recherche locale préservant l'orientation (Or-opt) permet un gain de distance statistiquement significatif ($\ge 8\%$) par rapport à un algorithme génétique standard non accordé.*

- **Hypothèse $H_2$ (Topologie Urbaine & Asymétrie OSRM) :**  
  *La matrice de distance routière réelle d'Agadir présente un degré d'asymétrie suffisant pour rendre inefficaces les heuristiques de retournement de sous-tours (comme le 2-opt symétrique standard), justifiant formellement l'utilisation du modèle ATSP orienté.*

- **Hypothèse $H_3$ (Opérateur de Voisinage Adapté) :**  
  *L'opérateur de relocalisation Or-opt (déplacement de chaînes de 1 à 3 sommets consécutifs sans inversion) surpasse l'opérateur 2-opt classique sur le graphe orienté d'Agadir en évitant les pénalités de détour dues aux sens uniques.*

- **Hypothèse $H_4$ (Gouvernance Contradictoire Multi-Agents) :**  
  *La structure duale associant la créativité cognitive de l'Analyste, la sévérité contradictoire du Judge (grille à 5 critères) et le veto déterministe absolu d'un algorithme Python pur élimine tout risque d'hallucination ou de dégradation de la solution certifiée.*

- **Hypothèse $H_5$ (Reproductibilité & Déterminisme Budgétaire) :**  
  *Le suivi dynamique des jetons (incluant les jetons de réflexion et le cache local) permet de garantir une exécution financièrement bornée et strictement inférieure aux plafonds de sécurité.*

---

### 4. VARIABLES ET MÉTRIQUES D'ÉVALUATION

| Variable | Nature | Description & Unité |
| :--- | :--- | :--- |
| **Distance Totale ($Z$)** | Dépendante | Somme des distances routières des 41 arcs OSRM (mètres). |
| **Gain Relatif ($\Delta Z_{\%}$)** | Dépendante | Pourcentage d'amélioration par rapport à la baseline Phase 4 : $\frac{Z_{\text{base}} - Z_{\text{opt}}}{Z_{\text{base}}} \times 100$. |
| **Facteur de Circuité ($CF_{ij}$)** | Dépendante | Ratio de détour routier : $CF_{ij} = \frac{d_{\text{OSRM}}(i, j)}{d_{\text{euclidien}}(i, j)} \ge 1{,}0$. |
| **Indice d'Asymétrie Globale ($\alpha$)** | Indépendante | Norme de Frobenius de l'asymétrie : $\alpha = \frac{\|C - C^T\|_F}{\|C\|_F}$. |
| **Score Contradictoire du Judge ($S_J$)** | Dépendante | Score pondéré à 5 critères : $S_J \in [0, 1]$. |
| **Taille de la Population ($N_{\text{pop}}$)** | Contrôle | Fixée à 50 individus dans le protocole certifié. |
| **Nombre de Générations ($G_{\text{max}}$)** | Contrôle | Fixé à 200 générations. |
| **Graines Aléatoires (*Seeds*)** | Contrôle | 10 graines indépendantes testées en Phase 5 pour garantir l'absence de biais d'initialisation. |

---

### 5. BENCHMARK COMPARATIF DES STRATÉGIES

L'évaluation compare cinq heuristiques et configurations progressives sur le réseau d'Agadir :
1. **$M_0$ — Baseline Aléatoire (Random Tour) :** Espérance mathématique sur $1\,000$ permutations aléatoires valides partant et revenant au dépôt #0.
2. **$M_1$ — Heuristique Gloutonne (Nearest Neighbor) :** Construction incrémentale en sélectionnant à chaque étape le plus proche voisin non visité sur la matrice asymétrique.
3. **$M_2$ — Algorithme Génétique Standard (Phase 4 Baseline) :** GA avec croisement OX, mutation swap/inversion sans recherche locale avancée (Résultat certifié : **$21\,014{,}3\text{ m}$**).
4. **$M_3$ — GA Hybride avec 2-opt Naïf :** GA avec recherche locale 2-opt symétrique inversant les sous-chaînes.
5. **$M_4$ — GA Hybride Optimisé Optuna + Or-opt (Phase 5/6/7 Certifiée) :** Solution optimale certifiée avec relocalisation orientée de blocs (Résultat certifié : **$18\,933{,}1\text{ m}$**).

---

### 6. CONDITIONS DE REPRODUCTIBILITÉ ET SANCTUARISATION

- **Sanctuarisation des Données :** Les 4 fichiers de référence (`delivery_points_40.csv`, `distance_matrix.csv`, `duration_matrix.csv`, `tsp_optimized_route.json`) doivent conserver leurs empreintes SHA-256 certifiées à $100\%$ tout au long des expériences.
- **Environnement Isolé :** Toute simulation ou calcul comparatif s'exécute dans un script dédié [`scripts/run_phase8_experiments.py`](file:///Users/ouaarab/Documents/AGADIR%20MAPPING/scripts/run_phase8_experiments.py) écrivant exclusivement dans `outputs/reports/` et `outputs/figures/`.
- **Règle d'Inviolabilité :** Aucune nouvelle tournée ne pourra remplacer la tournée certifiée de $18\,933{,}1\text{ m}$ qui demeure la référence intangible du projet.

---

### 7. CRITÈRES D'ACCEPTATION SCIENTIFIQUE
Le protocole sera validé si et seulement si :
1. Les 4 empreintes SHA-256 pré- et post-expériences sont strictement identiques.
2. Le recalcul exact sur `distance_matrix.csv` donne précisément $18\,933{,}1\text{ m}$ ($18{,}9331\text{ km}$).
3. L'indice d'asymétrie $\alpha$ de la matrice routière d'Agadir est strictement supérieur à 0,15, validant mathématiquement le modèle ATSP.
4. Le facteur de circuité moyen sur les 41 segments est supérieur à 1,20, démontrant l'impact des détours viaires urbains face au modèle vol d'oiseau.
5. La suite complète des tests de non-régression s'exécute avec 100% de réussite.
