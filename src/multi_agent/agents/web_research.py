"""
Agent Web Research pour AGADIR MAPPING.
Collecte, filtre, déduplique et sanitise les informations du Web technique sur le Last-Mile TSP.
Gère les timeouts, les erreurs HTTP, le backoff exponentiel avec jitter et la mise en cache SQLite.
"""

from __future__ import annotations

import asyncio
import datetime
import logging
import random
import re
import urllib.parse
from typing import Any, Callable, Dict, List, Optional, Set

import requests

from src.multi_agent.audit_logger import AuditLogger
from src.multi_agent.cache import SQLiteCacheManager
from src.multi_agent.config import MultiAgentConfig, load_multi_agent_config
from src.multi_agent.exceptions import NetworkTimeoutException, ProviderException
from src.multi_agent.schemas import (
    AgentRole,
    WebSearchRequest,
    WebSearchResponse,
    WebSourceItem,
)
from src.multi_agent.security import SecurityValidator

logger = logging.getLogger("agadir.multi_agent.web_research")

# Domaines académiques et techniques réputés
REPUTABLE_DOMAINS: Set[str] = {
    "arxiv.org",
    "github.com",
    "sciencedirect.com",
    "researchgate.net",
    "acm.org",
    "ieee.org",
    "springer.com",
    "semanticscholar.org",
    "nature.com",
    "informs.org",
    "openreview.net"
}


