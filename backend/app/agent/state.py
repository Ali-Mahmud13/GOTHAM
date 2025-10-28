"""Agent state definition."""

from typing import TypedDict


class AgentState(TypedDict):
    message: str
    response: str
