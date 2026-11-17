# RAPPORT OFFICIEL — PHASE 6.1
## Document 6 : Protocoles de Communication et Modèles de Données
**Projet :** AGADIR MAPPING — Last Mile TSP Optimization  
**Date d'audit :** 16/11/2026  
**Auteur :** Antigravity (Google DeepMind Team)  
**Classification :** Spécification Technique & Conception Système  

---

## 1. Principes du Protocole de Communication

Le système multi-agents d'AGADIR MAPPING repose sur un protocole d'échange de messages **asynchrone ou synchrone typé**, modélisé en **Pydantic v2**. 

Chaque interaction est caractérisée par :
1. **Un identifiant de mission unique (`mission_id`) :** Permet la corrélation de bout en bout de tous les messages.
2. **Un identifiant de requête (`request_id`) et un horodatage UTC strict.**
3. **Une immutabilité des messages transmis :** Les agents ne modifient jamais les objets reçus, ils génèrent de nouveaux messages de réponse.
4. **Des statuts d'exécution explicites :** `PENDING`, `IN_PROGRESS`, `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `TIMEOUT`.

---

## 2. Modèles de Données Normalisés (Schémas Pydantic / JSON)

### 2.1. `AgentRequest` (Enveloppe de Requête Standard)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "AgentRequest",
  "type": "object",
  "properties": {
    "mission_id": { "type": "string", "description": "Identifiant global de la mission" },
    "request_id": { "type": "string", "description": "Identifiant unique de la requête" },
    "sender_agent_id": { "type": "string", "description": "Agent émetteur (ex: central_orchestrator)" },
    "target_agent_id": { "type": "string", "description": "Agent destinataire (ex: web_research_agent)" },
    "task_type": { "type": "string", "enum": ["web_search", "scholar_search", "analyze", "judge", "validate"] },
    "payload": { "type": "object", "description": "Données spécifiques à la tâche" },
    "timeout_seconds": { "type": "number", "default": 30.0 },
    "created_at_utc": { "type": "string", "format": "date-time" }
  },
  "required": ["mission_id", "request_id", "sender_agent_id", "target_agent_id", "task_type", "payload", "created_at_utc"]
}
```

### 2.2. `AgentResponse` (Enveloppe de Réponse Standard)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "AgentResponse",
  "type": "object",
  "properties": {
    "mission_id": { "type": "string" },
    "request_id": { "type": "string" },
    "responder_agent_id": { "type": "string" },
    "status": { "type": "string", "enum": ["SUCCESS", "PARTIAL_SUCCESS", "FAILED", "TIMEOUT"] },
    "data": { "type": "object", "description": "Données résultantes structurées" },
    "error_message": { "type": ["string", "null"] },
    "execution_time_seconds": { "type": "number" },
    "completed_at_utc": { "type": "string", "format": "date-time" }
  },
  "required": ["mission_id", "request_id", "responder_agent_id", "status", "data", "execution_time_seconds", "completed_at_utc"]
}
```

### 2.3. `ResearchSource` (Source Web Unitaire)
```json
{
  "title": "ResearchSource",
  "type": "object",
  "properties": {
    "source_id": { "type": "string" },
    "url": { "type": "string", "format": "uri" },
    "title": { "type": "string" },
    "snippet": { "type": "string" },
    "domain": { "type": "string" },
    "reputation_level": { "type": "string", "enum": ["HIGH", "MEDIUM", "LOW", "UNVERIFIED"] },
    "published_year": { "type": ["integer", "null"] },
    "retrieved_at_utc": { "type": "string", "format": "date-time" }
  },
  "required": ["source_id", "url", "title", "snippet", "domain", "reputation_level", "retrieved_at_utc"]
}
```

