"""
Gestionnaire de cache persistant SQLite pour les agents de recherche externe.
Assure la mise en cache locale dédupliquée des requêtes Web et Semantic Scholar avec TTL.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, Optional


class SQLiteCacheManager:
    """
    Gestionnaire de cache local persistant basé sur SQLite.
    Supporte les espaces de noms ('web', 'scholar', 'paper'), la gestion fine du TTL
    et le nettoyage des entrées expirées.
    """

    def __init__(self, db_path: Optional[Path | str] = None):
        if db_path is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.db_path = base_dir / "data" / "agents_cache" / "agents_cache.sqlite"
        else:
            self.db_path = Path(db_path)

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialise la table de cache et ses index."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_cache (
                    cache_key TEXT PRIMARY KEY,
                    namespace TEXT NOT NULL,
                    query TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_lookup 
                ON search_cache(namespace, cache_key, expires_at)
            """)
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def compute_cache_key(namespace: str, query: str) -> str:
        """Calcule une clé de hachage SHA-256 déterministe pour une requête donnée."""
        normalized = f"{namespace.strip().lower()}:{query.strip().lower()}"
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def get(self, namespace: str, query: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un élément du cache s'il existe et n'a pas expiré.
        Supprime l'entrée si le TTL est dépassé et retourne None.
        """
        ns = namespace.strip().lower()
        cache_key = self.compute_cache_key(ns, query)
        now = time.time()

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT response_json, expires_at FROM search_cache 
                WHERE cache_key = ? AND namespace = ?
            """, (cache_key, ns))
            row = cursor.fetchone()

            if row is None:
                return None

            response_json, expires_at = row
            if now > expires_at:
                # Entrée expirée : suppression immédiate
                cursor.execute("DELETE FROM search_cache WHERE cache_key = ?", (cache_key,))
                conn.commit()
                return None

            return json.loads(response_json)
        except Exception:
            return None
        finally:
            conn.close()

    def set(self, namespace: str, query: str, data: Dict[str, Any], ttl_days: int = 30) -> None:
        """Enregistre un résultat dans le cache avec un TTL défini en jours."""
        ns = namespace.strip().lower()
        cache_key = self.compute_cache_key(ns, query)
        now = time.time()
        expires_at = now + (ttl_days * 86400.0)
        serialized = json.dumps(data, sort_keys=True)

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO search_cache (
                    cache_key, namespace, query, response_json, created_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (cache_key, ns, query.strip(), serialized, now, expires_at))
            conn.commit()
        finally:
            conn.close()

    def delete(self, namespace: str, query: str) -> bool:
        """Supprime une entrée spécifique du cache."""
        ns = namespace.strip().lower()
        cache_key = self.compute_cache_key(ns, query)
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM search_cache WHERE cache_key = ?", (cache_key,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def clear_expired(self) -> int:
        """Nettoie toutes les entrées expirées de la base SQLite."""
        now = time.time()
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM search_cache WHERE expires_at < ?", (now,))
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    def get_stats(self) -> Dict[str, int]:
        """Retourne le nombre d'entrées valides par espace de noms."""
        now = time.time()
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT namespace, COUNT(*) FROM search_cache 
                WHERE expires_at >= ? GROUP BY namespace
            """, (now,))
            return dict(cursor.fetchall())
        finally:
            conn.close()
