# RAPPORT OFFICIEL — PHASE 6.1 (REVU ET SÉCURISÉ)
## Document 5 : Sécurité Système, Isolation POSIX, Audit Trail Cryptographique et Détection de Falsification
**Projet :** AGADIR MAPPING — Last Mile TSP Optimization  
**Date de révision :** 16/11/2026  
**Auteur :** Antigravity (Google DeepMind Team)  
**Classification :** Spécification Technique & Conception Système  

---

## 1. Principes Directeurs de Sécurité

Dans une architecture multi-agents combinant des flux web externes non fiables, des inférences LLM et des calculs combinatoires critiques, la sécurité repose sur quatre piliers techniques :
1. **Isolation Granulaire et Imposée au Niveau Système :** Séparation des identités de processus et accès en lecture seule physiquement imposé au niveau OS sur les données des Phases 1 à 5.
2. **Défense en Profondeur contre l'Injection de Prompt :** Confinement hermétique des données externes (*Untrusted Input*) dans des balises XML imperméables.
3. **Piste d'Audit Cryptographiquement Chaînée (*Tamper-Evident*) :** Scellement de chaque événement par hachage SHA-256 canonique permettant de détecter formellement toute falsification (altération, insertion, suppression, réordonnancement ou troncature).
4. **Validation Humaine Obligatoire :** Aucune donnée de référence ni aucune tournée certifiée ne peut être modifiée par les agents ou l'orchestrateur.

---

## 2. Spécifications d'Isolation POSIX et Permissions Système

Pour garantir que l'intégrité des données ne dépende pas uniquement de la bonne volonté du code Python, des barrières strictes sont imposées au niveau du système d'exploitation :

```
┌────────────────────────────────────────────────────────────────────────┐
│               ENVIRONNEMENT SYSTÈME & IDENTITÉS POSIX                  │
├───────────────────────────────────┬────────────────────────────────────┤
│ Service Orchestrateur             │ Processus Agents & Workers         │
│ UID: 1001 (agadir_orchestrator)   │ UID: 1002 (agadir_agent_worker)    │
│ GID: 1001 (agadir_group)          │ GID: 1001 (agadir_group)           │
│ Privilèges admin: INTERDIT        │ Privilèges admin: INTERDIT         │
│ no_new_privs = 1                  │ no_new_privs = 1                   │
└───────────────────────────────────┴────────────────────────────────────┘
```

### 2.1. Séparation des Identités Système
- L'Orchestrateur et les Agents exécutent leurs tâches sous des comptes de service distincts non privilégiés (`agadir_orchestrator` et `agadir_agent_worker`).
- **Interdiction absolue des privilèges administrateur :** Aucun accès `sudo`, exclusion de tout binaire à bit `setuid`/`setgid`, et verrouillage du drapeau noyau `no_new_privs` interdisant toute escalade de privilèges. Toutes les capacités Linux sensibles (ex. `CAP_DAC_OVERRIDE`, `CAP_SYS_ADMIN`) sont retirées.

### 2.2. Accès en Lecture Seule Imposé au Niveau Système sur les Données Certifiées
L'inviolabilité des données des Phases 1 à 5 repose sur deux mécanismes complémentaires :
1. **Propriété Système et Permissions Stricte :**  
   Les répertoires `data/processed/`, `src/genetic_algorithm/`, `src/optimization/`, `src/routing/` sont détenus par un utilisateur système distinct (ex. `root` ou `agadir_admin`), avec les permissions :
   - Fichiers de données : mode `0444` (`-r--r--r--`).
   - Répertoires : mode `0555` (`dr-xr-xr-x`).
   Ni l'Orchestrateur (UID 1001) ni les Agents (UID 1002) ne disposent du droit d'écriture au niveau système de fichiers.
2. **Montage en Lecture Seule (*Read-Only Bind Mount*) :**  
   En environnement conteneurisé ou de production, le dossier `data/processed/` est monté avec l'option explicite `ro` (`mount -o ro,bind data/processed /workspace/data/processed`), rendant toute tentative d'écriture physiquement rejetée par le noyau du système d'exploitation (`EROFS : Read-only file system`).
3. **Confinement des Écritures :**  
   Les processus du système multi-agents disposent de droits d'écriture **exclusivement** dans les sous-répertoires de travail de la Phase 6 :
   - `outputs/audit/` : Écriture de l'audit trail et des empreintes cryptographiques.
   - `outputs/reports/` : Écriture des rapports Markdown d'analyse.
   - `data/agents_output/` : Écriture des résultats JSON structurés.
   - `data/agents_cache/` : Écriture des bases locales SQLite de cache.

### 2.3. Empreintes SHA-256 Pré- et Post-Mission
Au lancement et à l'arrêt de toute mission, l'Orchestrateur recalcule l'empreinte SHA-256 de chaque fichier protégé :
- `data/processed/delivery_points_40.csv`
- `data/processed/distance_matrix.csv`
- `data/processed/duration_matrix.csv`
- `data/results/tsp_optimized_route.json`  
Si une quelconque divergence est détectée, le système déclenche un arrêt d'urgence immédiat (*Panic Stop*).

---

## 3. Audit Trail Cryptographique et Détection de Falsification

Pour garantir une traçabilité rigoureuse sans prétendre à une inviolabilité absolue, le système met en œuvre une **chaîne d'audit à intégrité vérifiable** basée sur SHA-256.

### 3.1. Spécification Formelle du Hachage Canonique
Chaque événement d'audit consigné dans `outputs/audit/mission_{id}.jsonl` est un objet JSON strict.

