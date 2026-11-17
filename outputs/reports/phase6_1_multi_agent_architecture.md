# RAPPORT OFFICIEL — PHASE 6.1
## Document 2 : Architecture Générale du Système Multi-Agents IA
**Projet :** AGADIR MAPPING — Last Mile TSP Optimization  
**Date d'audit :** 16/11/2026  
**Auteur :** Antigravity (Google DeepMind Team)  
**Classification :** Spécification Technique & Conception Système  

---

## 1. Philosophie et Principes Fondateurs

Le système multi-agents d'AGADIR MAPPING est guidé par un impératif épistémologique fondamental : **la primauté de la preuve vérifiable sur le consensus déclaratif**.

Contrairement aux architectures multi-agents classiques qui s'appuient sur un vote majoritaire entre plusieurs instances de LLM (susceptibles d'halluciner de concert sur des calculs combinatoires), notre architecture sépare rigoureusement :
1. **L'exploration floue et la recherche bibliographique :** Dévolues aux agents de recherche web et scientifiques ainsi qu'à l'analyste Gemini.
2. **Le raisonnement critique et l'arbitrage contradictoire :** Confiés à un Agent Juge spécialisé qui confronte les sources et les hypothèses.
3. **La vérification déterministe inviolable :** Exécutée en pur code Python par un composant hermétique, non-LLM, recalculant les distances, les coordonnées et les permutations sur la matrice OSRM 41x41 réelle.

---

## 2. Décomposition des Six Composants du Système

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        UTILISATEUR / INTERFACE                         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Requête de Mission
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    AGENT 6 — ORCHESTRATEUR CENTRAL                     │
│         Planification DAG, Routage, Synchronisation, Logging           │
└───────┬───────────────────────────┬────────────────────────────┬───────┘
        │ Déclenchement             │ Déclenchement              │
        ▼                           ▼                            │
┌───────────────────────────┐ ┌───────────────────────────┐      │
│  AGENT 1 : WEB RESEARCH   │ │ AGENT 2 : SEMANTIC SCHOLAR│      │
│ Collecte Web & Veille TSP │ │ Papiers académiques & DOI │      │
└─────────────┬─────────────┘ └─────────────┬─────────────┘      │
              │ Données brutes filtrées     │ Papiers indexés    │
              └──────────────┬──────────────┘                    │
                             ▼                                   │
              ┌───────────────────────────┐                      │
              │  AGENT 3 : GEMINI ANALYST │                      │
              │ Analyse critique & Thèses │                      │
              └──────────────┬────────────┘                      │
                             │ Propositions structurées          │
                             ▼                                   │
              ┌───────────────────────────┐                      │
              │   AGENT 4 : JUDGE AGENT   │                      │
              │ Évaluation des preuves    │                      │
              │ ACCEPTED/REJECTED/REVIEW  │                      │
              └──────────────┬────────────┘                      │
                             │ Hypothèses numériques             │
                             ▼                                   │
              ┌───────────────────────────┐                      │
              │  AGENT 5 : VALIDATEUR     │                      │
              │  DÉTERMINISTE (PYTHON)    │                      │
              │ Calcul strict OSRM 41x41  │                      │
              └──────────────┬────────────┘                      │
                             │ Verdict mathématique certifié     │
                             ▼                                   │
              ┌───────────────────────────┐                      │
              │  COLLECTEUR & RAPPORT     │◄─────────────────────┘
              └──────────────┬────────────┘
                             │ Rapport Final Traçable
                             ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        UTILISATEUR / VALIDATION                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Rôle des six agents :

1. **Agent 1 — Web Research Agent :** Explore le web technique pour identifier les innovations récentes, les bibliothèques d'optimisation et les benchmarks récents sur le Last-Mile TSP.
2. **Agent 2 — Semantic Scholar Agent :** Interroge l'Academic Graph pour extraire des articles scientifiques avec métadonnées formelles (titres, auteurs, résumé, DOI, citations) sur l'ATSP et les métaheuristiques hybrides. Gère explicitement le mode anonyme (pool partagé soumis au throttling global) et le mode authentifié (`x-api-key`), avec backoff exponentiel et cache persistant SQLite.
3. **Agent 3 — Gemini Analyst (Moteur IA Configurable) :** Synthétise les données des deux premiers agents, évalue la faisabilité théorique, détecte les angles morts et émet des propositions d'amélioration concrètes. Moteur entièrement découplé du code métier via configuration externe (modèle économique configurable par défaut, ex. `gemini-3.8-flash`, et modèle haute capacité sur demande explicite, ex. `gemini-4-carbon`, avec possibilité d'abstraction multi-fournisseurs).
4. **Agent 4 — Judge Agent :** Analyse contradictoirement les affirmations de l'Analyste au regard des sources. Assigne un statut (`ACCEPTED`, `REJECTED`, `NEEDS_REVIEW`) et un score de confiance probatoire.
5. **Agent 5 — Deterministic Validator (Python) :** Valide toute proposition touchant au calcul numérique ou à l'ordonnancement en recalculant les coûts exacts sur la matrice OSRM 41x41 certifiée en LECTURE SEULE stricte. Dispose d'un veto mathématique absolu.
6. **Agent 6 — Central Orchestrator :** Reçoit l'instruction utilisateur, génère le plan d'exécution DAG, coordonne les appels, gère les pannes/timeouts, maintient la chaîne de hachage SHA-256 de l'audit trail (JSONL + SQLite) et agrège le rapport final.