class WebResearchAgent:
    """
    Agent autonome de recherche web technique avec résilience réseau et isolation des données.
    """

    def __init__(
        self,
        config: Optional[MultiAgentConfig] = None,
        cache_manager: Optional[SQLiteCacheManager] = None,
        http_requester: Optional[Callable[..., requests.Response]] = None
    ):
        self.config = config or load_multi_agent_config()
        self.cache = cache_manager or SQLiteCacheManager()
        self._http_requester = http_requester or requests.get
        self.user_agent = "AgadirMapping/1.0 (academic research; TSP optimization)"

    @staticmethod
    def extract_domain(url: str) -> str:
        """Extrait le nom de domaine principal d'une URL."""
        try:
            parsed = urllib.parse.urlparse(url)
            netloc = parsed.netloc.lower()
            if netloc.startswith("www."):
                netloc = netloc[4:]
            return netloc
        except Exception:
            return ""

    def is_reputable(self, url: str) -> bool:
        """Vérifie si le domaine de l'URL appartient aux sources techniques reconnues."""
        domain = self.extract_domain(url)
        return any(domain == rep or domain.endswith("." + rep) for rep in REPUTABLE_DOMAINS)

    @staticmethod
    def extract_publication_year(text: str) -> Optional[int]:
        """Tente d'extraire une année de publication crédible (1970 - année courante)."""
        current_year = datetime.datetime.now(datetime.timezone.utc).year
        matches = re.findall(r"\b(19[7-9]\d|20[0-2]\d)\b", text)
        if matches:
            years = [int(m) for m in matches if int(m) <= current_year]
            if years:
                return max(years)
        return None

    @staticmethod
    def detect_contradictions(snippets: List[str]) -> List[str]:
        """Détecte d'éventuelles contradictions heuristiques entre extraits."""
        contradictions = []
        has_symmetric_claim = any("symmetric tsp" in s.lower() and "asymmetric" not in s.lower() for s in snippets)
        has_asymmetric_claim = any("asymmetric" in s.lower() for s in snippets)
        if has_symmetric_claim and has_asymmetric_claim:
            contradictions.append(
                "Divergence identifiée : certains extraits supposent la symétrie des distances, "
                "ce qui est invalide pour le réseau routier d'Agadir."
            )
        return contradictions

    def _execute_http_with_retry(
        self,
        url: str,
        params: Dict[str, Any],
        timeout: float,
        max_retries: int = 3
    ) -> requests.Response:
        """Exécute une requête HTTP avec gestion des statuts 429, timeouts et backoff exponentiel."""
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/json"
        }

        last_exception = None
        for attempt in range(max_retries):
            try:
                response = self._http_requester(url, params=params, headers=headers, timeout=timeout)
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    wait_time = (2 ** attempt) + random.uniform(0.1, 0.5)
                    logger.warning(f"[WebResearch] HTTP 429 reçu. Pause de {wait_time:.2f}s (essai {attempt+1}/{max_retries})")
                    time_to_sleep = min(wait_time, 10.0)
                    import time
                    time.sleep(time_to_sleep)
                elif response.status_code >= 500:
                    wait_time = (1.5 ** attempt) + random.uniform(0.1, 0.3)
                    import time
                    time.sleep(wait_time)
                else:
                    response.raise_for_status()
            except requests.Timeout as e:
                last_exception = NetworkTimeoutException(f"Délai d'attente réseau ({timeout}s) dépassé pour {url}: {e}")
            except requests.RequestException as e:
                last_exception = ProviderException(f"Erreur HTTP lors de la requête web: {e}")

        if last_exception:
            raise last_exception
        raise ProviderException(f"Échec de la requête web après {max_retries} tentatives.")

    async def search(
        self,
        request: WebSearchRequest,
        audit_logger: Optional[AuditLogger] = None
    ) -> WebSearchResponse:
        """
        Effectue une recherche Web complète avec consultation du cache local,
        filtrage de réputation, sanitisation XML étanche et déduplication des URLs.
        """
        start_time = datetime.datetime.now(datetime.timezone.utc)

        if audit_logger:
            await audit_logger.log_event(
                agent_id=AgentRole.WEB_RESEARCH,
                action="SEARCH_INITIATED",
                payload_summary={"query": request.query, "max_results": request.max_results}
            )

        # 1. Consultation du Cache Local SQLite
        cached_result = self.cache.get("web", request.query)
        if cached_result:
            logger.info(f"[WebResearch] Cache Hit pour la requête : '{request.query}'")
            if audit_logger:
                await audit_logger.log_event(
                    agent_id=AgentRole.WEB_RESEARCH,
                    action="CACHE_HIT",
                    payload_summary={"query": request.query, "sources_count": len(cached_result.get("sources", []))}
                )
            cached_result["request_id"] = request.request_id
            cached_result["status"] = "SUCCESS_FROM_CACHE"
            return WebSearchResponse.model_validate(cached_result)

        # 2. Exécution Réseau (ou repli contrôlé)
        sources: List[WebSourceItem] = []
        seen_urls: Set[str] = set()

        try:
            # Appel asynchrone non bloquant pour le moteur HTTP
            loop = asyncio.get_running_loop()
            
            # Utilisation de l'endpoint DuckDuckGo Lite ou Instant Search
            endpoint = "https://html.duckduckgo.com/html/"
            params = {"q": request.query}

            response = await loop.run_in_executor(
                None,
                self._execute_http_with_retry,
                endpoint,
                params,
                self.config.web_research.timeout_seconds,
                3
            )

            # Extraction et parsing des résultats HTML / texte
            html_text = response.text
            # Regex robuste d'extraction des résultats DuckDuckGo HTML
            raw_results = re.findall(
                r'<a[^>]+class="result__url"[^>]+href="([^"]+)"[^>]*>.*?</a>.*?<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
                html_text,
                re.DOTALL | re.IGNORECASE
            )

            for raw_url, raw_snippet in raw_results:
                clean_url = urllib.parse.unquote(raw_url).strip()
                if clean_url.startswith("//duckduckgo.com/l/?uddg="):
                    # Décodage de la redirection DuckDuckGo
                    clean_url = clean_url.split("uddg=")[-1].split("&")[0]
                    clean_url = urllib.parse.unquote(clean_url)

                if clean_url in seen_urls:
                    continue
                seen_urls.add(clean_url)

                clean_snippet = re.sub(r"<[^>]+>", "", raw_snippet).strip()
                domain = self.extract_domain(clean_url)

                # Filtrage optionnel par domaines cibles
                if request.target_domains and not any(domain.endswith(td) for td in request.target_domains):
                    continue

                pub_year = self.extract_publication_year(clean_snippet)
                is_rep = self.is_reputable(clean_url)

                # Sanitisation stricte du contenu pour neutraliser toute injection
                sanitized_snippet = SecurityValidator.sanitize_untrusted_evidence(
                    text=clean_snippet,
                    source_id=f"WEB-{len(sources)+1:02d}",
                    domain=domain
                )

                item = WebSourceItem(
                    url=clean_url,
                    title=f"Source Web : {domain}",
                    snippet=sanitized_snippet,
                    published_year=pub_year,
                    is_reputable_domain=is_rep,
                    crawled_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()
                )
                sources.append(item)
                if len(sources) >= request.max_results:
                    break

        except Exception as e:
            logger.warning(f"[WebResearch] Erreur lors de la requête réseau ({e}). Mode dégradé activé.")
            if audit_logger:
                await audit_logger.log_event(
                    agent_id=AgentRole.WEB_RESEARCH,
                    action="NETWORK_WARNING",
                    payload_summary={"error": str(e), "query": request.query}
                )

        # 3. Consolidation et Enregistrement dans le Cache SQLite
        elapsed = (datetime.datetime.now(datetime.timezone.utc) - start_time).total_seconds()
        status_str = "SUCCESS" if sources else "EMPTY_RESULTS"

        response_data = WebSearchResponse(
            request_id=request.request_id,
            status=status_str,
            sources_found=len(sources),
            sources=sources,
            execution_time_seconds=round(elapsed, 3)
        )

        if sources:
            self.cache.set(
                namespace="web",
                query=request.query,
                data=response_data.model_dump(),
                ttl_days=self.config.web_research.cache_ttl_days
            )

        if audit_logger:
            await audit_logger.log_event(
                agent_id=AgentRole.WEB_RESEARCH,
                action="SEARCH_COMPLETED",
                payload_summary={
                    "sources_count": len(sources),
                    "status": status_str,
                    "reputable_count": sum(1 for s in sources if s.is_reputable_domain)
                }
            )

        return response_data
