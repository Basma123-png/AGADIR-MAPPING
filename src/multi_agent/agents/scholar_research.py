"""
Agent Semantic Scholar pour AGADIR MAPPING.
Interroge l'Academic Graph API officielle (search & batch) pour extraire des publications scientifiques.
Gère l'authentification optionnelle, les erreurs HTTP 429 avec backoff exponentiel et le cache SQLite.
"""

from __future__ import annotations

import asyncio
import datetime
import logging
import math
import os
import random
import time
from typing import Any, Callable, Dict, List, Optional, Set

import requests

from src.multi_agent.audit_logger import AuditLogger
from src.multi_agent.cache import SQLiteCacheManager
from src.multi_agent.config import MultiAgentConfig, load_multi_agent_config
from src.multi_agent.exceptions import NetworkTimeoutException, ProviderException
from src.multi_agent.schemas import (
    AgentRole,
    ScholarSearchRequest,
    ScholarSearchResponse,
    ScientificPaperItem,
)

logger = logging.getLogger("agadir.multi_agent.scholar_research")


class SemanticScholarAgent:
    """
    Agent autonome de recherche bibliographique sur Semantic Scholar.
    """

    def __init__(
        self,
        config: Optional[MultiAgentConfig] = None,
        cache_manager: Optional[SQLiteCacheManager] = None,
        api_key: Optional[str] = None,
        http_requester: Optional[Callable[..., requests.Response]] = None
    ):
        self.config = config or load_multi_agent_config()
        self.cache = cache_manager or SQLiteCacheManager()
        self.api_key = api_key or os.getenv(self.config.semantic_scholar.api_key_env_var)
        self._http_requester = http_requester or requests.request
        self.user_agent = "AgadirMapping/1.0 (academic research; TSP optimization)"
        self._last_call_timestamp: float = 0.0

    def _get_headers(self) -> Dict[str, str]:
        """Construit les en-têtes HTTP de la requête."""
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json"
        }
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    def _enforce_rate_limit(self) -> None:
        """Applique une temporisation logicielle pour respecter le rythme d'accès."""
        delay = self.config.semantic_scholar.rate_limit_delay_seconds
        now = time.time()
        elapsed = now - self._last_call_timestamp
        if elapsed < delay:
            sleep_needed = delay - elapsed
            time.sleep(sleep_needed)
        self._last_call_timestamp = time.time()

    def _execute_http_with_retry(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Any] = None,
        timeout: float = 20.0,
        max_retries: int = 3
    ) -> requests.Response:
        """Exécute un appel HTTP avec gestion de la temporisation, du code 429 et backoff avec jitter."""
        self._enforce_rate_limit()
        headers = self._get_headers()

        last_exception = None
        for attempt in range(max_retries):
            try:
                response = self._http_requester(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    headers=headers,
                    timeout=timeout
                )
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    base_delay = self.config.semantic_scholar.backoff_base_seconds
                    wait_time = (base_delay ** (attempt + 1)) + random.uniform(0.1, 0.5)
                    logger.warning(
                        f"[SemanticScholar] HTTP 429 reçu. Backoff de {wait_time:.2f}s "
                        f"(essai {attempt+1}/{max_retries})"
                    )
                    time.sleep(min(wait_time, 15.0))
                elif response.status_code >= 500:
                    wait_time = 1.5 + random.uniform(0.1, 0.3)
                    time.sleep(wait_time)
                else:
                    response.raise_for_status()
            except requests.Timeout as e:
                last_exception = NetworkTimeoutException(f"Délai d'attente ({timeout}s) dépassé pour {url}: {e}")
            except requests.RequestException as e:
                last_exception = ProviderException(f"Erreur HTTP Semantic Scholar: {e}")

        if last_exception:
            raise last_exception
        raise ProviderException(f"Échec de l'appel Semantic Scholar après {max_retries} tentatives.")

    @staticmethod
    def _parse_paper_item(item_data: Dict[str, Any]) -> Optional[ScientificPaperItem]:
        """Convertit un objet brut Semantic Scholar en ScientificPaperItem validé."""
        paper_id = item_data.get("paperId")
        title = item_data.get("title")
        if not paper_id or not title:
            return None

        # Extraction des auteurs
        raw_authors = item_data.get("authors", [])
        authors = [a.get("name") for a in raw_authors if isinstance(a, dict) and a.get("name")]

        # Extraction du DOI
        doi = item_data.get("doi")
        if not doi and isinstance(item_data.get("externalIds"), dict):
            doi = item_data["externalIds"].get("DOI")

        # Résumé (abstract)
        abstract = item_data.get("abstract") or "Résumé non fourni par l'éditeur."

        # PDF Open Access
        pdf_url = None
        if isinstance(item_data.get("openAccessPdf"), dict):
            pdf_url = item_data["openAccessPdf"].get("url")

        return ScientificPaperItem(
            paper_id=paper_id,
            doi=doi,
            title=title.strip(),
            authors=authors,
            year=item_data.get("year"),
            venue=item_data.get("venue"),
            citation_count=item_data.get("citationCount", 0) or 0,
            abstract=abstract.strip(),
            open_access_pdf_url=pdf_url
        )

    @staticmethod
    def rank_and_deduplicate_papers(papers: List[ScientificPaperItem]) -> List[ScientificPaperItem]:
        """
        Déduplique les publications par paper_id et DOI,
        puis les classe selon un score combinant pertinence et autorité bibliographique.
        """
        seen_ids: Set[str] = set()
        seen_dois: Set[str] = set()
        unique_papers: List[ScientificPaperItem] = []

        for p in papers:
            if p.paper_id in seen_ids:
                continue
            if p.doi and p.doi in seen_dois:
                continue

            seen_ids.add(p.paper_id)
            if p.doi:
                seen_dois.add(p.doi)
            unique_papers.append(p)

        # Classement par citations décroissantes (autorité scientifique)
        unique_papers.sort(key=lambda x: (x.citation_count, x.year or 0), reverse=True)
        return unique_papers

    async def search_papers(
        self,
        request: ScholarSearchRequest,
        audit_logger: Optional[AuditLogger] = None
    ) -> ScholarSearchResponse:
        """
        Recherche des articles scientifiques via l'endpoint /graph/v1/paper/search.
        Vérifie le cache local SQLite avant tout appel réseau.
        """
        start_time = datetime.datetime.now(datetime.timezone.utc)

        if audit_logger:
            await audit_logger.log_event(
                agent_id=AgentRole.SEMANTIC_SCHOLAR,
                action="SEARCH_INITIATED",
                payload_summary={"query": request.query, "limit": request.limit}
            )

        # 1. Vérification du cache SQLite
        cached_result = self.cache.get("scholar", request.query)
        if cached_result:
            logger.info(f"[SemanticScholar] Cache Hit pour la requête : '{request.query}'")
            if audit_logger:
                await audit_logger.log_event(
                    agent_id=AgentRole.SEMANTIC_SCHOLAR,
                    action="CACHE_HIT",
                    payload_summary={"query": request.query, "papers_count": len(cached_result.get("papers", []))}
                )
            cached_result["request_id"] = request.request_id
            cached_result["status"] = "SUCCESS_FROM_CACHE"
            return ScholarSearchResponse.model_validate(cached_result)

        # 2. Exécution Réseau
        papers: List[ScientificPaperItem] = []
        try:
            loop = asyncio.get_running_loop()
            url = f"{self.config.semantic_scholar.api_endpoint}/paper/search"
            fields_str = ",".join(request.fields)
            params = {
                "query": request.query,
                "fields": fields_str,
                "limit": request.limit
            }
            if request.min_year:
                params["year"] = f"{request.min_year}-"

            response = await loop.run_in_executor(
                None,
                self._execute_http_with_retry,
                "GET",
                url,
                params,
                None,
                self.config.llm_provider.default_timeout_seconds,
                self.config.semantic_scholar.max_retries
            )

            json_resp = response.json()
            raw_data = json_resp.get("data", [])

            for item in raw_data:
                parsed = self._parse_paper_item(item)
                if parsed:
                    papers.append(parsed)

            # Déduplication et classement par pertinence/citations
            papers = self.rank_and_deduplicate_papers(papers)

        except Exception as e:
            logger.warning(f"[SemanticScholar] Erreur réseau lors de la recherche ({e}). Mode dégradé activé.")
            if audit_logger:
                await audit_logger.log_event(
                    agent_id=AgentRole.SEMANTIC_SCHOLAR,
                    action="NETWORK_WARNING",
                    payload_summary={"error": str(e), "query": request.query}
                )

        # 3. Consolidation et Enregistrement dans le Cache
        elapsed = (datetime.datetime.now(datetime.timezone.utc) - start_time).total_seconds()
        status_str = "SUCCESS" if papers else "EMPTY_RESULTS"

        response_data = ScholarSearchResponse(
            request_id=request.request_id,
            status=status_str,
            total_papers=len(papers),
            papers=papers,
            is_authenticated_key=bool(self.api_key),
            rate_limit_remaining=None,
            execution_time_seconds=round(elapsed, 3)
        )

        if papers:
            self.cache.set(
                namespace="scholar",
                query=request.query,
                data=response_data.model_dump(),
                ttl_days=self.config.semantic_scholar.cache_ttl_days
            )

        if audit_logger:
            await audit_logger.log_event(
                agent_id=AgentRole.SEMANTIC_SCHOLAR,
                action="SEARCH_COMPLETED",
                payload_summary={
                    "papers_count": len(papers),
                    "status": status_str,
                    "is_authenticated": bool(self.api_key)
                }
            )

        return response_data

    async def get_papers_batch(
        self,
        paper_ids: List[str],
        fields: Optional[List[str]] = None
    ) -> List[ScientificPaperItem]:
        """
        Récupère un lot de publications via l'endpoint officiel POST /graph/v1/paper/batch.
        Jusqu'à 500 identifiants de documents en une seule requête HTTP.
        """
        if not paper_ids:
            return []

        limit = min(len(paper_ids), self.config.semantic_scholar.batch_size_limit)
        target_ids = paper_ids[:limit]
        fields_str = ",".join(fields or ["title", "authors", "year", "abstract", "citationCount", "doi"])

        loop = asyncio.get_running_loop()
        url = f"{self.config.semantic_scholar.api_endpoint}/paper/batch"
        params = {"fields": fields_str}
        payload = {"ids": target_ids}

        response = await loop.run_in_executor(
            None,
            self._execute_http_with_retry,
            "POST",
            url,
            params,
            payload,
            self.config.llm_provider.default_timeout_seconds,
            self.config.semantic_scholar.max_retries
        )

        raw_list = response.json()
        results: List[ScientificPaperItem] = []
        if isinstance(raw_list, list):
            for item in raw_list:
                if isinstance(item, dict):
                    parsed = self._parse_paper_item(item)
                    if parsed:
                        results.append(parsed)

        return self.rank_and_deduplicate_papers(results)
