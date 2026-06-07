"""Shared LLM tool-use loop for all persona-based agents."""
import json
from datetime import datetime, timezone
from typing import Any, cast

import anthropic


def run_agent(
    ticker: str,
    key_figures: dict[str, Any],
    system_prompt: str,
    tools: list[Any],
    tool_dispatch: dict[str, Any],
    agent_name: str,
) -> dict[str, Any]:
    """Run one agent's tool-use loop and return the standard agent output dict."""
    client = anthropic.Anthropic()
    messages: list[Any] = [
        {
            "role": "user",
            "content": (
                f"Analyze {ticker}.\n\n"
                f"Key financial figures:\n{json.dumps(key_figures, indent=2)}"
            ),
        }
    ]
    tool_results_log: dict[str, Any] = {}

    for _ in range(10):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=cast(Any, tools),
            messages=cast(Any, messages),
        )

        if response.stop_reason == "end_turn":
            break

        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        if not tool_use_blocks:
            break

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for tc in tool_use_blocks:
            inp = cast(dict[str, Any], tc.input)

            if tc.name == "submit_analysis":
                return {
                    "agent":     agent_name,
                    "ticker":    ticker,
                    "signal":    inp["signal"],
                    "score":     float(inp["score"]),
                    "summary":   inp["summary"],
                    "details":   tool_results_log,
                    "flags":     inp["flags"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            fn = tool_dispatch.get(tc.name)
            if fn:
                try:
                    result = fn(**inp)
                except Exception as exc:
                    result = {"error": str(exc)}
                tool_results_log[tc.name] = result
                content = json.dumps(result)
            else:
                content = f"Unknown tool: {tc.name}"

            tool_results.append({
                "type":        "tool_result",
                "tool_use_id": tc.id,
                "content":     content,
            })

        messages.append({"role": "user", "content": tool_results})

    return {
        "agent":     agent_name,
        "ticker":    ticker,
        "signal":    "neutral",
        "score":     5.0,
        "summary":   "Analysis incomplete — agent did not submit a final verdict.",
        "details":   tool_results_log,
        "flags":     ["Agent loop ended without submit_analysis"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
