from langgraph.graph import StateGraph, END
from simple_agent.nodes import check_email_attention
from simple_agent.state import EmailState


# Define the graph
workflow = StateGraph(EmailState)

# Add node
workflow.add_node("check_email_attention", check_email_attention)

# Set entry point
workflow.set_entry_point("check_email_attention")

# Go straight to END after checking
workflow.add_edge("check_email_attention", END)

# Compile the graph
graph = workflow.compile()
