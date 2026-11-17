"""
Tests unitaires pour SemanticScholarAgent.
Vérifie les requêtes de recherche et par lots (batch), le parsing bibliographique (DOI, auteurs, citations),
la déduplication, le classement par autorité, l'authentification x-api-key, le backoff HTTP 429 et le cache SQLite.
"""

import asyncio
import json
import pytest
import requests
from unittest.mock import MagicMock

from src.multi_agent.agents.scholar_research import SemanticScholarAgent
from src.multi_agent.audit_logger import AuditLogger
from src.multi_agent.cache import SQLiteCacheManager
from src.multi_agent.config import load_multi_agent_config
from src.multi_agent.schemas import ScholarSearchRequest, ScholarSearchResponse, ScientificPaperItem


@pytest.fixture
def test_config(tmp_path):
    cfg = load_multi_agent_config()
    cfg.security.audit_trail_dir = str(tmp_path / "audit")
    cfg.security.audit_sqlite_db = str(tmp_path / "audit" / "test_audit.db")
    cfg.security.fingerprints_file = str(tmp_path / "audit" / "fingerprints.json")
    return cfg


@pytest.fixture
def cache(tmp_path):
    db_file = tmp_path / "scholar_cache.sqlite"
    return SQLiteCacheManager(db_path=db_file)


def create_mock_json_response(status_code: int, data: any) -> requests.Response:
    resp = requests.Response()
    resp.status_code = status_code
    resp._content = json.dumps(data).encode("utf-8")
    resp.encoding = "utf-8"
    return resp


def test_scholar_search_nominal(test_config, cache):
    """Vérifie le parsing complet des métadonnées bibliographiques (DOI, auteurs, citations, PDF)."""
    raw_api_data = {
        "total": 1,
        "data": [
            {
                "paperId": "pid-001",
                "title": "A Memetic Algorithm for the Asymmetric Traveling Salesperson Problem",
                "authors": [{"name": "A. Berrada"}, {"name": "C. Cordeau"}],
                "year": 2023,
                "venue": "European Journal of Operational Research",
                "citationCount": 54,
                "abstract": "We investigate directed cycles and edge-exchange neighborhood operators.",
                "externalIds": {"DOI": "10.1016/j.ejor.2023.01.001"},
                "openAccessPdf": {"url": "https://doi.org/10.1016/j.ejor.2023.01.001.pdf"}
            }
        ]
    }
    mock_requester = MagicMock(return_value=create_mock_json_response(200, raw_api_data))
    agent = SemanticScholarAgent(config=test_config, cache_manager=cache, http_requester=mock_requester)

    async def _test():
        req = ScholarSearchRequest(
            request_id="req-sch-01",
            query="asymmetric tsp memetic algorithm",
            limit=5
        )
        res = await agent.search_papers(req)

        assert isinstance(res, ScholarSearchResponse)
        assert res.status == "SUCCESS"
        assert res.total_papers == 1
        assert len(res.papers) == 1

        p = res.papers[0]
        assert p.paper_id == "pid-001"
        assert p.title == "A Memetic Algorithm for the Asymmetric Traveling Salesperson Problem"
        assert p.doi == "10.1016/j.ejor.2023.01.001"
        assert p.authors == ["A. Berrada", "C. Cordeau"]
        assert p.year == 2023
        assert p.citation_count == 54
        assert p.open_access_pdf_url == "https://doi.org/10.1016/j.ejor.2023.01.001.pdf"
        assert "directed cycles" in p.abstract

    asyncio.run(_test())


def test_scholar_search_deduplication_and_citation_ranking(test_config, cache):
    """Vérifie la déduplication par ID/DOI et l'ordonnancement par nombre de citations décroissant."""
    raw_api_data = {
        "total": 3,
        "data": [
            {
                "paperId": "pid-low",
                "title": "Low citation paper",
                "authors": [{"name": "Author 1"}],
                "year": 2024,
                "citationCount": 5,
                "doi": "10.1000/1"
            },
            {
                "paperId": "pid-high",
                "title": "Seminal ATSP paper",
                "authors": [{"name": "Author 2"}],
                "year": 2020,
                "citationCount": 120,
                "doi": "10.1000/2"
            },
            {
                "paperId": "pid-dup",
                "title": "Duplicate of seminal paper",
                "authors": [{"name": "Author 2"}],
                "year": 2020,
                "citationCount": 120,
                "doi": "10.1000/2"  # Même DOI -> doit être dédupliqué
            }
        ]
    }
    mock_requester = MagicMock(return_value=create_mock_json_response(200, raw_api_data))
    agent = SemanticScholarAgent(config=test_config, cache_manager=cache, http_requester=mock_requester)

    async def _test():
        req = ScholarSearchRequest(request_id="req-sch-dedup", query="dedup test", limit=10)
        res = await agent.search_papers(req)

        # 3 items reçus mais 1 doublon de DOI -> 2 uniques
        assert res.total_papers == 2
        # Classement : l'article avec 120 citations en premier
        assert res.papers[0].paper_id == "pid-high"
        assert res.papers[0].citation_count == 120
        assert res.papers[1].paper_id == "pid-low"
        assert res.papers[1].citation_count == 5

    asyncio.run(_test())


