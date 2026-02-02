# RevisionAgent: AI-Powered Flashcard Generation System

An intelligent agent that automatically generates high-quality Anki flashcards from academic lecture notes using Retrieval-Augmented Generation (RAG) and Large Language Models.

## Overview

RevisionAgent transforms the tedious process of creating study materials into an automated, intelligent workflow. By combining document retrieval, natural language processing, and spaced repetition software integration, this system generates contextually accurate flashcards on demand from academic content.

## Key Features

- **Retrieval-Augmented Generation (RAG)**: Semantic search across embedded lecture notes using vector similarity
- **Agentic Workflow**: Autonomous LLM agent that reasons through retrieval, generation, and persistence phases
- **Anki Integration**: Direct flashcard creation via AnkiConnect API with automatic deck organization
- **Evaluation Framework**: LLM-as-a-judge evaluation pipeline using LangSmith for quality assessment
- **Modular Architecture**: Clean separation of concerns across RAG, tools, prompts, and agent logic

## Technical Stack

**AI/ML Framework**
- LangChain for agentic workflows and tool orchestration
- OpenAI GPT-4o-mini for question generation
- OpenAI text-embedding-3-small for semantic search

**Vector Database**
- ChromaDB for document embeddings and similarity retrieval
- PyPDFLoader for document ingestion
- RecursiveCharacterTextSplitter for intelligent chunking

**Integration & Evaluation**
- AnkiConnect API for flashcard persistence
- LangSmith for dataset management and evaluation
- Custom LLM-as-a-judge evaluators for quality control

## Architecture

```
User Input (Topic)
       ↓
   Agent (GPT-4o-mini)
       ↓
Phase 1: Retrieval Tool
       ↓ [Vector Search]
   ChromaDB Vector Store
       ↓ [Top-5 Chunks]
Phase 2: Q/A Generation
       ↓ [LLM Processing]
Phase 3: Persistence Tool
       ↓ [AnkiConnect API]
   Anki Deck Structure
```

### Core Components

**[RAG.py](RAG.py)** - Vector store initialization and retriever configuration
- Loads and chunks PDF documents (1000 char chunks, 200 char overlap)
- Creates persistent ChromaDB collection with OpenAI embeddings
- Configures similarity-based retrieval (k=5)

**[tools.py](tools.py)** - LangChain tool definitions
- `retrieval_tool`: Semantic search across lecture notes
- `add_anki_notes`: Batch flashcard creation with subdeck management

**[prompts.py](prompts.py)** - System prompt engineering
- Three-phase agent workflow definition (Retrieval → Generation → Persistence)
- Structured output format enforcement for Q/A pairs
- Tool usage guidelines and error handling

**[agent2.py](agent2.py)** - Agent instantiation and execution
- Creates tool-enabled LangChain agent with GPT-4o-mini
- Demonstrates agent invocation patterns
- Example topics from Linear Algebra domain

**[run_eval.py](run_eval.py)** - Evaluation pipeline
- LangSmith dataset integration
- Custom correctness evaluator using LLM-as-a-judge pattern
- Automated batch evaluation with concurrency control

## Sample Workflow

```python
# User request
"Generate revision questions on the topic: eigenvalues"

# Agent execution
1. Calls retrieval_tool("eigenvalues")
   → Returns 5 most relevant document chunks

2. Analyzes retrieved content
   → Generates structured Q/A pairs:
   [
     {"front": "What is an eigenvalue?", "back": "A scalar λ such that Av = λv..."},
     {"front": "How do you find eigenvalues?", "back": "Solve det(A - λI) = 0..."}
   ]

3. Calls add_anki_notes(topic="eigenvalues", qa_pairs=[...])
   → Creates "Linear Algebra::eigenvalues" subdeck
   → Adds flashcards with tags ["auto_generated", "rag"]

# Result
"Successfully added 5 flashcards to 'Linear Algebra::eigenvalues'."
```

## Technical Highlights

### 1. Semantic Retrieval
Uses cosine similarity on OpenAI embeddings to find contextually relevant content rather than keyword matching, ensuring flashcards capture conceptual understanding.

### 2. Tool-Based Agent Architecture
Implements the ReAct (Reasoning + Acting) pattern where the LLM reasons about which tools to use and when, enabling autonomous multi-step workflows.

### 3. Structured Output Generation
Enforces strict JSON schema for Q/A pairs through prompt engineering, ensuring consistent integration with Anki's data model.

### 4. Evaluation-Driven Development
Integrates LangSmith evaluation framework from the start, enabling systematic quality assessment and iterative improvement.

### 5. Error Handling & Edge Cases
- Validates Q/A pair structure before API calls
- Handles missing information gracefully (returns warning instead of empty flashcards)
- Timeout protection on AnkiConnect requests
- Deck creation with error recovery

## Development Journey

The project evolved through rapid iteration:

**Day 1** - Initial RAG pipeline with basic flashcard generation
**Day 1.1** - Enhanced prompts to enforce Anki-specific Q/A format
**Day 1.2** - Refactored into modular architecture (separated RAG, tools, prompts)
**Current** - Added LangSmith evaluation framework and correctness assessments

## Future Enhancements

Planned improvements demonstrate forward-thinking design:

1. **Semantic Deduplication** - Check for semantically similar flashcards before adding to prevent redundancy
2. **Conversation Memory** - Implement persistent agent memory for multi-turn refinement
3. **Iteration Control** - Add max depth guards to prevent excessive retrieval loops
4. **Custom MCP Server** - Build dedicated Anki-Connect MCP server for richer tool integration
5. **Enhanced Evaluators** - Expand evaluation metrics beyond correctness (coherence, difficulty, etc.)

## Skills Demonstrated

- **AI Engineering**: RAG system design, prompt engineering, agentic workflows
- **LLM Integration**: OpenAI API usage, embeddings, tool calling
- **Software Architecture**: Modular design, separation of concerns, clean interfaces
- **Data Engineering**: Vector databases, document processing, chunking strategies
- **Quality Assurance**: Evaluation frameworks, LLM-as-a-judge patterns
- **API Integration**: RESTful API consumption (AnkiConnect), error handling
- **Python Development**: Type hints, async patterns, dependency management

## Getting Started

```bash
# Install dependencies
pip install langchain langchain-openai langchain-chroma langsmith openevals python-dotenv requests

# Set up environment variables
echo "OPENAI_API_KEY=your_key_here" > .env
echo "LANGSMITH_API_KEY=your_key_here" >> .env
echo "ANKI_CONNECT_URL=http://localhost:8765" >> .env

# Ensure Anki is running with AnkiConnect plugin installed

# Run the agent
python agent2.py

# Run evaluation
python run_eval.py
```

## Project Structure

```
RevisionAgent/
├── RAG.py              # Vector store and retriever setup
├── tools.py            # LangChain tool definitions
├── prompts.py          # System prompt templates
├── agent2.py           # Agent configuration and execution
├── run_eval.py         # LangSmith evaluation pipeline
├── create_dataset.py   # Dataset management utilities
└── future_improvements.md  # Roadmap and known issues
```

## Context

This project showcases practical application of modern AI engineering patterns:
- Moving beyond simple LLM completion to agentic, tool-using systems
- Grounding LLM outputs in external knowledge bases (RAG)
- Building production-ready evaluation infrastructure
- Integrating AI into existing workflows (Anki ecosystem)

Developed as a personal productivity tool that evolved into a demonstration of AI engineering capabilities applicable to educational technology, knowledge management, and content automation domains.

---

**Tech Stack Summary**: Python • LangChain • OpenAI API • ChromaDB • LangSmith • RESTful APIs
