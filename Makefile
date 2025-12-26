.PHONY: install dev clean start help test test-eval test-eval-parallel test-eval-rich test-eval-dry

# Python interpreter
PYTHON := python3

# Virtual environment directory
VENV := .venv

help:
	@echo "Available commands:"
	@echo "  make install       - Create virtual environment and install dependencies"
	@echo "  make dev           - Start LangGraph development server"
	@echo "  make clean         - Remove virtual environment"
	@echo "  make start         - Alias for 'make dev'"
	@echo "  make test          - Run unit tests with pytest"
	@echo "  make test-eval     - Run evaluation tests with LangSmith tracking and caching (sequential)"
	@echo "  make test-eval-parallel - Run evals in parallel without caching (fresh LLM calls)"
	@echo "  make test-eval-rich - Run evals with rich LangSmith terminal output (no parallel)"
	@echo "  make test-eval-dry - Run evals in dry-run mode (no LangSmith tracking)"

install: $(VENV)/bin/activate

$(VENV)/bin/activate: simple_agent/requirements.txt
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r simple_agent/requirements.txt
	$(VENV)/bin/pip install -U "langgraph-cli[inmem]"
	@echo "Virtual environment created. Run 'source $(VENV)/bin/activate' to activate."

dev: install
	$(VENV)/bin/langgraph dev

start: dev

test:
	$(VENV)/bin/pytest tests/test_graph.py -v

# Run evals with caching (sequential - VCR caching doesn't work with parallel execution)
test-eval:
	LANGSMITH_TEST_CACHE=eval/cassettes \
	LANGSMITH_TEST_SUITE='Email Classification Tests' $(VENV)/bin/pytest eval/test_evals.py -v $(if $(JUDGE_MODEL),--judge-model=$(JUDGE_MODEL),)

# Run evals in parallel without caching (fresh LLM calls, faster but costs more)
test-eval-parallel:
	LANGSMITH_TEST_SUITE='Email Classification Tests' $(VENV)/bin/pytest eval/test_evals.py -v -n auto $(if $(JUDGE_MODEL),--judge-model=$(JUDGE_MODEL),)

# Run evals with rich LangSmith output (no parallelization - xdist not compatible with --langsmith-output)
test-eval-rich:
	LANGSMITH_TEST_CACHE=eval/cassettes \
	LANGSMITH_TEST_SUITE='Email Classification Tests' $(VENV)/bin/pytest eval/test_evals.py -v --langsmith-output $(if $(JUDGE_MODEL),--judge-model=$(JUDGE_MODEL),)

# Run evals without sending to LangSmith (dry-run mode, sequential with caching)
test-eval-dry:
	LANGSMITH_TEST_TRACKING=false \
	LANGSMITH_TEST_CACHE=eval/cassettes \
	LANGSMITH_TEST_SUITE='Email Classification Tests' $(VENV)/bin/pytest eval/test_evals.py -v $(if $(JUDGE_MODEL),--judge-model=$(JUDGE_MODEL),)

clean:
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true