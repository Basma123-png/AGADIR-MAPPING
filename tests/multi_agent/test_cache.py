"""
Tests unitaires pour SQLiteCacheManager.
Vérifie la persistance, l'isolation des espaces de noms, le TTL, l'expiration et le nettoyage.
"""

import time
import pytest
from pathlib import Path
from src.multi_agent.cache import SQLiteCacheManager


@pytest.fixture
def cache(tmp_path):
    db_file = tmp_path / "test_cache.sqlite"
    return SQLiteCacheManager(db_path=db_file)


def test_cache_set_and_get(cache):
    """Vérifie l'enregistrement et la récupération nominale d'un objet JSON."""
    data = {"status": "SUCCESS", "results": [1, 2, 3], "meta": {"count": 3}}
    cache.set("web", "tsp agadir", data, ttl_days=1)

    cached = cache.get("web", "tsp agadir")
    assert cached is not None
    assert cached["status"] == "SUCCESS"
    assert cached["results"] == [1, 2, 3]
    assert cached["meta"]["count"] == 3


def test_cache_miss(cache):
    """Vérifie qu'une clé inexistante retourne None."""
    assert cache.get("web", "requete_inexistante") is None
    assert cache.get("scholar", "autre_requete") is None


def test_cache_namespace_isolation(cache):
    """Vérifie que deux espaces de noms distincts ne se chevauchent pas avec la même requête."""
    web_data = {"agent": "web"}
    scholar_data = {"agent": "scholar"}

    cache.set("web", "asymmetric tsp", web_data)
    cache.set("scholar", "asymmetric tsp", scholar_data)

    assert cache.get("web", "asymmetric tsp") == web_data
    assert cache.get("scholar", "asymmetric tsp") == scholar_data


def test_cache_case_insensitivity_and_key_computation(cache):
    """Vérifie que la clé de cache est insensible aux espaces et à la casse."""
    data = {"found": True}
    cache.set("web", "  TSP Agadir  ", data)

    # Récupération avec variations de casse et d'espaces
    assert cache.get("web", "tsp agadir") == data
    assert cache.get("WEB", "  TSP AGADIR  ") == data


def test_cache_expiration_ttl(cache):
    """Vérifie qu'une entrée dont le TTL est dépassé retourne None et est purgée."""
    data = {"temp": True}
    # TTL négatif pour forcer l'expiration immédiate
    cache.set("web", "expired query", data, ttl_days=-1)

    assert cache.get("web", "expired query") is None


def test_cache_clear_expired(cache):
    """Vérifie le nettoyage global des entrées expirées."""
    cache.set("web", "valid 1", {"v": 1}, ttl_days=1)
    cache.set("web", "expired 1", {"v": 2}, ttl_days=-1)
    cache.set("scholar", "expired 2", {"v": 3}, ttl_days=-2)

    purged_count = cache.clear_expired()
    assert purged_count == 2
    assert cache.get("web", "valid 1") is not None


def test_cache_delete(cache):
    """Vérifie la suppression ciblée d'une entrée."""
    cache.set("web", "to delete", {"ok": 1})
    assert cache.get("web", "to delete") is not None

    deleted = cache.delete("web", "to delete")
    assert deleted is True
    assert cache.get("web", "to delete") is None

    # Suppression d'une entrée déjà inexistante
    assert cache.delete("web", "to delete") is False


def test_cache_stats(cache):
    """Vérifie le calcul statistique des entrées valides par espace de noms."""
    cache.set("web", "q1", {"d": 1}, ttl_days=1)
    cache.set("web", "q2", {"d": 2}, ttl_days=1)
    cache.set("scholar", "q3", {"d": 3}, ttl_days=1)
    cache.set("scholar", "q_exp", {"d": 4}, ttl_days=-1)  # Expiré

    stats = cache.get_stats()
    assert stats.get("web") == 2
    assert stats.get("scholar") == 1
