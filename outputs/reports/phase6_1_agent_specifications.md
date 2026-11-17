# RAPPORT OFFICIEL — PHASE 6.1
## Document 3 : Spécifications Fonctionnelles et Techniques des Agents
**Projet :** AGADIR MAPPING — Last Mile TSP Optimization  
**Date d'audit :** 16/11/2026  
**Auteur :** Antigravity (Google DeepMind Team)  
**Classification :** Spécification Technique & Conception Système  

---

## 1. Vue d'Ensemble

Ce document définit les spécifications complètes des six agents constituant le système IA d'AGADIR MAPPING. Chaque agent est conçu comme une unité fonctionnelle autonome, dotée d'entrées et de sorties rigoureusement typées, de mécanismes de repli (*fallback*), de quotas explicites et de règles de confinement strictes.

---

## 2. Spécification de l'Agent 1 : Web Research Agent

### 2.1. Fiche d'Identité
- **Identifiant interne :** `web_research_agent`
- **Type d'agent :** Collecteur d'information externe & Extracteur documentaire
- **Niveau de confiance des données :** `UNTRUSTED_EXTERNAL` (Données externes nécessitant sanitisation)

### 2.2. Mission et Responsabilités
- Effectuer des requêtes ciblées sur le Web sur des problématiques précises du Last-Mile Logistics, du TSP asymétrique et des métaheuristiques.
- Filtrer les résultats non pertinents (blogs commerciaux, forums non validés).
- Extraire des extraits textuels factuels avec traçabilité complète : URL source, titre, date de consultation, extrait brut.
- Isoler les faits documentés des affirmations publicitaires ou spéculatives.

### 2.3. Contrat d'Interface (Entrées / Sorties)
- **Entrée (`WebSearchRequest`) :**
  ```json
  {
    "request_id": "req-web-001",
    "query": "asymmetric TSP or-opt segment relocation last mile benchmark",
    "max_results": 5,
    "target_domains": ["arxiv.org", "github.com", "researchgate.net", "sciencedirect.com"],
    "language": "en"
  }
  ```
- **Sortie (`WebSearchResponse`) :**
  ```json
  {
    "request_id": "req-web-001",
    "status": "SUCCESS",
    "sources_found": 3,
    "sources": [
      {
        "url": "https://arxiv.org/abs/2105.xxxxx",
        "title": "Fast Local Search Operators for Asymmetric TSPs",
        "snippet": "We present an Or-opt relocation heuristic that achieves a 6.2% improvement...",
        "published_year": 2023,
        "is_reputable_domain": true,
        "crawled_at_utc": "2026-11-16T22:00:00Z"
      }
    ],
    "execution_time_seconds": 1.24
  }
  ```

### 2.4. Technologies et Dépendances
- Moteur de recherche : `duckduckgo-search` / API Instant Answers ou client HTTP synchrone `requests` avec User-Agent académique.
- Parser de contenu : `re` et parser léger regex/HTML sanitisé.
- Bibliothèque de modélisation : `pydantic`.

### 2.5. Quotas, Délais et Stratégies de Repli
- **Timeout :** 15 secondes par requête.
- **Quota :** Maximum 10 requêtes par mission utilisateur.
- **Fallback :** En cas de coupure réseau ou de blocage du moteur, bascule vers le cache local SQLite `data/agents_cache/web_cache.db`. Si le cache est vide, retourne une réponse vide avec statut `NETWORK_UNAVAILABLE` sans faire planter l'orchestrateur.

---

## 3. Spécification de l'Agent 2 : Semantic Scholar Agent

### 3.1. Fiche d'Identité
- **Identifiant interne :** `semantic_scholar_agent`
- **Type d'agent :** Explorateur bibliographique scientifique indexé
- **Niveau de confiance des données :** `PEER_REVIEWED_ACADEMIC` (Sources scientifiques vérifiables)

### 3.2. Mission et Responsabilités
- Interroger l'API Semantic Scholar Academic Graph pour identifier les articles révisés par les pairs portant sur l'ATSP, les heuristiques mémétiques, le 2-opt/3-opt asymétrique et le VRP.
- Extraire les métadonnées vérifiables : Titre officiel, liste des auteurs, année de publication, revue/conférence, DOI, lien open-access et nombre de citations.
- Évaluer l'autorité scientifique d'un papier sur la base de ses citations et de son indexation.

