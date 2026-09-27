"""Pure Python text cleanup and numerical helpers for the Analytics Lead."""

import math
import re
import unicodedata
from collections.abc import Sequence


def normalize_text(text: str) -> str:
    """Normalize Unicode and whitespace, retaining script-significant joiners.

    Line boundaries are retained for resume interpretation. This is text cleanup,
    not a guarantee against prompt injection; the extractor treats text as data.
    """
    text = unicodedata.normalize("NFKC", text).replace("\r\n", "\n").replace("\r", "\n")
    text = "".join(
        c for c in text if c in "\n\t\u200c\u200d" or not unicodedata.category(c).startswith("C")
    )
    if not text.replace("\u200c", "").replace("\u200d", "").strip():
        return ""
    return "\n".join(
        line for line in (re.sub(r"[^\S\n]+", " ", s).strip() for s in text.split("\n")) if line
    )


def cosine_similarity(candidate: Sequence[float], job: Sequence[float]) -> float:
    """Return cosine similarity in [-1, 1] for equal-length finite vectors.

    Raises ValueError for empty, mismatched, zero-norm or non-finite vectors.
    Scale before computing norms to avoid overflow on large finite inputs.
    Both vectors must come from the same model, revision and preprocessing.
    Similarity is not a hiring probability or a calibrated fit percentage.
    """
    a, b = [float(v) for v in candidate], [float(v) for v in job]
    if not a or len(a) != len(b):
        raise ValueError("Vectors must be nonempty and have identical dimensions")
    if not all(math.isfinite(v) for v in a + b):
        raise ValueError("Vectors must contain only finite numbers")
    sa, sb = max(map(abs, a)), max(map(abs, b))
    if sa == 0 or sb == 0:
        raise ValueError("Cosine similarity is undefined for a zero vector")
    a, b = [v / sa for v in a], [v / sb for v in b]
    value = math.fsum(x * y for x, y in zip(a, b, strict=True)) / (math.hypot(*a) * math.hypot(*b))
    return max(-1.0, min(1.0, value))
