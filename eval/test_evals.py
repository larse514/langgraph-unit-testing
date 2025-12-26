"""Pytest tests for email classification graph using LangSmith caching."""

import json
import pytest
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from langsmith import expect, testing as t

from simple_agent.agent import graph
from eval.evaluators import (
    summary_faithfulness_evaluator,
    summary_completeness_evaluator,
    summary_conciseness_evaluator,
    summary_triage_usefulness_evaluator,
)


def load_test_cases():
    """Load test cases from dataset.jsonl."""
    dataset_path = Path(__file__).parent / "dataset.jsonl"
    cases = []
    with open(dataset_path) as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                cases.append({
                    "inputs": data["inputs"],
                    "outputs": data["outputs"],
                })
    return cases


TEST_CASES = load_test_cases()


@pytest.mark.langsmith
@pytest.mark.parametrize(
    "sample_email",
    TEST_CASES,
    ids=[case["inputs"]["email_subject"] for case in TEST_CASES]
)
def test_email_classification(sample_email):
    """Test that the email classification graph correctly classifies emails."""
    # Log inputs and expected outputs to LangSmith
    t.log_inputs(sample_email["inputs"])
    t.log_reference_outputs(sample_email["outputs"])
    
    state = {
        "email_subject": sample_email["inputs"]["email_subject"],
        "email_body": sample_email["inputs"]["email_body"],
        "email_to": sample_email["inputs"]["email_to"],
        "requires_attention": None,
        "jira_ticket_id": None,
    }
    
    result = graph.invoke(state)
    
    # Log actual outputs to LangSmith
    ticket_created = result["jira_ticket_id"] is not None
    t.log_outputs({
        "requires_attention": result["requires_attention"],
        "ticket_created": ticket_created,
    })
    
    expected_attention = sample_email["outputs"]["requires_attention"]
    expected_ticket = sample_email["outputs"]["should_create_ticket"]
    
    # Use expect for assertions - auto-logs feedback to LangSmith
    expect(result["requires_attention"]).to_equal(expected_attention)
    expect(ticket_created).to_equal(expected_ticket)


# =============================================================================
# LLM-as-Judge Summary Evaluations
# =============================================================================

SUMMARY_EVALUATORS = [
    ("faithfulness", summary_faithfulness_evaluator, 0.8),
    ("completeness", summary_completeness_evaluator, 0.6),
    ("conciseness", summary_conciseness_evaluator, 0.8),
    ("triage_usefulness", summary_triage_usefulness_evaluator, 0.6),
]


@pytest.mark.langsmith
@pytest.mark.parametrize(
    "sample_email",
    TEST_CASES, 
    ids=[case["inputs"]["email_subject"] for case in TEST_CASES]
)
@pytest.mark.parametrize(
    "evaluator_name,evaluator_fn,threshold",
    SUMMARY_EVALUATORS,
    ids=[e[0] for e in SUMMARY_EVALUATORS]
)
def test_email_summary_quality(sample_email, evaluator_name, evaluator_fn, threshold):
    """Test that email summaries meet quality thresholds using LLM-as-judge evaluators."""
    # Log inputs and expected outputs to LangSmith
    t.log_inputs(sample_email["inputs"])
    t.log_reference_outputs(sample_email["outputs"])
    
    state = {
        "email_subject": sample_email["inputs"]["email_subject"],
        "email_body": sample_email["inputs"]["email_body"],
        "email_to": sample_email["inputs"]["email_to"],
        "requires_attention": None,
        "jira_ticket_id": None,
        "email_summary": None,
    }
    
    # Run the graph to generate the summary
    result = graph.invoke(state)
    
    # Log actual outputs to LangSmith
    t.log_outputs({"email_summary": result.get("email_summary")})
    
    # Run the evaluator within trace_feedback context
    # This separates LLM-as-judge calls from application traces
    with t.trace_feedback():
        eval_result = evaluator_fn(result, sample_email)
        t.log_feedback(
            key=evaluator_name,
            score=eval_result["score"],
            comment=eval_result.get("comment"),
        )
    
    # Use expect for threshold assertion - auto-logs 'expectation' feedback to LangSmith
    # Subtract small epsilon since expect only has > not >=
    expect(eval_result["score"]).to_be_greater_than(threshold - 0.001)

