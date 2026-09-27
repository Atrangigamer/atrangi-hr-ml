"""Load one SentenceTransformer; uses CUDA when available, CPU otherwise."""

import logging
import math
from typing import Any

from .errors import ServiceError

logger = logging.getLogger("ml_service")


class Embedder:
    """Own the startup-loaded model; invoke only under the shared inference gate."""

    def __init__(self, model_path: str) -> None:
        import torch
        from sentence_transformers import SentenceTransformer

        if torch.version.hip:
            raise RuntimeError(
                "ROCm/HIP PyTorch is not supported; use CUDA or CPU PyTorch."
            )
        cuda_ok = bool(torch.version.cuda) and torch.cuda.is_available()
        device = "cuda" if cuda_ok else "cpu"
        if not cuda_ok:
            logger.warning("CUDA unavailable; embedding model running on CPU (slower).")
        self.model: Any = SentenceTransformer(
            model_path, device=device, local_files_only=True, trust_remote_code=False
        )
        self.model.eval()
        if self.model.get_embedding_dimension() != 384:
            raise RuntimeError("Embedding model must produce exactly 384 dimensions")

    def embed(self, text: str) -> list[float]:
        """Embed without silent truncation, returning normalized Python floats."""
        import torch

        tokens = self.model.tokenizer(text, add_special_tokens=True, truncation=False)["input_ids"]
        if len(tokens) > self.model.max_seq_length:
            raise ServiceError(
                422,
                "embedding_text_too_long",
                f"Text exceeds this model's {self.model.max_seq_length}-token limit; split into shorter passages.",
            )
        with torch.inference_mode():
            vector = self.model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
        values = [float(v) for v in vector.tolist()]
        if (
            len(values) != 384
            or not all(math.isfinite(v) for v in values)
            or not math.isclose(math.hypot(*values), 1.0, rel_tol=1e-5, abs_tol=1e-5)
        ):
            raise RuntimeError("Embedding model produced an invalid vector")
        return values

    def close(self) -> None:
        """Release model references after all inference has drained."""
        self.model = None
