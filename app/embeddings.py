"""Explicit ONNX CPU deployment or PyTorch CUDA/CPU embedding backends."""

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
        import os

        self._use_onnx = os.environ.get("ML_EMBEDDING_BACKEND", "torch") == "onnx"
        if self._use_onnx:
            from pathlib import Path

            import onnxruntime as ort
            from tokenizers import Tokenizer

            options = ort.SessionOptions()
            options.intra_op_num_threads = 1
            options.inter_op_num_threads = 1
            options.enable_cpu_mem_arena = False
            options.enable_mem_pattern = False
            self.model = ort.InferenceSession(
                str(Path(model_path) / "model.onnx"), sess_options=options,
                providers=["CPUExecutionProvider"],
            )
            self._tokenizer = Tokenizer.from_file(str(Path(model_path) / "tokenizer.json"))
            self._tokenizer.no_truncation()
            self._tokenizer.no_padding()
            logger.info("Embedder loaded via quantized ONNX CPU backend")
            return

        import torch
        from sentence_transformers import SentenceTransformer

        if torch.version.hip:
            raise RuntimeError("ROCm/HIP PyTorch is not supported.")
        device = "cuda" if torch.version.cuda and torch.cuda.is_available() else "cpu"
        self.model: Any = SentenceTransformer(
            model_path, device=device, local_files_only=True, trust_remote_code=False
        )
        self.model.eval()
        if self.model.get_embedding_dimension() != 384:
            raise RuntimeError("Embedding model must produce exactly 384 dimensions")
        self._torch = torch
        logger.info("Embedder loaded via PyTorch device=%s", device)

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
        encoded = self._tokenizer.encode(text, add_special_tokens=True)
        if len(encoded.ids) > _MAX_SEQ_LEN:
            raise ServiceError(
                422, "embedding_text_too_long",
                f"Text exceeds this model's {_MAX_SEQ_LEN}-token limit; split into shorter passages.",
            )
        enc = {
            "input_ids": np.asarray([encoded.ids], dtype=np.int64),
            "attention_mask": np.asarray([encoded.attention_mask], dtype=np.int64),
            "token_type_ids": np.asarray([encoded.type_ids], dtype=np.int64),
        }
        inputs = {item.name: enc[item.name] for item in self.model.get_inputs()}
        token_embeddings = self.model.run(None, inputs)[0]
        # Mean pooling — pure numpy, no PyTorch needed
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
