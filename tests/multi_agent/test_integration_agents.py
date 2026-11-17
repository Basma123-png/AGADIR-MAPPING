"""
Tests d'intégration de bout en bout pour la Phase 6.3.
Vérifie la coordination parallèle (Fan-out) des agents Web et Semantic Scholar,
la dégradation gracieuse en cas de panne de l'un ou des deux agents,
l'intégrité de la chaîne cryptographique d'audit et la non-altération des données officielles.
"""

import asyncio
import json
import pytest
import requests
from unittest.mock import MagicMock

from src.multi_agent.agents.scholar_research import SemanticScholarAgent
from src.multi_agent.agents.web_research import WebResearchAgent
from src.multi_agent.audit_logger import verify_audit_trail_chain
from src.multi_agent.base_provider import MockLLMProvider
from src.multi_agent.cache import SQLiteCacheManager
from src.multi_agent.config import load_multi_agent_config
from src.multi_agent.orchestrator import CentralOrchestrator
from src.multi_agent.schemas import ExecutionMode, FinalReport, VerdictStatus


@pytest.fixture
def test_config(tmp_path):
    cfg = load_multi_agent_config()
    cfg.security.audit_trail_dir = str(tmp_path / "audit")
    cfg.security.audit_sqlite_db = str(tmp_path / "audit" / "test_audit.db")
    cfg.security.fingerprints_file = str(tmp_path / "audit" / "fingerprints.json")
    return cfg


@pytest.fixture
def test_cache(tmp_path):
    db_file = tmp_path / "integration_cache.sqlite"
    return SQLiteCacheManager(db_path=db_file)


def create_mock_web_response() -> requests.Response:
    resp = requests.Response()
    resp.status_code = 200
    html = """
    <html><body>
    <div class="result">
        <a class="result__url" href="https://arxiv.org/abs/2305.99999">arxiv.org</a>
        <a class="result__snippet">Recent advances in asymmetric routing and Or-opt heuristics 2023.</a>
    </div>
    </body></html>
    """
    resp._content = html.encode("utf-8")
    resp.encoding = "utf-8"
    return resp


def create_mock_scholar_response() -> requests.Response:
    resp = requests.Response()
    resp.status_code = 200
    data = {
        "total": 1,
        "data": [
            {
                "paperId": "pid-integ-01",
                "title": "Asymmetric Vehicle Routing in Coastal Networks",
                "authors": [{"name": "M. Alami"}, {"name": "S. Tazi"}],
                "year": 2023,
                "citationCount": 42,
                "abstract": "Analysis of asymmetric TSP benchmarks under topological constraints.",
                "externalIds": {"DOI": "10.1016/j.trb.2023.05.002"}
            }
        ]
    }
    resp._content = json.dumps(data).encode("utf-8")
    resp.encoding = "utf-8"
    return resp


def test_orchestrator_parallel_fanout_nominal(test_config, test_cache):
    """Vérifie l'exécution nominale conjointe et parallèle des deux agents de recherche."""
    web_requester = MagicMock(return_value=create_mock_web_response())
    scholar_requester = MagicMock(return_value=create_mock_scholar_response())

    web_agent = WebResearchAgent(test_config, cache_manager=test_cache, http_requester=web_requester)
    scholar_agent = SemanticScholarAgent(test_config, cache_manager=test_cache, http_requester=scholar_requester)
    provider = MockLLMProvider(test_config, simulated_delay_seconds=0.01)

    orchestrator = CentralOrchestrator(
        config=test_config,
        llm_provider=provider,
        cache_manager=test_cache,
        web_agent=web_agent,
        scholar_agent=scholar_agent
    )

    async def _test():
        report = await orchestrator.run_mission(
            topic="Optimisation asymétrique ATSP Agadir avec Or-opt",
            execution_mode=ExecutionMode.ECONOMIC
        )

        assert isinstance(report, FinalReport)
        assert report.web_sources_consulted == 1
        assert report.papers_analyzed == 1
        assert report.theses_evaluated >= 1
        assert report.judge_verdict == VerdictStatus.ACCEPTED_PENDING_VALIDATION
        assert report.deterministic_validation.reference_distance_m == 18933.1

        # Vérification des appels HTTP
        web_requester.assert_called_once()
        scholar_requester.assert_called_once()

        # Vérification de l'intégrité de la chaîne cryptographique d'audit
        is_valid, msg = verify_audit_trail_chain(
            report.audit_trail_path,
            expected_final_hash=report.final_audit_hash
        )
        assert is_valid is True
        assert "certifiée intègre" in msg

    asyncio.run(_test())


