# LangGraph Testing Demo

An example project to show how to test & evaluate LangGraph applications. 

## What It Does

This project implements a simple email triage agent that:

1. **Checks if an email requires attention** — Uses OpenAI to classify incoming support emails as urgent or non-urgent
2. **Creates a Jira ticket** — If the email requires attention, a (stubbed) Jira ticket is created
3. **Logs and skips** — If the email doesn't require attention, it logs and ends the graph

The key focus is demonstrating how to:
- Use **dependency injection** in LangGraph graphs via a factory function
- Write **unit tests** that stub out LLM calls and external services
- Test **graph routing logic** without hitting real APIs
- Evaluate graphs using ***LangSmith evaluators***

## Commands

| Command | Description |
|---------|-------------|
| `make install` | Create virtual environment and install dependencies |
| `make dev` | Start the LangGraph development server |
| `make start` | Alias for `make dev` |
| `make test` | Run unit tests with pytest |
| `make clean` | Remove virtual environment and cached files |

## Additional Dependencies

The following are **not** included in `requirements.txt` and must be set up separately:

### LangGraph CLI

The LangGraph CLI is installed automatically via `make install`, but if you're installing manually:

```bash
pip install -U "langgraph-cli[inmem]"
```

### Environment Variables

Create a `.env` file in the project root with your OpenAI API key:

```bash
cp .env.example .env
# Then edit .env and add your actual API key
```

## Quick Start

```bash
# 1. Install dependencies
make install

# 2. Activate the virtual environment
source .venv/bin/activate

# 3. Set up your environment variables
cp .env.example .env
# Edit .env with your OPENAI_API_KEY

# 4. Run tests (no API key needed — tests use stubs!)
make test

# 5. Run evals (requires API key)
make test-eval
# 6. Start the dev server (requires API key)
make dev
```