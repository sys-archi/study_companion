"""FAISS-backed per-document vector store."""

import json
from pathlib import Path

import faiss
import numpy as np
from django.conf import settings


class DocumentVectorStore:
    """
    Manages a FAISS index and chunk metadata for one document.
    Persisted to disk under VECTOR_STORE_DIR/{document_id}/.
    """

    def __init__(self, document_id: int):
        self.document_id = document_id
        self.store_dir = Path(settings.VECTOR_STORE_DIR) / str(document_id)
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.store_dir / "index.faiss"
        self.meta_path = self.store_dir / "metadata.json"
        self._index = None
        self._metadata: list[dict] = []

    def _load(self):
        if self._index is not None:
            return
        if self.index_path.exists() and self.meta_path.exists():
            self._index = faiss.read_index(str(self.index_path))
            self._metadata = json.loads(self.meta_path.read_text(encoding="utf-8"))
        else:
            self._index = None
            self._metadata = []

    def build(self, chunk_records: list[dict], vectors: list[list[float]]):
        """
        Build and persist index from chunk records and embedding vectors.
        chunk_records: [{"chunk_id": int, "chunk_index": int, "text": str}, ...]
        """
        if not vectors:
            return

        dim = len(vectors[0])
        matrix = np.array(vectors, dtype=np.float32)
        faiss.normalize_L2(matrix)

        index = faiss.IndexFlatIP(dim)
        index.add(matrix)

        self._index = index
        self._metadata = chunk_records
        faiss.write_index(index, str(self.index_path))
        self.meta_path.write_text(json.dumps(self._metadata), encoding="utf-8")

    def search(self, query_vector: list[float], top_k: int = 5) -> list[dict]:
        """Return top-k chunks with scores."""
        self._load()
        if self._index is None or self._index.ntotal == 0:
            return []

        q = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(q)
        k = min(top_k, self._index.ntotal)
        scores, indices = self._index.search(q, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            meta = self._metadata[idx]
            results.append({**meta, "score": float(score)})
        return results

    def delete(self):
        """Remove persisted vector store files."""
        if self.index_path.exists():
            self.index_path.unlink()
        if self.meta_path.exists():
            self.meta_path.unlink()
        if self.store_dir.exists() and not any(self.store_dir.iterdir()):
            self.store_dir.rmdir()
