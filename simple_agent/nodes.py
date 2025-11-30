import logging
import uuid

from simple_agent.state import EmailState

logger = logging.getLogger(__name__)

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


def check_email_attention(state: EmailState) -> EmailState:
    """Determine if an email requires attention based on subject and body."""
    subject = state["email_subject"].lower()
    body = state["email_body"].lower()
    
    # Check if any urgent keywords are in the subject or body
    combined_text = f"{subject} {body}"
    
    requires_attention = any(keyword in combined_text for keyword in URGENT_KEYWORDS)
    
    return {"requires_attention": requires_attention}


class JiraClient:
    """Stubbed Jira client that simulates ticket creation."""
    
    def create_ticket(self, summary: str, description: str) -> str:
        """Create a Jira ticket (stubbed - just logs and returns fake ID)."""
        ticket_id = f"JIRA-{uuid.uuid4().hex[:6].upper()}"
        logger.info(f"[STUB] Created Jira ticket {ticket_id}: {summary}")
        return ticket_id


def create_jira_ticket(state: EmailState) -> EmailState:
    """Create a Jira ticket for emails that require attention."""
    client = JiraClient()
    
    summary = f"Email requires attention: {state['email_subject']}"
    description = f"Email to: {state['email_to']}\n\nBody:\n{state['email_body']}"
    
    ticket_id = client.create_ticket(summary, description)
    logger.info(f"Created Jira ticket {ticket_id} for email: {state['email_subject']}")
    
    return {"jira_ticket_id": ticket_id}


def log_no_attention_needed(state: EmailState) -> EmailState:
    """Log that the email does not require attention."""
    logger.info(f"Email does not require attention: {state['email_subject']}")
    return {}
