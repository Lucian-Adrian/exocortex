# Exo - Executive OS

> **Your personal knowledge memory system powered by AI.**

Exo is an intelligent knowledge management system that ingests content from multiple sources, extracts insights using AI, and provides semantic search across your personal knowledge base.

## ✨ Features

- **Multi-source Ingestion**: Import from Markdown, URLs, Slack messages, and transcripts
- **AI-Powered Processing**: Automatic summarization, entity extraction, and commitment tracking
- **Semantic Search**: Query your knowledge using natural language
- **Commitment Tracking**: Never forget what you promised or what was promised to you
- **REST API**: Full-featured API for integrations
- **CLI**: Command-line interface for quick operations
- **LangChain Integration**: Use Exo as a retriever in RAG pipelines
- **n8n Compatible**: Webhook endpoints for automation workflows
- **LLMOps Ready**: Built-in observability with Langfuse and evaluation with DeepEval

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/lucian-adrian/exocortex.git
cd exocortex

# Install with all dependencies
pip install -e ".[all]"

# Or install specific extras
pip install -e ".[cli]"      # CLI only
pip install -e ".[api]"      # REST API
pip install -e ".[langchain]" # LangChain integration
pip install -e ".[llmops]"   # Observability & evaluation
pip install -e ".[dev]"      # Development tools
```

### Configuration

Create a `.env` file in the project root:

```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
GEMINI_API_KEY=your-gemini-api-key

# Optional
EXO_API_KEY=your-api-key-for-auth  # Required for API authentication
GEMINI_MODEL=gemini-2.5-flash-lite  # Default model
EXO_ENABLE_TRACING=true  # Enable Langfuse tracing

# Langfuse (optional, for observability)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
```

### Database Setup

Run the SQL migrations in Supabase:

```sql
-- Run in order:
-- 1. docs/db/01_memories.sql
-- 2. docs/db/02_embeddings.sql
-- 3. docs/db/03_functions.sql
```

## 📖 Usage

### CLI

```bash
# Ingest content
exo ingest "Meeting notes: Discussed Q4 roadmap with John. He committed to deliver the API by Dec 15."

# Ingest from file
exo ingest --file notes.md --source-type markdown

# Query your knowledge
exo query "What did John commit to?"

# Query with JSON output
exo query "pending commitments" --json
```

### Python API

```python
from exo.pipeline import Orchestrator
from exo.schemas import SourceType

# Create orchestrator
orchestrator = Orchestrator()

# Ingest content
result = await orchestrator.ingest(
    text="Meeting with Alice about the new feature launch.",
    source_type=SourceType.MARKDOWN,
)
print(f"Created memory: {result.id}")
print(f"Summary: {result.enriched.summary}")

# Query knowledge
response = await orchestrator.query("What did we discuss with Alice?")
print(f"Answer: {response.answer}")
```

### REST API

```bash
# Start the API server
uvicorn exo.api.app:app --reload

# Health check
curl http://localhost:8000/health

# Ingest content (requires X-API-Key header)
curl -X POST http://localhost:8000/api/memories \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"text": "Meeting notes...", "source_type": "markdown"}'

# Query
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"query": "What are my pending commitments?"}'
```

### LangChain Integration

```python
from exo.integrations.langchain import ExoRetriever
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA

# Create retriever
retriever = ExoRetriever(top_k=5, similarity_threshold=0.7)

# Create RAG chain
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True,
)

# Query
result = qa_chain.invoke({"query": "What meetings do I have this week?"})
```

## 🧪 Testing

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=exo --cov-report=html

# Run RAG evaluation (requires API keys)
pytest tests/rag/ -v
```

## 📁 Project Structure

```
exo/
├── schemas/          # Pydantic models
├── db/               # Supabase database layer
├── ai/               # Gemini AI provider
├── pipeline/         # Core orchestration logic
├── cli/              # Click CLI commands
├── api/              # FastAPI REST API
├── integrations/     # LangChain, n8n helpers
└── llmops/           # Observability & evaluation

tests/
├── unit/             # Unit tests
├── integration/      # Integration tests
└── rag/              # RAG evaluation tests

docs/
├── specs/            # Design specifications
├── db/               # SQL migrations
└── examples/         # Usage examples
```

## 🔧 Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run linter
ruff check exo/

# Run type checker
mypy exo/

# Format code
ruff format exo/
```

## 📚 Documentation

- [Design Specs](docs/specs/) - Architecture and requirements
- [API Documentation](docs/api/) - OpenAPI specification
- [Database Schema](docs/db/) - SQL migrations and schema
- [Examples](docs/examples/) - Usage examples

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](contributing.md) for:

- Development setup
- Code style guidelines
- Pull request process
- Testing requirements

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

*Built with ❤️ using Python, Supabase, and Google Gemini*
