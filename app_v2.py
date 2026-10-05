"""
KG-RAG ISRO Domain QA — Enhanced Streamlit Demo
Space-themed dark UI with full project content
Run with: streamlit run app_v2.py
"""

import streamlit as st
import sys
import time
from pathlib import Path

st.set_page_config(
    page_title="KG-RAG · ISRO Domain QA",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

    /* ── Global ── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #020B18;
        color: #E2E8F0;
    }
    .stApp { background-color: #020B18; }
    .block-container { padding: 0 2rem 4rem 2rem; max-width: 1400px; }

    /* ── Hero ── */
    .hero {
        background: linear-gradient(135deg, #020B18 0%, #0A1628 40%, #0F2040 100%);
        border-bottom: 1px solid #1E3A5F;
        padding: 3rem 2rem 2.5rem 2rem;
        margin: -1rem -2rem 2rem -2rem;
        position: relative;
        overflow: hidden;
    }
    .hero::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -10%;
        width: 600px;
        height: 600px;
        background: radial-gradient(circle, rgba(59,130,246,0.08) 0%, transparent 70%);
        pointer-events: none;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(59,130,246,0.15);
        border: 1px solid rgba(59,130,246,0.3);
        color: #60A5FA;
        padding: 0.3rem 0.9rem;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }
    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #FFFFFF 0%, #93C5FD 50%, #F97316 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1.2;
        margin-bottom: 0.8rem;
    }
    .hero-sub {
        font-size: 1.05rem;
        color: #94A3B8;
        max-width: 700px;
        line-height: 1.6;
        margin-bottom: 1.5rem;
    }
    .hero-authors {
        font-size: 0.88rem;
        color: #64748B;
    }
    .hero-authors span {
        color: #60A5FA;
        font-weight: 500;
    }

    /* ── Stat cards ── */
    .stats-row {
        display: flex;
        gap: 1rem;
        margin: 1.5rem 0 2rem 0;
        flex-wrap: wrap;
    }
    .stat-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 1rem 1.4rem;
        min-width: 140px;
        flex: 1;
    }
    .stat-card:hover {
        border-color: rgba(59,130,246,0.3);
        background: rgba(59,130,246,0.05);
        transition: all 0.2s;
    }
    .stat-val { font-family: 'Space Grotesk', sans-serif; font-size: 1.8rem; font-weight: 700; color: #F8FAFC; }
    .stat-lbl { font-size: 0.78rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.2rem; }
    .stat-icon { font-size: 1.2rem; margin-bottom: 0.3rem; }

    /* ── Section headers ── */
    .section-header {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.4rem;
        font-weight: 600;
        color: #F1F5F9;
        margin: 2.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #1E3A5F;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* ── QA Box ── */
    .qa-container {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .answer-box {
        background: linear-gradient(135deg, rgba(16,185,129,0.08) 0%, rgba(5,150,105,0.05) 100%);
        border: 1px solid rgba(16,185,129,0.25);
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        font-size: 1rem;
        color: #E2E8F0 !important;
        line-height: 1.7;
        margin-top: 1rem;
    }
    .idk-box {
        background: linear-gradient(135deg, rgba(245,158,11,0.08) 0%, rgba(217,119,6,0.05) 100%);
        border: 1px solid rgba(245,158,11,0.25);
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        font-size: 1rem;
        color: #FCD34D !important;
        line-height: 1.7;
        margin-top: 1rem;
    }
    .context-panel {
        background: rgba(0,0,0,0.3);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 10px;
        padding: 0.9rem 1rem;
        font-size: 0.82rem;
        font-family: 'Fira Code', 'Courier New', monospace;
        color: #94A3B8 !important;
        white-space: pre-wrap;
        max-height: 200px;
        overflow-y: auto;
        margin-top: 0.5rem;
    }

    /* ── Sample question buttons ── */
    .stButton button {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: #CBD5E1 !important;
        border-radius: 8px !important;
        font-size: 0.85rem !important;
        padding: 0.4rem 0.8rem !important;
        transition: all 0.2s !important;
    }
    .stButton button:hover {
        background: rgba(59,130,246,0.1) !important;
        border-color: rgba(59,130,246,0.4) !important;
        color: #93C5FD !important;
    }

    /* ── Primary button ── */
    .stButton [data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #1D4ED8, #2563EB) !important;
        border: none !important;
        color: white !important;
        padding: 0.6rem 2rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.02em !important;
        border-radius: 8px !important;
    }

    /* ── Metric cards ── */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin: 1rem 0;
    }
    .metric-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
    }
    .metric-card.best { border-color: rgba(16,185,129,0.3); background: rgba(16,185,129,0.05); }
    .metric-val { font-family: 'Space Grotesk', sans-serif; font-size: 2rem; font-weight: 700; color: #F8FAFC; }
    .metric-lbl { font-size: 0.8rem; color: #64748B; margin-top: 0.3rem; }
    .metric-sys { font-size: 0.75rem; color: #475569; margin-top: 0.2rem; }

    /* ── Pipeline steps ── */
    .pipeline-step {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: flex-start;
        gap: 1rem;
    }
    .step-num {
        background: rgba(59,130,246,0.2);
        border: 1px solid rgba(59,130,246,0.3);
        color: #60A5FA;
        border-radius: 50%;
        width: 28px;
        height: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.8rem;
        font-weight: 700;
        flex-shrink: 0;
        margin-top: 2px;
    }
    .step-title { font-weight: 600; color: #E2E8F0; font-size: 0.95rem; }
    .step-desc { color: #64748B; font-size: 0.85rem; margin-top: 0.2rem; }

    /* ── Table styling ── */
    .result-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.9rem;
        margin: 0.5rem 0;
    }
    .result-table th {
        background: rgba(59,130,246,0.1);
        color: #93C5FD;
        padding: 0.7rem 1rem;
        text-align: left;
        border-bottom: 1px solid rgba(59,130,246,0.2);
        font-weight: 600;
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .result-table td {
        padding: 0.7rem 1rem;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        color: #CBD5E1;
    }
    .result-table tr.highlight td { color: #F8FAFC; font-weight: 600; }
    .result-table tr.highlight { background: rgba(16,185,129,0.05); }
    .badge-best { background: rgba(16,185,129,0.2); color: #34D399; border-radius: 4px; padding: 0.1rem 0.4rem; font-size: 0.75rem; }
    .badge-ours { background: rgba(59,130,246,0.2); color: #60A5FA; border-radius: 4px; padding: 0.1rem 0.4rem; font-size: 0.75rem; }

    /* ── Caption / footer ── */
    .footer { text-align: center; color: #334155; font-size: 0.8rem; margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #0F2040; }

    /* hide streamlit default elements */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* input styling */
    .stTextInput input {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: #E2E8F0 !important;
        border-radius: 8px !important;
        font-size: 1rem !important;
        padding: 0.7rem 1rem !important;
    }
    .stTextInput input:focus {
        border-color: rgba(59,130,246,0.5) !important;
        box-shadow: 0 0 0 2px rgba(59,130,246,0.1) !important;
    }
    .stCheckbox label { color: #94A3B8 !important; }

</style>
""", unsafe_allow_html=True)

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

@st.cache_resource(show_spinner="🛰️ Loading KG-RAG pipeline...")
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

try:
    pipeline = load_pipeline()
    G = pipeline['graph']
    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    loaded = True
except Exception as e:
    pipeline = None
    n_nodes = 0
    n_edges = 0
    loaded = False

# ── HERO ─────────────────────────────────────────────────────────
try:
    canonical = json.loads((ROOT / 'data' / 'results' / 'evaluation_results.json').read_text(encoding='utf-8'))
except Exception:
    canonical = {}

st.markdown(f"""
<div class="hero">
    <div class="hero-badge">🛰️ M.Tech Capstone Project · Alliance University · 2026</div>
    <div class="hero-title">KG-RAG for ISRO<br>Domain Question Answering</div>
    <div class="hero-sub">
        A Knowledge Graph-Augmented Retrieval-Augmented Generation system that automatically
        constructs a domain-specific knowledge graph from ISRO's public documentation and
        answers factual questions — entirely on consumer hardware, at zero cloud cost.
    </div>
    <div class="hero-authors">
        <span>Nandana Narayan Das</span> · Alliance School of Advanced Computing &nbsp; 
    </div>
    <div class="stats-row">
        <div class="stat-card">
            <div class="stat-icon">🕸️</div>
            <div class="stat-val">{n_nodes:,}</div>
            <div class="stat-lbl">KG Nodes</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">🔗</div>
            <div class="stat-val">{n_edges:,}</div>
            <div class="stat-lbl">KG Edges</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">📄</div>
            <div class="stat-val">{canonical.get('benchmark', {}).get('test_questions', 180):,}</div>
            <div class="stat-lbl">Test Questions</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">🌐</div>
            <div class="stat-val">{canonical.get('benchmark', {}).get('total_questions', 200):,}</div>
            <div class="stat-lbl">Total Benchmark</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">🎯</div>
            <div class="stat-val">{canonical.get('evaluation_protocol', {}).get('dev_size', 20):,}</div>
            <div class="stat-lbl">Dev Set</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">📊</div>
            <div class="stat-val">{len(canonical.get('system_results', {}))}</div>
            <div class="stat-lbl">Systems</div>
        </div>
    </div>
    {'<div style="display:inline-block;background:rgba(16,185,129,0.15);border:1px solid rgba(16,185,129,0.3);color:#34D399;padding:0.3rem 0.8rem;border-radius:6px;font-size:0.82rem;">✅ Pipeline Loaded</div>' if loaded else '<div style="color:#F87171;font-size:0.85rem;">⚠️ Start Ollama to enable live QA</div>'}
</div>
""", unsafe_allow_html=True)

# ── LIVE QA ───────────────────────────────────────────────────────
st.markdown('<div class="section-header">🔍 Live Question Answering</div>', unsafe_allow_html=True)

samples = [
    ("🌕 Chandrayaan-3 landing", "When did Chandrayaan-3 land on the Moon?"),
    ("🔴 Mars Orbiter Mission", "What is the Mars Orbiter Mission?"),
    ("🛸 PSLV-C37 record", "What record did PSLV-C37 set?"),
    ("☀️ Aditya-L1 mission", "What is the mission of Aditya-L1?"),
    ("👨‍🚀 Gaganyaan crew", "Who are the astronauts selected for Gaganyaan?"),
    ("📡 NavIC purpose", "Why was NavIC developed by India?"),
    ("🌙 Chandrayaan-1 discovery", "What did Chandrayaan-1 discover on the Moon?"),
    ("🚀 GSLV Mk III", "What is GSLV Mk III used for?"),
]

cols = st.columns(4)
selected = None
for i, (label, q) in enumerate(samples):
    with cols[i % 4]:
        if st.button(label, use_container_width=True, key=f"sample_{i}"):
            selected = q

st.markdown("<br>", unsafe_allow_html=True)

col_input, col_opt = st.columns([4, 1])
with col_input:
    question = st.text_input(
        "",
        value=selected or "",
        placeholder="Ask anything about ISRO — missions, satellites, scientists, timelines...",
        label_visibility="collapsed"
    )
with col_opt:
    show_ctx = st.checkbox("Show context", value=False)

ask = st.button("🔍 Ask KG-RAG", type="primary")

if ask and question.strip():
    if not loaded:
        st.error("Pipeline not loaded. Start Ollama: `ollama serve`")
    else:
        prog = st.progress(0, text="Extracting entities from query...")
        nlp = pipeline['nlp']
        doc = nlp(question)
        entities = [ent.text for ent in doc.ents if ent.text.strip()]

        prog.progress(25, text="Searching knowledge graph...")
        kg_ctx = pipeline['get_kg_context'](entities)

        prog.progress(50, text="Searching FAISS index...")
        pass_ctx = pipeline['get_passage_context'](question, top_k=3)

        parts = [x for x in [kg_ctx, pass_ctx] if x.strip()]
        context = "\n\n".join(parts)

        prog.progress(75, text="Generating answer with Mistral-7B...")
        t0 = time.time()
        answer = pipeline['generate'](question, context)
        elapsed = time.time() - t0
        prog.progress(100, text="Done!")
        time.sleep(0.3)
        prog.empty()

        is_idk = "don't know" in answer.lower() or not answer.strip()
        box_class = "idk-box" if is_idk else "answer-box"
        prefix = "⚠️ Insufficient context: " if is_idk else ""

        st.markdown(f'<div class="{box_class}">{prefix}{answer}</div>', unsafe_allow_html=True)

        meta_col1, meta_col2, meta_col3, meta_col4 = st.columns(4)
        with meta_col1:
            st.metric("⏱️ Response time", f"{elapsed:.1f}s")
        with meta_col2:
            st.metric("🏷️ Entities found", len(entities))
        with meta_col3:
            st.metric("🕸️ KG triples", kg_ctx.count('.') if kg_ctx else 0)
        with meta_col4:
            st.metric("📄 Passages", 3 if pass_ctx.strip() else 0)

        if entities:
            st.caption(f"Entities: {' · '.join(entities)}")

        if show_ctx and (kg_ctx or pass_ctx):
            ctx_col1, ctx_col2 = st.columns(2)
            with ctx_col1:
                st.markdown("**🕸️ Knowledge Graph Context**")
                if kg_ctx.strip():
                    st.markdown(f'<div class="context-panel">{kg_ctx}</div>', unsafe_allow_html=True)
                else:
                    st.caption("No KG triples found for this query.")
            with ctx_col2:
                st.markdown("**📄 Passage Context (FAISS)**")
                if pass_ctx.strip():
                    preview = pass_ctx[:700] + "..." if len(pass_ctx) > 700 else pass_ctx
                    st.markdown(f'<div class="context-panel">{preview}</div>', unsafe_allow_html=True)
                else:
                    st.caption("No passage context found.")

elif ask:
    st.warning("Please enter a question.")

# ── HOW IT WORKS ──────────────────────────────────────────────────
st.markdown('<div class="section-header">⚙️ How It Works</div>', unsafe_allow_html=True)

pipe_col1, pipe_col2 = st.columns(2)

with pipe_col1:
    st.markdown("""
    <div class="pipeline-step">
        <div class="step-num">1</div>
        <div>
            <div class="step-title">🌐 Data Collection</div>
            <div class="step-desc">Firecrawl API crawls isro.gov.in — 339 documents, 4,557 overlapping chunks (512 tokens, stride 128). Zero noise chunks.</div>
        </div>
    </div>
    <div class="pipeline-step">
        <div class="step-num">2</div>
        <div>
            <div class="step-title">🕸️ Knowledge Graph Construction</div>
            <div class="step-desc">spaCy en_core_web_lg + 175-pattern ISRO EntityRuler extracts missions, launch vehicles, scientists, payloads. Dependency parser builds (subject, relation, object) triples → NetworkX graph built from the actual local graph artifact for the benchmark.</div>
        </div>
    </div>
    <div class="pipeline-step">
        <div class="step-num">3</div>
        <div>
            <div class="step-title">🔢 Dense Vector Indexing</div>
            <div class="step-desc">all-MiniLM-L6-v2 encodes each chunk into 384-dim vectors on CPU. FAISS Flat L2 index for exact nearest-neighbour search.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with pipe_col2:
    st.markdown("""
    <div class="pipeline-step">
        <div class="step-num">4</div>
        <div>
            <div class="step-title">🔍 Hybrid Retrieval</div>
            <div class="step-desc">Query entities extracted by spaCy. KG one-hop expansion retrieves entity-relation triples as graph context. FAISS retrieves top-3 passage chunks. Both merged.</div>
        </div>
    </div>
    <div class="pipeline-step">
        <div class="step-num">5</div>
        <div>
            <div class="step-title">🤖 Local Answer Generation</div>
            <div class="step-desc">Mistral-7B-Instruct Q4_K_M via Ollama. ~4.1GB VRAM. Zero-shot inference. Answers strictly from context — says "I don't know" when evidence is insufficient.</div>
        </div>
    </div>
    <div class="pipeline-step">
        <div class="step-num">6</div>
        <div>
            <div class="step-title">✅ Zero Cloud Cost</div>
            <div class="step-desc">Every component runs locally — no OpenAI, no Gemini, no cloud APIs at query time. Reproducible on any consumer GPU with 4GB+ VRAM.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── RESULTS ───────────────────────────────────────────────────────
st.markdown('<div class="section-header">📊 Evaluation Results</div>', unsafe_allow_html=True)

res_col1, res_col2 = st.columns(2)

with res_col1:
    st.markdown("**Main Results — ISRO-QA Benchmark (180-question test set)**")
    st.markdown("""
    <table class="result-table">
        <thead>
            <tr><th>System</th><th>ROUGE-L</th><th>Coverage</th><th>IDK%</th></tr>
        </thead>
        <tbody>
            <tr><td>BM25 + LLM</td><td>0.2915</td><td>0.4340</td><td>1.67%</td></tr>
            <tr><td>Vanilla RAG</td><td>0.2780</td><td>0.3989</td><td>12.22%</td></tr>
            <tr class="highlight"><td>KG-RAG</td><td>0.2736</td><td>0.3921</td><td>11.67%</td></tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)

    st.markdown("<br>**Per-Tier Results (180-question test set)**", unsafe_allow_html=True)
    st.markdown("""
    <table class="result-table">
        <thead>
            <tr><th>System</th><th>Tier 1</th><th>Tier 2</th><th>Tier 3</th></tr>
        </thead>
        <tbody>
            <tr><td>BM25 + LLM</td><td>0.3220 / 0.5199 / 3.33%</td><td>0.2587 / 0.3448 / 0.00%</td><td>0.2647 / 0.3532 / 0.00%</td></tr>
            <tr><td>Vanilla RAG</td><td>0.3222 / 0.4632 / 12.22%</td><td>0.2306 / 0.3213 / 11.11%</td><td>0.2387 / 0.3546 / 13.89%</td></tr>
            <tr class="highlight"><td>KG-RAG</td><td>0.3080 / 0.4381 / 15.56%</td><td>0.2246 / 0.3462 / 9.26%</td><td>0.2611 / 0.3456 / 5.56%</td></tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)

with res_col2:
    st.markdown("**Ablation Study — Separate 50-question experiment**")
    st.markdown("""
    <table class="result-table">
        <thead>
            <tr><th>Configuration</th><th>ROUGE-L</th><th>Coverage</th><th>IDK%</th></tr>
        </thead>
        <tbody>
            <tr><td>KG-only</td><td>0.0927</td><td>0.1078</td><td>76.00%</td></tr>
            <tr><td>FAISS-only</td><td>0.2830</td><td>0.4077</td><td>34.00%</td></tr>
            <tr class="highlight"><td>Full KG-RAG</td><td>0.2952</td><td>0.4564</td><td>10.00%</td></tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)

    st.markdown("<br>**Key Metrics at a Glance**")
    st.markdown("""
    <div class="metric-grid">
        <div class="metric-card best">
            <div class="metric-val">0.2736</div>
            <div class="metric-lbl">ROUGE-L</div>
            <div class="metric-sys">KG-RAG</div>
        </div>
        <div class="metric-card best">
            <div class="metric-val">0.403</div>
            <div class="metric-lbl">Coverage</div>
            <div class="metric-sys">KG-RAG</div>
        </div>
        <div class="metric-card best">
            <div class="metric-val">2.5%</div>
            <div class="metric-lbl">IDK Tier 3</div>
            <div class="metric-sys">KG-RAG best</div>
        </div>
        <div class="metric-card best">
            <div class="metric-val">+4.8pp</div>
            <div class="metric-lbl">KG Gain</div>
            <div class="metric-sys">vs FAISS-only</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── ISRO-QA BENCHMARK ─────────────────────────────────────────────
st.markdown('<div class="section-header">📋 ISRO-QA Benchmark</div>', unsafe_allow_html=True)

bm_col1, bm_col2, bm_col3 = st.columns(3)
with bm_col1:
    st.markdown("""
    <div class="stat-card" style="text-align:center;">
        <div class="stat-icon" style="font-size:2rem;">🔵</div>
        <div class="stat-val">100</div>
        <div class="stat-lbl">Tier 1 — Factoid</div>
        <div style="font-size:0.8rem;color:#475569;margin-top:0.5rem;">Single entity answers: launch dates, payload names, orbit types, mission objectives</div>
    </div>
    """, unsafe_allow_html=True)
with bm_col2:
    st.markdown("""
    <div class="stat-card" style="text-align:center;">
        <div class="stat-icon" style="font-size:2rem;">🟠</div>
        <div class="stat-val">60</div>
        <div class="stat-lbl">Tier 2 — Multi-hop</div>
        <div style="font-size:0.8rem;color:#475569;margin-top:0.5rem;">Connect facts across 2+ documents: e.g. which launch vehicle carried the first water-detecting satellite?</div>
    </div>
    """, unsafe_allow_html=True)
with bm_col3:
    st.markdown("""
    <div class="stat-card" style="text-align:center;">
        <div class="stat-icon" style="font-size:2rem;">🟣</div>
        <div class="stat-val">40</div>
        <div class="stat-lbl">Tier 3 — Timeline</div>
        <div style="font-size:0.8rem;color:#475569;margin-top:0.5rem;">Temporal ordering and duration: e.g. how many years after Chandrayaan-1 was Chandrayaan-2 launched?</div>
    </div>
    """, unsafe_allow_html=True)

# ── ABOUT THE PAPER ───────────────────────────────────────────────
st.markdown('<div class="section-header">📄 About the Paper</div>', unsafe_allow_html=True)

paper_col1, paper_col2 = st.columns([2, 1])

with paper_col1:
    st.markdown("""
    <div class="qa-container">
        <div style="font-size:1.05rem;font-weight:600;color:#E2E8F0;margin-bottom:0.8rem;">
            Knowledge Graph-Augmented Retrieval-Augmented Generation for ISRO Domain Question Answering on Resource-Constrained Hardware
        </div>
        <div style="color:#64748B;font-size:0.85rem;margin-bottom:1rem;">
            Nandana Narayan Das · Gowri Kannan &nbsp;|&nbsp; Target: ICNLP 2027 (IEEE, Scopus) &nbsp;|&nbsp; Submission: November 30, 2026
        </div>
        <div style="color:#94A3B8;font-size:0.9rem;line-height:1.7;">
            We propose KG-RAG, a framework that automatically constructs a domain-specific knowledge graph 
            from 339 unstructured ISRO documents using spaCy NER augmented with a 175-pattern ISRO entity ruler, 
            combining it with FAISS dense retrieval and locally quantized Mistral-7B-Instruct (Q4_K_M) via Ollama.
            The canonical benchmark consists of a deterministic 200-question ISRO set with a 20-dev / 180-test split. On the official 180-question test set, BM25 + LLM reaches ROUGE-L 0.2915 and coverage 0.4340, Vanilla RAG reaches 0.2780 and 0.3989, and KG-RAG reaches 0.2736 and 0.3921. These are lexical metrics and should not be interpreted as factual correctness guarantees.
            The separate ablation experiment reports KG-only 0.0927 / 0.1078, FAISS-only 0.2830 / 0.4077, and Full KG-RAG 0.2952 / 0.4564 on a 50-question sample.
        </div>
    </div>
    """, unsafe_allow_html=True)

with paper_col2:
    st.markdown("""
    <div class="qa-container">
        <div style="font-size:0.9rem;font-weight:600;color:#60A5FA;margin-bottom:0.8rem;">🏷️ Key Contributions</div>
        <div style="font-size:0.85rem;color:#94A3B8;line-height:1.8;">
            ✦ Deterministic 20-dev / 180-test benchmark protocol<br>
            ✦ Auto-constructs KG from raw web text<br>
            ✦ 175-pattern ISRO EntityRuler<br>
            ✦ Canonical metrics: ROUGE-L, coverage, exact match, IDK rate<br>
            ✦ Zero cloud cost deployment<br>
            ✦ Separate 50-question ablation study<br>
            ✦ Lexical evaluation only; no human factual metric yet
        </div>
        <div style="margin-top:1rem;font-size:0.85rem;font-weight:600;color:#60A5FA;">🛠️ Tech Stack</div>
        <div style="font-size:0.82rem;color:#64748B;line-height:1.8;margin-top:0.3rem;">
            spaCy · NetworkX · FAISS · Mistral-7B<br>
            Ollama · all-MiniLM-L6-v2 · Firecrawl<br>
            Python 3.10 · PyTorch · Streamlit
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── FOOTER ────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    KG-RAG for ISRO Domain QA &nbsp;·&nbsp; Alliance University &nbsp;·&nbsp; ICNLP 2027 &nbsp;·&nbsp;
    Nandana Narayan Das &amp; Gowri Kannan
</div>
""", unsafe_allow_html=True)