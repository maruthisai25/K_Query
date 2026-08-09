from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.config import Config
from src.k8s_client import K8sClient
from src.llm_service import LLMService, LLMServiceError
from src.prometheus_client import PrometheusClient
from src.resilience import CircuitBreakerOpen, ollama_circuit_breaker
from src.vector_store import VectorStore


class _AsyncCM:
    """Async context manager returning a fixed value.

    aiohttp is used as `async with ClientSession() as s` / `async with s.get()
    as r`. A bare MagicMock does not implement that protocol, so both layers
    are wrapped in this instead.
    """

    def __init__(self, value):
        self._value = value

    async def __aenter__(self):
        return self._value

    async def __aexit__(self, *exc_info):
        return False


def _fake_response(status=200, json_body=None, text_body=""):
    response = Mock()
    response.status = status
    response.json = AsyncMock(return_value=json_body if json_body is not None else {})
    response.text = AsyncMock(return_value=text_body)
    return response


def _patch_aiohttp(response):
    """Patch aiohttp.ClientSession so every get/post yields `response`."""
    session = Mock()
    session.get = Mock(return_value=_AsyncCM(response))
    session.post = Mock(return_value=_AsyncCM(response))
    return patch("aiohttp.ClientSession", return_value=_AsyncCM(session)), session


@pytest.fixture(autouse=True)
def reset_ollama_breaker():
    """The breaker is module-level global state; keep it out of other tests."""
    ollama_circuit_breaker.call_succeeded()
    yield
    ollama_circuit_breaker.call_succeeded()


@pytest.fixture
def mock_config():
    """Mock configuration for tests"""
    config = Mock()
    config.ollama_url = "http://localhost:11434"
    config.MODEL_PATH = "llama2:7b"
    config.QDRANT_URL = "http://localhost:6333"
    config.KUBERNETES_NAMESPACE = "default"
    return config


@pytest.mark.asyncio
async def test_llm_service_health_check():
    """Test model service health check"""
    service = LLMService()
    patcher, _ = _patch_aiohttp(_fake_response(status=200))

    with patcher:
        result = await service.health_check()
        assert result is True


@pytest.mark.asyncio
async def test_generate_response_returns_model_output():
    """Happy path: the generated text is returned verbatim."""
    service = LLMService()
    patcher, _ = _patch_aiohttp(_fake_response(json_body={"response": "scale the deployment"}))

    with patch.object(service, "ensure_model_loaded", AsyncMock()), patcher:
        assert await service.generate_response("how do I scale?") == "scale the deployment"


@pytest.mark.asyncio
async def test_generate_response_retries_then_raises_on_http_error():
    """A non-200 from Ollama must raise, and must be retried before it does.

    This is the behaviour the @with_retries/@with_circuit_breaker decorators
    depend on: when generate_response swallowed errors and returned a string,
    neither decorator ever saw a failure.
    """
    service = LLMService()
    patcher, session = _patch_aiohttp(_fake_response(status=500, text_body="boom"))

    with (
        patch.object(service, "ensure_model_loaded", AsyncMock()),
        patch("src.resilience.asyncio.sleep", AsyncMock()),
        patcher,
    ):
        with pytest.raises(LLMServiceError) as excinfo:
            await service.generate_response("why are my pods crashing?")

    assert "500" in str(excinfo.value)
    assert session.post.call_count == 3, "with_retries(max_attempts=3) did not retry"


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_repeated_failures():
    """Three failed calls open the breaker, and the next call fails fast."""
    service = LLMService()
    patcher, session = _patch_aiohttp(_fake_response(status=500, text_body="boom"))

    with (
        patch.object(service, "ensure_model_loaded", AsyncMock()),
        patch("src.resilience.asyncio.sleep", AsyncMock()),
        patcher,
    ):
        for _ in range(3):
            with pytest.raises(LLMServiceError):
                await service.generate_response("ping")

        calls_before = session.post.call_count

        with pytest.raises(CircuitBreakerOpen):
            await service.generate_response("ping")

    assert session.post.call_count == calls_before, "open breaker still called Ollama"


@pytest.mark.asyncio
async def test_vector_store_search():
    """Test vector store search functionality"""
    store = VectorStore("http://localhost:6333")

    # Mock the encoder
    with patch.object(store, "encoder") as mock_encoder:
        mock_encoder.encode.return_value.tolist.return_value = [0.1] * 384

        # Mock the client search
        with patch.object(store, "client") as mock_client:
            mock_hit = Mock()
            mock_hit.payload = {"content": "test content", "source": "test.md"}
            mock_hit.score = 0.9
            mock_client.search.return_value = [mock_hit]

            results = await store.search("test query", limit=1)

            assert len(results) == 1
            assert results[0]["content"] == "test content"
            assert results[0]["score"] == 0.9


@pytest.mark.asyncio
async def test_k8s_client_get_pods():
    """Test K8s client pod retrieval"""
    client = K8sClient()

    with patch.object(client, "v1") as mock_v1:
        # Mock pod list
        mock_pod = Mock()
        mock_pod.metadata.name = "test-pod"
        mock_pod.status.phase = "Running"

        mock_pods = Mock()
        mock_pods.items = [mock_pod]

        mock_v1.list_namespaced_pod.return_value = mock_pods

        info = await client._get_pods_info()
        assert "test-pod(Running)" in info


def test_circuit_breaker():
    """Test circuit breaker functionality"""
    from src.resilience import CircuitBreaker

    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)

    # Test normal operation
    assert cb.can_execute() is True
    assert cb.state == "closed"

    # Test failures
    cb.call_failed()
    assert cb.state == "closed"

    cb.call_failed()
    assert cb.state == "open"
    assert cb.can_execute() is False

    # Test recovery. Rather than sleeping out the recovery window, move the
    # recorded failure into the past. Sleeping 1.1s against a 1s timeout leaves
    # a 100ms margin, which is not enough on a loaded machine -- this test
    # failed exactly once that way while a container build was running.
    cb.last_failure_time = datetime.now() - timedelta(seconds=cb.recovery_timeout + 1)
    assert cb.can_execute() is True
    assert cb.state == "half-open"

    cb.call_succeeded()
    assert cb.state == "closed"


@pytest.mark.asyncio
async def test_prometheus_client_health_check():
    """Test Prometheus client health check"""
    client = PrometheusClient("http://localhost:9090")
    patcher, _ = _patch_aiohttp(_fake_response(status=200))

    with patcher:
        result = await client.health_check()
        assert result is True


@pytest.mark.asyncio
async def test_k8s_client_health_check():
    """Test K8s client health check"""
    client = K8sClient()

    with patch.object(client, "v1") as mock_v1:
        mock_v1.list_namespace.return_value = Mock()

        result = await client.health_check()
        assert result is True


def test_config_validation():
    """Test configuration validation"""
    config = Config()

    # Test with missing required vars
    config.SLACK_BOT_TOKEN = ""
    config.SLACK_SIGNING_SECRET = ""
    assert config.validate() is False

    # Test with valid config
    config.SLACK_BOT_TOKEN = "xoxb-test-token"
    config.SLACK_SIGNING_SECRET = "test-secret"
    assert config.validate() is True

    # Test with invalid token format
    config.SLACK_BOT_TOKEN = "invalid-token"
    assert config.validate() is False


if __name__ == "__main__":
    pytest.main([__file__])
