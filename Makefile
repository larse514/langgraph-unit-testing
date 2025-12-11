.PHONY: install dev clean start help test test-eval

# Python interpreter
PYTHON := python3

# Virtual environment directory
VENV := .venv

help:
	@echo "Available commands:"
	@echo "  make install  - Create virtual environment and install dependencies"
	@echo "  make dev      - Start LangGraph development server"
	@echo "  make clean    - Remove virtual environment"
	@echo "  make start    - Alias for 'make dev'"
	@echo "  make test     - Run unit tests with pytest"
	@echo "  make test-eval - Run evaluation tests with LangSmith caching"

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

test-eval:
	LANGSMITH_TEST_TRACKING=false \
	LANGSMITH_TEST_CACHE=eval/cassettes \
	$(VENV)/bin/pytest eval/test_evals.py -v

clean:
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true