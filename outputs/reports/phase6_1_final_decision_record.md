# RAPPORT OFFICIEL — PHASE 6.1 (ACTUALISÉ ET FINALISÉ)
## Document 9 : Registre des Décisions d'Architecture (Architecture Decision Record - ADR)
**Projet :** AGADIR MAPPING — Last Mile TSP Optimization  
**Sous-phase :** 6.1 — Spécification et Conception du Système Multi-Agents IA  
**Date :** 16/11/2026  
**Auteur :** Antigravity (Google DeepMind Team)  
**Statut :** VALIDÉ AVEC ADDENDUM FINAL DE PRÉ-IMPLÉMENTATION  

---

## 1. CONTEXTE ET HISTORIQUE DU PROJET

Le projet AGADIR MAPPING dispose d'un socle algorithmique et géographique intégralement validé lors des Phases 1 à 5 :
- **40 destinations réelles de livraison** à Agadir + **1 dépôt central (#0 — Place Al Amal)**.
- **Matrices routières OSRM réelles** de distances ($41 \times 41$) et de durées ($41 \times 41$), asymétriques et non modifiables.
- **Tournée officielle certifiée de référence** :
  $$\text{Tournée} = [0, 36, 13, 30, 21, 6, 33, 27, 25, 26, 7, 9, 38, 3, 10, 11, 17, 28, 37, 2, 14, 12, 5, 35, 16, 22, 39, 8, 1, 19, 20, 32, 40, 24, 29, 4, 23, 31, 15, 18, 34, 0]$$
  $$\text{Distance certifiée} = \mathbf{18\,933{,}1\text{ mètres}}$$
- Suite de **29 tests de régression automatisés `pytest`** validée à 100%.

La Phase 6.1 vise à concevoir l'architecture technique d'un système multi-agents IA dédié à la recherche, l'analyse contradictoire et la validation d'hypothèses d'amélioration, sans jamais compromettre l'intégrité de la solution acquise.

---

## 2. LES TROIS ARBITRAGES FONDAMENTAUX VALIDÉS

### Arbitrage 1 : Modèle Rapide et Économique par Défaut, Modèle Avancé sur Demande
- **Décision :** Utilisation d'un modèle d'inférence rapide, léger et économique pour l'ensemble des tâches courantes d'agrégation et de filtrage.
- **Activation conditionnelle :** Réservation des modèles à haute capacité de raisonnement et fenêtres étendues uniquement aux requêtes critiques nécessitant une analyse mathématique lourde, et **sur demande explicite**.
- **Agnosticisme :** Les identifiants de modèles sont totalement découplés du code applicatif et gérés dans un fichier de configuration externe, permettant une migration transparente vers de futurs modèles ou d'autres fournisseurs via l'interface `BaseLLMProvider`.

### Arbitrage 2 : Résilience Réseau et Mode Hors-Ligne (Fallback Local)
- **Décision :** Mise en œuvre d'une architecture de repli à base de bases SQLite locales persistantes (`data/agents_cache/`).
- **Validation hors-ligne :** Capacité d'exécuter des missions de test complètes et la suite d'intégration continue `pytest` sans aucune connectivité Internet (`BypassSandbox: false`), en s'appuyant sur les données en cache et des simulations contrôlées.

### Arbitrage 3 : Audit Trail Hybride Sécurisé (JSONL + SQLite)
- **Décision :** Double persistance des événements opérationnels :
  1. Flux séquentiel append-only en JSON Lines (`outputs/audit/mission_{id}.jsonl`).
  2. Base relationnelle SQLite (`outputs/audit/orchestrator_audit.db`) pour l'indexation, le requêtage rapide et les tableaux de bord.
- **Scellement cryptographique :** Intégration obligatoire d'une chaîne de hachage SHA-256 liant chaque événement à son prédécesseur.

---

## 3. RELEVÉ DÉTAILLÉ DES CORRECTIONS TECHNIQUES APPORTÉES

Le tableau suivant récapitule les 5 axes de corrections techniques validés :

| Domaine | État Antérieur | Correction et État Cible Actualisé | Documents Modifiés |
| :--- | :--- | :--- | :--- |
| **1. Tarification Gemini & Thinking Tokens** | Tarifs obsolètes ou fictifs ($0.15/$0.60) ; pas de prise en compte du raisonnement. | Tarifs officiels Developer API en vigueur fin 2026 : `gemini-3.8-flash` ($0.75/$3.75) et `gemini-4-carbon` ($2.00/$10.00). Inclusion explicite des tokens de réflexion (*thinking*) au tarif output. Non-pérennité des tarifs, vérification pré-mission et blocage préventif si non vérifiables. | `phase6_1_api_and_cost_analysis.md`<br/>`phase6_1_agent_specifications.md`<br/>`phase6_1_acceptance_criteria.md` |
| **2. Quota Semantic Scholar** | Présenté comme un quota fixe ou non contesté de 1 req/s universel. | 1 req/s clarifié comme quota introductif documenté pour clé API, sans garantie permanente ni immunité contre la congestion. Configuration adaptable du rythme, backoff exponentiel adaptatif sur HTTP 429 et requêtes batch. | `phase6_1_agent_specifications.md`<br/>`phase6_1_api_and_cost_analysis.md`<br/>`phase6_1_acceptance_criteria.md` |
| **3. Audit Trail SHA-256 & Détection Falsification** | Présenté abusivement comme "inviolable" sans spécification stricte du hachage. | Remplacé par "falsification-détectable" (*tamper-evident*). Définition précise : sérialisation canonique ordonnée incluant `prev_hash` et excluant strictement `event_hash`. Détection d'altération, suppression, insertion, réordonnancement et détection de troncature par conservation externe du `final_event_hash`. Limites formellement documentées face à un administrateur système root. | `phase6_1_security_and_data_protection.md`<br/>`phase6_1_communication_protocols.md`<br/>`phase6_1_acceptance_criteria.md` |
| **4. Isolation POSIX et Système** | Permissions déclaratives théoriques sans séparation d'identités. | Séparation des identités de service : UID 1001 (`agadir_orchestrator`) vs UID 1002 (`agadir_agent_worker`). Privilèges administrateur (`sudo`, `setuid`) interdits, `no_new_privs = 1`. Lecture seule imposée au niveau OS (`0444`/`0555` et montage bind `ro`). Écritures confinées aux répertoires autorisés Phase 6. Contrôle SHA-256 au démarrage/clôture. | `phase6_1_security_and_data_protection.md`<br/>`phase6_1_acceptance_criteria.md` |
| **5. Disjoncteur Financier à Réservation Préalable** | Contrôle financier a posteriori après consommation. | Ajout d'une réservation préalable du budget pire-cas avant émission réseau : rejet immédiat si $\text{Coût}_{\text{cumulé}} + \text{Coût}_{\text{réservé}} > 0{,}50\text{ USD}$. Politique *Fail-Closed* : blocage préventif en cas de tarif non vérifié, de modèle inconnu ou de métadonnées de consommation absentes. | `phase6_1_api_and_cost_analysis.md`<br/>`phase6_1_acceptance_criteria.md` |

---

## 4. RÉFÉRENCES OFFICIELLES CONSULTÉES

1. **Google Gemini Developer API Documentation (ai.google.dev / cloud.google.com) :**
   - *Model Lifecycle & Deprecations* : Confirmation de la fin de vie des modèles `gemini-2.5` en octobre 2026.
   - *Pricing & Token Usage* : Barèmes officiels en vigueur pour `gemini-3.8-flash` ($0.75/$3.75) et `gemini-4-carbon` ($2.00/$10.00). Règle de facturation des tokens de réflexion (*thinking tokens*) au plein tarif de sortie (*output*).
   - *Context Caching & Batch API* : Réductions applicables sur les lectures de cache et les requêtes asynchrones par lots.
2. **Semantic Scholar API Documentation (api.semanticscholar.org) :**
   - *Rate Limits & Partner Access* : Distinction entre le pool mondial anonyme mutualisé (~1 000 req/s mondial) et le quota introductif documenté d'une clé API (1 req/s de base).
   - *Batch Endpoints* : Spécification de `POST /graph/v1/paper/batch` pour le traitement groupé de 500 documents.
3. **Standards Cryptographiques et POSIX :**
   - *NIST FIPS 180-4* (Secure Hash Standard - SHA-256).
   - *RFC 8785* (JSON Canonicalization Scheme - JCS) pour la reproductibilité déterministe des empreintes JSON.
   - *POSIX.1-2017* et Linux Security Architecture (`prctl(PR_SET_NO_NEW_PRIVS)`).

---

## 5. MODÈLES CONFIGURABLES ET FICHIER DÉCOUPLÉ

La configuration complète est isolée dans `config/multi_agent_config.json` :
```json
{
  "system_version": "6.1.1",
  "llm_provider": {
    "type": "google_genai",
    "api_key_env_var": "GEMINI_API_KEY",
    "timeout_seconds": 30
  },
  "models": {
    "default_fast": "gemini-3.8-flash",
    "advanced_reasoning": "gemini-4-carbon",
    "fallback": "gemini-3.8-flash"
  },
  "pricing_per_million_tokens": {
    "gemini-3.8-flash": { "input": 0.75, "output": 3.75, "cached": 0.075 },
    "gemini-4-carbon": { "input": 2.00, "output": 10.00, "cached": 0.10 }
  },
  "semantic_scholar": {
    "api_endpoint": "https://api.semanticscholar.org/graph/v1",
    "api_key_env_var": "SEMANTIC_SCHOLAR_API_KEY",
    "max_retries": 3,
    "backoff_base_seconds": 2.0,
    "rate_limit_delay_seconds": 1.1
  },
  "budget_guardrails": {
    "warning_threshold_usd": 0.10,
    "kill_switch_usd": 0.50,
    "pre_allocation_check": true,
    "fail_closed_if_unverified": true
  }
}
```

---

## 6. LIMITES CONNUES DU SYSTÈME

1. **Frontière du Modèle de Menace Administrateur :**  
   La chaîne de hachage SHA-256 garantit la détection infaillible de toute altération accidentelle, corruption réseau, ou tentative de modification émanant d'un processus non privilégié ou d'un agent IA. **Cependant, elle ne doit jamais être qualifiée d'inviolable :** un utilisateur ou attaquant disposant de privilèges administrateur complets sur le système d'exploitation (`root` / `wheel`) conserve la capacité physique de modifier simultanément les fichiers journaux, le hash final externe et de recalculer une chaîne cohérente.
2. **Volatilité et Régulation Dynamique de Semantic Scholar :**  
   Même avec une clé API et un quota introductif de 1 req/s, le service peut réguler dynamiquement son trafic et renvoyer des réponses `HTTP 429` en période de congestion mondiale de l'infrastructure AI2.
3. **Non-Pérennité Contractuelle des Offres Fournisseurs :**  
   Les tarifs d'API et les quotas gratuits ne sont jamais garantis de manière permanente et peuvent évoluer unilatéralement.

---

## 7. RISQUES RÉSIDUELS ET STRATÉGIES D'ATTÉNUATION

| Risque Résiduel | Probabilité | Impact | Stratégie d'Atténuation Validée |
| :--- | :---: | :---: | :--- |
| **Modification unilatérale des tarifs API** | Moyenne | Faible | Vérification obligatoire avant chaque mission et politique *Fail-Closed* bloquante. |
| **Poussée de charge sur Semantic Scholar** | Moyenne | Faible | Backoff exponentiel adaptatif avec jitter, requêtes par lots batch et cache SQLite persistant. |
| **Dépassement de budget en cours de requête** | Faible | Moyen | Réservation préalable du budget pire-cas calculée avant chaque appel. |
| **Troncature de journal par un attaquant** | Faible | Moyen | Conservation externe du `final_event_hash` dans `outputs/audit/mission_fingerprints.json`. |
| **Tentative d'altération de la tournée officielle** | Élevée (LLM) | Nul | Veto absolu du Validateur Déterministe Python sur la matrice OSRM en lecture seule. |

---

## 8. DÉCISIONS RESTANT À PRENDRE LORS DE LA PHASE 6.2

Les points suivants devront être arbitrés lors du développement du socle :
1. **Souscription d'une clé Semantic Scholar Partenaire :** Décision de déployer avec le pool anonyme + backoff ou de fournir une clé individuelle dès le premier test réseau.
2. **Déploiement de l'Ancrage Distant (Optionnel) :** Décision d'activer la réplication des hashes d'audit vers un bucket distant en écriture unique (WORM) ou un commit Git signé.
3. **Validation Humaine Obligatoire :** Autorisation formelle, distincte et explicite pour engager le codage de la Phase 6.2.

---

## 9. ENGAGEMENT DE CONFORMITÉ ET RESTRICTIONS

Le présent document atteste formellement que :
- **Aucune ligne de code d'agent n'a été rédigée.**
- **Aucun module n'a été créé dans `src/multi_agent/`.**
- **Aucun fichier de données ni aucun code des Phases 1 à 5 n'a été modifié.**
- **La tournée de référence certifiée de 18 933,1 mètres demeure strictement inchangée.**
- **Les 29 tests de régression `pytest` demeurent 100% verts.**
- **Les travaux sont arrêtés et aucune implémentation de la Phase 6.2 n'est engagée sans autorisation explicite.**
