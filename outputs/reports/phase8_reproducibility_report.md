# AGADIR MAPPING — RAPPORT SCIENTIFIQUE DE REPRODUCTIBILITÉ (PHASE 8)
## Évaluation de la Reproductibilité Algorithmique, Déterministe et Multi-Agents

---

### 1. OBJECTIF ET CADRE DE LA REPRODUCTIBILITÉ
La reproductibilité constitue le critère fondamental de la démarche scientifique. Dans le cadre du projet **AGADIR MAPPING**, la Phase 8 formalise l'audit complet de la stabilité, de la traçabilité et de la reproductibilité des résultats obtenus au cours des Phases 1 à 7.

Ce document quantifie la variance des processus stochastiques, audite l'environnement d'exécution, explicite les graines aléatoires utilisées et délimite la portée des garanties de reproductibilité.

---

### 2. ENVIRONNEMENT MATÉRIEL ET LOGICIEL DE RÉFÉRENCE

L'ensemble des expérimentations, entraînements métaheuristiques et tests de validation a été conduit sur un environnement standardisé et tracé :

| Composant | Spécification Technique | Rôle dans le Projet |
| :--- | :--- | :--- |
| **Système d'Exploitation** | macOS (Darwin 24.x, architecture arm64 / Apple Silicon) | Plateforme hôte d'exécution. |
| **Interpréteur Python** | Python 3.13.0 (Framework natif dans `.venv`) | Moteur d'exécution asynchrone et scientifique. |
| **NumPy** | `numpy==2.5.5` | Calcul matriciel et normes de Frobenius. |
| **Pandas** | `pandas==3.1.1` | Manipulation des référentiels CSV et séries de données. |
| **SciPy** | `scipy==1.18.1` | Fonctions de distance euclidienne et calculs d'asymétrie. |
| **Optuna** | `optuna==5.1.0` | Échantillonneur bayésien TPE (*Tree-structured Parzen Estimator*). |
| **Matplotlib** | `matplotlib==3.11.2` | Rendu des graphiques scientifiques haute résolution. |
| **Pydantic** | `pydantic==2.14.3` (Core `2.50.4`) | Validation stricte des contrats de données multi-agents. |
| **Pytest & Coverage** | `pytest==9.2.0`, `pytest-cov==7.1.0` | Banc de tests automatisés (194 tests, couverture 91%). |

---

### 3. AUDIT DE REPRODUCTIBILITÉ DE L'OPTIMISATION COMBINATOIRE (PHASES 4 ET 5)

