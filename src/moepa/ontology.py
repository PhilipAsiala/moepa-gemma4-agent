"""Layer 2: Ontology — directed AST multigraph + embedding-backed context bounds."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Set

import numpy as np


class OntologySubstrate:
    def __init__(self, graph_path: Path, embedding_path: Optional[Path] = None):
        with open(graph_path, "r", encoding="utf-8") as f:
            self.graph_data = json.load(f)
        self.nodes: Dict[str, dict] = {
            n["id"]: n for n in self.graph_data.get("nodes", [])
        }
        self.edges: List[dict] = self.graph_data.get("edges", [])
        self.embeddings = None
        if embedding_path is not None and embedding_path.exists():
            self.embeddings = np.load(embedding_path)

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
