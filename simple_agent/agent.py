from langgraph.graph import StateGraph, END
from simple_agent.nodes import (
    check_email_attention,
    create_jira_ticket,
    log_no_attention_needed,
)
from simple_agent.state import EmailState


# Define the graph
workflow = StateGraph(EmailState)

# Add nodes
workflow.add_node("check_email_attention", check_email_attention)
workflow.add_node("create_jira_ticket", create_jira_ticket)
workflow.add_node("log_no_attention_needed", log_no_attention_needed)

# Set entry point
workflow.set_entry_point("check_email_attention")

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

# Compile the graph
graph = workflow.compile()
