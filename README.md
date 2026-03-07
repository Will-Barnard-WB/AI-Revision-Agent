# RevisionAgent — Technical Recruiter Overview

RevisionAgent is a production-style **agentic learning platform** that ingests lecture PDFs, retrieves grounded knowledge with RAG, generates study outputs, and integrates with Anki through MCP.

It demonstrates end-to-end AI product engineering:

- **Agent orchestration** (LangGraph Deep Agent + custom toolchain)
- **Real-time web app** (FastAPI, WebSocket streaming, async task lifecycle)
- **RAG pipeline** (PDF ingestion, chunking, embeddings, Chroma retrieval)
- **External integration** (MCP client/server + AnkiConnect)
- **Guardrailed autonomy** (tool limits + human approval interrupts)
- **Persistent memory + observability** (memory sections, activity logs, plain-English summaries)
- **LLM evaluation pipeline** (curated dataset, LangSmith experiments, hybrid evaluator suite)

---

## What this system does

### User-facing capabilities
- Chat-based revision assistant with markdown and math-rendered responses
- File browser for generated documents and uploaded lectures
- History page with conversation summaries and plain-English activity logs
- Upload-to-process flow for lecture PDFs

### Agent capabilities
- Collection-aware semantic retrieval from ingested lecture notes
- PDF ingestion into Chroma collections
- Web-search fallback (bounded)
- Memory updates across profile, collections, decks, preferences, activity
- Anki deck/card operations via MCP tools

### Autonomous background mode
- Ambient loop watches `agent_fs/lectures/` for new PDFs
- Auto-ingests, runs agent workflows, writes manifest/logs

---

## Evaluation & Observability

A production-grade evaluation pipeline built on **LangSmith** to systematically measure agent quality, track regressions, and surface failure modes over time.

### Curated Evaluation Dataset

A hand-curated dataset (`revision-questions-dataset`) was built in LangSmith covering representative agent tasks across different topics and edge cases:

| Example | Input | What it tests |
|---------|-------|---------------|
| MLE | Retrieve all Anki flashcards for: MLE | Well-populated deck, high-coverage retrieval |
| Eigenvalues | Retrieve all Anki flashcards for: eigenvalues | Dense deck with mathematical notation |
| Symmetric Bilinear Forms | Retrieve all Anki flashcards for: symmetric bilinear forms | Large deck with duplicate detection |
| Basis | Retrieve all Anki flashcards for: basis | **Gap case** — no dedicated cards exist |

The "basis" example is particularly valuable: it tests whether the agent gracefully handles missing knowledge — reporting the gap honestly and offering next steps — rather than hallucinating cards that don't exist.

### Three-Layer Evaluator Suite

Evaluations use a hybrid approach combining **deterministic rule-based checks** and an **LLM-as-judge**, giving both fast/cheap signal and nuanced semantic scoring.

#### 1. `count_flashcards` — Deterministic structural check
Counts flashcard-like items in the output using regex patterns that handle both numbered list format (`1.`, `2)`) and markdown table format (`| 1 |`). Scores 1.0 if at least one flashcard is detected, 0.0 otherwise.

```
[flashcard_count] score=1.0 — Found 10 flashcards.
```

> **Why it matters:** Catches regressions where the agent returns prose explanations instead of structured flashcard output — a fast, zero-cost check that runs on every experiment.

#### 2. `references_topic` — Deterministic relevance check
Extracts meaningful keywords from the user's input and verifies they appear in the output. Scores 1.0 if matched, 0.0 if not.

```
[references_topic] score=1.0 — Output references topic keywords.
```

> **Why it matters:** Catches topic drift — cases where the agent returns well-formatted cards but on the wrong subject.

#### 3. `llm_judge` — LLM-as-judge semantic scorer
Calls Claude via the Anthropic API to score each response across three dimensions (each out of 10): **Relevance**, **Completeness**, and **Clarity**. Returns a normalised 0–1 overall score and a one-sentence reasoning comment logged to LangSmith.

```
[llm_judge] score=0.9 — Relevance: 10/10, Completeness: 9/10, Clarity: 9/10 — 
Excellent coverage of MLE fundamentals with clear mathematical notation and 
logical progression from basic concepts to advanced topics.
```

> **Why it matters:** Captures quality signals that rule-based checks miss — mathematical correctness, depth of coverage, and pedagogical clarity. The gap case ("basis") correctly scored 0.0 overall (Relevance: 6, Completeness: 2, Clarity: 9), exposing a real knowledge gap in the Anki deck rather than an agent failure.

### Sample Experiment Results

From experiment `revision-agent-eval-c0367f4c`:

| Topic | flashcard_count | references_topic | llm_judge |
|-------|:-:|:-:|:-:|
| MLE | ✅ 1.0 | ✅ 1.0 | ✅ 0.9 |
| Eigenvalues | ✅ 1.0 | ✅ 1.0 | ✅ 0.9 |
| Symmetric Bilinear Forms | ✅ 1.0 | ✅ 1.0 | ✅ 0.9 |
| Basis (gap case) | ✅ 1.0 | ✅ 1.0 | ⚠️ 0.0 |

The basis result highlights exactly the kind of insight the pipeline is designed to surface: the agent behaved correctly (honest gap reporting + offer to create cards), but the low LLM judge score correctly flags that the user's request went unmet — pointing to a data gap rather than an agent bug.

### Running Evaluations

```bash
cd Evals
python run_eval.py
```

Results are tracked in LangSmith under the `revision-agent-eval` experiment prefix, enabling side-by-side comparison across agent versions.

---

## Architecture at a glance

