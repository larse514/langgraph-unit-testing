from simple_agent.state import EmailState

# Keywords that indicate an email requires attention
URGENT_KEYWORDS = [
    "urgent",
    "asap",
    "immediately",
    "critical",
    "important",
    "deadline",
    "action required",
    "time sensitive",
    "priority",
    "emergency",
]

def check_email_attention_stubbed(state: EmailState) -> EmailState:
    """Determine if an email requires attention based on subject and body."""
    subject = state["email_subject"].lower()
    body = state["email_body"].lower()
    
    # Check if any urgent keywords are in the subject or body
    combined_text = f"{subject} {body}"
    
    requires_attention = any(keyword in combined_text for keyword in URGENT_KEYWORDS)
    
    return {"requires_attention": requires_attention}