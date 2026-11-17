"""
Tests unitaires pour GeminiProvider.
Vérifie la génération structurée Pydantic v2, la gestion des erreurs HTTP,
le backoff 429, les timeouts, les réponses malformées et le calcul des tokens/coûts.
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from google.genai import errors
from src.multi_agent.config import load_multi_agent_config
from src.multi_agent.exceptions import NetworkTimeoutException, ProviderException
from src.multi_agent.gemini_provider import GeminiProvider
from src.multi_agent.schemas import (
    AnalysisReport,
    AnalysisReportRequest,
    FindingItem,
    GeminiAnalystLLMOutput,
    ScientificPaperItem,
    ThesisItem,
    TokenUsage,
    WebSourceItem,
)


@pytest.fixture
def test_config():
    return load_multi_agent_config()


def create_sample_request():
    return AnalysisReportRequest(
        request_id="req-test-01",
        mission_id="mission-test-01",
        topic="Apport de l'opérateur Or-opt 3-nœuds sur l'ATSP",
        project_context={"city": "Agadir", "reference_distance_m": 18933.1},
        web_evidence=[
            WebSourceItem(
                url="https://arxiv.org/abs/atsp-oropt",
                title="Or-opt for Asymmetric TSP",
                snippet="<untrusted_evidence source_id=\"WEB-01\">Or-opt heuristic improves asymmetric tours.</untrusted_evidence>",
                published_year=2023,
                is_reputable_domain=True,
                crawled_at_utc="2026-11-16T22:00:00Z"
            )
        ],
        academic_evidence=[
            ScientificPaperItem(
                paper_id="paper-atsp-001",
                doi="10.1016/j.cor.2022.105842",
                title="Memetic Algorithms for ATSP",
                authors=["K. Smith", "L. Benali"],
                year=2022,
                citation_count=48,
                abstract="We study directed local search operators on urban graphs."
            )
        ]
    )


def create_mock_gemini_response(
    raw_text: str,
    prompt_tokens: int = 1500,
    completion_tokens: int = 400,
    thinking_tokens: int = 120,
    cached_tokens: int = 0
):
    mock_resp = MagicMock()
    mock_resp.text = raw_text

    usage_meta = MagicMock()
    usage_meta.prompt_token_count = prompt_tokens
    usage_meta.candidates_token_count = completion_tokens
    usage_meta.thoughts_token_count = thinking_tokens
    usage_meta.cached_content_token_count = cached_tokens
    mock_resp.usage_metadata = usage_meta
    return mock_resp


def test_gemini_provider_nominal(test_config):
    """Vérifie l'inférence nominale, la validation Pydantic et le calcul financier."""
    valid_llm_json = json.dumps({
        "general_critique": "L'approche Or-opt est parfaitement compatible avec l'asymétrie.",
        "confidence_level": "HIGH",
        "main_findings": [
            {
                "finding_id": "F-01",
                "statement": "La relocalisation de chaînes de 3 nœuds respecte le sens unique des voies.",
                "category": "atsp",
                "supporting_source_ids": ["https://arxiv.org/abs/atsp-oropt", "paper-atsp-001"],
                "confidence": "HIGH"
            }
        ],
        "convergences": ["Les deux sources confirment la supériorité d'Or-opt sur 2-opt asymétrique."],
        "contradictions": [],
        "limitations": ["Absence de données de congestion dynamique."],
        "uncertainties": ["Temps d'arrêt variables au niveau du boulevard Mohammed V."],
        "missing_information": ["Pentes exactes des axes côtiers."],
        "recommendations": ["Préserver la tournée certifiée de 18 933,1 m."],
        "theses": [
            {
                "thesis_id": "TH-01",
                "hypothesis": "Or-opt-3 réduit les coûts sans violer l'orientation.",
                "scientific_rationale": "Propriété de préservation d'orientation.",
                "cited_papers": ["10.1016/j.cor.2022.105842"],
                "cited_web_sources": ["https://arxiv.org/abs/atsp-oropt"],
                "proposed_action": "Intégrer Or-opt dans la phase d'amélioration.",
                "requires_deterministic_validation": True
            }
        ]
    })

    mock_client = MagicMock()
    mock_generate = AsyncMock(return_value=create_mock_gemini_response(valid_llm_json))
    mock_client.aio.models.generate_content = mock_generate

    provider = GeminiProvider(
        config=test_config,
        api_key="TEST_GEMINI_KEY",
        model_name="gemini-3.8-flash",
        client=mock_client
    )

    async def _test():
        req = create_sample_request()
        report = await provider.generate_analysis(req)

        assert isinstance(report, AnalysisReport)
        assert report.model_id == "gemini-3.8-flash"
        assert report.confidence_level == "HIGH"
        assert len(report.main_findings) == 1
        assert report.main_findings[0].supporting_source_ids == [
            "https://arxiv.org/abs/atsp-oropt", "paper-atsp-001"
        ]
        assert len(report.theses) == 1
        assert report.token_usage.prompt_tokens == 1500
        assert report.token_usage.completion_tokens == 400
        assert report.token_usage.thinking_tokens == 120
        assert report.estimated_cost > 0.0
        assert report.execution_status == "SUCCESS"

    asyncio.run(_test())