def test_scholar_get_papers_batch(test_config, cache):
    """Vérifie l'endpoint officiel POST /graph/v1/paper/batch."""
    raw_batch_data = [
        {
            "paperId": "batch-1",
            "title": "Batch Paper 1",
            "citationCount": 30,
            "year": 2021
        },
        {
            "paperId": "batch-2",
            "title": "Batch Paper 2",
            "citationCount": 15,
            "year": 2022
        }
    ]
    mock_requester = MagicMock(return_value=create_mock_json_response(200, raw_batch_data))
    agent = SemanticScholarAgent(config=test_config, cache_manager=cache, http_requester=mock_requester)

    async def _test():
        papers = await agent.get_papers_batch(["batch-1", "batch-2"])

        assert len(papers) == 2
        assert papers[0].paper_id == "batch-1"
        assert papers[1].paper_id == "batch-2"

        # Vérification des arguments passés à http_requester
        mock_requester.assert_called_once()
        call_kwargs = mock_requester.call_args.kwargs
        assert call_kwargs["method"] == "POST"
        assert "/paper/batch" in call_kwargs["url"]
        assert call_kwargs["json"] == {"ids": ["batch-1", "batch-2"]}

    asyncio.run(_test())


def test_scholar_caching(test_config, cache):
    """Vérifie que la seconde requête identique est servie par le cache local SQLite."""
    raw_api_data = {
        "total": 1,
        "data": [{"paperId": "pid-cache", "title": "Cached Paper", "citationCount": 10}]
    }
    mock_requester = MagicMock(return_value=create_mock_json_response(200, raw_api_data))
    agent = SemanticScholarAgent(config=test_config, cache_manager=cache, http_requester=mock_requester)

    async def _test():
        req = ScholarSearchRequest(request_id="req-c-sch", query="cache scholar test", limit=5)

        # 1er appel : HTTP
        res1 = await agent.search_papers(req)
        assert res1.status == "SUCCESS"
        assert mock_requester.call_count == 1

        # 2e appel : Cache SQLite
        res2 = await agent.search_papers(req)
        assert res2.status == "SUCCESS_FROM_CACHE"
        assert res2.total_papers == res1.total_papers
        assert mock_requester.call_count == 1  # Pas de second appel HTTP

    asyncio.run(_test())


def test_scholar_rate_limit_and_http_429_backoff(test_config, cache):
    """Vérifie la reprise automatique sur HTTP 429 avec backoff et jitter."""
    resp_429 = create_mock_json_response(429, {"message": "Too Many Requests"})
    resp_200 = create_mock_json_response(200, {
        "total": 1,
        "data": [{"paperId": "pid-retry", "title": "Retry Succeeded", "citationCount": 1}]
    })

    mock_requester = MagicMock(side_effect=[resp_429, resp_200])
    agent = SemanticScholarAgent(config=test_config, cache_manager=cache, http_requester=mock_requester)

    async def _test():
        req = ScholarSearchRequest(request_id="req-retry-429", query="test 429 backoff", limit=5)
        res = await agent.search_papers(req)

        assert res.status == "SUCCESS"
        assert mock_requester.call_count == 2
        assert len(res.papers) == 1
        assert res.papers[0].title == "Retry Succeeded"

    asyncio.run(_test())


def test_scholar_authenticated_headers(test_config, cache):
    """Vérifie l'injection de l'en-tête x-api-key en mode authentifié."""
    mock_requester = MagicMock(return_value=create_mock_json_response(200, {"data": []}))
    agent = SemanticScholarAgent(
        config=test_config,
        cache_manager=cache,
        api_key="TEST_API_KEY_SECRET",
        http_requester=mock_requester
    )

    async def _test():
        req = ScholarSearchRequest(request_id="req-auth", query="auth test", limit=1)
        res = await agent.search_papers(req)

        assert res.is_authenticated_key is True
        call_kwargs = mock_requester.call_args.kwargs
        assert call_kwargs["headers"].get("x-api-key") == "TEST_API_KEY_SECRET"

    asyncio.run(_test())


def test_scholar_network_timeout_graceful(test_config, cache):
    """Vérifie qu'un timeout réseau est intercepté et déclenche le mode dégradé propre."""
    mock_requester = MagicMock(side_effect=requests.Timeout("Semantic Scholar timeout"))
    agent = SemanticScholarAgent(config=test_config, cache_manager=cache, http_requester=mock_requester)

    async def _test():
        req = ScholarSearchRequest(request_id="req-to", query="timeout query", limit=5)
        res = await agent.search_papers(req)

        assert res.status == "EMPTY_RESULTS"
        assert res.total_papers == 0
        assert len(res.papers) == 0

    asyncio.run(_test())


def test_scholar_audit_trail_logging(test_config, cache):
    """Vérifie la journalisation cryptographique des étapes de recherche scientifique."""
    raw_api_data = {
        "total": 1,
        "data": [{"paperId": "pid-audit", "title": "Audit Paper", "citationCount": 20}]
    }
    mock_requester = MagicMock(return_value=create_mock_json_response(200, raw_api_data))
    agent = SemanticScholarAgent(config=test_config, cache_manager=cache, http_requester=mock_requester)
    audit = AuditLogger(test_config)

    async def _test():
        req = ScholarSearchRequest(request_id="req-audit-sch", query="audit query", limit=1)
        await agent.search_papers(req, audit_logger=audit)
        await audit.close_mission()

        lines = []
        with open(audit.jsonl_path, "r", encoding="utf-8") as f:
            for l in f:
                lines.append(json.loads(l))

        actions = [entry["action"] for entry in lines]
        assert "SEARCH_INITIATED" in actions
        assert "SEARCH_COMPLETED" in actions

    asyncio.run(_test())
