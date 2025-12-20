"""Custom evaluators for the email classification graph."""

import os
from typing import Any, Dict

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel

DEFAULT_JUDGE_MODEL = "gpt-4o-mini"


def get_judge_model() -> str:
    """Get the LLM judge model from environment or use default."""
    return os.environ.get("LLM_JUDGE_MODEL", DEFAULT_JUDGE_MODEL)


def does_email_require_attention_evaluator(run: Dict[str, Any], example: Dict[str, Any]) -> Dict[str, Any]:
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


def should_ticket_be_created_evaluator(run: Dict[str, Any], example: Dict[str, Any]) -> Dict[str, Any]:
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


# =============================================================================
# LLM-as-Judge Evaluators for Email Summary
# =============================================================================


class FaithfulnessResponse(BaseModel):
    """Response schema for faithfulness evaluation."""
    is_faithful: bool
    reasoning: str


class CompletenessResponse(BaseModel):
    """Response schema for completeness evaluation."""
    captures_main_topic: bool
    captures_requests_or_problems: bool
    captures_urgency_if_present: bool
    overall_score: int  # 0-3 scale
    reasoning: str


class ConcisenessResponse(BaseModel):
    """Response schema for conciseness evaluation."""
    is_concise: bool
    sentence_count: int
    reasoning: str


class TriageResponse(BaseModel):
    """Response schema for triage usefulness evaluation."""
    would_help_triage: bool
    clarity_score: int  # 1-5 scale
    reasoning: str


def summary_faithfulness_evaluator(run: Dict[str, Any], example: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate if the summary is faithful to the original email (no hallucinations).
    
    Priority: Critical - Hallucinations in summaries could cause incorrect ticket handling.
    
    Args:
        run: The run output containing email_summary
        example: The example containing original email inputs
    
    Returns:
        Dictionary with 'key', 'score' (0 or 1), and 'comment'
    """
    email_subject = example["inputs"]["email_subject"]
    email_body = example["inputs"]["email_body"]
    summary = run.get("email_summary", "")
    
    instructions = """You are evaluating whether an email summary is faithful to the original email.

A summary is FAITHFUL if:
- All claims in the summary can be verified from the original email
- No new information is invented or hallucinated
- The tone/urgency accurately reflects the original

A summary is NOT FAITHFUL if:
- It contains information not present in the original email
- It misrepresents the intent or content of the email
- It exaggerates or downplays the severity inappropriately"""

    msg = f"""Original Email Subject: {email_subject}
Original Email Body: {email_body}

Generated Summary: {summary}

Is this summary faithful to the original email?"""

    llm = ChatOpenAI(model=get_judge_model(), temperature=0).with_structured_output(FaithfulnessResponse)
    
    messages = [
        SystemMessage(content=instructions),
        HumanMessage(content=msg),
    ]
    
    response = llm.invoke(messages)
    
    return {
        "key": "summary_faithfulness",
        "score": 1 if response.is_faithful else 0,
        "comment": response.reasoning,
    }


def summary_completeness_evaluator(run: Dict[str, Any], example: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate if the summary captures all key information from the email.
    
    Priority: High - Ensures agents get all relevant context.
    
    Args:
        run: The run output containing email_summary
        example: The example containing original email inputs
    
    Returns:
        Dictionary with 'key', 'score' (0-1 normalized), and 'comment'
    """
    email_subject = example["inputs"]["email_subject"]
    email_body = example["inputs"]["email_body"]
    summary = run.get("email_summary", "")
    
    instructions = """You are evaluating whether an email summary is complete.

A complete summary should capture:
1. The main topic or issue being discussed
2. Any specific requests or problems mentioned (if present in the original)
3. The urgency or tone (if the email conveys urgency, frustration, etc.)

IMPORTANT: Only score based on elements that ARE present in the original email.
If the original email has no specific requests, problems, or urgency, the summary 
should NOT be penalized for not including them. A simple thank-you email or 
informational update that captures the main topic should score 3/3.

Score 0-3 based on how many relevant elements are captured."""

    msg = f"""Original Email Subject: {email_subject}
Original Email Body: {email_body}

Generated Summary: {summary}

Evaluate the completeness of this summary."""

    llm = ChatOpenAI(model=get_judge_model(), temperature=0).with_structured_output(CompletenessResponse)
    
    messages = [
        SystemMessage(content=instructions),
        HumanMessage(content=msg),
    ]
    
    response = llm.invoke(messages)
    
    return {
        "key": "summary_completeness",
        "score": response.overall_score / 3,  # Normalize to 0-1
        "comment": response.reasoning,
    }


def summary_conciseness_evaluator(run: Dict[str, Any], example: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate if the summary is appropriately concise (2-3 sentences).
    
    Priority: Medium - Quality check for adherence to prompt spec.
    
    Args:
        run: The run output containing email_summary
        example: The example (not used, but required for evaluator signature)
    
    Returns:
        Dictionary with 'key', 'score' (0-1), and 'comment'
    """
    summary = run.get("email_summary", "")
    
    instructions = """You are evaluating whether an email summary is appropriately concise.

A concise summary should be:
- 2-3 sentences long
- Free of unnecessary filler or greeting phrases
- Direct and to the point

Count the sentences in the summary."""

    msg = f"""Generated Summary: {summary}

Count the sentences and evaluate conciseness."""

    llm = ChatOpenAI(model=get_judge_model(), temperature=0).with_structured_output(ConcisenessResponse)
    
    messages = [
        SystemMessage(content=instructions),
        HumanMessage(content=msg),
    ]
    
    response = llm.invoke(messages)
    
    # Score based on sentence count: 1-3 is ideal, 4 is acceptable, others are poor
    sentence_count = response.sentence_count
    if 1 <= sentence_count <= 3:
        score = 1.0
    elif sentence_count == 4:
        score = 0.5
    else:
        score = 0.0
    
    return {
        "key": "summary_conciseness",
        "score": score,
        "comment": f"Sentence count: {response.sentence_count}. {response.reasoning}",
    }


def summary_triage_usefulness_evaluator(run: Dict[str, Any], example: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate if the summary would help a support agent triage the ticket.
    
    Priority: High - Directly measures business value.
    
    Args:
        run: The run output containing email_summary
        example: The example containing email subject
    
    Returns:
        Dictionary with 'key', 'score' (0-1 normalized), and 'comment'
    """
    email_subject = example["inputs"]["email_subject"]
    summary = run.get("email_summary", "")
    
    instructions = """You are a support team manager evaluating email summaries for ticket triage.

A useful summary for triage should:
- Quickly convey what the sender needs or what the email is about
- Help prioritize the email's urgency (or indicate it's low priority if applicable)
- Be clear enough that an agent doesn't need to read the full email

NOTE: Not all emails are customer support requests. For internal emails (team updates, 
meeting notes) or simple informational emails (thank you notes, positive feedback), 
evaluate based on whether the summary clearly conveys the main point. These emails 
should score well if the summary is clear and accurate, even without customer-specific needs.

Rate clarity 1-5 (5 = perfectly clear, 1 = confusing/unhelpful)."""

    msg = f"""Email Subject: {email_subject}
Generated Summary: {summary}

Would this summary help a support agent quickly triage this ticket?"""

    llm = ChatOpenAI(model=get_judge_model(), temperature=0).with_structured_output(TriageResponse)
    
    messages = [
        SystemMessage(content=instructions),
        HumanMessage(content=msg),
    ]
    
    response = llm.invoke(messages)
    
    return {
        "key": "summary_triage_usefulness",
        "score": response.clarity_score / 5,  # Normalize to 0-1
        "comment": response.reasoning,
    }
