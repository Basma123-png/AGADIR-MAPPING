# RAPPORT OFFICIEL — PHASE 6.1
## Document 7 : Feuille de Route et Planification Opérationnelle (Phases 6.1 à 6.8)
**Projet :** AGADIR MAPPING — Last Mile TSP Optimization  
**Date d'audit :** 16/11/2026  
**Auteur :** Antigravity (Google DeepMind Team)  
**Classification :** Spécification Technique & Conception Système  

---

## 1. Découpage Méthodologique

Pour garantir une progression maîtrisée, traçable et sans régression, le développement de la Phase 6 est scindé en **huit sous-phases séquentielles**. Chaque sous-phase fait l'objet de livrables précis, de tests unitaires dédiés et d'une validation formelle avant d'engager la suivante.

---

## 2. Plan Détaillé des Sous-Phases

### Phase 6.1 : Architecture, Spécifications et Étude Préalable (Phase Actuelle)
- **Objectif :** Conception exhaustive, audit du code existant, modélisation des protocoles, étude des quotas et des coûts, sans aucun développement.
- **Prérequis :** Phase 5 validée et auditée (tournée officielle certifiée à 18 933,1 m).
- **Livrables :** Les 8 documents de conception dans `outputs/reports/` et les diagrammes d'architecture Mermaid.
- **Critère de passage :** Validation humaine formelle du dossier de conception avant tout développement.

---

### Phase 6.2 : Cœur de Communication et Orchestrateur Central
- **Objectif :** Implémenter le socle d'échange de messages typés, la machine à états finis et l'orchestrateur central.
- **Prérequis :** Phase 6.1 validée.
- **Fichiers à créer :**
  - `src/agents/models.py` : Définition des classes Pydantic v2 (`AgentRequest`, `AgentResponse`, `FinalReport`, etc.).
  - `src/agents/orchestrator.py` : Moteur DAG coordonnant le cycle de vie des missions.
  - `src/agents/logger.py` : Journalisation d'audit en JSON Lines (`multi_agents_audit.jsonl`).
- **Livrables :** `tests/test_agents_orchestrator.py`, rapport de validation `phase6_2_orchestrator_report.md`.
- **Tests d'acceptation :** 100% des tests unitaires validant l'instanciation de l'orchestrateur, la création des requêtes et le routage mock.

---

### Phase 6.3 : Web Research Agent
- **Objectif :** Développer le collecteur web documentaire dédié aux problématiques TSP/VRP.
- **Prérequis :** Phase 6.2 validée.
- **Fichiers à créer :**
  - `src/agents/web_research_agent.py` : Client de recherche DuckDuckGo et parseur HTML léger sanitisé.
  - `src/agents/cache_manager.py` : Gestionnaire de cache persistant SQLite pour les requêtes web.
- **Livrables :** `tests/test_web_research_agent.py`, rapport de validation `phase6_3_web_agent_report.md`.
- **Tests d'acceptation :** Extraction réussie de 3 sources web pertinentes avec URL, snippets et année, détection des tentatives d'injections de prompt, bon fonctionnement du cache local.

---

### Phase 6.4 : Semantic Scholar Agent
- **Objectif :** Implémenter le client de recherche bibliographique sur l'Academic Graph de Semantic Scholar.
- **Prérequis :** Phase 6.3 validée.
- **Fichiers à créer :**
  - `src/agents/semantic_scholar_agent.py` : Client API avec limite de débit intégrée (1 req/s) et backoff exponentiel.
- **Livrables :** `tests/test_semantic_scholar_agent.py`, rapport `phase6_4_scholar_agent_report.md`.
- **Tests d'acceptation :** Récupération réussie d'articles sur l'ATSP avec extraction de titres, auteurs, DOI, citations et gestion gracieuse du code HTTP 429.

---

