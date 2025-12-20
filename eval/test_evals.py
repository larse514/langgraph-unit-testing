"""Pytest tests for email classification graph using LangSmith caching."""

import json
import pytest
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

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


@pytest.mark.parametrize(
    "example",
    TEST_CASES,
    ids=[case["inputs"]["email_subject"] for case in TEST_CASES]
)
def test_email_classification(example):
    """Test that the email classification graph correctly classifies emails."""
    state = {
        "email_subject": example["inputs"]["email_subject"],
        "email_body": example["inputs"]["email_body"],
        "email_to": example["inputs"]["email_to"],
        "requires_attention": None,
        "jira_ticket_id": None,
    }
    
    result = graph.invoke(state)
    
    expected_attention = example["outputs"]["requires_attention"]
    expected_ticket = example["outputs"]["should_create_ticket"]
    
    assert result["requires_attention"] == expected_attention, (
        f"Expected requires_attention={expected_attention}, "
        f"got {result['requires_attention']} for subject: {example['inputs']['email_subject']}"
    )
    
    ticket_created = result["jira_ticket_id"] is not None
    assert ticket_created == expected_ticket, (
        f"Expected ticket_created={expected_ticket}, "
        f"got {ticket_created} for subject: {example['inputs']['email_subject']}"
    )


# =============================================================================
# LLM-as-Judge Summary Evaluations
# =============================================================================

SUMMARY_EVALUATORS = [
    ("faithfulness", summary_faithfulness_evaluator, 0.8),
    ("completeness", summary_completeness_evaluator, 0.6),
    ("conciseness", summary_conciseness_evaluator, 0.8),
    ("triage_usefulness", summary_triage_usefulness_evaluator, 0.6),
]


@pytest.mark.parametrize(
    "example",
    TEST_CASES,
    ids=[case["inputs"]["email_subject"] for case in TEST_CASES]
)
@pytest.mark.parametrize(
    "evaluator_name,evaluator_fn,threshold",
    SUMMARY_EVALUATORS,
    ids=[e[0] for e in SUMMARY_EVALUATORS]
)
def test_email_summary_quality(example, evaluator_name, evaluator_fn, threshold):
    """Test that email summaries meet quality thresholds using LLM-as-judge evaluators."""
    state = {
        "email_subject": example["inputs"]["email_subject"],
        "email_body": example["inputs"]["email_body"],
        "email_to": example["inputs"]["email_to"],
        "requires_attention": None,
        "jira_ticket_id": None,
        "email_summary": None,
    }
    
    # Run the graph to generate the summary
    result = graph.invoke(state)
    
    # Run the evaluator
    eval_result = evaluator_fn(result, example)
    
    assert eval_result["score"] >= threshold, (
        f"{evaluator_name} score {eval_result['score']:.2f} below threshold {threshold} "
        f"for subject: {example['inputs']['email_subject']}. "
        f"Comment: {eval_result.get('comment', 'N/A')}"
    )

