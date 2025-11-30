import pytest
from simple_agent.agent import graph
from simple_agent.state import EmailState


def test_graph_flags_email_with_urgent_keyword():
    """Test that an email with urgent keywords is flagged as requiring attention."""
    input_state: EmailState = {
        "email_subject": "URGENT: Server outage needs immediate fix",
        "email_body": "The production server is down. Please address this ASAP.",
        "email_to": "oncall@company.com",
        "requires_attention": None,
    }

    result = graph.invoke(input_state)

    assert result["requires_attention"] is True


def test_graph_does_not_flag_normal_email():
    """Test that a normal email without urgent keywords is not flagged."""
    input_state: EmailState = {
        "email_subject": "Weekly team sync notes",
        "email_body": "Here are the notes from today's meeting. Have a great weekend!",
        "email_to": "team@company.com",
        "requires_attention": None,
    }

    result = graph.invoke(input_state)

    assert result["requires_attention"] is False