---

## 3. Topologie d'Orchestration : Comparaison et Recommandation

Nous avons étudié trois architectures de coordination possibles :

### A. Architecture Purement Séquentielle (Pipeline linéaire)
- *Principe :* Web $\to$ Scholar $\to$ Analyst $\to$ Judge $\to$ Validator.
- *Avantages :* Simplicité de mise en œuvre, débogage aisé.
- *Inconvénients :* Temps d'exécution doublé car les requêtes réseau externes (Web et Semantic Scholar) ne sont pas parallélisées ; blocage complet si une étape amont ralentit.

### B. Architecture Purement Parallèle (Fan-out / Fan-in complet)
- *Principe :* L'orchestrateur lance tous les agents en même temps et tente de fusionner les résultats.
- *Avantages :* Vitesse maximale en théorie.
- *Inconvénients :* L'Analyste et le Juge ont besoin des résultats de recherche pour travailler ; le parallélisme total introduit une désynchronisation cognitive et augmente le risque d'hallucinations.

### C. Architecture Recommandée : Pipeline Hybride DAG (Directed Acyclic Graph Conditionnel)
- *Principe :*
  - **Étape 1 (Parallèle / Fan-out) :** Lancement simultané de l'Agent Web Research et de l'Agent Semantic Scholar.
  - **Étape 2 (Jointure) :** Agrégation des sources et transmission à l'Agent Gemini Analyst.
  - **Étape 3 (Analyse & Confrontation) :** Transmission de l'analyse et des sources à l'Agent Judge.
  - **Étape 4 (Validation Conditionnelle) :** Si et seulement si le Judge valide une proposition impliquant des calculs numériques, déclenchement du Validateur Déterministe Python.
  - **Étape 5 (Restitution) :** Synthèse finale consolidée et enregistrement du rapport d'audit.

> [!TIP]
> **Décision d'architecture :** AGADIR MAPPING adopte l'**Architecture Hybride DAG Conditionnelle**, qui allie la rapidité de la collecte parallèle à la rigueur de la chaîne d'arbitrage séquentielle.

---

## 4. Diagramme Mermaid Général de l'Architecture

```mermaid
graph TD
    classDef client fill:#f9f9f9,stroke:#333,stroke-width:2px;
    classDef orchestrator fill:#d1ecf1,stroke:#0c5460,stroke-width:2px;
    classDef research fill:#d4edda,stroke:#155724,stroke-width:2px;
    classDef llm fill:#fff3cd,stroke:#856404,stroke-width:2px;
    classDef deterministic fill:#f8d7da,stroke:#721c24,stroke-width:2px;
    classDef storage fill:#e2e3e5,stroke:#383d41,stroke-width:2px;

    User["Utilisateur / Interface Tkinter"]:::client
    Orch["Orchestrateur Central (Python)"]:::orchestrator
    
    subgraph Configuration_Externe ["Configuration Indépendante"]
        Conf["config/multi_agent_config.json<br>(Modèles, Toggles, Quotas)"]:::storage
    end

    subgraph Collecte_Parallele ["Phase 1 : Collecte Parallèle (Fan-out)"]
        WebAg["Web Research Agent<br>(DuckDuckGo / Crawling)"]:::research
        ScholAg["Semantic Scholar Agent<br>(Graph API + SQLite Cache + Backoff)"]:::research
    end
    
    subgraph Analyse_Arbitrage ["Phase 2 : Analyse et Jugement (Fan-in)"]
        GemAg["Gemini Analyst<br>(Moteur Configurable: Flash/Carbon/Pro)"]:::llm
        JudgeAg["Judge Agent<br>(Arbitre Épistémologique & Contradictoire)"]:::llm
    end
    
    subgraph Verification_Stricte ["Phase 3 : Vérification Mathématique (Veto)"]
        ValDet["Validateur Déterministe<br>(Code Python Pur - 0 LLM)"]:::deterministic
    end

    subgraph Stockage_Et_Donnees ["Données Certifiées (READ-ONLY)"]
        OSRM["Matrice OSRM 41x41<br>(distance_matrix.csv)"]:::storage
        Points["40 Destinations + Dépôt<br>(delivery_points_40.csv)"]:::storage
        RefTour["Tournée Officielle<br>(18 933,1 m)"]:::storage
    end

    subgraph Tracabilite_Audit ["Audit Trail Inviolable"]
        AuditChain["Journal Audit JSONL + SQLite<br>(Chaîne de hachage SHA-256)"]:::storage
    end

    Conf -.->|Paramètres & Quotas| Orch
    User -->|Mission de recherche| Orch
    Orch -->|Fan-out parallèle| WebAg
    Orch -->|Fan-out parallèle| ScholAg
    
    WebAg -->|Sources web isolées &lt;untrusted&gt;| GemAg
    ScholAg -->|Articles scientifiques &amp; DOI vérifiés| GemAg
    
    GemAg -->|Rapport d'analyse structuré| JudgeAg
    WebAg -.->|Preuves brutes| JudgeAg
    ScholAg -.->|Preuves brutes| JudgeAg
    
    JudgeAg -->|Hypothèses numériques à vérifier| ValDet
    ValDet -->|Accès strict en LECTURE SEULE| OSRM
    ValDet -->|Accès strict en LECTURE SEULE| Points
    ValDet -->|Accès strict en LECTURE SEULE| RefTour
    
    ValDet -->|Verdict déterministe certifié| Orch
    JudgeAg -->|Décision formelle ACCEPTED/REJECTED| Orch
    
    Orch -->|Événements & Hashes chaînés| AuditChain
    Orch -->|Rapport final probatoire| User
```

