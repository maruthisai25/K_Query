from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Qdrant
from langchain.chains import RetrievalQA
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
from typing import Optional, List, Any
import aiohttp
import logging
from .config import Config

logger = logging.getLogger(__name__)

class OllamaLLM(LLM):
    """Custom LangChain LLM wrapper for Ollama"""
    
    model_name: str = "llama2:7b"
    ollama_url: str = "http://localhost:11434"
    temperature: float = 0.7
    
    @property
    def _llm_type(self) -> str:
        return "ollama"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
    ) -> str:
        """Synchronous call to Ollama"""
        # This would need to be implemented with requests library
        # For async support, use _acall
        raise NotImplementedError("Use async version")
    
    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
    ) -> str:
        """Async call to Ollama"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "stop": stop or []
                }
            }
            
            async with session.post(
                f"{self.ollama_url}/api/generate",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("response", "")
                else:
                    raise Exception(f"Ollama error: {response.status}")

class LangChainRouter:
    """LangChain-based routing for DevOps knowledge retrieval"""
    
    def __init__(self):
        self.config = Config()
        self.embeddings = None
        self.vector_store = None
        self.qa_chain = None
        self.llm = None
        
    async def initialize(self):
        """Initialize LangChain components"""
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Initialize Qdrant vector store
        self.vector_store = Qdrant(
            client=None,  # Will be initialized with Qdrant client
            collection_name="devops_knowledge",
            embeddings=self.embeddings
        )
        
        # Initialize custom Ollama LLM
        self.llm = OllamaLLM(
            model_name=self.config.MODEL_PATH,
            ollama_url=self.config.ollama_url,
            temperature=0.7
        )
        
        # Create retrieval QA chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(
                search_kwargs={"k": 3}
            ),
            return_source_documents=True
        )
    
    async def query(self, question: str, context: Optional[str] = None) -> dict:
        """Query the knowledge base with LangChain"""
        if not self.qa_chain:
            await self.initialize()
        
        # Enhance question with context if provided
        full_question = question
        if context:
            full_question = f"Context: {context}\n\nQuestion: {question}"
        
        # Get response from LangChain
        result = await self.qa_chain.ainvoke({"query": full_question})
        
        return {
            "answer": result["result"],
            "source_documents": result.get("source_documents", [])
        }
