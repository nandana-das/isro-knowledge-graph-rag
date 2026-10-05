"""
KG-RAG ISRO Domain QA — Streamlit Demo
KG-RAG only version
Run with: streamlit run app.py
"""

import json
import streamlit as st
import sys
import time
from pathlib import Path

st.set_page_config(
    page_title="KG-RAG: ISRO Domain QA",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-title { font-size: 2.2rem; font-weight: 700; color: #012258; margin-bottom: 0.2rem; }
    .subtitle { font-size: 1rem; color: #555; margin-bottom: 1.5rem; }
    .stat-box { background: #E8F4F8; border-left: 4px solid #012258; padding: 0.8rem 1rem; border-radius: 4px; margin-bottom: 0.5rem; }
    .stat-number { font-size: 1.6rem; font-weight: 700; color: #012258; }
    .stat-label { font-size: 0.85rem; color: #555; }
    .answer-kgrag { background: #F0FFF4; border-left: 4px solid #2E7D32; padding: 1.2rem; border-radius: 6px; font-size: 1.05rem; min-height: 100px; color: #1A1A1A !important; line-height: 1.6; }
    .idk-box { background: #FFF3E0; border-left: 4px solid #E65100; padding: 1.2rem; border-radius: 6px; font-size: 1.05rem; color: #1A1A1A !important; }
    .context-box { background: #F8F9FA; border: 1px solid #DEE2E6; padding: 0.8rem; border-radius: 4px; font-size: 0.82rem; font-family: monospace; white-space: pre-wrap; max-height: 200px; overflow-y: auto; color: #333 !important; }
</style>
""", unsafe_allow_html=True)

ROOT = Path(__file__).resolve().parent
RESULTS_PATH = ROOT / "data" / "results" / "evaluation_results.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_canonical_results():
    if not RESULTS_PATH.exists():
        return {}
    with RESULTS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_resource(show_spinner="Loading KG-RAG pipeline...")
def load_pipeline():
    from src.retriever.kg_retriever import get_kg_context, _load_graph
    from src.retriever.faiss_retriever import get_passage_context
    from src.generator.ollama_api import generate
    import spacy
    from src.kg_builder.entity_ruler import add_entity_ruler

    nlp = spacy.load("en_core_web_lg")
    nlp = add_entity_ruler(nlp)
    G = _load_graph()

    return {
        'get_kg_context': get_kg_context,
        'get_passage_context': get_passage_context,
        'generate': generate,
        'nlp': nlp,
        'graph': G,
    }

# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🚀 KG-RAG for ISRO")
    st.markdown("---")

    canonical = load_canonical_results()
    results = canonical.get("system_results", {})
    graph_stats = canonical.get("graph_stats", {})
    try:
        pipeline = load_pipeline()
        G = pipeline['graph']
        n_nodes = G.number_of_nodes()
        n_edges = G.number_of_edges()
        st.success("Pipeline loaded ✅")
    except Exception as e:
        st.error(f"Pipeline error: {e}")
        pipeline = None
        n_nodes = int(graph_stats.get("nodes", 0) or 0)
        n_edges = int(graph_stats.get("edges", 0) or 0)

    st.markdown("### 📊 System Stats")
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-number">{n_nodes:,}</div>
        <div class="stat-label">KG Nodes</div>
    </div>
    <div class="stat-box">
        <div class="stat-number">{n_edges:,}</div>
        <div class="stat-label">KG Edges</div>
    </div>
    <div class="stat-box">
        <div class="stat-number">{len(results) if results else 0}</div>
        <div class="stat-label">Systems Evaluated</div>
    </div>
    <div class="stat-box">
        <div class="stat-number">{canonical.get('evaluation_protocol', {}).get('test_size', 0)}</div>
        <div class="stat-label">Test Questions</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### ⚙️ Pipeline")
    st.markdown("""
    - **Scraper:** Firecrawl API
    - **NER:** spaCy + 175-pattern ISRO EntityRuler
    - **KG:** NetworkX MultiDiGraph
    - **Encoder:** all-MiniLM-L6-v2
    - **Index:** FAISS Flat L2
    - **LLM:** Mistral-7B-Instruct Q4_K_M
    """)

    st.markdown("### 📈 Canonical Benchmark")
    if results:
        kg = results.get("kg_rag", {})
        st.markdown(f"""
        | Metric | Score |
        |---|---|
        | ROUGE-L | {kg.get('rouge_l', 0.0):.4f} |
        | Coverage | {kg.get('reference_token_coverage', 0.0):.4f} |
        | Exact Match | {kg.get('exact_match', 0.0):.4f} |
        | IDK Rate | {kg.get('idk_rate', 0.0):.4f} |
        """)
    else:
        st.markdown("Results file is not available yet.")

    show_context = st.checkbox("Show retrieved context", value=False)

# ── Main ──────────────────────────────────────────────────────────
st.markdown('<div class="main-title">🛰️ KG-RAG: ISRO Domain QA</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Knowledge Graph-Augmented Retrieval-Augmented Generation on Resource-Constrained Hardware</div>', unsafe_allow_html=True)
st.markdown("**Alliance University · Nandana Narayan Das · Gowri Kannan**")
st.markdown("---")

# ── Sample questions ──────────────────────────────────────────────
st.markdown("#### 💡 Try a sample question")

col1, col2, col3 = st.columns(3)
samples = [
    ("🌕 Chandrayaan-3", "When did Chandrayaan-3 land on the Moon?"),
    ("🔴 Mangalyaan", "What was the primary objective of Mangalyaan?"),
    ("🛸 PSLV record", "What record did PSLV-C37 set?"),
    ("☀️ Aditya-L1", "What is the mission of Aditya-L1?"),
    ("👨‍🚀 Gaganyaan", "Who are the astronauts selected for Gaganyaan?"),
    ("📡 NavIC", "Why was NavIC developed by India?"),
]

selected = None
with col1:
    for label, q in samples[:2]:
        if st.button(label, use_container_width=True):
            selected = q
with col2:
    for label, q in samples[2:4]:
        if st.button(label, use_container_width=True):
            selected = q
with col3:
    for label, q in samples[4:]:
        if st.button(label, use_container_width=True):
            selected = q

st.markdown("---")

question = st.text_input(
    "Ask any ISRO question:",
    value=selected or "",
    placeholder="e.g. When was Chandrayaan-2 launched?"
)

ask_btn = st.button("🔍 Ask KG-RAG", type="primary")

# ── Answer ────────────────────────────────────────────────────────
if ask_btn and question.strip():
    if pipeline is None:
        st.error("Pipeline not loaded. Make sure Ollama is running.")
    else:
        with st.spinner("Retrieving from KG and FAISS..."):
            nlp = pipeline['nlp']
            doc = nlp(question)
            entities = [ent.text for ent in doc.ents if ent.text.strip()]
            kg_ctx = pipeline['get_kg_context'](entities)
            pass_ctx = pipeline['get_passage_context'](question, top_k=3)
            parts = [x for x in [kg_ctx, pass_ctx] if x.strip()]
            context = "\n\n".join(parts)

        with st.spinner("Generating answer with Mistral-7B..."):
            t0 = time.time()
            answer = pipeline['generate'](question, context)
            elapsed = time.time() - t0

        st.markdown("---")
        st.markdown("### 💬 Answer")

        is_idk = "don't know" in answer.lower() or not answer.strip()
        if is_idk:
            st.markdown(f'<div class="idk-box">⚠️ {answer}</div>', unsafe_allow_html=True)
            st.caption("The system could not find sufficient evidence in the ISRO corpus.")
        else:
            st.markdown(f'<div class="answer-kgrag">{answer}</div>', unsafe_allow_html=True)

        st.caption(f"⏱️ {elapsed:.1f}s | Entities: {', '.join(entities) if entities else 'none'} | KG triples: {kg_ctx.count('.') if kg_ctx else 0}")

        if show_context:
            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### 🕸️ KG Context (Graph Triples)")
                if kg_ctx.strip():
                    st.markdown(f'<div class="context-box">{kg_ctx}</div>', unsafe_allow_html=True)
                else:
                    st.info("No KG triples found for this query.")
            with c2:
                st.markdown("#### 📄 Passage Context (FAISS)")
                if pass_ctx.strip():
                    preview = pass_ctx[:600] + "..." if len(pass_ctx) > 600 else pass_ctx
                    st.markdown(f'<div class="context-box">{preview}</div>', unsafe_allow_html=True)
                else:
                    st.info("No passage context found.")

elif ask_btn and not question.strip():
    st.warning("Please enter a question.")

# ── Expandable sections ───────────────────────────────────────────
st.markdown("---")
with st.expander("📐 How KG-RAG Works", expanded=False):
    st.markdown("""
    ```
    User Query
        │
        ├─── spaCy NER + ISRO EntityRuler (175 patterns)
        │         │
        │    KG Lookup → 1-hop Neighbourhood Expansion
        │         │
        │    Graph Context (entity-relation triples)
        │
        ├─── MiniLM-L6-v2 Encoder → FAISS Search
        │         │
        │    Passage Context (top-3 chunks)
        │
        └─── Merge → Mistral-7B-Instruct Q4_K_M (Ollama)
                  │
              Final Answer
    ```
    """)

with st.expander("📊 Canonical Evaluation Results", expanded=False):
    canonical = load_canonical_results()
    results = canonical.get("system_results", {})
    if results:
        st.markdown("""
        #### ISRO-QA Benchmark (180-question test set)
        | System | ROUGE-L | Coverage | Exact Match | IDK% |
        |---|---:|---:|---:|---:|
        | BM25 + LLM | 0.2915 | 0.4340 | 0.0278 | 1.67% |
        | Vanilla RAG | 0.2780 | 0.3989 | 0.0333 | 12.22% |
        | KG-RAG | 0.2736 | 0.3921 | 0.0333 | 11.67% |
        """)
        tier_results = canonical.get("tier_results", {})
        if tier_results:
            st.markdown("""
            #### Per-tier results on the 180-question test set
            | System | Tier 1 | Tier 2 | Tier 3 |
            |---|---|---|---|
            | BM25 + LLM | 0.3220 / 0.5199 / 0.0556 / 3.33% | 0.2587 / 0.3448 / 0.0000 / 0.00% | 0.2647 / 0.3532 / 0.0000 / 0.00% |
            | Vanilla RAG | 0.3222 / 0.4632 / 0.0667 / 12.22% | 0.2306 / 0.3213 / 0.0000 / 11.11% | 0.2387 / 0.3546 / 0.0000 / 13.89% |
            | KG-RAG | 0.3080 / 0.4381 / 0.0667 / 15.56% | 0.2246 / 0.3462 / 0.0000 / 9.26% | 0.2611 / 0.3456 / 0.0000 / 5.56% |
            """)
    else:
        st.info("Canonical evaluation results are not available yet. See data/results/evaluation_results.json.")

st.caption("KG-RAG for ISRO Domain QA · Alliance University · ICNLP 2027")