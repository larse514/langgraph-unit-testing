import pytest
from simple_agent.agent import create_graph
from simple_agent.state import EmailState
from tests.stubs.stub_nodes import check_email_attention_stubbed


def test_graph_flags_email_with_urgent_keyword_and_creates_ticket():
    # Create test graph with stubbed check_email_attention
    graph = create_graph(check_email_attention=check_email_attention_stubbed)

    """Test that an email with urgent keywords is flagged and a Jira ticket is created."""
    input_state: EmailState = {
        "email_subject": "URGENT: Server outage needs immediate fix",
        "email_body": "The production server is down. Please address this ASAP.",
        "email_to": "oncall@company.com",
        "requires_attention": None,
        "jira_ticket_id": None,
    }

    result = graph.invoke(input_state)

    assert result["requires_attention"] is True
    assert result["jira_ticket_id"] is not None
    assert result["jira_ticket_id"].startswith("JIRA-")


def test_graph_does_not_flag_normal_email_and_no_ticket():
    # Create test graph with stubbed check_email_attention
    graph = create_graph(check_email_attention=check_email_attention_stubbed)

    """Test that a normal email without urgent keywords is not flagged and no ticket is created."""
    input_state: EmailState = {
        "email_subject": "Weekly team sync notes",
        "email_body": "Here are the notes from today's meeting. Have a great weekend!",
        "email_to": "team@company.com",
        "requires_attention": None,
        "jira_ticket_id": None,
    }

    result = graph.invoke(input_state)

    assert result["requires_attention"] is False
    assert result["jira_ticket_id"] is None