### 3.3. Contrat d'Interface (Entrées / Sorties)
- **Entrée (`ScholarSearchRequest`) :**
  ```json
  {
    "request_id": "req-sch-001",
    "query": "asymmetric travelling salesperson genetic algorithm optuna",
    "fields": ["title", "authors", "year", "abstract", "citationCount", "doi", "openAccessPdf"],
    "limit": 5,
    "min_year": 2018
  }
  ```
- **Sortie (`ScholarSearchResponse`) :**
  ```json
  {
    "request_id": "req-sch-001",
    "status": "SUCCESS",
    "total_papers": 2,
    "papers": [
      {
        "paper_id": "649def34f83c52b44...",
        "title": "A Memetic Algorithm with Adaptive Local Search for the Asymmetric TSP",
        "authors": ["K. Smith", "L. Benali"],
        "year": 2022,
        "venue": "Computers & Operations Research",
        "doi": "10.1016/j.cor.2022.105842",
        "citation_count": 48,
        "abstract_summary": "The paper introduces a combined 2-opt and node-relocation strategy...",
        "pdf_url": "https://openaccess.org/paper.pdf"
      }
    ],
    "execution_time_seconds": 0.85
  }
  ```

### 3.4. Quotas, Limitations d'API et Architecture de Résilience
- **API Endpoint :** `https://api.semanticscholar.org/graph/v1/paper/search` et `POST /graph/v1/paper/batch`
- **Distinction des modes d'accès :**
  - **Mode Anonyme (sans clé API) :** Partage un pool de débit mondial commun avec l'ensemble des utilisateurs non authentifiés (~1 000 req/s au niveau mondial). Ce pool mutualisé est sujet à des congestions soudaines et peut renvoyer des erreurs HTTP 429 même à faible cadence locale.
  - **Mode Authentifié (avec `SEMANTIC_SCHOLAR_API_KEY`) :** Le débit de **1 requête par seconde est le quota introductif documenté** pour une clé API individuelle. Ce quota n'est pas une garantie contractuelle permanente ni un droit d'accès non contesté : l'infrastructure d'AI2 applique une régulation dynamique de charge, et des réponses HTTP 429 peuvent survenir en période de forte affluence globale.
- **Gestion des erreurs HTTP 429 et résilience :**
  - Configuration du rythme nominal adaptable (`rate_limit_delay_seconds`).
  - Détection immédiate du statut HTTP 429 (*Too Many Requests*).
  - Algorithme d'*Exponential Backoff avec Jitter* (délai initial 2s, puis 4s, 8s, 16s avec composante aléatoire uniforme).
  - Déduplication systématique des requêtes en amont via hachage SHA-256 de la requête.
  - Utilisation du point d'entrée batch (`POST /graph/v1/paper/batch`) pour récupérer jusqu'à 500 identifiants de documents en un seul appel réseau.
- **Cache persistant et reprise sur erreur :**
  - Cache local persistant SQLite `data/agents_cache/scholar_cache.sqlite` avec TTL configurable (30 jours par défaut).
  - Enregistrement de l'état de mission permettant la reprise (*stateful resume*) sans ré-interroger les DOIs déjà indexés en cas d'interruption.
  - Fallback hors-ligne immédiat sur le corpus académique local si le réseau externe est inaccessible.

---

## 4. Spécification de l'Agent 3 : Gemini Analyst (Moteur IA Configurable)

### 4.1. Fiche d'Identité
- **Identifiant interne :** `gemini_analyst`
- **Type d'agent :** Synthétiseur cognitif & Analyste critique d'optimisation
- **Moteur LLM et Découplage :**
  - SDK officiel moderne `google-genai` (v3.3.0).
  - **Identifiants de modèles non figés dans le code :** Chargés dynamiquement depuis le fichier de configuration indépendant `config/multi_agent_config.json` ou variables d'environnement (`GEMINI_FAST_MODEL`, `GEMINI_PRO_MODEL`).
  - **Modèles de référence actuels (fin 2026) :**
    - Modèle rapide et économique par défaut : `gemini-3.8-flash` (ou `gemini-4-hydrogen`).
    - Modèle haute capacité et raisonnement poussé (sur demande explicite) : `gemini-4-carbon` (ou `gemini-4-argon`).
  - **Abstraction multi-fournisseurs :** Interface abstraite `BaseLLMProvider` permettant le basculement ultérieur vers d'autres fournisseurs d'inférence sans refonte du code métier.