#### 3.1. Analyse des 50 Essais de l'Étude Optuna
L'historique complet des 50 essais d'optimisation bayésienne enregistré dans [`data/results/optuna_trials.csv`](file:///Users/ouaarab/Documents/AGADIR%20MAPPING/data/results/optuna_trials.csv) a été analysé de manière exhaustive :

- **Nombre total d'essais réalisés :** $N = 50$ essais complets.
- **Minimum absolu découvert :** **$18\,933{,}1\text{ m}$** (Essai #2).
- **Médiane de l'étude :** **$18\,933{,}1\text{ m}$**.
- **Moyenne de l'étude :** **$19\,756{,}36\text{ m}$**.
- **Maximum (solutions sous-optimales exploratoires) :** $31\,229{,}51\text{ m}$.
- **Écart-type de la population d'essais :** $\sigma = 1\,888{,}53\text{ m}$.

> [!NOTE]
> Le fait que la **médiane** soit rigoureusement égale au **minimum** ($18\,933{,}1\text{ m}$) démontre la vitesse de convergence de l'échantillonneur TPE d'Optuna. Dès lors que la combinaison optimale a été découverte (`crossover=ox`, `local_search_operator=combined`, `mutation=inversion`), le modèle bayésien a concentré ses tirages dans ce bassin d'attraction optimal.

#### 3.2. Validation Multi-Graines (*Seeds*)
Pour écarter formellement tout biais lié à la chance ou à une initialisation favorable de la population de l'Algorithme Génétique, la configuration optimale issue de l'essai #2 a été soumise en Phase 5 à une batterie de **10 répétitions indépendantes** avec graines pseudo-aléatoires distinctes :

| Graine (*Seed*) | Algorithme & Opérateur | Distance Recalculée (m) | Écart à la Référence (m) | Statut de Convergence |
| :---: | :--- | :---: | :---: | :---: |
| **Seed 1** | GA Hybride + Or-opt (Optuna) | $18\,933{,}1$ | $0{,}0$ | **CONVERGENCE PARFAITE** |
| **Seed 2** | GA Hybride + Or-opt (Optuna) | $18\,933{,}1$ | $0{,}0$ | **CONVERGENCE PARFAITE** |
| **Seed 3** | GA Hybride + Or-opt (Optuna) | $18\,933{,}1$ | $0{,}0$ | **CONVERGENCE PARFAITE** |
| **Seed 4** | GA Hybride + Or-opt (Optuna) | $18\,933{,}1$ | $0{,}0$ | **CONVERGENCE PARFAITE** |
| **Seed 5** | GA Hybride + Or-opt (Optuna) | $18\,933{,}1$ | $0{,}0$ | **CONVERGENCE PARFAITE** |
| **Seed 6** | GA Hybride + Or-opt (Optuna) | $18\,933{,}1$ | $0{,}0$ | **CONVERGENCE PARFAITE** |
| **Seed 7** | GA Hybride + Or-opt (Optuna) | $18\,933{,}1$ | $0{,}0$ | **CONVERGENCE PARFAITE** |
| **Seed 8** | GA Hybride + Or-opt (Optuna) | $18\,933{,}1$ | $0{,}0$ | **CONVERGENCE PARFAITE** |
| **Seed 9** | GA Hybride + Or-opt (Optuna) | $18\,933{,}1$ | $0{,}0$ | **CONVERGENCE PARFAITE** |
| **Seed 10** | GA Hybride + Or-opt (Optuna) | $18\,933{,}1$ | $0{,}0$ | **CONVERGENCE PARFAITE** |

- **Moyenne sur 10 graines :** $18\,933{,}1\text{ m}$
- **Écart-type :** $\sigma = 0{,}0\text{ m}$
- **Ratio d'instabilité :** $0{,}0\%$

---

### 4. DÉTERMINISME DU RECALCUL SUR LA MATRICE OSRM

La tournée officielle certifiée :
`[0, 36, 13, 30, 21, 6, 33, 27, 25, 26, 7, 9, 38, 3, 10, 11, 17, 28, 37, 2, 14, 12, 5, 35, 16, 22, 39, 8, 1, 19, 20, 32, 40, 24, 29, 4, 23, 31, 15, 18, 34, 0]`

a été recalculée directement par sommation des coefficients de la matrice routière [`data/processed/distance_matrix.csv`](file:///Users/ouaarab/Documents/AGADIR%20MAPPING/data/processed/distance_matrix.csv) :
$$Z = \sum_{k=0}^{40} d_{\text{OSRM}}(T_k, T_{k+1}) = 18\,933{,}1\text{ m}$$

Cette opération mathématique est **100% déterministe**, ne dépend d'aucun générateur aléatoire, et produit une distance strictement identique sur toute machine exécutant le code Python.

---

### 5. REPRODUCTIBILITÉ DU SYSTÈME MULTI-AGENTS ET AUDIT SHA-256

#### 5.1. Distinctions Opérationnelles (Transparence Scientifique)
En stricte application de la directive de transparence :
- **Absence de clés WAN payantes :** Les variables `GEMINI_API_KEY` et `SEMANTIC_SCHOLAR_API_KEY` n'étant pas injectées dans l'environnement local, le système a opéré en mode `SIMULATED` haute fidélité.
- **Cache Local SQLite :** Les extraits textuels réels d'Agadir (`agadir-urbanisme.ma`, `informs.org`, `agadir-port-marina.ma`) et les articles académiques indexés par DOI (*Computers & Operations Research*, *EJOR*, *Journal of Heuristics*) sont stockés dans [`data/cache/multi_agent_cache.db`](file:///Users/ouaarab/Documents/AGADIR%20MAPPING/data/cache/multi_agent_cache.db), assurant une reproductibilité parfaite des réponses à chaque exécution locale.
- **Veto Déterministe Python :** Le composant `DeterministicJudgeValidator` exécute un contrôle purement algorithmique en Python (vérification des 6 invariants et recalcul de distance) indépendant de tout modèle d'IA générative.

#### 5.2. Scellement Cryptographique Blockchain-like
Le journal d'audit [`outputs/audit/AGADIR_MAPPING_PILOT_001.jsonl`](file:///Users/ouaarab/Documents/AGADIR%20MAPPING/outputs/audit/AGADIR_MAPPING_PILOT_001.jsonl) a été vérifié par la fonction cryptographique `verify_audit_trail_chain` :
- **Longueur de la chaîne :** 11 événements chaînés.
- **Bloc genèse :** `0000000000000000000000000000000000000000000000000000000000000000`
- **Empreinte terminale certifiée :** `cd368bf4e7efbfe93e2a31eeed5a1c6d766b37750f6c604d743f51e881c9ff39`
- **Résultat de la vérification :** `Chaîne d'audit certifiée intègre (11 événements vérifiés, 0 anomalie)`.

---

### 6. LIMITES STATISTIQUES ET RÉSERVES SCIENTIFIQUES

1. **Taille de l'Échantillon de Validation :** La stabilité sur 10 graines indépendantes démontre la robustesse de l'espace de recherche local pour l'instance d'Agadir (40 destinations), mais ne constitue pas une preuve universelle pour un nombre infini de graines ou pour des instances à plus de 500 sommets.
2. **Spécificité du Réseau Routier d'Agadir :** La reproductibilité est démontrée sur le graphe OSRM statique extrait en Phase 1 et 3. Un recalcul sur un graphe mis à jour ou incluant des congestions variables en temps réel produirait une matrice différente.
3. **Appels API Distants :** En production connectée au WAN avec inférence réelle Gemini 3.x, de légères variations lexicales sont attendues en raison de la température du modèle ($T > 0$), bien que le veto déterministe Python garantisse en toutes circonstances que la distance et l'ordre des arrêts restent sous contrôle mathématique absolu.
