"""
Tests unitaires pour l'audit trail cryptographique SHA-256 (JSONL + SQLite).
Vérifie la détection formelle de toute falsification : altération, suppression,
insertion, réordonnancement et troncature.
"""

import asyncio
import json
import pytest
from pathlib import Path

from src.multi_agent.audit_logger import AuditLogger, verify_audit_trail_chain
from src.multi_agent.config import load_multi_agent_config


@pytest.fixture
def config_temp(tmp_path):
    cfg = load_multi_agent_config()
    cfg.security.audit_trail_dir = str(tmp_path / "audit")
    cfg.security.audit_sqlite_db = str(tmp_path / "audit" / "test_audit.db")
    cfg.security.fingerprints_file = str(tmp_path / "audit" / "fingerprints.json")
    return cfg


def test_nominal_audit_chain_and_verification(config_temp):
    """Vérifie la création nominale de la chaîne de hachage et sa certification réussie."""
    async def _test():
        logger = AuditLogger(config_temp, mission_id="mission-nominal-001")

        # Événement 0 (Genèse)
        rec_0 = await logger.log_event("orchestrator", "START", {"step": 0})
        assert rec_0.event_index == 0
        assert rec_0.prev_hash == "0" * 64
        assert len(rec_0.event_hash) == 64

        # Événement 1
        rec_1 = await logger.log_event("web_agent", "FETCH", {"step": 1})
        assert rec_1.event_index == 1
        assert rec_1.prev_hash == rec_0.event_hash

        # Événement 2
        rec_2 = await logger.log_event("analyst", "ANALYZE", {"step": 2})
        assert rec_2.event_index == 2
        assert rec_2.prev_hash == rec_1.event_hash

        final_hash = await logger.close_mission()
        assert final_hash == rec_2.event_hash

        # Vérification complète de la chaîne
        is_valid, msg = verify_audit_trail_chain(logger.jsonl_path, expected_final_hash=final_hash)
        assert is_valid is True
        assert "certifiée intègre" in msg

    asyncio.run(_test())


def test_detect_event_content_modification(config_temp):
    """Vérifie qu'une modification d'un seul caractère dans un événement est immédiatement détectée."""
    async def _test():
        logger = AuditLogger(config_temp, mission_id="mission-tamper-001")
        await logger.log_event("orchestrator", "START", {"val": 100})
        await logger.log_event("analyst", "ANALYZE", {"val": 200})
        await logger.log_event("judge", "JUDGE", {"val": 300})
        final_hash = await logger.close_mission()

        # Altération de la ligne 2 (val 200 -> 999)
        lines = logger.jsonl_path.read_text(encoding="utf-8").strip().split("\n")
        record = json.loads(lines[1])
        record["payload_summary"]["val"] = 999  # Attaque
        lines[1] = json.dumps(record)
        logger.jsonl_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        is_valid, msg = verify_audit_trail_chain(logger.jsonl_path, expected_final_hash=final_hash)
        assert is_valid is False
        assert "Altération de contenu détectée à la ligne 2" in msg

    asyncio.run(_test())


def test_detect_event_deletion(config_temp):
    """Vérifie que la suppression d'un événement intermédiaire est immédiatement détectée."""
    async def _test():
        logger = AuditLogger(config_temp, mission_id="mission-delete-001")
        await logger.log_event("orchestrator", "START", {})
        await logger.log_event("analyst", "STEP_1", {})
        await logger.log_event("judge", "STEP_2", {})
        final_hash = await logger.close_mission()

        # Suppression de la ligne 2
        lines = logger.jsonl_path.read_text(encoding="utf-8").strip().split("\n")
        del lines[1]
        logger.jsonl_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        is_valid, msg = verify_audit_trail_chain(logger.jsonl_path, expected_final_hash=final_hash)
        assert is_valid is False
        assert "Rupture de séquence d'index" in msg or "Rupture de chaîne" in msg

    asyncio.run(_test())


def test_detect_event_insertion(config_temp):
    """Vérifie que l'insertion d'un faux événement parasite est immédiatement détectée."""
    async def _test():
        logger = AuditLogger(config_temp, mission_id="mission-insert-001")
        await logger.log_event("orchestrator", "START", {})
        await logger.log_event("judge", "END", {})
        final_hash = await logger.close_mission()

        # Insertion d'un événement factice au milieu
        lines = logger.jsonl_path.read_text(encoding="utf-8").strip().split("\n")
        fake_event = {
            "event_index": 1,
            "event_id": "evt-fake",
            "mission_id": "mission-insert-001",
            "timestamp_utc": "2026-11-16T22:00:00Z",
            "agent_id": "hacker",
            "action": "INJECT",
            "payload_summary": {},
            "prev_hash": "a" * 64,
            "event_hash": "b" * 64
        }
        lines.insert(1, json.dumps(fake_event))
        logger.jsonl_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        is_valid, msg = verify_audit_trail_chain(logger.jsonl_path, expected_final_hash=final_hash)
        assert is_valid is False

    asyncio.run(_test())


def test_detect_event_reordering(config_temp):
    """Vérifie que l'inversion de deux événements consécutifs est immédiatement détectée."""
    async def _test():
        logger = AuditLogger(config_temp, mission_id="mission-reorder-001")
        await logger.log_event("orchestrator", "EVT_0", {})
        await logger.log_event("agent_1", "EVT_1", {})
        await logger.log_event("agent_2", "EVT_2", {})
        final_hash = await logger.close_mission()

        # Inversion des événements 1 et 2
        lines = logger.jsonl_path.read_text(encoding="utf-8").strip().split("\n")
        lines[1], lines[2] = lines[2], lines[1]
        logger.jsonl_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        is_valid, msg = verify_audit_trail_chain(logger.jsonl_path, expected_final_hash=final_hash)
        assert is_valid is False
        assert "Rupture de séquence d'index" in msg or "Rupture de chaîne" in msg

    asyncio.run(_test())


def test_detect_log_truncation(config_temp):
    """Vérifie que la troncature de la fin du journal est détectée grâce au hash certifié externe."""
    async def _test():
        logger = AuditLogger(config_temp, mission_id="mission-truncate-001")
        await logger.log_event("orchestrator", "EVT_0", {})
        await logger.log_event("agent_1", "EVT_1", {})
        rec_2 = await logger.log_event("agent_2", "EVT_2", {})
        final_hash = await logger.close_mission()

        # Troncature de la dernière ligne
        lines = logger.jsonl_path.read_text(encoding="utf-8").strip().split("\n")
        truncated_lines = lines[:-1]  # Supprime rec_2
        logger.jsonl_path.write_text("\n".join(truncated_lines) + "\n", encoding="utf-8")

        # La chaîne interne des deux premières lignes est cohérente, MAIS la troncature est détectée via expected_final_hash
        is_valid, msg = verify_audit_trail_chain(logger.jsonl_path, expected_final_hash=final_hash)
        assert is_valid is False
        assert "Troncature de fin de journal détectée" in msg

    asyncio.run(_test())
