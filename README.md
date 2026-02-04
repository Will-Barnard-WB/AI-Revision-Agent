# RevisionAgent 🎓

An intelligent AI agent that automatically generates high-quality Anki flashcards from lecture notes using RAG (Retrieval-Augmented Generation) and custom MCP server integration.

## 🚀 Key Features

- **Custom MCP Server**: Built a production-ready Model Context Protocol server for Anki operations (view decks, create cards, manage content)
- **RAG-Powered Retrieval**: ChromaDB vector database with OpenAI embeddings for semantic search over lecture materials
- **Multi-Phase Agent**: LangChain-based orchestration with retrieval → generation → persistence workflow
- **Evaluation Pipeline**: Dataset creation and experiment tracking for monitoring agent performance
- **Tool Guards**: Smart prevention of redundant/costly repeated tool calls

## 🏗️ Architecture

```
Agents/          # Agent orchestration (ReAct, workflow, MCP integration)
├── prompts.py   # System prompts with strict deck/tool rules
└── agent_mcp.py # Main agent with MCP tools + RAG retrieval

MCP/             # Custom MCP server implementation
└── anki_mcp.py  # FastMCP server for AnkiConnect API

Database/        # Vector storage and retrieval
└── RAG.py       # ChromaDB setup with document chunking

Tools/           # Custom tools and guards
Evals/           # Evaluation and monitoring pipeline
```

## 🛠️ Tech Stack

- **Agent Framework**: LangChain
- **Vector Database**: ChromaDB + OpenAI Embeddings
- **MCP Server**: FastMCP (HTTP transport)
- **Integration**: AnkiConnect API
- **LLM**: OpenAI (configurable)

## 💡 How It Works

1. **User provides a topic** (e.g., "eigenvalues")
2. **Agent retrieves** relevant content from vectorized lecture notes
3. **LLM generates** 10 contextually-grounded Q/A pairs
4. **MCP server persists** flashcards to Anki in structured decks (`Linear Algebra::<topic>`)

## 📊 Design Decisions

- **Strict tool guardrails** to prevent hallucination and redundant searches
- **Modular architecture** for easy extension to new subjects/formats
- **Evaluation-first approach** with datasets and metrics for continuous improvement
- **Single-responsibility MCP tools** for atomic Anki operations

## 🔮 Future Enhancements

- Semantic deduplication before card creation
- Conversational memory for multi-turn interactions
- Max iteration limits for search loops
- Forgiving tool calls with error learning/logging

---

**Built with modern AI agent patterns** • [View commit history for 4-day development log](https://github.com/)