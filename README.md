# Revision Agent: AI-Powered Agentic Study System

A sophisticated multi-agent orchestration system that combines **LangGraph deep agents**, **Model Context Protocol (MCP) servers**, and **AI tools** to automate study material generation, spaced repetition flashcard creation, and exam preparation.

## Overview

Revision Agent is an intelligent tutoring assistant designed to help students efficiently prepare for exams by:
- Extracting and retrieving key concepts from lecture notes using **Retrieval-Augmented Generation (RAG)**
- Automatically generating high-quality flashcards for the **Anki spaced repetition system**
- Creating exam-style practice questions and revision materials
- Coordinating multi-stage workflows through autonomous sub-agents with human-in-the-loop validation

Built on **LangGraph's DeepAgents framework**, this system demonstrates advanced AI orchestration patterns including agent-to-agent delegation, context passing, middleware supervision, and filesystem-based state management.

---

## Architecture

### Core Components

#### 1. **Main Orchestrator Agent**
- Coordinates all sub-agents and tool calls
- Maintains a TODO-list for task tracking and transparency
- Implements a three-phase workflow: Retrieve → Delegate → Report
- Built on LangGraph's deep agent framework with custom prompt engineering

#### 2. **Sub-Agents** (Specialized Delegates)
- **Anki Flashcard Agent**: Generates flashcards from retrieved content and persists to Anki
- **Information Retrieval Agent**: Handles RAG queries, document ingestion, and web search
- **File-Handling Agent**: Creates revision summaries, exam papers, and study materials

#### 3. **Custom MCP Server**
- **Anki MCP Server** (`anki_mcp.py`): Provides standardized protocol for:
  - Listing/creating Anki decks
  - Listing/creating Anki cards
  - Deck and collection management
  - Direct integration with Anki's SQLite database

#### 4. **Tool Suite**

**Retrieval & Knowledge Tools:**
- `retrieval_tool()`: Vector similarity search over lecture notes (Chroma + OpenAI embeddings)
- `ingest_documents_tool()`: Add new PDFs to the knowledge base
- `tavily_search()`: Web search for supplementary materials

**Workflow Management:**
- `think_tool()`: Critical reasoning checkpoints (used sparingly for complex decisions)
- `write_todos()`: Task tracking and progress visualization

**LangGraph Built-in Tools:**
- File operations: read, write, edit, glob
- Code execution and analysis

#### 5. **Middleware & Safety**
- **Human-in-the-Loop Validation**: Sensitive operations (file writes) require human approval
- **Tool Call Rate Limiting**: Prevents infinite loops and excessive API calls
- **Recursion Depth Constraints**: Limits agent decision-making depth
- **FilesystemBackend**: Virtual filesystem with configurable interrupt policies

#### 6. **Knowledge Backend**
- **Vector Database**: ChromaDB with OpenAI embeddings (text-embedding-3-small)
- **Persistence**: SQLite-backed vector storage for persistent retrieval
- **Agent Storage**: Filesystem-based checkpointing for agent state

---

## Key Features

✅ **Multi-Agent Orchestration**: Specialized agents delegated based on task requirements  
✅ **Context-Aware Delegation**: Agents receive full context in task descriptions (no hidden state)  
✅ **RAG Integration**: Vector-based retrieval from lecture notes with semantic search  
✅ **Anki Automation**: Directly create flashcards in your Anki collection  
✅ **Human Validation**: Optional human approval gates for critical actions  
✅ **Task Transparency**: TODO-list tracking provides clear progress visibility  
✅ **Custom MCP Protocol**: Standardized communication with external tools (Anki)  
✅ **Production-Ready Checkpointing**: LangSmith integration for evaluation and debugging  

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| **Agentic Framework** | LangGraph (DeepAgents) |
| **LLM** | OpenAI (GPT-4/3.5-turbo) |
| **Vector Store** | ChromaDB + OpenAI Embeddings |
| **Knowledge Source** | PDF documents + web search (Tavily) |
| **External Integration** | Model Context Protocol (MCP) |
| **Spaced Repetition** | Anki + AnkiConnect |
| **State Management** | FilesystemBackend + LangSmith |
| **Language** | Python 3.11+ |

---

## Getting Started

### Prerequisites
- Python 3.11+
- OpenAI API key
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
# Edit .env and add your OpenAI API key
```

### Configuration

1. **Knowledge Base Setup**:
   ```bash
   # Place your lecture PDF in the project root
   # Then run the RAG setup (one-time):
   python -c "from RAG import setup_retriever; setup_retriever()"
   ```

2. **Anki Configuration**:
   - Install AnkiConnect addon in Anki
   - Ensure Anki is running on `http://localhost:8765`
   - Create a base deck (e.g., "Linear Algebra")

3. **API Keys** (in `.env`):
   ```
   OPENAI_API_KEY=sk-...
   TAVILY_API_KEY=tvly-...
   ```

---

## Usage

