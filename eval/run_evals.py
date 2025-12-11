"""Run LangSmith evaluations on the email classification graph."""

import json
import os
from pathlib import Path
from typing import Dict, Any

from langsmith import evaluate

from simple_agent.agent import graph
from eval.evaluators import correctness_evaluator, ticket_creation_evaluator


def load_dataset(file_path: str) -> list:
    """Load the evaluation dataset from a JSONL file."""
    dataset = []
    with open(file_path, "r") as f:
        for line in f:
            if line.strip():
                dataset.append(json.loads(line))
    return dataset


def run_graph(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the graph with the given inputs.
    
    Args:
        inputs: Dictionary containing email_subject, email_body, email_to
    
    Returns:
        The final state from the graph execution
    """
    # Convert inputs to EmailState format
    state = {
        "email_subject": inputs["email_subject"],
        "email_body": inputs["email_body"],
        "email_to": inputs["email_to"],
        "requires_attention": None,
        "jira_ticket_id": None,
    }
    
    # Run the graph
    result = graph.invoke(state)
    return result


def main():
    """Main function to run evaluations."""
    # Load dataset
    dataset_path = Path(__file__).parent / "dataset.jsonl"
    dataset = load_dataset(str(dataset_path))
    
    print(f"Loaded {len(dataset)} test cases from {dataset_path}")
    
    # Check for LangSmith API key
    api_key = os.getenv("LANGCHAIN_API_KEY")
    if not api_key:
        print("Warning: LANGCHAIN_API_KEY not set. Results will not be logged to LangSmith.")
        print("Set LANGCHAIN_API_KEY in your .env file to enable LangSmith logging.")
    
    # Run evaluations
    # evaluate() returns an iterator, so we convert it to a list
    results = list(evaluate(
        target=run_graph,
        data=dataset,
        evaluators=[correctness_evaluator, ticket_creation_evaluator],
        experiment_prefix="email-classification",
        description="Evaluation of email classification graph correctness and ticket creation",
    ))
    
    # Print summary statistics
    print("\n" + "=" * 60)
    print("Evaluation Results Summary")
    print("=" * 60)
    
    # Calculate accuracy for each evaluator
    # Results structure: each result has a 'results' list with evaluator outputs
    correctness_scores = []
    ticket_scores = []
    
    for result in results:
        # Each result contains evaluator outputs in the 'results' field
        eval_results = result.get("results", [])
        if len(eval_results) >= 2:
            correctness_scores.append(eval_results[0].get("score", 0))
            ticket_scores.append(eval_results[1].get("score", 0))
        elif len(eval_results) == 1:
            # Handle case where only one evaluator result is present
            key = eval_results[0].get("key", "")
            score = eval_results[0].get("score", 0)
            if key == "correctness":
                correctness_scores.append(score)
            elif key == "ticket_creation":
                ticket_scores.append(score)
    
    if correctness_scores:
        correctness_accuracy = sum(correctness_scores) / len(correctness_scores) * 100
        print(f"\nCorrectness Evaluator:")
        print(f"  Accuracy: {correctness_accuracy:.1f}% ({sum(correctness_scores)}/{len(correctness_scores)} correct)")
    
    if ticket_scores:
        ticket_accuracy = sum(ticket_scores) / len(ticket_scores) * 100
        print(f"\nTicket Creation Evaluator:")
        print(f"  Accuracy: {ticket_accuracy:.1f}% ({sum(ticket_scores)}/{len(ticket_scores)} correct)")
    
    print(f"\nOverall:")
    print(f"  Total test cases: {len(dataset)}")
    if correctness_scores and ticket_scores:
        both_passed = sum(1 for c, t in zip(correctness_scores, ticket_scores) if c == 1 and t == 1)
        print(f"  Both evaluators passed: {both_passed}/{len(dataset)}")
    
    if api_key:
        print(f"\nResults have been logged to LangSmith.")
        print(f"View results at: https://smith.langchain.com/")
    else:
        print(f"\nNote: Set LANGCHAIN_API_KEY to log results to LangSmith.")
    
    print("=" * 60)


if __name__ == "__main__":
    main()

