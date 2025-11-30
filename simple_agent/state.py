from typing import TypedDict, Optional


class EmailState(TypedDict):
    # Input
    email_body: str
    email_subject: str
    email_to: str
    # Output
    requires_attention: Optional[bool]
    jira_ticket_id: Optional[str]
