from kubernetes import client, config
from kubernetes.client.rest import ApiException
import logging
import asyncio
from typing import Dict, List, Optional
from .config import Config

logger = logging.getLogger(__name__)

class K8sClient:
    def __init__(self):
        self.config = Config()
        self._load_k8s_config()
        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.namespace = self.config.KUBERNETES_NAMESPACE or "default"
    
    def _load_k8s_config(self):
        """Load Kubernetes configuration"""
        try:
            # Try in-cluster config first (when running in pod)
            config.load_incluster_config()
            logger.info("Loaded in-cluster Kubernetes config")
        except:
            try:
                # Fall back to local kubeconfig
                config.load_kube_config()
                logger.info("Loaded local Kubernetes config")
            except Exception as e:
                logger.error(f"Failed to load Kubernetes config: {str(e)}")
    
    async def get_relevant_info(self, query: str) -> str:
        """Get relevant Kubernetes information based on query"""
        try:
            info_parts = []
            query_lower = query.lower()
            
            # Get pod information if query mentions pods
            if "pod" in query_lower:
                pods_info = await self._get_pods_info()
                if pods_info:
                    info_parts.append(f"Pods: {pods_info}")
            
            # Get deployment information if query mentions deployments
            if "deployment" in query_lower:
                deployments_info = await self._get_deployments_info()
                if deployments_info:
                    info_parts.append(f"Deployments: {deployments_info}")
            
            # Get service information if query mentions services
            if "service" in query_lower:
                services_info = await self._get_services_info()
                if services_info:
                    info_parts.append(f"Services: {services_info}")
            
            # Get events if query mentions errors or issues
            if any(word in query_lower for word in ["error", "issue", "problem", "fail"]):
                events_info = await self._get_recent_events()
                if events_info:
                    info_parts.append(f"Recent Events: {events_info}")
            
            return " | ".join(info_parts) if info_parts else "No relevant Kubernetes information found."
            
        except Exception as e:
            logger.error(f"Error getting Kubernetes info: {str(e)}")
            return f"Error accessing Kubernetes: {str(e)}"
    
    async def _get_pods_info(self) -> str:
        """Get pod status information"""
        try:
            loop = asyncio.get_event_loop()
            pods = await loop.run_in_executor(
                None, 
                lambda: self.v1.list_namespaced_pod(namespace=self.namespace)
            )
            
            pod_info = []
            for pod in pods.items[:5]:  # Limit to 5 pods
                status = pod.status.phase
                name = pod.metadata.name
                pod_info.append(f"{name}({status})")
            
            return ", ".join(pod_info)
        except ApiException as e:
            logger.error(f"Error getting pods: {str(e)}")
            return f"Error getting pods: {e.reason}"
    
    async def _get_deployments_info(self) -> str:
        """Get deployment status information"""
        try:
            loop = asyncio.get_event_loop()
            deployments = await loop.run_in_executor(
                None,
                lambda: self.apps_v1.list_namespaced_deployment(namespace=self.namespace)
            )
            
            deployment_info = []
            for deployment in deployments.items[:5]:  # Limit to 5 deployments
                name = deployment.metadata.name
                ready = deployment.status.ready_replicas or 0
                desired = deployment.status.replicas or 0
                deployment_info.append(f"{name}({ready}/{desired})")
            
            return ", ".join(deployment_info)
        except ApiException as e:
            logger.error(f"Error getting deployments: {str(e)}")
            return f"Error getting deployments: {e.reason}"
    
    async def _get_services_info(self) -> str:
        """Get service information"""
        try:
            loop = asyncio.get_event_loop()
            services = await loop.run_in_executor(
                None,
                lambda: self.v1.list_namespaced_service(namespace=self.namespace)
            )
            
            service_info = []
            for service in services.items[:5]:  # Limit to 5 services
                name = service.metadata.name
                service_type = service.spec.type
                service_info.append(f"{name}({service_type})")
            
            return ", ".join(service_info)
        except ApiException as e:
            logger.error(f"Error getting services: {str(e)}")
            return f"Error getting services: {e.reason}"
    
    async def _get_recent_events(self) -> str:
        """Get recent events"""
        try:
            loop = asyncio.get_event_loop()
            events = await loop.run_in_executor(
                None,
                lambda: self.v1.list_namespaced_event(namespace=self.namespace)
            )
            
            # Sort by timestamp and get recent events
            recent_events = sorted(
                events.items,
                key=lambda x: x.last_timestamp or x.first_timestamp,
                reverse=True
            )[:3]
            
            event_info = []
            for event in recent_events:
                reason = event.reason
                message = event.message[:100]  # Truncate long messages
                event_info.append(f"{reason}: {message}")
            
            return " | ".join(event_info)
        except ApiException as e:
            logger.error(f"Error getting events: {str(e)}")
            return f"Error getting events: {e.reason}"
    
    async def health_check(self) -> bool:
        """Check if Kubernetes API is accessible"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.v1.list_namespace(limit=1)
            )
            return True
        except Exception as e:
            logger.error(f"Kubernetes health check failed: {str(e)}")
            return False