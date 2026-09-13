from abc import ABC, abstractmethod
from typing import List
import hashlib
import httpx
import numpy as np
from app.core.config import settings

class BaseEmbeddingProvider(ABC):
    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """Generate vector embedding for single text."""
        pass

    @abstractmethod
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for multiple texts."""
        pass

class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, api_key: str, model: str = "text-embedding-3-small", dimensions: int = 1536):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.dimensions = dimensions

    async def get_embedding(self, text: str) -> List[float]:
        res = await self.client.embeddings.create(input=text, model=self.model)
        return res.data[0].embedding

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        res = await self.client.embeddings.create(input=texts, model=self.model)
        return [item.embedding for item in res.data]

class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """Direct high-performance HTTP REST client for Google Gemini Embeddings."""
    def __init__(self, api_key: str, model: str = "gemini-embedding-001", dimensions: int = 1536):
        self.api_key = api_key
        raw_model = model.replace("models/", "")
        # Map common aliases to working models
        if "004" in raw_model or "001" in raw_model:
            self.model = "gemini-embedding-001"
        else:
            self.model = raw_model
        self.dimensions = dimensions
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}"

    async def get_embedding(self, text: str) -> List[float]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}:embedContent?key={self.api_key}",
                json={
                    "content": {"parts": [{"text": text}]},
                    "outputDimensionality": self.dimensions
                }
            )
            if resp.status_code != 200:
                raise RuntimeError(f"Gemini embedding error ({resp.status_code}): {resp.text}")
            data = resp.json()
            return data["embedding"]["values"]

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        async with httpx.AsyncClient(timeout=60.0) as client:
            requests = [
                {
                    "model": f"models/{self.model}",
                    "content": {"parts": [{"text": t}]},
                    "outputDimensionality": self.dimensions
                }
                for t in texts
            ]
            results = []
            # Batch in chunks of up to 50
            for i in range(0, len(requests), 50):
                batch = requests[i:i + 50]
                resp = await client.post(
                    f"{self.base_url}:batchEmbedContents?key={self.api_key}",
                    json={"requests": batch}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("embeddings", []):
                        results.append(item["values"])
                else:
                    # Fallback to single requests if batch fails
                    for req in batch:
                        r = await client.post(
                            f"{self.base_url}:embedContent?key={self.api_key}",
                            json={"content": req["content"], "outputDimensionality": self.dimensions}
                        )
                        if r.status_code == 200:
                            results.append(r.json()["embedding"]["values"])
                        else:
                            raise RuntimeError(f"Gemini embedding batch fallback error: {r.text}")
            return results

class MockEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic normalized embedding provider for offline testing and local development."""
    def __init__(self, dimensions: int = 1536):
        self.dimensions = dimensions

    def _hash_vector(self, text: str) -> List[float]:
        seed = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16) % (2**32)
        rng = np.random.RandomState(seed)
        vec = rng.randn(self.dimensions).astype(np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    async def get_embedding(self, text: str) -> List[float]:
        return self._hash_vector(text)

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [self._hash_vector(t) for t in texts]

def get_embedding_provider() -> BaseEmbeddingProvider:
    provider = settings.EMBEDDING_PROVIDER.lower()
    if provider == "openai" and settings.OPENAI_API_KEY:
        return OpenAIEmbeddingProvider(
            api_key=settings.OPENAI_API_KEY,
            model=settings.EMBEDDING_MODEL,
            dimensions=settings.EMBEDDING_DIMENSIONS,
        )
    elif provider == "gemini" and settings.GEMINI_API_KEY:
        return GeminiEmbeddingProvider(
            api_key=settings.GEMINI_API_KEY,
            model=settings.EMBEDDING_MODEL,
            dimensions=settings.EMBEDDING_DIMENSIONS,
        )
    return MockEmbeddingProvider(dimensions=settings.EMBEDDING_DIMENSIONS)