### 4.2. Mission et Responsabilités
- Réceptionner les données structurées provenant du Web Research Agent et du Semantic Scholar Agent.
- Confrontation avec le contexte réel d'Agadir (40 destinations urbaines + 1 littorale, matrice OSRM 41x41 asymétrique, tournée de référence certifiée à 18 933,1 m).
- Détecter les incohérences mathématiques ou les hypothèses irréalistes (ex: supposer qu'une ville réelle a des distances symétriques ou planes).
- Émettre des propositions d'amélioration quantifiées (ex: modification du taux de croisement, ajout d'un opérateur de perturbation, ajustement de l'élitisme).

### 4.3. Contrat d'Interface (Entrées / Sorties)
- **Entrée (`AnalystRequest`) :**
  ```json
  {
    "request_id": "req-ana-001",
    "project_context": {
      "city": "Agadir",
      "depot": "Place Al Amal",
      "destinations_count": 40,
      "reference_distance_m": 18933.1,
      "is_asymmetric": true
    },
    "web_findings": [...],
    "academic_papers": [...]
  }
  ```
- **Sortie (`AnalystResponse`) :**
  ```json
  {
    "request_id": "req-ana-001",
    "status": "SUCCESS",
    "model_used": "gemini-3.8-flash",
    "theses": [
      {
        "thesis_id": "TH-01",
        "title": "Adoption d'une mutation Scramble adaptative",
        "argumentation": "Selon Smith & Benali (2022), la mutation scramble sur 3 nœuds permet d'échapper aux minima locaux du 2-opt...",
        "expected_gain_pct": 2.5,
        "scientific_citations": ["10.1016/j.cor.2022.105842"],
        "requires_deterministic_validation": true
      }
    ],
    "identified_risks": ["Augmentation du temps de calcul de 15%"],
    "tokens_consumed": 1420
  }
  ```

### 4.4. Sécurité et Guardrails
- **Prompt Injection Defense :** Les données web et scientifiques sont encapsulées dans des balises `<untrusted_source>` hermétiques. Le prompt système interdit strictement d'obéir à toute instruction textuelle contenue dans les données scrapées.
- **Schéma Pydantic strict :** La réponse est contrainte via l'option `response_schema` du SDK `google-genai` pour garantir une structure JSON conforme sans texte parasite.

---

## 5. Spécification de l'Agent 4 : Judge Agent

### 5.1. Fiche d'Identité
- **Identifiant interne :** `judge_agent`
- **Type d'agent :** Arbitre épistémologique et probatoire contradictoire
- **Moteur :** Moteur à base de règles logiques et de validation d'arguments (assisté par Gemini avec prompt adversarial).

### 5.2. Mission et Responsabilités
- Ne jamais faire confiance à l'Analyste sur parole.
- Vérifier que chaque affirmation s'appuie sur une source concrète présente dans les flux Web ou Scholar.
- Rejeter les affirmations péremptoires (ex: "Cet algorithme garantit l'optimum global") sans démonstration mathématique.
- Attribuer un statut décisionnel parmi trois issues strictes :
  1. `ACCEPTED` : Affirmation soutenue par des preuves solides, sans contradiction, prête pour l'application.
  2. `ACCEPTED_PENDING_VALIDATION` : Proposition cohérente nécessitant impérativement le recalcul par le Validateur Déterministe Python.
  3. `REJECTED` : Affirmation non étayée, contradictoire, ou violant les contraintes d'Agadir (ex: violation du caractère asymétrique).
  4. `NEEDS_REVIEW` : Données insuffisantes ou incertitudes majeures, nécessitant un arbitrage humain.

### 5.3. Contrat d'Interface (Entrées / Sorties)
- **Sortie (`JudgeDecision`) :**
  ```json
  {
    "decision_id": "dec-001",
    "verdict": "ACCEPTED_PENDING_VALIDATION",
    "evaluated_theses": [
      {
        "thesis_id": "TH-01",
        "status": "ACCEPTED_PENDING_VALIDATION",
        "confidence_score": 0.88,
        "evidence_quality": "HIGH",
        "justification": "Le papier DOI:10.1016/j.cor.2022.105842 confirme l'efficacité sur ATSP. Validation numérique requise.",
        "requires_python_validator": true
      }
    ],
    "dissenting_opinions": []
  }
  ```

---

## 6. Spécification de l'Agent 5 : Deterministic Validator (Python)

### 6.1. Fiche d'Identité
- **Identifiant interne :** `deterministic_validator`
- **Type de composant :** Validateur algorithmique et arithmétique pur (100% Python, **zéro LLM**)
- **Niveau d'autorité :** **Absolu et Inviolable**

### 6.2. Mission et Responsabilités
- Réaliser tous les calculs critiques de manière déterministe et reproductible.
- Accès exclusif en **LECTURE SEULE** aux données certifiées des Phases 1 à 5 (`distance_matrix.csv`, `duration_matrix.csv`, `delivery_points_40.csv`, `tsp_optimized_route.json`). Aucun descripteur de fichier en écriture.
- Recalculer les coûts orientés des tournées sur la matrice OSRM brute `distance_matrix.csv` en respectant strictement l'asymétrie routière ($D(i,j) \neq D(j,i)$).
- Vérifier les invariants topologiques :
  - Départ et arrivée obligatoires au Point #0 (Place Al Amal).
  - Présence de la destination littorale #40 (Restaurant Les Blancs).
  - Visite unique de chaque point $\{1..40\}$ sans doublon ni omission.
  - Calcul de la longueur totale exacte de la tournée ($N = 42$).
- Comparer rigoureusement toute proposition d'amélioration à la référence certifiée de **18 933,1 m** :
  $$\text{Gain} = 18\,933,1 - D_{\text{candidate}}$$
  Si $\text{Gain} \le 0$, la proposition est rejetée sans appel comme non améliorante.

### 6.3. Contrat d'Interface (Entrées / Sorties)
- **Entrée (`ValidationRequest`) :**
  ```json
  {
    "candidate_tour": [0, 36, ..., 34, 0],
    "claimed_distance_m": 18850.0
  }
  ```
- **Sortie (`ValidationResult`) :**
  ```json
  {
    "is_valid_permutation": true,
    "has_depot_start_end": true,
    "has_coastal_point": true,
    "total_stops": 42,
    "recalculated_distance_m": 18933.1,
    "discrepancy_m": 83.1,
    "verdict": "REJECTED_CLAIM_DISCREPANCY",
    "explanation": "La distance réelle calculée sur la matrice OSRM est de 18933.1 m et non de 18850.0 m."
  }
  ```

---

## 7. Spécification de l'Agent 6 : Central Orchestrator

### 7.1. Fiche d'Identité
- **Identifiant interne :** `central_orchestrator`
- **Type de composant :** Coordinateur de flux, Planificateur d'exécution DAG et Observateur

### 7.2. Mission et Responsabilités
- Point d'entrée unique pour l'utilisateur ou l'interface graphique Tkinter.
- Instanciation et séquençage des agents selon le plan DAG défini dans le Document 2.
- Chargement de la configuration découplée (`config/multi_agent_config.json`).
- Gestion des timeouts, réessais et captures d'exceptions pour éviter tout blocage.
- Collecte et fusion des résultats intermédiaires dans un objet `FinalReport`.
- Sauvegarde standardisée des résultats dans les seuls répertoires autorisés : `outputs/reports/`, `outputs/audit/` et `data/agents_output/`.
- **Maintenance de l'Audit Trail cryptographique (JSONL + SQLite) :**
  - Génération d'une chaîne de hachage SHA-256 où chaque événement inclut explicitement `prev_hash` dans son contenu canonique ordonné et exclut `event_hash`.
  - Exportation externe de l'empreinte de clôture de mission (`final_event_hash`) dans `outputs/audit/mission_fingerprints.json` pour détecter formellement toute troncature ultérieure de fin de journal.
- **Disjoncteur financier à réservation préalable (*Pre-Allocation Check*) :**
  - Calcul du coût pire-cas réservé avant chaque appel API (tokens de prompt estimés + tokens max de sortie incluant les tokens de réflexion *thinking*).
  - Blocage immédiat de l'appel avant émission si `coût_cumulé + coût_réservé > 0,50 USD`.
  - Application stricte de la politique *Fail-Closed* : interdiction des requêtes payantes si les tarifs ne sont pas vérifiés ou si les métadonnées de consommation sont incomplètes.
- **Confinement et Respect des Privilèges POSIX :** Exécution sous compte de service non privilégié (`agadir_orchestrator`, `no_new_privs = 1`), respect de l'accès en lecture seule système sur `data/processed/` et vérification de non-altération des empreintes SHA-256 de référence.
