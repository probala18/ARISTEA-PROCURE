"""
Embedding Provider Abstraction for Module 5.
Supports 384-dimensional vector embeddings for Indian Standards and search queries.

Architectural Rule:
The ONNX embedding provider is the primary neural semantic retrieval mechanism (Torch-free).
The deterministic embedding provider is strictly an offline/testing fallback and
must never be presented as equivalent to pretrained semantic embeddings.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import os
import logging
import hashlib
import numpy as np

from backend.app.core.config import settings

logger = logging.getLogger("retrieval.embedding")


class EmbeddingTextBuilder:
    """Constructs canonical domain embedding text from standard fields and relationships."""

    @staticmethod
    def build_standard_embedding_text(standard: Any) -> str:
        """
        Builds rich embedding text from:
        - standard number & canonical ID
        - title
        - scope
        - description
        - category & subject area
        - keywords
        - relationships (normative refs, testing, safety, supersedes)
        Strictly excludes any fabricated information.
        """
        parts = []

        std_num = getattr(standard, "is_number", "") or ""
        std_id = getattr(standard, "standard_id", "") or ""
        title = getattr(standard, "title", "") or ""
        category = getattr(standard, "category", "") or ""
        subject = getattr(standard, "subject_area", "") or ""
        scope = getattr(standard, "scope", "") or ""
        description = getattr(standard, "description", "") or ""
        keywords = getattr(standard, "keywords", None) or []
        supersedes = getattr(standard, "supersedes", "") or ""

        if std_id:
            parts.append(f"Standard ID: {std_id}")
        if std_num and std_num != std_id:
            parts.append(f"IS Number: {std_num}")
        if title:
            parts.append(f"Title: {title}")
        if category:
            parts.append(f"Category: {category}")
        if subject:
            parts.append(f"Subject Area: {subject}")
        if scope:
            parts.append(f"Scope: {scope}")
        if description and description != scope:
            parts.append(f"Description: {description}")
        if keywords:
            if isinstance(keywords, list):
                parts.append(f"Keywords: {', '.join(keywords)}")
            else:
                parts.append(f"Keywords: {str(keywords)}")
        if supersedes:
            parts.append(f"Supersedes: {supersedes}")

        return " | ".join(parts)


class BaseEmbeddingProvider(ABC):
    """Abstract interface for 384-dimensional embedding models."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding vector dimension (fixed to 384)."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Human-readable identifier of the embedding model."""
        pass

    @property
    @abstractmethod
    def is_pretrained(self) -> bool:
        """True for real neural pretrained models; False for offline testing fallbacks."""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Embeds a single search query."""
        pass

    @abstractmethod
    def embed_standard(self, standard: Any) -> List[float]:
        """Embeds a standard entity using canonical text construction."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch embeds multiple texts."""
        pass


class DeterministicSemanticEmbeddingProvider(BaseEmbeddingProvider):
    """
    Offline/testing fallback provider.
    Generates deterministic 384-dimensional unit-normalized vectors using feature hashing
    and character n-gram projections.
    IMPORTANT: This is strictly an offline fallback and not equivalent to pretrained embeddings.
    """

    def __init__(self, dimension: int = 384):
        self._dim = dimension

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def model_name(self) -> str:
        return "deterministic-offline-fallback-384d"

    @property
    def is_pretrained(self) -> bool:
        return False

    def embed_query(self, text: str) -> List[float]:
        return self._vectorize(text)

    def embed_standard(self, standard: Any) -> List[float]:
        text = EmbeddingTextBuilder.build_standard_embedding_text(standard)
        return self._vectorize(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self._vectorize(t) for t in texts]

    def _vectorize(self, text: str) -> List[float]:
        if not text or not text.strip():
            # Zero vector normalized to unit length along first dimension
            v = np.zeros(self._dim, dtype=np.float32)
            v[0] = 1.0
            return v.tolist()

        vec = np.zeros(self._dim, dtype=np.float32)
        tokens = text.lower().replace("|", " ").replace(":", " ").replace("-", " ").split()

        for token in tokens:
            # Word-level hash projection
            h = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dim
            sign = 1.0 if ((h >> 8) % 2 == 0) else -1.0
            vec[idx] += sign * 1.5

            # Character 3-gram projections for morphological/partial matching
            if len(token) >= 3:
                for i in range(len(token) - 2):
                    ngram = token[i:i+3]
                    h_ng = int(hashlib.md5(ngram.encode("utf-8")).hexdigest(), 16)
                    idx_ng = h_ng % self._dim
                    sign_ng = 1.0 if ((h_ng >> 4) % 2 == 0) else -1.0
                    vec[idx_ng] += sign_ng * 0.5

        # L2 Unit Normalization
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        else:
            vec[0] = 1.0

        return vec.tolist()


