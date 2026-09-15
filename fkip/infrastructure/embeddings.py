from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from hashlib import blake2b


class EmbeddingModel:
    def embed(self, text: str) -> list[float]:
        raise NotImplementedError


@dataclass(frozen=True)
class HashingEmbeddingModel(EmbeddingModel):
    dimensions: int = 256

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"[a-zA-Z][a-zA-Z\-]{2,}", text.lower())
        counts = Counter(tokens)
        for token, count in counts.items():
            index = _stable_index(token, self.dimensions)
            vector[index] += float(count)
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [round(value / norm, 8) for value in vector]


def _stable_index(token: str, dimensions: int) -> int:
    digest = blake2b(token.encode("utf-8"), digest_size=4).digest()
    return int.from_bytes(digest, "big") % dimensions

