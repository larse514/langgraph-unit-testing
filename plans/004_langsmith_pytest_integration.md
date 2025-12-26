# 004: LangSmith Pytest Integration Improvements

## Original Prompt

> review the langsmith pytest documentation and the current eval configuration. propose a plan to better take advantage of langsmith pytest library
>
> https://docs.langchain.com/langsmith/pytest

## Plan

### Current State Analysis

The existing setup partially uses LangSmith pytest features:
- `@pytest.mark.langsmith` on summary quality tests only
- `LANGSMITH_TEST_CACHE` for caching
- `LANGSMITH_TEST_SUITE` for grouping
- Custom evaluators that return dicts but don't integrate with LangSmith feedback logging

### Key Improvements

#### 1. Add LangSmith tracking to classification tests

Currently `test_email_classification` lacks `@pytest.mark.langsmith`, meaning those tests aren't tracked in LangSmith experiments. Add the decorator and proper logging.

```python
from langsmith import expect, testing as t

@pytest.mark.langsmith  # Added decorator
@pytest.mark.parametrize("sample_email", TEST_CASES, ...)
def test_email_classification(sample_email):
    ...
```

#### 2. Use `t.log_inputs/outputs/reference_outputs` in all tests

Add explicit logging to create proper LangSmith dataset columns with inputs, outputs, and reference outputs.

```python
def test_email_classification(sample_email):
    # Log inputs and expected outputs to LangSmith
    t.log_inputs(sample_email["inputs"])
    t.log_reference_outputs(sample_email["outputs"])
    
    result = graph.invoke(state)
    
    # Log actual outputs to LangSmith
    ticket_created = result["jira_ticket_id"] is not None
    t.log_outputs({
        "requires_attention": result["requires_attention"],
        "ticket_created": ticket_created,
    })
```

#### 3. Use `t.log_feedback()` for evaluator scores

Instead of only asserting, log feedback to LangSmith for rich experiment metrics.

```python
# Log feedback for evaluator scores
t.log_feedback(
    key=evaluator_name,
    score=eval_result["score"],
    comment=eval_result.get("comment"),
)
```

#### 4. Use `t.trace_feedback()` for LLM-as-judge calls

This separates evaluation LLM calls from application traces - a best practice from the docs.

```python
# Run the evaluator within trace_feedback context
# This separates LLM-as-judge calls from application traces
with t.trace_feedback():
    eval_result = evaluator_fn(result, sample_email)
    t.log_feedback(
        key=evaluator_name,
        score=eval_result["score"],
        comment=eval_result.get("comment"),
    )
```

#### 5. Use `expect` utility instead of `assert`

For assertions that auto-log feedback to LangSmith.

```python
from langsmith import expect

# Instead of: assert result["requires_attention"] == expected_attention
expect(result["requires_attention"]).to_equal(expected_attention)
expect(ticket_created).to_equal(expected_ticket)

# For threshold checks (expect only has > not >=, so subtract epsilon)
expect(eval_result["score"]).to_be_greater_than(threshold - 0.001)
```

### Files Modified

- `eval/test_evals.py`: Main test refactoring
- `Makefile`: Fixed VCR caching race condition with parallel execution

### Expected Benefits

1. **Better LangSmith datasets** - Proper input/output/reference columns in datasets
2. **Richer experiment metrics** - Feedback scores visible in LangSmith UI
3. **Cleaner traces** - LLM-as-judge calls separated from application traces
4. **Comprehensive tracking** - All tests (classification + summary) tracked together

## Follow-up Changes

### Use `expect` instead of `assert`

> use the langsmith expect rather than assert

Replaced all `assert` statements with LangSmith's `expect` utility:
- `expect(result["requires_attention"]).to_equal(expected_attention)`
- `expect(ticket_created).to_equal(expected_ticket)`
- `expect(eval_result["score"]).to_be_greater_than(threshold - 0.001)`

### Fix VCR Caching Race Condition

Tests were failing with `RuntimeError: Set changed size during iteration` due to VCR.py not being thread-safe with parallel execution.

**Solution:** Updated Makefile to separate caching and parallel execution:

| Command | Caching | Parallel | Use Case |
|---------|---------|----------|----------|
| `make test-eval` | Yes | No | Default - uses cached LLM responses, reliable |
| `make test-eval-parallel` | No | Yes | Fresh LLM calls, faster but costs more |
| `make test-eval-rich` | Yes | No | Rich LangSmith terminal output |
| `make test-eval-dry` | Yes | No | Local testing without LangSmith tracking |

```makefile
# Run evals with caching (sequential - VCR caching doesn't work with parallel execution)
test-eval:
	LANGSMITH_TEST_CACHE=eval/cassettes \
	LANGSMITH_TEST_SUITE='Email Classification Tests' pytest eval/test_evals.py -v

# Run evals in parallel without caching (fresh LLM calls, faster but costs more)
test-eval-parallel:
	LANGSMITH_TEST_SUITE='Email Classification Tests' pytest eval/test_evals.py -v -n auto
```

