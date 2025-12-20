# Parameterize LLM-as-Judge Model

## Summary

Add a `--judge-model` pytest CLI option to configure which model is used for LLM-as-judge evaluations, defaulting to `gpt-4o-mini`.

## Changes

### 1. Update [`eval/evaluators.py`](eval/evaluators.py)

Add a helper function to retrieve the judge model from an environment variable:

```python
import os

DEFAULT_JUDGE_MODEL = "gpt-4o-mini"

def get_judge_model() -> str:
    """Get the LLM judge model from environment or use default."""
    return os.environ.get("LLM_JUDGE_MODEL", DEFAULT_JUDGE_MODEL)
```

Update all 4 evaluators to use `get_judge_model()` instead of the hardcoded string:

- `summary_faithfulness_evaluator` (line 131)
- `summary_completeness_evaluator` (line 185)
- `summary_conciseness_evaluator` (line 229)
- `summary_triage_usefulness_evaluator` (line 289)

### 2. Create [`eval/conftest.py`](eval/conftest.py)

Add pytest configuration to accept the CLI option and set the environment variable:

```python
import os
import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--judge-model",
        action="store",
        default=None,
        help="LLM model to use for judge evaluations (default: gpt-4o-mini)"
    )

@pytest.fixture(scope="session", autouse=True)
def set_judge_model(request):
    model = request.config.getoption("--judge-model")
    if model:
        os.environ["LLM_JUDGE_MODEL"] = model
```

### 3. Update [`Makefile`](Makefile)

Update `test-eval` target to document and support the model option:

```makefile
test-eval:
	LANGSMITH_TEST_TRACKING=false \
	LANGSMITH_TEST_CACHE=eval/cassettes \
	$(VENV)/bin/pytest eval/test_evals.py -v -n auto $(if $(JUDGE_MODEL),--judge-model=$(JUDGE_MODEL),)
```

## Usage

```bash
# Use default model (gpt-4o-mini)
make test-eval

# Specify a different model
make test-eval JUDGE_MODEL=gpt-4

# Or directly with pytest
pytest eval/test_evals.py --judge-model=gpt-4
```