### Phase 6.5 : Gemini Analyst Agent
- **Objectif :** Développer l'agent d'analyse critique exploitant le SDK officiel `google-genai`.
- **Prérequis :** Phase 6.4 validée, variable `GEMINI_API_KEY` configurée dans `.env`.
- **Fichiers à créer :**
  - `src/agents/gemini_analyst.py` : Client Gemini typé avec `response_schema` Pydantic et balisage de prompt hermétique.
- **Livrables :** `tests/test_gemini_analyst.py`, rapport `phase6_5_gemini_analyst_report.md`.
- **Tests d'acceptation :** Génération d'une synthèse critique structurée confrontant des sources réelles au contexte d'Agadir, zéro injection de prompt possible.

---

### Phase 6.6 : Judge Agent (Arbitre Épistémologique)
- **Objectif :** Développer l'agent d'arbitrage contradictoire fondé sur la preuve probatoire.
- **Prérequis :** Phase 6.5 validée.
- **Fichiers à créer :**
  - `src/agents/judge_agent.py` : Moteur d'évaluation contradictoire, attribution des verdicts (`ACCEPTED`, `REJECTED`, `NEEDS_REVIEW`).
- **Livrables :** `tests/test_judge_agent.py`, rapport `phase6_6_judge_agent_report.md`.
- **Tests d'acceptation :** Rejet automatique de toute affirmation péremptoire non sourcée, acceptation conditionnelle des thèses nécessitant une validation numérique.

---

### Phase 6.7 : Deterministic Validator (Python)
- **Objectif :** Intégrer le composant de validation mathématique pure, hermétique et indépendant des LLMs.
- **Prérequis :** Phase 6.6 validée, matrice `distance_matrix.csv` certifiée.
- **Fichiers à créer :**
  - `src/agents/deterministic_validator.py` : Recalcul strict sur la matrice OSRM 41x41, vérification des 42 arrêts, du dépôt #0 et du littoral #40.
- **Livrables :** `tests/test_deterministic_validator.py`, rapport `phase6_7_validator_report.md`.
- **Tests d'acceptation :** Détection infaillible d'un doublon, rejet d'une tournée omettant le dépôt #0, vérification numérique au centième de millimètre.

---

### Phase 6.8 : Intégration Globale, Tests End-to-End et Mission Pilote
- **Objectif :** Intégration complète de la chaîne DAG et exécution d'une mission de benchmark pilote.
- **Prérequis :** Phases 6.2 à 6.7 validées.
- **Mission pilote :** *"Étude bibliographique et expérimentale de l'apport potentiel d'un opérateur 3-opt asymétrique sur la tournée d'Agadir (18 933,1 m)"*.
- **Livrables :** `scripts/run_phase6_multi_agent.py`, suite de tests end-to-end `tests/test_multi_agent_pipeline.py`, rapport final consolidé `outputs/reports/phase6_final_mission_report.md`.
- **Tests d'acceptation :** Exécution complète de la mission en moins de 15 secondes, rapport final traçable et archivé, intégrité absolue des données de référence.

---

## 3. Matrice de Dépendances et Diagramme de Gantt Logique

```text
Phase 6.1 (Architecture & Spécifications) [EN COURS]
   │
   ▼ (Validation Utilisateur Requise)
Phase 6.2 (Socle Pydantic & Orchestrateur)
   │
   ├──────────────────────────┐
   ▼                          ▼
Phase 6.3 (Web Agent)      Phase 6.4 (Scholar Agent)
   │                          │
   └──────────┬───────────────┘
              ▼
Phase 6.5 (Gemini Analyst)
              │
              ▼
Phase 6.6 (Judge Agent)
              │
              ▼
Phase 6.7 (Validateur Déterministe Python)
              │
              ▼
Phase 6.8 (Intégration Globale & Mission Pilote)
```

Ce découpage progressif évite tout effet tunnel et garantit que chaque agent est testé unitairement avant son insertion dans l'orchestrateur.
