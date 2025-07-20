import aiohttp
import json
import logging
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from .config import Config

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, qdrant_url: str):
        self.qdrant_url = qdrant_url.rstrip('/')
        self.collection_name = "devops_knowledge"
        self.client = QdrantClient(url=qdrant_url)
        self.encoder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.vector_size = 384  # all-MiniLM-L6-v2 output dimension
    
    async def search(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for relevant documents in the vector store"""
        try:
            # Generate embedding for the query
            query_vector = self.encoder.encode(query).tolist()
            
            # Search in Qdrant
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit
            )
            
            # Format results
            results = []
            for hit in search_result:
                results.append({
                    "content": hit.payload.get("content", ""),
                    "source": hit.payload.get("source", ""),
                    "score": hit.score,
                    "metadata": hit.payload
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            # Fallback to keyword search if vector search fails
            return await self._keyword_search(query, limit)
    
    async def _keyword_search(self, query: str, limit: int) -> List[Dict]:
        """Fallback keyword-based search"""
        try:
            # Simple keyword matching in stored documents
            response = self.client.scroll(
                collection_name=self.collection_name,
                limit=100  # Get more docs for keyword filtering
            )
            
            query_lower = query.lower()
            relevant_docs = []
            
            for point in response[0]:
                content = point.payload.get("content", "").lower()
                if any(keyword in content for keyword in query_lower.split()):
                    relevant_docs.append({
                        "content": point.payload.get("content", ""),
                        "source": point.payload.get("source", ""),
                        "score": 0.5,  # Default score for keyword match
                        "metadata": point.payload
                    })
            
            # Sort by relevance (number of keyword matches)
            relevant_docs.sort(
                key=lambda x: sum(1 for kw in query_lower.split() if kw in x["content"].lower()),
                reverse=True
            )
            
            return relevant_docs[:limit]
            
        except Exception as e:
            logger.error(f"Error in keyword search: {str(e)}")
            return []
    
    async def add_document(self, content: str, metadata: Dict) -> bool:
        """Add a document to the vector store"""
        try:
            # Generate embedding
            embedding = self.encoder.encode(content).tolist()
            
            # Create point
            point = PointStruct(
                id=hash(content) % (10**8),  # Generate ID from content hash
                vector=embedding,
                payload={
                    "content": content,
                    **metadata
                }
            )
            
            # Upsert to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.info(f"Added document to vector store: {content[:100]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error adding document: {str(e)}")
            return False
    
    async def initialize_collection(self) -> bool:
        """Initialize the Qdrant collection"""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name in collection_names:
                logger.info(f"Collection {self.collection_name} already exists")
                return True
            
            # Create collection
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
            
            logger.info(f"Created collection {self.collection_name}")
            
            # Add initial FAQ documents
            await self._populate_initial_faqs()
            
            return True
                        
        except Exception as e:
            logger.error(f"Error initializing collection: {str(e)}")
            return False
    
    async def _populate_initial_faqs(self):
        """Populate initial FAQ documents with real embeddings"""
        faqs = [
            {
                "content": "To troubleshoot pod issues: 1) Check pod status with kubectl get pods -n <namespace> 2) Describe the pod with kubectl describe pod <pod-name> 3) Check logs with kubectl logs <pod-name> 4) Common issues include ImagePullBackOff (wrong image), CrashLoopBackOff (app crashes), and Pending (resource constraints)",
                "source": "kubernetes-troubleshooting.md",
                "category": "kubernetes",
                "tags": ["pods", "troubleshooting", "kubectl"]
            },
            {
                "content": "High CPU usage troubleshooting: 1) Check resource limits with kubectl describe pod <pod-name> 2) Monitor with kubectl top pods 3) Common causes: insufficient CPU limits, inefficient code, memory leaks causing CPU thrashing, high traffic load 4) Solutions: increase CPU limits, optimize application code, implement horizontal pod autoscaling",
                "source": "performance-troubleshooting.md",
                "category": "performance",
                "tags": ["cpu", "performance", "monitoring"]
            },
            {
                "content": "Deployment troubleshooting: 1) Check deployment status with kubectl get deployments 2) Describe deployment with kubectl describe deployment <name> 3) Check replica sets with kubectl get rs 4) Common issues: image pull errors, resource constraints, failed health checks 5) Verify image tags, resource limits, and readiness/liveness probes",
                "source": "deployment-guide.md",
                "category": "kubernetes",
                "tags": ["deployment", "troubleshooting", "replicas"]
            }
        ]
        
        for faq in faqs:
            content = faq.pop("content")
            await self.add_document(content, faq)
    
    async def health_check(self) -> bool:
        """Check if Qdrant is accessible"""
        try:
            info = self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {str(e)}")
            return False
