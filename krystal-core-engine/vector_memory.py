"""Pinecone vector database for Krystal's long-term semantic memory."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from pinecone import Pinecone, ServerlessSpec
    from google import genai
    PINECONE_AVAILABLE = True
    GENAI_AVAILABLE = True
except ImportError as e:
    PINECONE_AVAILABLE = False
    GENAI_AVAILABLE = False
    missing_packages = []
    if 'pinecone' in str(e):
        missing_packages.append('pinecone')
    if 'google' in str(e):
        missing_packages.append('google-genai')
    print(f"Warning: Vector memory not available. Install with: pip install {' '.join(missing_packages)}")


class PineconeManager:
    """Manages long-term semantic memory using Pinecone vector database."""
    
    def __init__(self, api_key: Optional[str] = None, index_name: str = "krystal-memory"):
        """
        Initialize Pinecone connection.
        
        Args:
            api_key: Pinecone API key (defaults to environment variable)
            index_name: Name of the Pinecone index
        """
        self.is_available = False
        self.index_name = index_name
        self.index = None
        
        if not PINECONE_AVAILABLE or not GENAI_AVAILABLE:
            return
            
        try:
            # Initialize Pinecone client
            self.api_key = api_key or os.environ.get('PINECONE_API_KEY')
            if not self.api_key:
                print("Warning: PINECONE_API_KEY environment variable not set")
                return
                
            self.pinecone_client = Pinecone(api_key=self.api_key)
            
            # Initialize embedding model
            self.embedding_model = 'text-embedding-004'
            # Get Gemini key from Krystal's custom key management
            from api_router import KeyManager
            root = Path(__file__).resolve().parent.parent
            env_file = root / ".env"
            keys = KeyManager(env_path=env_file if env_file.is_file() else None)
            
            # Use the first available Gemini key
            gemini_key = None
            if keys.has_gemini_keys():
                gemini_key = keys.get_next_gemini_key()
            
            self.genai_client = genai.Client(api_key=gemini_key or os.environ.get('GOOGLE_API_KEY'))
            
            # Connect or create index
            self._connect_index()
            self.is_available = True
            
        except Exception as e:
            print(f"Warning: Could not initialize Pinecone: {e}")
            self.is_available = False
    
    def _connect_index(self) -> None:
        """Connect to or create the Pinecone index."""
        try:
            # Check if index exists
            if self.index_name not in self.pinecone_client.list_indexes().names():
                # Create new index
                self.pinecone_client.create_index(
                    name=self.index_name,
                    dimension=768,  # text-embedding-004 dimension
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1")
                )
                print(f"Created new Pinecone index: {self.index_name}")
            
            # Connect to index
            self.index = self.pinecone_client.Index(self.index_name)
            
        except Exception as e:
            print(f"Warning: Could not connect to Pinecone index: {e}")
            self.index = None
    
    def _create_embedding(self, text: str) -> Optional[List[float]]:
        """Create embedding for text using Google's model."""
        if not self.is_available or not text:
            return None
            
        try:
            result = self.genai_client.models.embed_content(
                model=self.embedding_model,
                contents=text
            )
            return result.embedding.values
        except Exception as e:
            print(f"Warning: Embedding creation failed: {e}")
            return None
    
    def store_memory(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store text and metadata in vector memory.
        
        Args:
            text: The text to store
            metadata: Additional metadata (timestamp, type, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available or not self.index:
            return False
            
        try:
            # Create embedding
            embedding = self._create_embedding(text)
            if not embedding:
                return False
            
            # Prepare metadata
            if metadata is None:
                metadata = {}
            
            metadata.update({
                'timestamp': str(uuid.uuid4()),
                'stored_at': str(os.time())
            })
            
            # Upsert to Pinecone
            self.index.upsert(
                vectors=[{
                    'id': metadata.get('timestamp', str(uuid.uuid4())),
                    'values': embedding,
                    'metadata': {
                        'text': text,
                        **metadata
                    }
                }]
            )
            return True
            
        except Exception as e:
            print(f"Warning: Memory storage failed: {e}")
            return False
    
    def recall_memory(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Recall relevant memories based on query.
        
        Args:
            query: The search query
            top_k: Number of results to return
            
        Returns:
            List of relevant memories with metadata
        """
        if not self.is_available or not self.index:
            return []
            
        try:
            # Create query embedding
            query_embedding = self._create_embedding(query)
            if not query_embedding:
                return []
            
            # Search Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            # Format results
            memories = []
            for match in results.matches:
                metadata = match.metadata
                memories.append({
                    'text': metadata.get('text', ''),
                    'score': match.score,
                    'metadata': {k: v for k, v in metadata.items() if k != 'text'}
                })
            
            return memories
            
        except Exception as e:
            print(f"Warning: Memory recall failed: {e}")
            return []


# Global instance for easy access
_pinecone_manager: Optional[PineconeManager] = None


def initialize_pinecone(api_key: Optional[str] = None) -> PineconeManager:
    """
    Initialize Pinecone memory system.
    
    Args:
        api_key: Pinecone API key
        
    Returns:
        The PineconeManager instance
    """
    global _pinecone_manager
    
    if _pinecone_manager is None:
        _pinecone_manager = PineconeManager(api_key=api_key)
    
    return _pinecone_manager


def store_memory(text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
    """
    Global function to store memory.
    
    Args:
        text: The text to store
        metadata: Additional metadata
        
    Returns:
        True if successful, False otherwise
    """
    global _pinecone_manager
    
    if _pinecone_manager is None:
        _pinecone_manager = initialize_pinecone()
    
    return _pinecone_manager.store_memory(text, metadata)


def recall_memory(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Global function to recall memories.
    
    Args:
        query: The search query
        top_k: Number of results to return
        
    Returns:
        List of relevant memories
    """
    global _pinecone_manager
    
    if _pinecone_manager is None:
        _pinecone_manager = initialize_pinecone()
    
    return _pinecone_manager.recall_memory(query, top_k)
