"""Download only the pinned upstream quantized model and Rust tokenizer data."""

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

REVISION = "e8f8c211226b894fcb81acc59f3b34ba3efd5f42"
REPOSITORY = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def main() -> None:
    """Publish completed files atomically and record vector-space identity."""
    destination = Path(sys.argv[1] if len(sys.argv) > 1 else "models/embedding_onnx")
    destination.mkdir(parents=True, exist_ok=True)
    files = {}
    for source, name in [("onnx/model_quint8_avx2.onnx", "model.onnx"),
                         ("tokenizer.json", "tokenizer.json")]:
        target = destination / name
        temporary = target.with_suffix(target.suffix + ".partial")
        url = f"https://huggingface.co/{REPOSITORY}/resolve/{REVISION}/{source}"
        with urllib.request.urlopen(url, timeout=120) as response, temporary.open("wb") as stream:
            while block := response.read(1024 * 1024):
                stream.write(block)
        temporary.replace(target)
        files[name] = hashlib.sha256(target.read_bytes()).hexdigest()
    (destination / "model_manifest.json").write_text(json.dumps({
        "repository": REPOSITORY, "revision": REVISION,
        "artifact": "onnx/model_quint8_avx2.onnx", "dimensions": 384,
        "max_tokens": 128, "pooling": "attention-masked-mean-l2",
        "vector_space": "multilingual-minilm-l12-v2-quint8-avx2-v1", "sha256": files,
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