def test_gemini_provider_malformed_response_raises(test_config):
    """Vérifie qu'une réponse JSON non conforme au schéma Pydantic lève ProviderException."""
    invalid_json = '{"general_critique": "Manque les champs obligatoires", "invalid_key": 123}'

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(
        return_value=create_mock_gemini_response(invalid_json)
    )

    provider = GeminiProvider(
        config=test_config,
        api_key="TEST_KEY",
        client=mock_client
    )

    async def _test():
        req = create_sample_request()
        with pytest.raises(ProviderException) as exc_info:
            await provider.generate_analysis(req)
        assert "malformée non conforme" in str(exc_info.value)

    asyncio.run(_test())


def test_gemini_provider_empty_response_raises(test_config):
    """Vérifie qu'une réponse vide de Gemini lève une ProviderException explicite."""
    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(
        return_value=create_mock_gemini_response("   ")
    )

    provider = GeminiProvider(config=test_config, api_key="TEST_KEY", client=mock_client)

    async def _test():
        req = create_sample_request()
        with pytest.raises(ProviderException) as exc_info:
            await provider.generate_analysis(req)
        assert "Réponse vide" in str(exc_info.value)

    asyncio.run(_test())


def test_gemini_provider_timeout_handling(test_config):
    """Vérifie le déclenchement de NetworkTimeoutException en cas de dépassement de délai."""
    async def delayed_generate(*args, **kwargs):
        await asyncio.sleep(0.5)
        return create_mock_gemini_response("{}")

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = delayed_generate

    # Timeout configuré très court (0.05s) pour forcer le timeout
    test_config.llm_provider.default_timeout_seconds = 0.05

    provider = GeminiProvider(config=test_config, api_key="TEST_KEY", client=mock_client)

    async def _test():
        req = create_sample_request()
        with pytest.raises(NetworkTimeoutException) as exc_info:
            await provider.generate_analysis(req)
        assert "Délai d'attente réseau" in str(exc_info.value)

    asyncio.run(_test())


def test_gemini_provider_http_429_retry_success(test_config):
    """Vérifie la gestion du statut 429 / RESOURCE_EXHAUSTED avec reprise après backoff."""
    valid_json = json.dumps({
        "general_critique": "Reprise réussie après 429.",
        "confidence_level": "MODERATE",
        "main_findings": [],
        "convergences": [],
        "contradictions": [],
        "limitations": [],
        "uncertainties": [],
        "missing_information": [],
        "recommendations": [],
        "theses": []
    })

    err_429 = errors.APIError(429, {"error": {"message": "Resource exhausted: quota exceeded"}})

    mock_client = MagicMock()
    # Premier appel lève 429, second réussit
    mock_client.aio.models.generate_content = AsyncMock(
        side_effect=[err_429, create_mock_gemini_response(valid_json)]
    )

    provider = GeminiProvider(config=test_config, api_key="TEST_KEY", client=mock_client)

    async def _test():
        req = create_sample_request()
        report = await provider.generate_analysis(req)
        assert report.execution_status == "SUCCESS"
        assert mock_client.aio.models.generate_content.call_count == 2

    asyncio.run(_test())


def test_gemini_provider_unknown_model_pricing_check(test_config):
    """Vérifie le blocage immédiat si le modèle n'a pas de tarif vérifiable."""
    provider = GeminiProvider(
        config=test_config,
        api_key="TEST_KEY",
        model_name="gemini-unknown-experimental"
    )

    async def _test():
        req = create_sample_request()
        with pytest.raises(ProviderException) as exc_info:
            await provider.generate_analysis(req)
        assert "inconnu ou sa tarification" in str(exc_info.value)

    asyncio.run(_test())


def test_gemini_provider_missing_api_key_raises(test_config, monkeypatch):
    """Vérifie qu'un appel sans clé API configurée signale explicitement l'indisponibilité."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    provider = GeminiProvider(config=test_config, api_key=None)

    async def _test():
        req = create_sample_request()
        with pytest.raises(ProviderException) as exc_info:
            await provider.generate_analysis(req)
        assert "Clé API Gemini introuvable" in str(exc_info.value)

    asyncio.run(_test())