### 2.4. `ScientificPaper` (Article Académique Unitaire)
```json
{
  "title": "ScientificPaper",
  "type": "object",
  "properties": {
    "paper_id": { "type": "string" },
    "doi": { "type": ["string", "null"] },
    "title": { "type": "string" },
    "authors": { "type": "array", "items": { "type": "string" } },
    "year": { "type": "integer" },
    "venue": { "type": ["string", "null"] },
    "citation_count": { "type": "integer", "minimum": 0 },
    "abstract": { "type": "string" },
    "open_access_pdf_url": { "type": ["string", "null"] }
  },
  "required": ["paper_id", "title", "authors", "year", "citation_count", "abstract"]
}
```

### 2.5. `AnalysisReport` (Synthèse Émise par Gemini Analyst)
```json
{
  "title": "AnalysisReport",
  "type": "object",
  "properties": {
    "analysis_id": { "type": "string" },
    "model_name": { "type": "string" },
    "theses": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "thesis_id": { "type": "string" },
          "hypothesis": { "type": "string" },
          "scientific_rationale": { "type": "string" },
          "cited_papers": { "type": "array", "items": { "type": "string" } },
          "cited_web_sources": { "type": "array", "items": { "type": "string" } },
          "proposed_action": { "type": "string" },
          "requires_deterministic_validation": { "type": "boolean" },
          "candidate_permutation": { "type": ["array", "null"], "items": { "type": "integer" } }
        },
        "required": ["thesis_id", "hypothesis", "scientific_rationale", "requires_deterministic_validation"]
      }
    },
    "general_critique": { "type": "string" },
    "token_usage": {
      "type": "object",
      "properties": {
        "prompt_tokens": { "type": "integer" },
        "completion_tokens": { "type": "integer" },
        "thinking_tokens": { "type": "integer", "default": 0 },
        "cached_tokens": { "type": "integer", "default": 0 },
        "estimated_cost_usd": { "type": "number" }
      },
      "required": ["prompt_tokens", "completion_tokens", "estimated_cost_usd"]
    }
  },
  "required": ["analysis_id", "model_name", "theses", "general_critique", "token_usage"]
}
```

### 2.6. `JudgeDecision` (Verdict de l'Arbitre)
```json
{
  "title": "JudgeDecision",
  "type": "object",
  "properties": {
    "decision_id": { "type": "string" },
    "overall_verdict": { "type": "string", "enum": ["ACCEPTED", "REJECTED", "NEEDS_REVIEW", "ACCEPTED_PENDING_VALIDATION"] },
    "evaluations": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "thesis_id": { "type": "string" },
          "status": { "type": "string", "enum": ["ACCEPTED", "REJECTED", "NEEDS_REVIEW"] },
          "confidence_score": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
          "justification": { "type": "string" },
          "contradictions_found": { "type": "array", "items": { "type": "string" } }
        },
        "required": ["thesis_id", "status", "confidence_score", "justification"]
      }
    },
    "audit_notes": { "type": "string" }
  },
  "required": ["decision_id", "overall_verdict", "evaluations"]
}
```

### 2.7. `ValidationResult` (Preuve Mathématique Déterministe)
```json
{
  "title": "ValidationResult",
  "type": "object",
  "properties": {
    "validation_id": { "type": "string" },
    "is_valid": { "type": "boolean" },
    "reference_distance_m": { "type": "number" },
    "candidate_distance_m": { "type": "number" },
    "gain_m": { "type": "number" },
    "gain_pct": { "type": "number" },
    "constraints_check": {
      "type": "object",
      "properties": {
        "starts_at_depot_0": { "type": "boolean" },
        "ends_at_depot_0": { "type": "boolean" },
        "coastal_point_40_present": { "type": "boolean" },
        "total_stops_count": { "type": "integer" },
        "unique_destinations_count": { "type": "integer" },
        "has_duplicates": { "type": "boolean" }
      },
      "required": ["starts_at_depot_0", "ends_at_depot_0", "coastal_point_40_present", "total_stops_count", "unique_destinations_count", "has_duplicates"]
    },
    "verified_on_matrix": { "type": "string", "default": "distance_matrix.csv" },
    "timestamp_utc": { "type": "string", "format": "date-time" }
  },
  "required": ["validation_id", "is_valid", "reference_distance_m", "candidate_distance_m", "gain_m", "constraints_check", "timestamp_utc"]
}
```