```
+--------------------+        +--------------------+        +--------------------+
|  Événement #0      |        |  Événement #1      |        |  Événement #2      |
|  (Bloc Genèse)     |        |                    |        |                    |
|  prev_hash: "0"*64 |        |  prev_hash: H_0    |        |  prev_hash: H_1    |
|  Payload Canonique |        |  Payload Canonique |        |  Payload Canonique |
|  event_hash: H_0   | -----> |  event_hash: H_1   | -----> |  event_hash: H_2   |
+--------------------+        +--------------------+        +--------------------+
```

#### Définition Précise des Champs Inclus dans le Contenu Canonique :
Pour calculer l'empreinte d'un événement, on construit un sous-ensemble contenant **strictement** les champs suivants :
1. `event_index` : Entier séquentiel strictement monotone ($0, 1, 2, \dots$).
2. `event_id` : Chaîne UUIDv4 unique.
3. `mission_id` : Chaîne identifiant la mission.
4. `timestamp_utc` : Horodatage ISO-8601 UTC précis à la milliseconde.
5. `agent_id` : Identifiant de l'agent émetteur.
6. `action` : Nom normalisé de l'action exécutée.
7. `payload_summary` : Dictionnaire contenant les paramètres d'entrée/sortie de l'action.
8. `prev_hash` : Chaîne hexadécimale de 64 caractères contenant le hash de l'événement précédent (pour $i=0$, `prev_hash = "0" * 64`).

> [!IMPORTANT]
> **Règle d'Exclusion Stricte :** Le champ **`event_hash` est rigoureusement exclu** du contenu canonique à hacher, car il constitue précisément le résultat du hachage de ce contenu.

#### Algorithme de Sérialisation et de Hachage :
1. Les clés du dictionnaire canonique (incluant `prev_hash`) sont ordonnées alphabétiquement.
2. Les séparateurs superflus sont supprimés :
   $$\text{canonical\_bytes} = \text{json.dumps}(\text{event\_dict\_sans\_event\_hash}, \text{sort\_keys}=\text{True}, \text{separators}=(',', ':')).\text{encode}('utf-8')$$
3. Le hash est calculé par :
   $$\text{event\_hash} = \text{SHA256}(\text{canonical\_bytes}).\text{hexdigest}()$$

### 3.2. Capacités de Détection de Falsification
L'algorithme de contrôle détecte mathématiquement l'ensemble des anomalies suivantes :
1. **Événement Modifié :** Toute altération d'un caractère modifie son hash canonique, qui ne correspond plus à l'`event_hash` stocké, et invalide le `prev_hash` de l'événement suivant.
2. **Événement Supprimé :** Si l'événement $k$ est retiré, le `prev_hash` de l'événement $k+1$ ne correspondra plus au hash de l'événement $k-1$. De plus, la séquence des `event_index` présentera un saut ($k-1 \to k+1$).
3. **Événement Inséré :** L'insertion d'un faux événement entre $k$ et $k+1$ brise la liaison cryptographique car l'événement $k+1$ référence toujours $k$ et non le nouvel intrus.
4. **Événements Réordonnés :** L'inversion de deux lignes brise immédiatement la chaîne des `prev_hash` et viole la monotonicité des `event_index`.
5. **Troncature de Fin de Journal (Suppression des derniers événements) :**  
   Pour empêcher qu'un attaquant ne supprime discrètement les dernières lignes d'un journal sans briser la chaîne interne des lignes restantes :
   - À la clôture de la mission, l'Orchestrateur exporte une empreinte de clôture (*Mission Receipt*) dans un fichier scellé distinct : `outputs/audit/mission_fingerprints.json` (et/ou affichage direct à l'utilisateur) :
     ```json
     {
       "mission_id": "mission-20261116-01",
       "total_events": 14,
       "final_event_hash": "3f4a9b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a",
       "closed_at_utc": "2026-11-16T22:45:00Z"
     }
     ```
   - Si le journal JSONL est tronqué, le hash de sa dernière ligne différera du `final_event_hash` enregistré de manière externe, révélant la troncature.

---

## 4. Limites de Sécurité Face à un Administrateur Privilégié

> [!CAUTION]
> **Modèle de Menace et Limite Fondamentale :**  
> Cette architecture garantit une **détection infaillible des falsifications** vis-à-vis des agents IA, des processus applicatifs ou d'un attaquant non privilégié.  
> **Cependant, elle ne doit en aucun cas être qualifiée d'"inviolable" :** un utilisateur ou attaquant disposant des privilèges d'administration complète sur le système d'exploitation (accès `root` ou compte propriétaire sous macOS/Linux) a la possibilité technique de modifier les événements du journal ET de recalculer de manière cohérente l'ensemble de la chaîne de hachage SHA-256 ainsi que les empreintes locales.

### Mesures Complémentaires pour Étendre la Protection :
1. **Stockage WORM / Object Lock :** Réplication en continu vers un stockage cloud en écriture unique (ex. Google Cloud Storage avec Bucket Retention Policy ou AWS S3 Object Lock) interdisant toute modification ou suppression même par l'administrateur avant expiration du délai légal.
2. **Ancrage Cryptographique Externe :** Signature GPG du `final_event_hash` et publication dans un commit Git poussé vers un dépôt distant protégé.
3. **Journalisation Déportée (Syslog TLS) :** Transmission synchrone en flux continu vers un serveur SIEM distant inaccessible depuis la machine locale.