---

## 5. Diagramme Mermaid du Flux de Communication et d'Arbitrage

```mermaid
sequenceDiagram
    autonumber
    actor U as Utilisateur / CLI
    participant O as Orchestrateur Central
    participant W as Web Research Agent
    participant S as Semantic Scholar Agent
    participant G as Gemini Analyst
    participant J as Judge Agent
    participant V as Validateur Déterministe (Python)
    
    U->>O: Soumission d'une mission (ex: "Intégration d'un 3-opt asymétrique")
    activate O
    
    Note over O: Étape 1 : Collecte Parallèle
    par Requête Web
        O->>W: AgentRequest(task_type="web_search", query="ATSP 3-opt local search")
        activate W
        W-->>O: AgentResponse(sources=[...], status="SUCCESS")
        deactivate W
    and Requête Académique
        O->>S: AgentRequest(task_type="scholar_search", query="asymmetric TSP 3-opt")
        activate S
        S-->>O: AgentResponse(papers=[...], status="SUCCESS")
        deactivate S
    end
    
    Note over O: Étape 2 : Analyse Critique
    O->>G: AgentRequest(task_type="analyze", context={web: ..., scholar: ...})
    activate G
    G-->>O: AgentResponse(proposals=[...], critiques=[...])
    deactivate G
    
    Note over O: Étape 3 : Arbitrage Contradictoire
    O->>J: AgentRequest(task_type="judge", evidence={sources, papers, proposals})
    activate J
    Note over J: Vérification des citations,<br>évaluation probatoire
    J-->>O: JudgeDecision(status="ACCEPTED_PENDING_VALIDATION", claims=[...])
    deactivate J
    
    Note over O: Étape 4 : Validation Déterministe Python
    alt Présence de propositions algorithmiques ou numériques
        O->>V: ValidationRequest(matrix="OSRM 41x41", tour=candidate_tour)
        activate V
        Note over V: Calcul strict sans LLM<br>Vérification 42 arrêts, 0 doublon
        V-->>O: ValidationResult(is_valid=True, exact_cost_m=18933.1)
        deactivate V
    end
    
    Note over O: Étape 5 : Synthèse et Traçabilité
    O-->>U: FinalReport(decision="ACCEPTED", gain_m=..., audit_trail=...)
    deactivate O
```

---

## 6. Cycle de Vie et États d'une Mission Multi-Agents

Toute mission gérée par l'Orchestrateur suit une machine à états finis stricte :

```text
[INITIATED] 
    │
    ▼
[RESEARCHING] ──(Timeout / Erreur)──► [RETRYING_RESEARCH] ──► [FAILED_RESEARCH]
    │                                                                  │
    ▼ (Succès Web & Scholar)                                           ▼
[ANALYZING] ────────────────────────► [ANALYSIS_ERROR] ───────► [ABORTED]
    │
    ▼ (Succès Analyste)
[JUDGING] ──────────────────────────► [REJECTED] ─────────────► [COMPLETED_WITH_REJECTION]
    │
    ▼ (Acceptation sous condition)
[VALIDATING] ───────────────────────► [MATH_VIOLATION] ───────► [REJECTED_UNFEASIBLE]
    │
    ▼ (Validation mathématique 100%)
[CONSOLIDATING] 
    │
    ▼
[COMPLETED_SUCCESS]
```

Cette structure garantit qu'aucune conclusion erronée ou non prouvée ne puisse atteindre l'utilisateur.