class ONNXEmbeddingProvider(BaseEmbeddingProvider):
    """
    Torch-free ONNX Runtime neural embedding provider for 384-dimensional vectors.
    Uses 'sentence-transformers/all-MiniLM-L6-v2' ONNX artifacts with HuggingFace Tokenizers,
    attention-masked mean pooling, and L2 unit normalization.
    Runs entirely on CPU with zero PyTorch dependencies.
    """

    _cached_session = None
    _cached_tokenizer = None
    _cached_model_path: Optional[str] = None
    _cached_input_names: Optional[List[str]] = None

    def __init__(self, model_name: Optional[str] = None):
        self._model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self._session = None
        self._tokenizer = None
        self._input_names = []
        self._load_model()

    def _resolve_model_and_tokenizer(self):
        """Locates ONNX model and tokenizer from local resources or downloads via huggingface_hub."""
        possible_dirs = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "resources", "models", self._model_name),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "resources", "models", "all-MiniLM-L6-v2"),
        ]
        for pdir in possible_dirs:
            model_file = os.path.join(pdir, "model.onnx")
            tok_file = os.path.join(pdir, "tokenizer.json")
            if os.path.exists(model_file) and os.path.exists(tok_file):
                logger.info(f"Loaded ONNX model from local directory: {pdir}")
                return model_file, tok_file

        repo_id = self._model_name if "/" in self._model_name else f"sentence-transformers/{self._model_name}"
        from huggingface_hub import hf_hub_download
        model_file = hf_hub_download(repo_id=repo_id, filename="onnx/model.onnx")
        tok_file = hf_hub_download(repo_id=repo_id, filename="tokenizer.json")
        logger.info(f"Resolved ONNX model from Hugging Face Hub: {repo_id}")
        return model_file, tok_file

    def _load_model(self):
        """Loads ONNX Runtime session and tokenizer once per process."""
        if ONNXEmbeddingProvider._cached_session is not None and ONNXEmbeddingProvider._cached_tokenizer is not None:
            self._session = ONNXEmbeddingProvider._cached_session
            self._tokenizer = ONNXEmbeddingProvider._cached_tokenizer
            self._input_names = ONNXEmbeddingProvider._cached_input_names
            return

        try:
            import onnxruntime as ort
            from tokenizers import Tokenizer

            model_file, tok_file = self._resolve_model_and_tokenizer()

            opts = ort.SessionOptions()
            opts.intra_op_num_threads = int(os.getenv("ONNX_NUM_THREADS", "2"))
            opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

            session = ort.InferenceSession(model_file, sess_options=opts, providers=["CPUExecutionProvider"])
            tokenizer = Tokenizer.from_file(tok_file)
            tokenizer.enable_padding(pad_token="[PAD]")
            tokenizer.enable_truncation(max_length=256)

            input_names = [i.name for i in session.get_inputs()]

            ONNXEmbeddingProvider._cached_session = session
            ONNXEmbeddingProvider._cached_tokenizer = tokenizer
            ONNXEmbeddingProvider._cached_model_path = model_file
            ONNXEmbeddingProvider._cached_input_names = input_names

            self._session = session
            self._tokenizer = tokenizer
            self._input_names = input_names
            logger.info("Successfully initialized ONNX Runtime CPU embedding session.")
        except Exception as e:
            logger.error(f"Failed to initialize ONNXEmbeddingProvider: {e}")
            raise RuntimeError(
                f"Failed to load ONNX embedding model '{self._model_name}': {e}. "
                "Ensure onnxruntime and tokenizers are installed."
            ) from e

    @property
    def dimension(self) -> int:
        return settings.EMBEDDING_DIMENSION

    @property
    def model_name(self) -> str:
        return f"onnx/{self._model_name}"

    @property
    def is_pretrained(self) -> bool:
        return True

    def embed_query(self, text: str) -> List[float]:
        return self.embed_batch([text])[0]

    def embed_standard(self, standard: Any) -> List[float]:
        text = EmbeddingTextBuilder.build_standard_embedding_text(standard)
        return self.embed_query(text)

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        if not texts:
            return []

        all_embeddings: List[List[float]] = []

        for i in range(0, len(texts), batch_size):
            chunk = texts[i : i + batch_size]
            encoded = self._tokenizer.encode_batch(chunk)

            input_ids = np.array([e.ids for e in encoded], dtype=np.int64)
            attention_mask = np.array([e.attention_mask for e in encoded], dtype=np.int64)
            feeds = {"input_ids": input_ids, "attention_mask": attention_mask}
            if "token_type_ids" in self._input_names:
                feeds["token_type_ids"] = np.array([e.type_ids for e in encoded], dtype=np.int64)

            outputs = self._session.run(None, feeds)
            token_embeddings = outputs[0]

            # Mean pooling with attention mask
            input_mask_expanded = np.broadcast_to(
                np.expand_dims(attention_mask, -1), token_embeddings.shape
            ).astype(float)
            sum_embeddings = np.sum(token_embeddings * input_mask_expanded, axis=1)
            sum_mask = np.clip(input_mask_expanded.sum(axis=1), a_min=1e-9, a_max=None)
            mean_pooled = sum_embeddings / sum_mask

            # L2 unit normalization
            norms = np.linalg.norm(mean_pooled, axis=1, keepdims=True)
            normalized = mean_pooled / np.clip(norms, a_min=1e-12, a_max=None)
            all_embeddings.extend(normalized.tolist())

        return all_embeddings


# Backward compatibility alias
SentenceTransformerEmbeddingProvider = ONNXEmbeddingProvider


_cached_provider: Optional[BaseEmbeddingProvider] = None


def get_embedding_provider(prefer_pretrained: Optional[bool] = None) -> BaseEmbeddingProvider:
    """
    Factory to retrieve embedding provider.
    Returns ONNXEmbeddingProvider for production neural semantic retrieval (torch-free).
    Falls back to DeterministicSemanticEmbeddingProvider strictly if requested or in offline/test mode.
    """
    global _cached_provider

    backend = getattr(settings, "EMBEDDING_BACKEND", "onnx").lower()
    if backend == "deterministic":
        return DeterministicSemanticEmbeddingProvider()

    if prefer_pretrained is None:
        prefer_pretrained = getattr(settings, "USE_PRETRAINED_EMBEDDINGS", True)

    if prefer_pretrained:
        if _cached_provider is not None and isinstance(_cached_provider, ONNXEmbeddingProvider):
            return _cached_provider
        provider = ONNXEmbeddingProvider()
        _cached_provider = provider
        return provider

    return DeterministicSemanticEmbeddingProvider()
