
# RevisionAgent 🎓

Automatically generates high-quality Anki flashcards from your lecture notes using RAG (Retrieval-Augmented Generation) and a custom MCP server. Seamlessly integrates with AnkiConnect for reliable deck and card management. (Pinned project)

---


## 🚀 Features

- RAG-powered flashcard generation from your own lecture notes
- Reliable AnkiConnect and MCP server integration
- Deck and card listing, creation, and flashcard retrieval
- Sub-agent delegation with enforced RAG context


## 🏗️ Architecture

- Modular agent orchestration (retrieval, generation, persistence)
- FastMCP server for AnkiConnect API
- ChromaDB vector storage for semantic search


## 🛠️ Tech Stack

- LangChain agent framework
- ChromaDB + OpenAI Embeddings
- FastMCP server (HTTP)
- AnkiConnect API
- OpenAI LLM


## 💡 How It Works

1. User provides a topic (e.g., "eigenvalues")
2. Agent retrieves relevant content from your notes (RAG)
3. LLM generates contextually-grounded flashcards
4. MCP server persists flashcards to Anki in structured decks


## 📊 Design

- Strict tool guardrails to prevent hallucination and redundant searches
- Modular, extensible architecture
- Evaluation-first approach with datasets and metrics
- Single-responsibility MCP tools for atomic Anki operations


---
**Built with modern AI agent patterns**

**Built with modern AI agent patterns** • [View commit history for 4-day development log](https://github.com/)