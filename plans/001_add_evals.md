# Add LangSmith Evals for Email Classification Graph

## Overview

Set up LangSmith evals to test the correctness of the email classification graph. The graph should correctly identify urgent emails and create Jira tickets when needed.

## Implementation Plan

### 1. Add Dependencies

- Update `simple_agent/requirements.txt` to include `langsmith` package

### 2. Create Evaluation Dataset

- Create `eval/dataset.jsonl` with test email examples including:
- Input: `email_subject`, `email_body`, `email_to`
- Expected output: `requires_attention` (bool), `should_create_ticket` (bool)
- Test cases covering:
  - Urgent emails (server outages, critical bugs, security issues)
  - Non-urgent emails (feature requests, general questions)
  - Edge cases (ambiguous emails)

### 3. Create Evaluators

- Create `eval/evaluators.py` with custom evaluators:
- `correctness_evaluator`: Checks if `requires_attention` matches expected value
- `ticket_creation_evaluator`: Verifies Jira ticket is created when `requires_attention=True` and not created when `False`

### 4. Create Evaluation Runner

- Create `eval/run_evals.py` that:
- Loads the dataset from `eval/dataset.jsonl`
- Runs the graph on each test case
- Evaluates results using the custom evaluators
- Reports results to LangSmith
- Prints summary statistics

### 5. Update Configuration

- Ensure `.env` includes `LANGCHAIN_API_KEY` and `LANGCHAIN_TRACING_V2=true` for LangSmith integration
- Update `langgraph.json` if needed to support eval runs

## Files to Create/Modify

- `simple_agent/requirements.txt` - Add langsmith dependency
- `eval/dataset.jsonl` - Test dataset with email examples and expected outcomes
- `eval/evaluators.py` - Custom evaluator functions
- `eval/run_evals.py` - Main evaluation runner script
- `eval/__init__.py` - Make eval a Python package

## Key Implementation Details

- Use LangSmith's `evaluate` function to run evaluations
- Each dataset row should include both input state and expected outputs
- Evaluators will compare actual graph outputs against expected values
- Results will be logged to LangSmith for tracking over time

