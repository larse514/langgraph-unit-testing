import logging
import uuid

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from simple_agent.state import EmailState

logger = logging.getLogger(__name__)


def check_email_attention(state: EmailState) -> EmailState:
    """Determine if an email requires attention using OpenAI."""
    subject = state["email_subject"]
    body = state["email_body"]
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    system_prompt = """You are a support email classifier for a SaaS product. Your job is to determine if a customer support email requires immediate attention from the support team.

An email requires immediate attention if it contains:
- Service outages or downtime reports affecting the customer
- Critical bugs blocking the customer's workflow
- Security concerns or potential data breaches
- Billing issues such as failed payments or incorrect charges
- Account access problems (locked out, authentication failures)
- Data loss or corruption reports
- Compliance or legal concerns
- Customers expressing significant frustration or threatening to cancel

An email does NOT require immediate attention if it is:
- General feature requests or suggestions
- How-to questions or documentation requests
- Non-urgent feedback or praise
- Newsletter or marketing-related inquiries
- Routine account updates or preference changes

Respond with ONLY "yes" or "no" - nothing else."""

    human_prompt = f"""Subject: {subject}

Body: {body}

Does this email require immediate attention?"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ]
    
    response = llm.invoke(messages)
    answer = response.content.strip().lower()
    
    requires_attention = answer == "yes"
    
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
