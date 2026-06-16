"""Shared agent strategy — binds a name + system prompt to the common LLM loop."""
from dataclasses import dataclass
from typing import Any

from tools.llm_agent import run_agent
from tools.metrics import TOOL_DISPATCH
from tools.tool_schemas import ALL_TOOLS


@dataclass(frozen=True)
class AgentStrategy:
    """
    All agents run the same tool-use loop (run_agent). Create one instance per
    agent file and expose its .analyze as the module-level function so callers
    don't need to know about this class.
    """

    name: str
    system_prompt: str

    def analyze(self, ticker: str, key_figures: dict[str, Any]) -> dict[str, Any]:
        """Run this agent's LLM analysis and return the standard agent output dict."""
        return run_agent(
            ticker=ticker,
            key_figures=key_figures,
            system_prompt=self.system_prompt,
            tools=ALL_TOOLS,
            tool_dispatch=TOOL_DISPATCH,
            agent_name=self.name,
        )
