"""Custom evaluators for the email classification graph."""

from typing import Any, Dict


def correctness_evaluator(run: Dict[str, Any], example: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates if the graph correctly classified the email's attention requirement.
    
    Args:
        run: The run output from the graph execution, containing the final state
        example: The example from the dataset, containing expected outputs
    
    Returns:
        Dictionary with 'key' (evaluator name) and 'score' (1 if correct, 0 if incorrect)
    """
    expected_requires_attention = example["outputs"]["requires_attention"]
    
    # Extract the actual result from the run
    # The run output should be the final state from the graph
    actual_requires_attention = run.get("requires_attention")
    
    is_correct = actual_requires_attention == expected_requires_attention
    
    return {
        "key": "correctness",
        "score": 1 if is_correct else 0,
    }


def ticket_creation_evaluator(run: Dict[str, Any], example: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates if the Jira ticket was created (or not created) correctly.
    
    Args:
        run: The run output from the graph execution, containing the final state
        example: The example from the dataset, containing expected outputs
    
    Returns:
        Dictionary with 'key' (evaluator name) and 'score' (1 if correct, 0 if incorrect)
    """
    should_create_ticket = example["outputs"]["should_create_ticket"]
    actual_ticket_id = run.get("jira_ticket_id")
    
    # Ticket should be created if should_create_ticket is True
    # Ticket should NOT be created if should_create_ticket is False
    ticket_created = actual_ticket_id is not None
    
    is_correct = ticket_created == should_create_ticket
    
    return {
        "key": "ticket_creation",
        "score": 1 if is_correct else 0,
    }

