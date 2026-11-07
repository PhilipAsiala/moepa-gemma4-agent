"""Layer 2: Ontology — directed AST multigraph + embedding-backed context bounds.

Consumes the competition data substrate documented in docs/data-substrate.md:

- graphs/*.json  → nodes[{id, text, ...}], edges[{source, target, ...}]
- embeddings/*.npz → one float32[256] array per node id (competition layout)
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set

import numpy as np


class OntologySubstrate:
    def __init__(self, graph_path: Path, embedding_path: Optional[Path] = None):
        with open(graph_path, "r", encoding="utf-8") as f:
            self.graph_data = json.load(f)
        raw_nodes = self.graph_data.get("nodes", [])
        self.node_ids: List[str] = [n["id"] for n in raw_nodes if "id" in n]
        self.nodes: Dict[str, dict] = {n["id"]: n for n in raw_nodes if "id" in n}
        self.edges: List[dict] = self.graph_data.get("edges", [])
        self.embeddings: Optional[np.ndarray] = None
        if embedding_path is not None and embedding_path.exists():
            self.embeddings = self._load_embedding_matrix(embedding_path)

    def _load_embedding_matrix(self, embedding_path: Path) -> np.ndarray:
        """Build a (N, 256) matrix aligned to `self.node_ids` from .npz or .npy."""
        loaded = np.load(embedding_path)
        if isinstance(loaded, np.lib.npyio.NpzFile):
            missing = [nid for nid in self.node_ids if nid not in loaded.files]
            if missing:
                raise ValueError(
                    f"{len(missing)} graph nodes missing from {embedding_path.name} "
                    f"(e.g. {missing[0]!r})"
                )
            arr = np.stack([loaded[nid] for nid in self.node_ids]).astype(np.float32)
        else:
            arr = np.asarray(loaded)
            if arr.ndim != 2:
                raise ValueError(f"embeddings must be 2-d, got shape {arr.shape}")
            if arr.shape[0] != len(self.node_ids):
                raise ValueError(
                    f"embedding rows ({arr.shape[0]}) != node count ({len(self.node_ids)}); "
                    "rows must align with graph nodes in order"
                )
            arr = arr.astype(np.float32)
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return arr / norms

    def get_code_neighbors(self, symbol_id: str, hops: int = 1) -> Set[str]:
        """Traverse directed AST multigraph edges up to k hops (undirected expansion)."""
        visited: Set[str] = {symbol_id}
        frontier: Set[str] = {symbol_id}
        for _ in range(hops):
            next_frontier: Set[str] = set()
            for edge in self.edges:
                src, dst = edge.get("source"), edge.get("target")
                if src in frontier and dst in self.nodes and dst not in visited:
                    next_frontier.add(dst)
                elif dst in frontier and src in self.nodes and src not in visited:
                    next_frontier.add(src)
            visited.update(next_frontier)
            frontier = next_frontier
        return visited

    def build_bounded_context(self, seed_symbols: List[str], hops: int = 1) -> Dict[str, str]:
        """Formal ontological context map {symbol_id: source_text}."""
        active_symbols: Set[str] = set()
        for sym in seed_symbols:
            if sym in self.nodes:
                active_symbols.update(self.get_code_neighbors(sym, hops=hops))
        return {
            sym_id: self.nodes[sym_id].get("text", "")
            for sym_id in active_symbols
            if sym_id in self.nodes
        }

    def seed_symbols_from_text(self, text: str, limit: int = 8) -> List[str]:
        """Lexical seed extraction: short names / path hints from the issue that hit graph ids.

        Offline fallback when a query embedding for search_similar_code is unavailable.
        """
        tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", text))
        matched = [
            node_id
            for node_id in self.node_ids
            if node_id.split(".")[-1].split(":")[-1] in tokens
        ]
        if matched:
            return matched[:limit]
        # Path-like hints: "fastapi/routing.py" → prefix fastapi.routing
        path_hints = re.findall(
            r"([A-Za-z0-9_./-]+\.py)", text
        )
        for hint in path_hints:
            rel = hint.strip().lstrip("./")
            if rel.startswith("src/"):
                rel = rel[4:]
            prefix = rel[:-3].replace("/", ".")
            hits = [
                node_id
                for node_id in self.node_ids
                if node_id == prefix or node_id.startswith(prefix + ".")
            ]
            matched.extend(hits)
            if len(matched) >= limit:
                break
        # Deduplicate, preserve order.
        seen = set()
        ordered = []
        for node_id in matched:
            if node_id not in seen:
                seen.add(node_id)
                ordered.append(node_id)
        return ordered[:limit]

    def rank_seeds_by_embedding(
        self, query_vec: Sequence[float], top_n: int = 8
    ) -> List[str]:
        """Dense seed extraction against the 256-d substrate (search_similar_code offline).

        `query_vec` must already be the issue/traceback embedding in the same space as
        `embeddings/*.npy`. Returns node ids ordered by descending cosine similarity.
        """
        if self.embeddings is None:
            raise RuntimeError("no embeddings loaded; pass embedding_path to OntologySubstrate")
        q = np.asarray(query_vec, dtype=np.float32).reshape(-1)
        if q.shape[0] != self.embeddings.shape[1]:
            raise ValueError(
                f"query dim {q.shape[0]} != embedding dim {self.embeddings.shape[1]}"
            )
        qn = np.linalg.norm(q)
        if qn == 0:
            return []
        q = q / qn
        scores = self.embeddings @ q
        order = np.argsort(-scores)[:top_n]
        return [self.node_ids[i] for i in order]

    def reject_out_of_neighborhood(
        self, referenced_names: Iterable[str], allowed: Set[str]
    ) -> List[str]:
        """Return referenced short names that are neither in G_sub nor obviously stdlib-ish."""
        allowed_short = {a.split(".")[-1].split(":")[-1] for a in allowed}
        offenders = []
        for name in referenced_names:
            if name in allowed_short:
                continue
            if name in {"self", "cls", "super"} or name.startswith("_"):
                continue
            offenders.append(name)
        return offenders