def test_graceful_degradation_when_web_fails(test_config, test_cache):
    """Vérifie que la panne de l'agent Web n'interrompt pas la mission (dégradation gracieuse)."""
    # Web échoue avec une exception réseau
    failing_web_requester = MagicMock(side_effect=requests.ConnectionError("DNS resolution failed"))
    scholar_requester = MagicMock(return_value=create_mock_scholar_response())

    web_agent = WebResearchAgent(test_config, cache_manager=test_cache, http_requester=failing_web_requester)
    scholar_agent = SemanticScholarAgent(test_config, cache_manager=test_cache, http_requester=scholar_requester)
    provider = MockLLMProvider(test_config, simulated_delay_seconds=0.01)

    orchestrator = CentralOrchestrator(
        config=test_config,
        llm_provider=provider,
        cache_manager=test_cache,
        web_agent=web_agent,
        scholar_agent=scholar_agent
    )

    async def _test():
        report = await orchestrator.run_mission(
            topic="Mission avec défaillance Web",
            execution_mode=ExecutionMode.ECONOMIC
        )

        assert isinstance(report, FinalReport)
        assert report.web_sources_consulted == 0  # Mode dégradé pour le web
        assert report.papers_analyzed == 1         # Scholar a réussi
        assert report.deterministic_validation.reference_distance_m == 18933.1

        # Vérification de la chaîne d'audit
        is_valid, _ = verify_audit_trail_chain(report.audit_trail_path, report.final_audit_hash)
        assert is_valid is True

    asyncio.run(_test())


def test_graceful_degradation_when_scholar_fails(test_config, test_cache):
    """Vérifie que la panne de Semantic Scholar n'interrompt pas la mission (dégradation gracieuse)."""
    web_requester = MagicMock(return_value=create_mock_web_response())
    # Scholar échoue avec un code HTTP 500 répété
    failing_scholar_requester = MagicMock(side_effect=requests.HTTPError("500 Internal Server Error"))

    web_agent = WebResearchAgent(test_config, cache_manager=test_cache, http_requester=web_requester)
    scholar_agent = SemanticScholarAgent(test_config, cache_manager=test_cache, http_requester=failing_scholar_requester)
    provider = MockLLMProvider(test_config, simulated_delay_seconds=0.01)

    orchestrator = CentralOrchestrator(
        config=test_config,
        llm_provider=provider,
        cache_manager=test_cache,
        web_agent=web_agent,
        scholar_agent=scholar_agent
    )

    async def _test():
        report = await orchestrator.run_mission(
            topic="Mission avec défaillance Scholar",
            execution_mode=ExecutionMode.ECONOMIC
        )

        assert isinstance(report, FinalReport)
        assert report.web_sources_consulted == 1   # Web a réussi
        assert report.papers_analyzed == 0         # Scholar dégradé
        assert report.deterministic_validation.reference_distance_m == 18933.1

        is_valid, _ = verify_audit_trail_chain(report.audit_trail_path, report.final_audit_hash)
        assert is_valid is True

    asyncio.run(_test())


def test_graceful_degradation_when_both_agents_fail(test_config, test_cache):
    """Vérifie la robustesse maximale lorsque l'ensemble des agents externes échouent."""
    failing_web_requester = MagicMock(side_effect=requests.ConnectionError("Web offline"))
    failing_scholar_requester = MagicMock(side_effect=requests.ConnectionError("Scholar offline"))

    web_agent = WebResearchAgent(test_config, cache_manager=test_cache, http_requester=failing_web_requester)
    scholar_agent = SemanticScholarAgent(test_config, cache_manager=test_cache, http_requester=failing_scholar_requester)
    provider = MockLLMProvider(test_config, simulated_delay_seconds=0.01)

    orchestrator = CentralOrchestrator(
        config=test_config,
        llm_provider=provider,
        cache_manager=test_cache,
        web_agent=web_agent,
        scholar_agent=scholar_agent
    )

    async def _test():
        report = await orchestrator.run_mission(
            topic="Mission en isolation réseau totale",
            execution_mode=ExecutionMode.ECONOMIC
        )

        assert isinstance(report, FinalReport)
        assert report.web_sources_consulted == 0
        assert report.papers_analyzed == 0
        # La référence intouchable reste garantie
        assert report.deterministic_validation.reference_distance_m == 18933.1

        is_valid, _ = verify_audit_trail_chain(report.audit_trail_path, report.final_audit_hash)
        assert is_valid is True

    asyncio.run(_test())