```text
UI (HTMX/Tailwind + JS)
    -> FastAPI backend (server.py)
            -> Task orchestration + WebSocket status stream
            -> Approval interrupts for sensitive writes
            -> History summarization + file endpoints

Agent runtime (agent_factory.py)
    -> Deep Agent + scope-first prompt policy (prompts.py)
    -> Tools (tools.py): retrieval, ingest, web search, memory, MCP
    -> Middleware caps for retrieval/web calls

Knowledge layer
    -> RAG pipeline (RAG.py) + ChromaDB persistence
    -> Agent filesystem: lectures, documents, templates, memory

Integrations
    -> MCP Anki server (anki_mcp_server.py) via multi_server_mcp_client.py

Evaluation
    -> LangSmith experiment tracking
    -> Curated dataset (revision-questions-dataset)
    -> Hybrid evaluator suite (Evals/run_eval.py)
```

---

## Key technical highlights

1. **Bounded tool autonomy**: run/thread limits for retrieval and web search to prevent runaway traces.
2. **Scope-first behavior**: broad requests are clarified before expensive fan-out retrieval.
3. **Human-in-the-loop safety**: write operations can require explicit approve/reject.
4. **Memory integrity**: lock-protected, atomic memory writes with normalized activity dates.
5. **Readable observability**: compact task/activity summaries for easier debugging and UX.
6. **Hybrid evaluation**: deterministic structural checks + LLM-as-judge for nuanced semantic scoring, tracked across experiments in LangSmith.

---

## Primary files to review

| File | Purpose |
|------|---------|
| `server.py` | Async task orchestration, APIs, streaming, summaries, history/files endpoints |
| `agent_factory.py` | Model/tool composition, middleware limits, memory-injected prompt |
| `tools.py` | Retrieval/ingestion/web/memory tools |
| `RAG.py` | Collection lifecycle + retriever setup |
| `ambient.py` | Autonomous polling/ingestion loop |
| `anki_mcp_server.py` | MCP adapter for Anki actions |
| `Evals/run_eval.py` | LangSmith evaluation pipeline with 3-evaluator suite |
| `ui/templates/*` | Chat/files/history/ambient UX |

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| **Agentic Framework** | LangGraph (DeepAgents) |
| **LLM** | Anthropic Claude (claude-sonnet) |
| **Vector Store** | ChromaDB + OpenAI Embeddings |
| **Knowledge Source** | PDF documents + web search (Tavily) |
| **External Integration** | Model Context Protocol (MCP) |
| **Spaced Repetition** | Anki + AnkiConnect |
| **State Management** | FilesystemBackend + LangSmith |
| **Evaluation** | LangSmith + custom hybrid evaluator suite |
| **Language** | Python 3.11+ |

---

## Getting Started

### Prerequisites
- Python 3.11+
- Anthropic API key
- Anki (for flashcard creation)
- PDF lecture notes

### Installation

```bash
# Clone repository
git clone <repo-url>
cd RevisionAgent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env and add your API keys
```

### Configuration

1. **Knowledge Base Setup**:
   ```bash
   python -c "from RAG import setup_retriever; setup_retriever()"
   ```

2. **Anki Configuration**:
   - Install AnkiConnect addon in Anki
   - Ensure Anki is running on `http://localhost:8765`

3. **API Keys** (in `.env`):
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   OPENAI_API_KEY=sk-...
   LANGSMITH_API_KEY=...
   TAVILY_API_KEY=tvly-...
   ```

---

## Project Structure

```
RevisionAgent/
├── server.py                   # FastAPI backend + WebSocket streaming
├── agent_factory.py            # Agent composition + middleware
├── tools.py                    # Core tool definitions
├── RAG.py                      # Vector store initialization & retrieval
├── anki_mcp_server.py          # Anki MCP server implementation
├── multi_server_mcp_client.py  # MCP client for server communication
├── prompts.py                  # Agent system prompts
├── ambient.py                  # Autonomous background ingestion loop
│
├── Evals/
│   ├── run_eval.py             # LangSmith evaluation pipeline
│   └── create_dataset.py       # Dataset creation script
│
├── ui/templates/               # Chat/files/history/ambient UX
├── agent_fs/                   # Agent filesystem (lectures, docs, memory)
└── chroma.sqlite3              # Persistent vector database
```

---

## Key Design Patterns

### 1. Context-Aware Delegation
Sub-agents receive full context in task descriptions rather than relying on shared state:

```python
# ✅ Correct: Full context passed explicitly
task_description = f"""
Generate flashcards on eigenvalues.
Use ONLY this content: {retrieved_content}
"""
```

### 2. Human-in-the-Loop Validation
Sensitive write operations are intercepted by middleware:

```python
FilesystemBackend(
    interrupt_on={"write_file": {"allowed_decisions": ["approve", "reject"]}}
)
```

### 3. Hybrid Evaluation Strategy
Rule-based checks catch structural regressions cheaply; LLM judge catches semantic quality:

```python
results = evaluate(
    run_agent,
    data="revision-questions-dataset",
    evaluators=[count_flashcards, references_topic, llm_judge],
    experiment_prefix="revision-agent-eval",
)
```

---

## Contact & Attribution

**Author**: Will Barnard
**Questions/Issues**: [GitHub Issues](https://github.com/willbarnard/RevisionAgent/issues)

---

## Acknowledgments

- **LangGraph**: Deep agents framework
- **Anthropic Claude**: LLM backbone + LLM-as-judge evaluator
- **OpenAI**: Embeddings
- **ChromaDB**: Vector database
- **Anki / AnkiConnect**: Spaced repetition integration
- **LangSmith**: Experiment tracking and evaluation infrastructure