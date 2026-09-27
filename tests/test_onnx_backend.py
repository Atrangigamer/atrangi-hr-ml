"""Exercise the direct ONNX path without Torch, Transformers or Optimum."""

import sys
from types import SimpleNamespace

import numpy as np
import pytest

from app.embeddings import Embedder
from app.errors import ServiceError


def make_backend(monkeypatch, count=3):
    """Install lightweight doubles and explicitly prohibit the heavyweight stack."""
    monkeypatch.setenv("ML_EMBEDDING_BACKEND", "onnx")
    for name in ("torch", "transformers", "sentence_transformers", "optimum"):
        monkeypatch.setitem(sys.modules, name, None)
    calls = []

    class Session:
        def __init__(self, path, sess_options, providers):
            assert providers == ["CPUExecutionProvider"]
            assert sess_options.intra_op_num_threads == 1

        def get_inputs(self):
            return [SimpleNamespace(name=n) for n in ["input_ids", "attention_mask"]]

        def run(self, outputs, inputs):
            calls.append(inputs)
            assert inputs["input_ids"].dtype == np.int64
            values = np.zeros((1, count, 384), dtype=np.float32)
            values[0, :, 0] = 1
            values[0, -1, 1] = 999  # padding must not affect pooling
            return [values]

    tokenizer = SimpleNamespace(
        no_truncation=lambda: None, no_padding=lambda: None,
        encode=lambda text, add_special_tokens: SimpleNamespace(
            ids=[1] * count, attention_mask=[1] * (count - 1) + [0], type_ids=[0] * count),
    )
    monkeypatch.setitem(sys.modules, "onnxruntime", SimpleNamespace(
        SessionOptions=SimpleNamespace, InferenceSession=Session))
    monkeypatch.setitem(sys.modules, "tokenizers", SimpleNamespace(
        Tokenizer=SimpleNamespace(from_file=lambda path: tokenizer)))
    return calls


def test_direct_onnx_without_torch_and_masked_pooling(monkeypatch):
    calls = make_backend(monkeypatch)
    model = Embedder("synthetic")
    assert model.embed("synthetic") == [1.0] + [0.0] * 383
    assert len(calls) == 1
    model.close()


def test_onnx_rejects_long_input_without_inference(monkeypatch):
    calls = make_backend(monkeypatch, count=129)
    with pytest.raises(ServiceError) as error:
        Embedder("synthetic").embed("long")
    assert error.value.status == 422
    assert calls == []
