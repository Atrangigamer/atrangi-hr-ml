"""Prepare local model snapshots and a revision manifest before offline deployment."""

import argparse
import json
import shutil
from pathlib import Path


def main() -> None:
    """Resolve exact revisions once, download files, and record provenance."""
    from huggingface_hub import HfApi, hf_hub_download, snapshot_download

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path("models"))
    parser.add_argument("--embedding-revision", default="main")
    parser.add_argument("--llm-revision", default="main")
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    embedding_repo = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    llm_repo = "Qwen/Qwen2.5-1.5B-Instruct-GGUF"
    llm_file = "qwen2.5-1.5b-instruct-q4_k_m.gguf"
    api = HfApi()
    embedding_sha = api.model_info(embedding_repo, revision=args.embedding_revision).sha
    llm_sha = api.model_info(llm_repo, revision=args.llm_revision).sha
    snapshot_download(
        embedding_repo,
        revision=embedding_sha,
        local_dir=args.directory / "embedding",
        allow_patterns=["*.json", "*.txt", "*.model", "*.safetensors", "README.md"],
    )
    source = hf_hub_download(llm_repo, llm_file, revision=llm_sha)
    shutil.copyfile(source, args.directory / "resume.gguf")
    manifest = {
        "embedding": {"repo": embedding_repo, "revision": embedding_sha, "dimensions": 384},
        "llm": {"repo": llm_repo, "revision": llm_sha, "file": llm_file},
        "preprocessing": "nfkc-script-joiners-v2",
        "embedding_policy": "short-passages-no-truncation-v1",
    }
    (args.directory / "model_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(
        "Models prepared. Record model_manifest.json with your deployment and vector-space metadata."
    )


if __name__ == "__main__":
    main()
