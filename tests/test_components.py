import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.llm_service import LLMService
from src.vector_store import VectorStore
from src.k8s_client import K8sClient


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
    """Test LLM service health check"""
    service = LLMService()
    
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        
        result = await service.health_check()
        assert result is True


@pytest.mark.asyncio
async def test_vector_store_search():
    """Test vector store search functionality"""
    store = VectorStore("http://localhost:6333")
    
    # Mock the encoder
    with patch.object(store, 'encoder') as mock_encoder:
        mock_encoder.encode.return_value.tolist.return_value = [0.1] * 384
        
        # Mock the client search
        with patch.object(store, 'client') as mock_client:
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
    
    with patch.object(client, 'v1') as mock_v1:
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
    
    # Test recovery
    import time
    time.sleep(1.1)
    assert cb.can_execute() is True
    assert cb.state == "half-open"
    
    cb.call_succeeded()
    assert cb.state == "closed"


if __name__ == "__main__":
    pytest.main([__file__])
