from typing import Callable, Optional

from langgraph.graph import StateGraph, END

from simple_agent.nodes import (
    summarize_email as default_summarize_email,
    check_email_attention as default_check_email_attention,
    create_jira_ticket as default_create_jira_ticket,
    log_no_attention_needed as default_log_no_attention_needed,
)
from simple_agent.state import EmailState


def create_graph(
    summarize_email: Optional[Callable] = None,
    check_email_attention: Optional[Callable] = None,
    create_jira_ticket: Optional[Callable] = None,
    log_no_attention_needed: Optional[Callable] = None,
):
    """
    Factory method to create and compile the email processing graph.
    
    Args:
        summarize_email: Optional custom node function for summarizing emails.
        check_email_attention: Optional custom node function for checking email attention.
        create_jira_ticket: Optional custom node function for creating Jira tickets.
        log_no_attention_needed: Optional custom node function for logging no attention needed.
    
    Returns:
        Compiled LangGraph workflow.
    """
    # Use provided functions or fall back to defaults
    summarize_email_fn = summarize_email or default_summarize_email
    check_email_fn = check_email_attention or default_check_email_attention
    create_jira_fn = create_jira_ticket or default_create_jira_ticket
    log_no_attention_fn = log_no_attention_needed or default_log_no_attention_needed

    # Define the graph
    workflow = StateGraph(EmailState)

    # Add nodes
    workflow.add_node("summarize_email", summarize_email_fn)
    workflow.add_node("check_email_attention", check_email_fn)
    workflow.add_node("create_jira_ticket", create_jira_fn)
    workflow.add_node("log_no_attention_needed", log_no_attention_fn)

    # Set entry point
    workflow.set_entry_point("summarize_email")

    # Add edge from summarize_email to check_email_attention
    workflow.add_edge("summarize_email", "check_email_attention")

    # Add conditional edge based on attention check result
    workflow.add_conditional_edges(
        "check_email_attention",
        lambda state: "create_jira_ticket" if state["requires_attention"] else "log_no_attention_needed",
        {
            "create_jira_ticket": "create_jira_ticket",
            "log_no_attention_needed": "log_no_attention_needed",
        },
    )

    # Both paths lead to END
    workflow.add_edge("create_jira_ticket", END)
    workflow.add_edge("log_no_attention_needed", END)

    # Compile and return the graph
    return workflow.compile()


# Default compiled graph for production use
graph = create_graph()
