# LLM-as-a-Judge Evaluators for Email Summarization

## Original Prompt

> We have implemented a new feature to summarize the contents of a support email that has come into the langgraph support agent. We want to set up new evaluators, specifically langsmith's llm-as-a-judge.
>
> What evaluations should we setup?

## Reference Documentation

- [LangSmith LLM-as-a-Judge Documentation](https://docs.langchain.com/langsmith/llm-as-judge)

## Context

The `summarize_email` node generates a 2-3 sentence summary that captures:
- The main topic or issue
- Any specific requests or problems mentioned
- The urgency or tone if relevant

Summaries are stored in state and included in Jira ticket descriptions for support agent triage.

## Recommended Evaluators

### 1. Summary Faithfulness (Hallucination Detection)

**Priority:** 🔴 Critical

**Purpose:** Ensures the summary accurately reflects the email content without inventing information.

**Evaluation Criteria:**
- All claims in the summary can be verified from the original email
- No new information is invented or hallucinated
- The tone/urgency accurately reflects the original

```python
from langsmith import wrappers
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

oai_client = wrappers.wrap_openai(ChatOpenAI(model="gpt-4o", temperature=0))

def summary_faithfulness_evaluator(run: dict, example: dict) -> dict:
    """Evaluate if the summary is faithful to the original email (no hallucinations)."""
    
    class FaithfulnessResponse(BaseModel):
        is_faithful: bool
        reasoning: str
    
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

    response = oai_client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": msg}
        ],
        response_format=FaithfulnessResponse
    )
    
    return {
        "key": "summary_faithfulness",
        "score": 1 if response.choices[0].message.parsed.is_faithful else 0,
        "comment": response.choices[0].message.parsed.reasoning
    }
```

---

### 2. Summary Completeness

**Priority:** 🟡 High

**Purpose:** Checks if the summary captures all key points per prompt requirements.

**Evaluation Criteria:**
- Captures the main topic or issue
- Captures any specific requests or problems mentioned
- Captures the urgency or tone (if present)

```python
def summary_completeness_evaluator(run: dict, example: dict) -> dict:
    """Evaluate if the summary captures all key information from the email."""
    
    class CompletenessResponse(BaseModel):
        captures_main_topic: bool
        captures_requests_or_problems: bool
        captures_urgency_if_present: bool
        overall_score: int  # 0-3 scale
        reasoning: str
    
    email_subject = example["inputs"]["email_subject"]
    email_body = example["inputs"]["email_body"]
    summary = run.get("email_summary", "")
    
    instructions = """You are evaluating whether an email summary is complete.

A complete summary should capture:
1. The main topic or issue being discussed
2. Any specific requests or problems mentioned
3. The urgency or tone (if the email conveys urgency, frustration, etc.)

Score 0-3 based on how many of these elements are captured."""

    msg = f"""Original Email Subject: {email_subject}
Original Email Body: {email_body}

Generated Summary: {summary}

Evaluate the completeness of this summary."""

    response = oai_client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": msg}
        ],
        response_format=CompletenessResponse
    )
    
    parsed = response.choices[0].message.parsed
    return {
        "key": "summary_completeness",
        "score": parsed.overall_score / 3,  # Normalize to 0-1
        "comment": parsed.reasoning
    }
```

---

### 3. Summary Conciseness

**Priority:** 🟢 Medium

**Purpose:** Validates the summary meets the 2-3 sentence requirement without unnecessary fluff.

**Evaluation Criteria:**
- 2-3 sentences long
- Free of unnecessary filler or greeting phrases
- Direct and to the point

```python
def summary_conciseness_evaluator(run: dict, example: dict) -> dict:
    """Evaluate if the summary is appropriately concise (2-3 sentences)."""
    
    class ConcisenessResponse(BaseModel):
        is_concise: bool
        sentence_count: int
        reasoning: str
    
    summary = run.get("email_summary", "")
    
    instructions = """You are evaluating whether an email summary is appropriately concise.

A concise summary should be:
- 2-3 sentences long
- Free of unnecessary filler or greeting phrases
- Direct and to the point

Count the sentences and determine if the summary is concise."""

    msg = f"""Generated Summary: {summary}

Is this summary appropriately concise?"""

    response = oai_client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": msg}
        ],
        response_format=ConcisenessResponse
    )
    
    parsed = response.choices[0].message.parsed
    return {
        "key": "summary_conciseness",
        "score": 1 if parsed.is_concise else 0,
        "comment": f"Sentence count: {parsed.sentence_count}. {parsed.reasoning}"
    }
```

---

### 4. Triage Usefulness

**Priority:** 🟡 High

**Purpose:** Evaluates if summaries help support agents quickly understand and prioritize tickets.

**Evaluation Criteria:**
- Quickly conveys what the customer needs
- Helps prioritize the ticket's urgency
- Clear enough that an agent doesn't need to read the full email

```python
def summary_triage_usefulness_evaluator(run: dict, example: dict) -> dict:
    """Evaluate if the summary would help a support agent triage the ticket."""
    
    class TriageResponse(BaseModel):
        would_help_triage: bool
        clarity_score: int  # 1-5
        reasoning: str
    
    email_subject = example["inputs"]["email_subject"]
    summary = run.get("email_summary", "")
    
    instructions = """You are a support team manager evaluating email summaries for ticket triage.

A useful summary for triage should:
- Quickly convey what the customer needs
- Help prioritize the ticket's urgency
- Be clear enough that an agent doesn't need to read the full email

Rate clarity 1-5 (5 = perfectly clear, 1 = confusing/unhelpful)."""

    msg = f"""Email Subject: {email_subject}
Generated Summary: {summary}

Would this summary help a support agent quickly triage this ticket?"""

    response = oai_client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": msg}
        ],
        response_format=TriageResponse
    )
    
    parsed = response.choices[0].message.parsed
    return {
        "key": "summary_triage_usefulness",
        "score": parsed.clarity_score / 5,  # Normalize to 0-1
        "comment": parsed.reasoning
    }
```

---

## Priority Summary

| Evaluator | Priority | Rationale |
|-----------|----------|-----------|
| **Faithfulness** | 🔴 Critical | Hallucinations in summaries could cause incorrect ticket handling |
| **Completeness** | 🟡 High | Ensures agents get all relevant context |
| **Triage Usefulness** | 🟡 High | Directly measures business value |
| **Conciseness** | 🟢 Medium | Quality check for adherence to prompt spec |

## Dataset Considerations

Consider extending `dataset.jsonl` to include expected summary keywords for reference-based evaluation:

```jsonl
{"inputs": {...}, "outputs": {..., "expected_summary_contains": ["production server", "down", "critical"]}}
```

## Next Steps

1. Add evaluators to `eval/evaluators.py`
2. Update `eval/test_evals.py` to wire in new evaluators
3. Run evaluations against existing dataset to establish baseline metrics

