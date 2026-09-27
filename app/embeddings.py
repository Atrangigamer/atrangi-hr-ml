"""Embedding model loader: CUDA > CPU PyTorch > ONNX Runtime, in priority order."""

import logging
import math
from typing import Any

import numpy as np

from .errors import ServiceError

logger = logging.getLogger("ml_service")
_MAX_SEQ_LEN = 128  # paraphrase-multilingual-MiniLM-L12-v2 limit


class Embedder:
    """Own the startup-loaded model; invoke only under the shared inference gate."""

    def __init__(self, model_path: str) -> None:
        self._use_onnx = False
        try:
            import torch  # noqa: PLC0415
            if torch.version.hip:
                raise RuntimeError("ROCm/HIP PyTorch is not supported.")
            cuda_ok = bool(torch.version.cuda) and torch.cuda.is_available()
            device = "cuda" if cuda_ok else "cpu"
            if not cuda_ok:
                logger.warning("CUDA unavailable; trying CPU PyTorch.")
            from sentence_transformers import SentenceTransformer  # noqa: PLC0415
            self.model: Any = SentenceTransformer(
                model_path, device=device, local_files_only=True, trust_remote_code=False
            )
            self.model.eval()
            if self.model.get_embedding_dimension() != 384:
                raise RuntimeError("Embedding model must produce exactly 384 dimensions")
            self._torch = torch
            logger.info("Embedder loaded via PyTorch device=%s", device)
        except Exception as torch_err:  # noqa: BLE001
            logger.warning("PyTorch unavailable (%s); falling back to ONNX Runtime.", type(torch_err).__name__)
            try:
                from optimum.onnxruntime import ORTModelForFeatureExtraction  # noqa: PLC0415
                from transformers import AutoTokenizer  # noqa: PLC0415
                self.model = ORTModelForFeatureExtraction.from_pretrained(
                    model_path, local_files_only=True
                )
                self._tokenizer = AutoTokenizer.from_pretrained(
                    model_path, local_files_only=True
                )
                self._use_onnx = True
                logger.info("Embedder loaded via ONNX Runtime (~250 MB RAM).")
            except Exception as onnx_err:  # noqa: BLE001
                raise RuntimeError(
                    f"Could not load embedding model via PyTorch ({torch_err}) or ONNX ({onnx_err})"
                ) from onnx_err

    def embed(self, text: str) -> list[float]:
        """Embed without silent truncation, returning normalized Python floats."""
        if self._use_onnx:
            return self._embed_onnx(text)
        return self._embed_torch(text)

    def _embed_torch(self, text: str) -> list[float]:
        tokens = self.model.tokenizer(text, add_special_tokens=True, truncation=False)["input_ids"]
        if len(tokens) > self.model.max_seq_length:
            raise ServiceError(
                422,
                "embedding_text_too_long",
                f"Text exceeds this model's {self.model.max_seq_length}-token limit; split into shorter passages.",
            )
        with self._torch.inference_mode():
            vector = self.model.encode(
                text, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False
            )
        return self._validate(vector.tolist())

    def _embed_onnx(self, text: str) -> list[float]:
        enc = self._tokenizer(
            text, return_tensors="np", truncation=False, add_special_tokens=True
        )
        if enc["input_ids"].shape[1] > _MAX_SEQ_LEN:
            raise ServiceError(
                422,
                "embedding_text_too_long",
                f"Text exceeds this model's {_MAX_SEQ_LEN}-token limit; split into shorter passages.",
            )
        outputs = self.model(**enc)
        # Mean pooling — pure numpy, no PyTorch needed
        token_embeddings = outputs.last_hidden_state  # (1, seq, 384)
        mask = enc["attention_mask"].astype(np.float32)[..., np.newaxis]  # (1, seq, 1)
        pooled = (token_embeddings * mask).sum(axis=1) / mask.sum(axis=1).clip(min=1e-9)
        norm = pooled / np.linalg.norm(pooled, axis=-1, keepdims=True).clip(min=1e-9)
        return self._validate(norm[0].tolist())

    def _validate(self, values: list[float]) -> list[float]:
        values = [float(v) for v in values]
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
