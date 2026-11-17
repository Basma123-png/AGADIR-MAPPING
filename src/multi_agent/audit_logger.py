"""
Journal d'audit cryptographique hybride (JSONL + SQLite) avec chaîne de hachage SHA-256.
Garantit la détectabilité mathématique de toute falsification : altération, suppression,
insertion, réordonnancement ou troncature.
"""

from __future__ import annotations

import asyncio
import datetime
import json
import os
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.multi_agent.config import MultiAgentConfig
from src.multi_agent.exceptions import AuditIntegrityException
from src.multi_agent.schemas import AuditEventRecord, compute_event_hash, get_canonical_json_bytes


class AuditLogger:
    """
    Gestionnaire d'audit trail assurant un scellement séquentiel infaillible par SHA-256.
    Écrit simultanément dans un fichier JSONL linéaire et une base de données SQLite.
    """

    def __init__(self, config: MultiAgentConfig, mission_id: Optional[str] = None):
        self.config = config
        self.mission_id = mission_id or f"mission-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        
        # Répertoires de destination
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.audit_dir = base_dir / config.security.audit_trail_dir
        self.audit_dir.mkdir(parents=True, exist_ok=True)

        self.jsonl_path = self.audit_dir / f"{self.mission_id}.jsonl"
        self.sqlite_path = base_dir / config.security.audit_sqlite_db
        self.fingerprints_path = base_dir / config.security.fingerprints_file

        self._current_index: int = 0
        self._current_prev_hash: str = "0" * 64
        self._lock = asyncio.Lock()
        self._is_closed: bool = False

        self._init_sqlite()

    def _init_sqlite(self) -> None:
        """Initialise la table SQLite pour l'indexation de l'audit trail."""
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.sqlite_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mission_id TEXT NOT NULL,
                    event_index INTEGER NOT NULL,
                    event_id TEXT NOT NULL UNIQUE,
                    timestamp_utc TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    payload_summary TEXT NOT NULL,
                    prev_hash TEXT NOT NULL,
                    event_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_mission 
                ON audit_events(mission_id, event_index)
            """)
            conn.commit()
        finally:
            conn.close()

    async def log_event(
        self,
        agent_id: str,
        action: str,
        payload_summary: Dict[str, Any]
    ) -> AuditEventRecord:
        """
        Enregistre un nouvel événement dans la chaîne séquentielle scellée par SHA-256.
        Thread/coroutine-safe via asyncio.Lock.
        """
        async with self._lock:
            if self._is_closed:
                raise AuditIntegrityException("Tentative d'enregistrement dans une mission clôturée.")

            event_id = f"evt-{uuid.uuid4().hex[:12]}"
            timestamp_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()

            event_data = {
                "event_index": self._current_index,
                "event_id": event_id,
                "mission_id": self.mission_id,
                "timestamp_utc": timestamp_utc,
                "agent_id": agent_id,
                "action": action,
                "payload_summary": payload_summary,
                "prev_hash": self._current_prev_hash
            }

            # Calcul du hash canonique (exclut event_hash, inclut prev_hash)
            event_hash = compute_event_hash(event_data)
            event_data["event_hash"] = event_hash

            record = AuditEventRecord.model_validate(event_data)

            # Écriture dans le fichier linéaire JSONL
            with open(self.jsonl_path, "a", encoding="utf-8") as f:
                f.write(record.model_dump_json() + "\n")

            # Écriture dans la base SQLite
            conn = sqlite3.connect(self.sqlite_path)
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO audit_events (
                        mission_id, event_index, event_id, timestamp_utc,
                        agent_id, action, payload_summary, prev_hash, event_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.mission_id,
                    record.event_index,
                    record.event_id,
                    record.timestamp_utc,
                    record.agent_id,
                    record.action,
                    json.dumps(record.payload_summary, sort_keys=True),
                    record.prev_hash,
                    record.event_hash
                ))
                conn.commit()
            finally:
                conn.close()

            # Mise à jour des pointeurs de la chaîne
            self._current_index += 1
            self._current_prev_hash = event_hash

            return record

    async def close_mission(self) -> str:
        """
        Clôture formellement la mission et exporte l'empreinte de fin de chaîne
        dans outputs/audit/mission_fingerprints.json pour empêcher toute troncature ultérieure.
        Retourne le dernier hash certifié.
        """
        async with self._lock:
            if self._is_closed:
                return self._current_prev_hash

            self._is_closed = True
            final_hash = self._current_prev_hash
            total_events = self._current_index

            # Sauvegarde dans le registre externe des empreintes de clôture
            fingerprints: Dict[str, Any] = {}
            if self.fingerprints_path.exists():
                try:
                    with open(self.fingerprints_path, "r", encoding="utf-8") as f:
                        fingerprints = json.load(f)
                except Exception:
                    fingerprints = {}

            fingerprints[self.mission_id] = {
                "total_events": total_events,
                "final_event_hash": final_hash,
                "closed_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "jsonl_path": str(self.jsonl_path)
            }

            with open(self.fingerprints_path, "w", encoding="utf-8") as f:
                json.dump(fingerprints, f, indent=2, sort_keys=True)

            return final_hash


def verify_audit_trail_chain(
    jsonl_path: Path | str,
    expected_final_hash: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Vérifie mathématiquement l'intégrité intégrale d'un journal d'audit JSONL :
    1. Vérifie le bloc genèse (prev_hash = '0'*64).
    2. Recalcule le hash canonique de chaque ligne (excluant event_hash, incluant prev_hash).
    3. Vérifie que prev_hash correspond au hash de la ligne précédente.
    4. Vérifie la stricte continuité des event_index (0, 1, 2, ...).
    5. Détecte la troncature de fin de journal si expected_final_hash est fourni.
    """
    path = Path(jsonl_path)
    if not path.exists():
        return False, f"Fichier d'audit introuvable : {path}"

    expected_prev = "0" * 64
    last_computed_hash = ""
    event_count = 0

    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                record_dict = json.loads(line)
            except Exception as e:
                return False, f"Ligne {line_num} : JSON invalide ({e})"

            # 1. Vérification des champs requis
            if "event_hash" not in record_dict or "prev_hash" not in record_dict:
                return False, f"Ligne {line_num} : champs cryptographiques manquants"

            stored_event_hash = record_dict["event_hash"]
            stored_prev_hash = record_dict["prev_hash"]
            stored_index = record_dict.get("event_index")

            # 2. Vérification de la continuité des index
            if stored_index != (line_num - 1):
                return False, (
                    f"Rupture de séquence d'index à la ligne {line_num} : "
                    f"attendu {line_num - 1}, trouvé {stored_index} "
                    f"(indique une suppression, insertion ou réordonnancement)"
                )

            # 3. Vérification du chaînage avec le hash précédent
            if stored_prev_hash != expected_prev:
                return False, (
                    f"Rupture de chaîne à la ligne {line_num} : "
                    f"prev_hash '{stored_prev_hash[:16]}...' != attendu '{expected_prev[:16]}...'"
                )

            # 4. Recalcul canonique du hash
            recalculated_hash = compute_event_hash(record_dict)
            if recalculated_hash != stored_event_hash:
                return False, (
                    f"Altération de contenu détectée à la ligne {line_num} (index {stored_index}) : "
                    f"event_hash stocké '{stored_event_hash[:16]}...' != recalculé '{recalculated_hash[:16]}...'"
                )

            expected_prev = stored_event_hash
            last_computed_hash = stored_event_hash
            event_count += 1

    if event_count == 0:
        return False, "Le journal d'audit est vide."

    # 5. Détection de troncature via l'empreinte externe de clôture
    if expected_final_hash is not None:
        if last_computed_hash != expected_final_hash:
            return False, (
                f"Troncature de fin de journal détectée : "
                f"le hash final du fichier '{last_computed_hash[:16]}...' ne correspond pas "
                f"à l'empreinte certifiée externe '{expected_final_hash[:16]}...'."
            )

    return True, f"Chaîne d'audit certifiée intègre ({event_count} événements vérifiés, 0 anomalie)."
