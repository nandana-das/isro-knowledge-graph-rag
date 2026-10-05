"""Knowledge-graph context retrieval for the main KG-RAG pipeline.

The canonical pipeline uses one-hop neighbourhood expansion; two-hop retrieval
remains available as an optional experimental flag.
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path

from matplotlib import text
import networkx as nx

ROOT = Path(__file__).resolve().parents[2]
KG_PKL_PATH = ROOT / "data" / "kg" / "knowledge_graph.pkl"
KG_JSON_PATH = ROOT / "data" / "kg" / "knowledge_graph.json"

_graph: nx.MultiDiGraph | None = None


def _load_graph() -> nx.MultiDiGraph:
    global _graph
    if _graph is not None:
        return _graph

    if KG_PKL_PATH.exists():
        with open(KG_PKL_PATH, "rb") as f:
            _graph = pickle.load(f)
    elif KG_JSON_PATH.exists():
        data = json.loads(KG_JSON_PATH.read_text(encoding="utf-8"))
        _graph = nx.MultiDiGraph()
        for node in data.get("nodes", []):
            _graph.add_node(node)
        for edge in data.get("edges", []):
            _graph.add_edge(
                edge["source"],
                edge["target"],
                relation=edge.get("relation", "related_to"),
                source=edge.get("doc_source", ""),
            )
    else:
        _graph = nx.MultiDiGraph()

    return _graph


def _get_one_hop(G: nx.MultiDiGraph, entity: str) -> list[tuple[str, str, str]]:
    """Get all direct (one-hop) neighbours of an entity."""
    triples = []
    if entity not in G:
        return triples
    for _, neighbor, data in G.out_edges(entity, data=True):
        relation = data.get("relation", "related_to")
        triples.append((entity, relation, neighbor))
    for predecessor, _, data in G.in_edges(entity, data=True):
        relation = data.get("relation", "related_to")
        triples.append((predecessor, relation, entity))
    return triples


def _get_two_hop(G: nx.MultiDiGraph, entity: str, max_triples: int = 50) -> list[tuple[str, str, str]]:
    """
    Get one-hop and two-hop neighbours of an entity.
    Two-hop: entity -> neighbour -> neighbour_of_neighbour
    Limited to max_triples to avoid context explosion.
    """
    triples = []

    if entity not in G:
        return triples

    # One-hop neighbours
    one_hop_nodes = set()
    for _, neighbor, data in G.out_edges(entity, data=True):
        relation = data.get("relation", "related_to")
        triples.append((entity, relation, neighbor))
        one_hop_nodes.add(neighbor)
    for predecessor, _, data in G.in_edges(entity, data=True):
        relation = data.get("relation", "related_to")
        triples.append((predecessor, relation, entity))
        one_hop_nodes.add(predecessor)

    # Two-hop neighbours
    two_hop_triples = []
    for hop1_node in one_hop_nodes:
        for _, hop2_node, data in G.out_edges(hop1_node, data=True):
            if hop2_node == entity:
                continue
            relation = data.get("relation", "related_to")
            two_hop_triples.append((hop1_node, relation, hop2_node))
        for hop0_node, _, data in G.in_edges(hop1_node, data=True):
            if hop0_node == entity:
                continue
            relation = data.get("relation", "related_to")
            two_hop_triples.append((hop0_node, relation, hop1_node))

    remaining = max_triples - len(triples)
    triples.extend(two_hop_triples[:max(0, remaining)])

    return triples


NOISE_RELATIONS = {
    'compound', 'pobj', 'npadvmod', 'appos', 'nmod',
    'amod', 'det', 'punct', 'prep', 'cc', 'conj',
    'nsubj', 'dobj', 'attr', 'advmod', 'aux', 'mark',
    'ROOT', 'poss', 'relcl', 'acl', 'nummod', 'quantmod',
    'dep', 'parataxis', 'intj', 'expl', 'csubj', 'ccomp',
    'xcomp', 'advcl', 'pcomp', 'agent', 'neg', 'cop',
    'predet', 'preconj', 'possessive', 'case', 'nsubjpass',
    'auxpass', 'oprd', 'meta', 'dative', 'prt'
}

# Keep only clean verb-like relations
GOOD_RELATIONS = {
    'launch', 'carry', 'orbit', 'land', 'discover', 'develop',
    'build', 'design', 'operate', 'study', 'detect', 'image',
    'support', 'provide', 'use', 'include', 'contain', 'perform',
    'achieve', 'complete', 'conduct', 'establish', 'found', 'name',
    'lead', 'manage', 'head', 'direct', 'succeed', 'fail', 'crash',
    'insert', 'deploy', 'separate', 'communicate', 'track', 'monitor',
    'produce', 'generate', 'transmit', 'receive', 'measure', 'observe',
    'map', 'survey', 'explore', 'test', 'demonstrate', 'validate',
    'make', 'unveil', 'continue', 'be', 'have', 'carry_out',
    'relate', 'connect', 'link', 'associate', 'collaborate',
}


def _is_noise(text: str) -> bool:
    """Filter out pure dates, numbers, single chars, and garbage tokens."""
    text = text.strip()
    if len(text) < 3:
        return True
    alpha_count = sum(1 for c in text if c.isalpha())
    if alpha_count < 3:
        return True
    # Skip things that are mostly punctuation
    if text.startswith('(') or text.startswith('['):
        return True

    # Skip date fragments
    if any(month in text.lower() for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                                             'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
        if any(c.isdigit() for c in text):
          return True
    return False


def _serialize_triples(triples: list[tuple[str, str, str]]) -> str:
    """Convert triples to natural language sentences, filtering noise."""
    if not triples:
        return ""
    lines = []
    seen = set()
    for subj, rel, obj in triples:
        # Skip noisy dependency relations
        rel_lower = rel.lower()
        if any(noise in rel_lower for noise in NOISE_RELATIONS):
            continue
        # Skip noisy subjects or objects
        if _is_noise(subj) or _is_noise(obj):
            continue
        # Skip date-like relations
        if any(c.isdigit() for c in rel):
            continue
        # Skip subjects/objects with brackets
        if '(' in obj or '[' in obj:
            continue
        # Skip subjects that are phrases with common words
        skip_words = {'a ', 'an ', 'the ', 'live ', 'webinar', 'streaming'}
        if any(subj.lower().startswith(w) for w in skip_words):
            continue
                # Skip objects starting with articles/determiners
        obj_skip = {'a ', 'an ', 'the ', 'live ', 'webinar', 'streaming', 'of '}
        if any(obj.lower().startswith(w) for w in obj_skip):
            continue
        # Skip objects ending with month names
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                  'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        if any(obj.lower().endswith(m) for m in months):
            continue
        # Skip vague relations
        if rel.lower() in {'be', 'have'}:
            continue
        
        # Skip very long objects (likely garbled context)
        if len(obj) > 80 or len(subj) > 80:
            continue
        rel_text = rel.replace("_", " ").lower()
        line = f"{subj} {rel_text} {obj}."
        if line not in seen:
            lines.append(line)
            seen.add(line)
    return "\n".join(lines)


def get_kg_context(entities: list[str], two_hop: bool = False, max_triples_per_entity: int = 50) -> str:
    """
    Retrieve KG context for a list of entities.

    The canonical experiment uses one-hop expansion; two-hop remains an optional
    ablation mode rather than the default.
    """
    if not entities:
        return ""

    G = _load_graph()
    if G.number_of_nodes() == 0:
        return ""

    all_triples = []
    seen_triples = set()

    for entity in entities:
        if two_hop:
            triples = _get_two_hop(G, entity, max_triples=max_triples_per_entity)
        else:
            triples = _get_one_hop(G, entity)

        for triple in triples:
            key = (triple[0], triple[1], triple[2])
            if key not in seen_triples:
                all_triples.append(triple)
                seen_triples.add(key)

    if not all_triples:
        # Fuzzy fallback
        entity_lower = {e.lower() for e in entities}
        for node in G.nodes():
            if any(e in node.lower() or node.lower() in e for e in entity_lower):
                if two_hop:
                    triples = _get_two_hop(G, node, max_triples=20)
                else:
                    triples = _get_one_hop(G, node)
                for triple in triples:
                    key = (triple[0], triple[1], triple[2])
                    if key not in seen_triples:
                        all_triples.append(triple)
                        seen_triples.add(key)
                if all_triples:
                    break

    return _serialize_triples(all_triples)


if __name__ == "__main__":
    print(get_kg_context(["Chandrayaan-2", "PSLV"]))