"""Test the real embedding wrapper with controlled backend outputs."""

import sys
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.embeddings import Embedder
from app.errors import ServiceError


def backend(*, tokens=256, vector=None, dimension=384, hip=None, cuda="12.8", available=True):
    """Return minimal native module doubles with call assertions."""
    calls = []
    cuda_ok = bool(cuda) and available
    expected_device = "cuda" if cuda_ok else "cpu"

    class Transformer:
        max_seq_length = 256

        def __init__(self, path, **kwargs):
            assert kwargs == {
                "device": expected_device,
                "local_files_only": True,
                "trust_remote_code": False,
            }

        def eval(self):
            pass

        def get_embedding_dimension(self):
            return dimension

        def tokenizer(self, text, **kwargs):
            assert kwargs == {"add_special_tokens": True, "truncation": False}
            return {"input_ids": [1] * tokens}

        def encode(self, text, **kwargs):
            calls.append(text)
            assert kwargs["normalize_embeddings"] is True
            return SimpleNamespace(
                tolist=lambda: vector if vector is not None else [1.0] + [0.0] * 383
            )

    modules = {
        "torch": SimpleNamespace(
            version=SimpleNamespace(hip=hip, cuda=cuda),
            cuda=SimpleNamespace(is_available=lambda: available),
            inference_mode=nullcontext,
        ),
        "sentence_transformers": SimpleNamespace(SentenceTransformer=Transformer),
    }
    return modules, calls


def test_hip_is_rejected():
    """ROCm/HIP PyTorch must be rejected even when cuda is also set."""
    modules, _ = backend(hip="test-hip", cuda="12.8", available=True)
    with patch.dict(sys.modules, modules), pytest.raises(RuntimeError, match="ROCm"):
        Embedder("local")


@pytest.mark.parametrize(
    "cuda,available", [(None, True), ("12.8", False)]
)
def test_cpu_fallback_when_no_cuda(cuda, available):
    """When CUDA is absent the embedder must fall back to CPU without raising."""
    modules, _ = backend(hip=None, cuda=cuda, available=available)
    with patch.dict(sys.modules, modules):
        model = Embedder("local")
        assert len(model.embed("text")) == 384
        model.close()


def test_rejects_wrong_model_dimensions():
    modules, _ = backend(dimension=768)
    with patch.dict(sys.modules, modules), pytest.raises(RuntimeError, match="384"):
        Embedder("local")


@pytest.mark.parametrize("tokens", [255, 256, 257])
def test_token_boundary_never_silently_truncates(tokens):
    modules, calls = backend(tokens=tokens)
    with patch.dict(sys.modules, modules):
        model = Embedder("local")
        if tokens > 256:
            with pytest.raises(ServiceError) as caught:
                model.embed("text")
            assert caught.value.status == 422
            assert not calls
        else:
            assert len(model.embed("text")) == 384
            assert calls == ["text"]
        model.close()
        assert model.model is None


@pytest.mark.parametrize(
    "vector", [[0.0] * 384, [float("nan")] * 384, [float("inf")] * 384, [1.0] * 383]
)
def test_corrupt_native_vectors_rejected(vector):
    modules, _ = backend(vector=vector)
    with patch.dict(sys.modules, modules):
        model = Embedder("local")
        with pytest.raises(RuntimeError, match="invalid vector"):
            model.embed("text")


@pytest.mark.parametrize("magnitude", [0.5, 2.0])
def test_non_normalized_native_vector_rejected(magnitude):
    """A finite nonzero vector must still satisfy the public unit-norm contract."""
    modules, _ = backend(vector=[magnitude] + [0.0] * 383)
    with patch.dict(sys.modules, modules):
        model = Embedder("local")
        with pytest.raises(RuntimeError, match="invalid vector"):
            model.embed("text")