### Basic Usage: Generate Flashcards from Topic

```bash
python final_agent.py
```

Then interact with the agent through the CLI or programmatic interface:

```python
from final_agent import create_main_agent

# Create agent instance
agent = create_main_agent()

# Run a revision workflow
result = agent.invoke({
    "messages": [
        {
            "role": "user",
            "content": "Create 15 flashcards on eigenvalues from my Linear Algebra notes"
        }
    ]
})
```

### Workflow: Complete Revision Pipeline

1. **Agent receives user request** → "Create exam questions on matrix decomposition"
2. **Orchestrator creates TODO list** → Marks retrieval, generation, and reporting tasks
3. **Retrieval phase** → `retrieval_tool()` queries RAG database
4. **Delegation phase** → Passes retrieved content to File-Handling Agent
5. **File-Handling Agent** → Generates practice exam questions
6. **Human validation** → Middleware prompts for approval
7. **Reporting** → Agent summarizes results to user

---

## Project Structure

```
RevisionAgent/
├── final_agent.py              # Main orchestrator + LangGraph setup
├── tools.py                    # Core tool definitions
├── RAG.py                      # Vector store initialization & retrieval
├── anki_mcp.py                 # Anki MCP server implementation
├── multi_server_mcp_client.py  # MCP client for server communication
├── prompts.py                  # Agent system prompts
├── utils.py                    # Utility functions (message formatting)
├── model.py                    # LLM initialization
│
├── new_agent/
│   ├── new_prompts.py          # Alternative agent prompts
│   └── new_tools.py            # Extended tool definitions
│
├── Tools/
│   └── tool_guards.py          # Tool validation & safety checks
│
├── MCP/                        # MCP protocol implementations
├── Evals/                      # LangSmith evaluation dataset
├── AgentOutput/                # Generated study materials
│
└── chroma.sqlite3              # Persistent vector database

```

---

## Key Design Patterns

### 1. **Context-Aware Delegation**
Sub-agents don't have access to the main agent's retrieval results. Instead, the orchestrator passes full context in task descriptions:

```python
# ✅ Correct: Full context passed
task_description = f"""
Generate flashcards on eigenvalues.

Use ONLY this content:
{retrieved_content}
"""

# ❌ Incorrect: Expecting shared context
task_description = "Generate flashcards on eigenvalues"  # Sub-agent has no context
```

### 2. **Human-in-the-Loop Validation**
Sensitive operations (file writes) are intercepted by middleware:

```python
FilesystemBackend(
    interrupt_on={
        "write_file": {
            "allowed_decisions": ["approve", "reject"]
        }
    }
)
```

### 3. **Task Transparency via TODOs**
The agent maintains an evolving TODO list to show progress:

```python
# Phase 1: Initial plan
write_todos([
    {"content": "Retrieve eigenvalue content", "status": "in_progress"},
    {"content": "Generate flashcards", "status": "pending"},
    {"content": "Report results", "status": "pending"}
])

# Phase 2: After retrieval
write_todos([
    {"content": "Retrieve eigenvalue content", "status": "completed"},
    {"content": "Generate flashcards", "status": "in_progress"},
    {"content": "Report results", "status": "pending"}
])
```

---

## Advanced Features

### Extensibility
- Add new sub-agents by extending the deep agent framework
- Implement new tools as `@tool` decorated functions
- Create custom MCP servers for any external service

### Evaluation & Debugging
- LangSmith integration for tracing agent decisions
- Dataset creation and evaluation pipeline in `Evals/`
- Human-in-the-loop validation gates

### Production Considerations
- Filesystem backend configured for state persistence
- Checkpointing with memory saver for session recovery
- Rate limiting and recursion depth constraints

---

## Future Improvements

See [future_improvements.md](future_improvements.md) for planned enhancements including:
- Multi-document RAG with cross-document reasoning
- Adaptive spaced repetition scheduling
- Real-time collaboration features
- Evaluation harness expansion

---

## Development

### Running Evaluations
```bash
cd Evals
python run_eval.py
```

### Testing the RAG System
```python
from RAG import get_retriever

retriever = get_retriever()
results = retriever.invoke("What is an eigenvalue?")
for doc in results:
    print(doc.page_content)
```

### Debugging Agents
Enable verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Contributing

Contributions are welcome! Please:
1. Create a feature branch
2. Make your changes
3. Test with the evaluation suite
4. Submit a pull request

---

## License

[Specify License - e.g., MIT, Apache 2.0]

---

## Contact & Attribution

**Author**: Will Barnard  
**Questions/Issues**: [GitHub Issues](https://github.com/willbarnard/RevisionAgent/issues)

---

## Acknowledgments

- **LangGraph**: Deep agents framework
- **Anthropic Claude**: Initial architecture design consultation
- **OpenAI**: Embeddings and LLM capabilities
- **ChromaDB**: Vector database
- **Anki**: Spaced repetition system





