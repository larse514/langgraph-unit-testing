"""Pytest tests for email classification graph using LangSmith caching."""

import json
import pytest
from pathlib import Path

from simple_agent.agent import graph


def load_test_cases():
    """Load test cases from dataset.jsonl."""
    dataset_path = Path(__file__).parent / "dataset.jsonl"
    cases = []
    with open(dataset_path) as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                cases.append((
                    data["inputs"]["email_subject"],
                    data["inputs"]["email_body"],
                    data["inputs"]["email_to"],
                    data["outputs"]["requires_attention"],
                    data["outputs"]["should_create_ticket"],
                ))
    return cases


TEST_CASES = load_test_cases()


@pytest.mark.parametrize(
    "email_subject,email_body,email_to,expected_attention,expected_ticket",
    TEST_CASES,
    ids=[f"{TEST_CASES[i][0]}" for i in range(len(TEST_CASES))]
)
def test_email_classification(email_subject, email_body, email_to, expected_attention, expected_ticket):
    """Test that the email classification graph correctly classifies emails."""
    state = {
        "email_subject": email_subject,
        "email_body": email_body,
        "email_to": email_to,
        "requires_attention": None,
        "jira_ticket_id": None,
    }
    
    result = graph.invoke(state)
    
    assert result["requires_attention"] == expected_attention, (
        f"Expected requires_attention={expected_attention}, "
        f"got {result['requires_attention']} for subject: {email_subject}"
    )
    
    ticket_created = result["jira_ticket_id"] is not None
    assert ticket_created == expected_ticket, (
        f"Expected ticket_created={expected_ticket}, "
        f"got {ticket_created} for subject: {email_subject}"
    )

