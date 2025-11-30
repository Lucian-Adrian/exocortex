# Contributing to Exo

Thank you for your interest in contributing to Exo! This guide will help you get started.

## 🚀 Development Setup

### Prerequisites

- Python 3.13 or higher
- A Supabase account (free tier works)
- A Google AI Studio account (for Gemini API)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/lucian-adrian/exocortex.git
   cd exocortex
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   
   # Linux/Mac
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e ".[all]"
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. **Run tests to verify**
   ```bash
   pytest tests/unit/ -v
   ```

## 📁 Code Organization

```
exo/
├── schemas/          # Pydantic models - data structures
├── db/               # Database layer - Supabase operations
├── ai/               # AI layer - Gemini provider
├── pipeline/         # Core logic - orchestration
├── cli/              # CLI commands - Click
├── api/              # REST API - FastAPI
├── integrations/     # External integrations
└── llmops/           # Observability & evaluation
```

### Module Guidelines

- **schemas/**: Pure Pydantic models, no business logic
- **db/**: Only database operations, no AI calls
- **ai/**: Only AI operations, no database calls
- **pipeline/**: Orchestrates db + ai, contains business logic
- **cli/**: Thin wrapper around pipeline
- **api/**: Thin wrapper around pipeline with HTTP concerns

## 🎨 Code Style

### General Rules

- Use type hints for all function signatures
- Write docstrings for public functions
- Keep functions small and focused
- Prefer composition over inheritance

### Python Style

We use `ruff` for linting and formatting:

```bash
# Check for issues
ruff check exo/

# Auto-fix issues
ruff check exo/ --fix

# Format code
ruff format exo/
```

### Type Checking

We use `mypy` for static type checking:

```bash
mypy exo/
```

### Example Function

```python
async def process_content(
    text: str,
    source_type: SourceType,
    metadata: dict[str, Any] | None = None,
) -> Memory:
    """
    Process and store content in the knowledge base.
    
    Args:
        text: The raw text content to process
        source_type: Type of source (markdown, url, slack, transcript)
        metadata: Optional additional metadata
    
    Returns:
        The created Memory object with enriched content
    
    Raises:
        ExoError: If processing fails
    """
    ...
```

## 🧪 Testing

### Test Structure

```
tests/
├── unit/           # Fast, isolated tests (mocked dependencies)
├── integration/    # Tests with real services (requires credentials)
└── rag/            # RAG evaluation tests (requires API keys)
```

### Running Tests

```bash
# All unit tests
pytest tests/unit/ -v

# Specific test file
pytest tests/unit/test_schemas.py -v

# Specific test
pytest tests/unit/test_schemas.py::TestMemory::test_valid_memory -v

# With coverage
pytest tests/unit/ --cov=exo --cov-report=html
```

### Writing Tests

```python
import pytest
from exo.schemas import Memory, SourceType, EnrichedContent


class TestMemory:
    """Tests for Memory schema."""

    def test_valid_memory(self) -> None:
        """Creates a valid memory with required fields."""
        memory = Memory(
            raw_text="Test content",
            source_type=SourceType.MARKDOWN,
            enriched=EnrichedContent(
                summary="Test summary",
                entities=[],
                commitments=[],
            ),
        )
        
        assert memory.raw_text == "Test content"
        assert memory.source_type == SourceType.MARKDOWN
```

### Test Naming

- `test_<function>_<scenario>` for functions
- `test_<behavior>` for classes
- Use descriptive docstrings

## 🔄 Pull Request Process

### Before Submitting

1. **Create a branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make your changes**

3. **Run all checks**
   ```bash
   # Tests
   pytest tests/unit/ -v
   
   # Linting
   ruff check exo/
   
   # Type checking
   mypy exo/
   ```

4. **Commit with a clear message**
   ```bash
   git commit -m "feat: add semantic search filtering by date"
   ```

### Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `test:` - Adding or updating tests
- `refactor:` - Code change that neither fixes nor adds feature
- `chore:` - Maintenance tasks

Examples:
```
feat: add commitment due date filtering
fix: handle empty search results gracefully
docs: update API endpoint documentation
test: add tests for edge cases in query parsing
```

### PR Checklist

- [ ] Tests pass locally
- [ ] Linting passes
- [ ] Type checking passes
- [ ] Documentation updated (if needed)
- [ ] Commit messages follow convention
- [ ] PR description explains the change

## 🐛 Reporting Issues

### Bug Reports

Include:
1. Python version (`python --version`)
2. Exo version (`pip show exo-brain`)
3. Steps to reproduce
4. Expected vs actual behavior
5. Error messages/stack traces

### Feature Requests

Include:
1. Use case description
2. Proposed solution (if any)
3. Alternatives considered

## 🙏 Thank You!

Every contribution helps make Exo better. We appreciate your time and effort!

---

*Questions? Open an issue or reach out to the maintainers.*
