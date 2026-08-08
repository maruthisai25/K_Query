import logging
from typing import Dict, Optional

import aiohttp

logger = logging.getLogger(__name__)


class PrometheusClient:
    def __init__(self, prometheus_url: str):
        self.prometheus_url = prometheus_url.rstrip("/")
        self.query_endpoint = f"{self.prometheus_url}/api/v1/query"
        self.range_query_endpoint = f"{self.prometheus_url}/api/v1/query_range"

    async def get_relevant_metrics(self, query: str) -> str:
        """Get relevant Prometheus metrics based on query"""
        try:
            metrics_info = []
            query_lower = query.lower()

            # CPU metrics
            if "cpu" in query_lower:
                cpu_metrics = await self._get_cpu_metrics()
                if cpu_metrics:
                    metrics_info.append(f"CPU: {cpu_metrics}")

            # Memory metrics
            if "memory" in query_lower or "ram" in query_lower:
                memory_metrics = await self._get_memory_metrics()
                if memory_metrics:
                    metrics_info.append(f"Memory: {memory_metrics}")

            # Error rate metrics
            if any(word in query_lower for word in ["error", "fail", "5xx"]):
                error_metrics = await self._get_error_metrics()
                if error_metrics:
                    metrics_info.append(f"Errors: {error_metrics}")

            # Latency metrics
            if any(word in query_lower for word in ["latency", "response", "slow"]):
                latency_metrics = await self._get_latency_metrics()
                if latency_metrics:
                    metrics_info.append(f"Latency: {latency_metrics}")

            return " | ".join(metrics_info) if metrics_info else "No relevant metrics found."

        except Exception as e:
            logger.error(f"Error getting Prometheus metrics: {str(e)}")
            return f"Error accessing Prometheus: {str(e)}"

    async def _execute_query(self, query: str) -> Optional[Dict]:
        """Execute a Prometheus query"""
        try:
            async with aiohttp.ClientSession() as session:
                params = {"query": query}
                async with session.get(self.query_endpoint, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", {})
                    else:
                        logger.error(f"Prometheus query failed: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error executing Prometheus query: {str(e)}")
            return None

    async def _get_cpu_metrics(self) -> str:
        """Get CPU usage metrics"""
        try:
            # Query for average CPU usage across all pods
            query = "avg(rate(container_cpu_usage_seconds_total[5m])) * 100"
            result = await self._execute_query(query)

            if result and result.get("result"):
                value = float(result["result"][0]["value"][1])
                return f"Avg CPU: {value:.2f}%"

            return "CPU metrics unavailable"
        except Exception as e:
            logger.error(f"Error getting CPU metrics: {str(e)}")
            return "CPU metrics error"

    async def _get_memory_metrics(self) -> str:
        """Get memory usage metrics"""
        try:
            # Query for memory usage
            query = "avg(container_memory_usage_bytes / container_spec_memory_limit_bytes) * 100"
            result = await self._execute_query(query)

            if result and result.get("result"):
                value = float(result["result"][0]["value"][1])
                return f"Avg Memory: {value:.2f}%"

            return "Memory metrics unavailable"
        except Exception as e:
            logger.error(f"Error getting memory metrics: {str(e)}")
            return "Memory metrics error"

    async def _get_error_metrics(self) -> str:
        """Get error rate metrics"""
        try:
            # Query for HTTP 5xx error rate
            query = (
                'sum(rate(http_requests_total{status=~"5.."}[5m]))'
                " / sum(rate(http_requests_total[5m])) * 100"
            )
            result = await self._execute_query(query)

            if result and result.get("result"):
                value = float(result["result"][0]["value"][1])
                return f"Error Rate: {value:.2f}%"

            return "Error metrics unavailable"
        except Exception as e:
            logger.error(f"Error getting error metrics: {str(e)}")
            return "Error metrics error"

    async def _get_latency_metrics(self) -> str:
        """Get latency metrics"""
        try:
            # Query for 95th percentile latency
            query = (
                "histogram_quantile(0.95,"
                " sum(rate(http_request_duration_seconds_bucket[5m])) by (le))"
            )
            result = await self._execute_query(query)

            if result and result.get("result"):
                value = float(result["result"][0]["value"][1])
                return f"P95 Latency: {value:.3f}s"

            return "Latency metrics unavailable"
        except Exception as e:
            logger.error(f"Error getting latency metrics: {str(e)}")
            return "Latency metrics error"

    async def query_custom(self, query: str) -> Dict:
        """Execute a custom Prometheus query"""
        return await self._execute_query(query)

    async def health_check(self) -> bool:
        """Check if Prometheus is accessible"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.prometheus_url}/api/v1/query?query=up") as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Prometheus health check failed: {str(e)}")
            return False