### 2.8. `FinalReport` (Livrable Consolidé de Mission)
```json
{
  "title": "FinalReport",
  "type": "object",
  "properties": {
    "mission_id": { "type": "string" },
    "topic": { "type": "string" },
    "execution_mode": { "type": "string", "enum": ["ECONOMIC", "COMPLETE", "OFFLINE_CACHE"] },
    "executive_summary": { "type": "string" },
    "web_sources_consulted": { "type": "integer" },
    "papers_analyzed": { "type": "integer" },
    "theses_evaluated": { "type": "integer" },
    "judge_verdict": { "type": "string" },
    "deterministic_validation": { "type": ["object", "null"] },
    "total_execution_time_seconds": { "type": "number" },
    "total_estimated_cost_usd": { "type": "number" },
    "audit_trail_path": { "type": "string" },
    "audit_chain_length": { "type": "integer" },
    "final_audit_hash": { "type": "string", "pattern": "^[a-f0-9]{64}$" }
  },
  "required": ["mission_id", "topic", "execution_mode", "executive_summary", "judge_verdict", "total_execution_time_seconds", "final_audit_hash"]
}
```

### 2.9. `AuditEventRecord` (Enregistrement Scellé de la Chaîne d'Audit)
```json
{
  "title": "AuditEventRecord",
  "type": "object",
  "properties": {
    "event_index": { "type": "integer", "minimum": 0 },
    "event_id": { "type": "string" },
    "mission_id": { "type": "string" },
    "timestamp_utc": { "type": "string", "format": "date-time" },
    "agent_id": { "type": "string" },
    "action": { "type": "string" },
    "payload_summary": { "type": "object" },
    "prev_hash": { "type": "string", "pattern": "^[a-f0-9]{64}$" },
    "event_hash": { "type": "string", "pattern": "^[a-f0-9]{64}$" }
  },
  "required": ["event_index", "event_id", "mission_id", "timestamp_utc", "agent_id", "action", "prev_hash", "event_hash"]
}
```

> [!IMPORTANT]
> **Règle de Calcul du Hachage Canonique :**  
> `event_hash` est calculé par `SHA256(canonical_json(record_sans_event_hash))` où le dictionnaire sérialisé inclut obligatoirement `prev_hash` (les 64 zéros `"0"*64` pour l'index 0) et exclut formellement `event_hash`. L'empreinte finale de mission est conservée séparément dans `outputs/audit/mission_fingerprints.json` pour détecter toute troncature de fin de journal.

---

## 3. Gestion des Erreurs et Stratégies de Reprise

### Tableau des Codes d'Erreurs Normalisés :

| Code d'Erreur | Cause Déclenchante | Stratégie de Résolution Automatique |
| :--- | :--- | :--- |
| `ERR_NETWORK_TIMEOUT` | Expiration du délai réseau (15 s) | 2 réessais avec backoff exponentiel (1 s puis 2 s), puis bascule sur cache. |
| `ERR_API_RATE_LIMIT_429` | Quota dépassé (Semantic Scholar / Gemini) | Pause automatique de 2 s avec jitter aléatoire (50-200 ms), puis bascule mock/cache. |
| `ERR_PROMPT_INJECTION` | Mots suspects d'injection détectés dans la source | Rejet immédiat de la source sans la transmettre à l'Analyste. |
| `ERR_SCHEMA_VALIDATION` | Réponse JSON non conforme au modèle Pydantic | Requête de correction envoyée au modèle LLM ou rejet du résultat. |
| `ERR_CONSTRAINT_VIOLATION`| Violation d'une contrainte TSP (ex: doublon) | Rejet catégorique par le Validateur Déterministe. |

### Algorithme de Reprise (Exponential Backoff with Jitter) :
$$\text{Délai} = \min\left(\text{MaxDelay}, \text{BaseDelay} \times 2^{\text{tentative}}\right) + \text{Uniform}(0, 0.2)$$
Ce mécanisme évite d'engorger les APIs externes en cas de congestion temporaire.
