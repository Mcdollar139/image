"""Super Agent — interactive entry point.

Run with: `python -m super_agent.main` or `super-agent` (after install).
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    ThinkingBlock,
    ToolUseBlock,
)

from .subagents import AGENTS
from .tools import memory_server, web_server

SYSTEM_PROMPT = """You are Super-Agent, a highly capable autonomous assistant.

Capabilities you have:
- **Code**: read/write/edit files, run bash commands.
- **Web**: search the web (mcp__web__web_search) and fetch URLs (mcp__web__web_fetch).
- **Memory**: persistent key/value (mcp__memory__memory_*) and markdown notes (mcp__memory__note_*).
- **Delegation**: spawn subagents — `planner`, `researcher`, `coder`, `critic` — via the Task tool.

Operating principles:
1. For any non-trivial task, ask the `planner` subagent first to produce a checklist.
2. Delegate web research to the `researcher` subagent; do not browse from the main loop.
3. Delegate code authorship to the `coder` subagent for any task larger than a one-liner.
4. Before finalizing a substantial result, ask the `critic` subagent to review it.
5. Use memory tools to persist anything the user might want recalled later (preferences,
   project facts, prior findings). Check memory at the start of new sessions.
6. Be terse. Show your work via tool calls, not narration."""


def build_options(*, model: str | None = None, cwd: str | None = None) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        model=model or os.environ.get("SUPER_AGENT_MODEL", "claude-opus-4-7"),
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={
            "memory": memory_server,
            "web": web_server,
        },
        agents=AGENTS,
        # Allow all built-in + custom MCP tools. Tighten this for production.
        allowed_tools=[
            "Read",
            "Write",
            "Edit",
            "Bash",
            "Glob",
            "Grep",
            "Task",
            "mcp__memory__memory_remember",
            "mcp__memory__memory_recall",
            "mcp__memory__memory_list_keys",
            "mcp__memory__memory_forget",
            "mcp__memory__note_save",
            "mcp__memory__note_list",
            "mcp__memory__note_read",
            "mcp__memory__note_search",
            "mcp__web__web_search",
            "mcp__web__web_fetch",
        ],
        permission_mode="acceptEdits",
        cwd=cwd or os.getcwd(),
    )


async def _render_stream(client: ClaudeSDKClient) -> None:
    """Pretty-print streamed assistant messages."""
    async for msg in client.receive_response():
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    print(block.text, end="", flush=True)
                elif isinstance(block, ThinkingBlock):
                    # Skip thinking by default; uncomment to surface it.
                    pass
                elif isinstance(block, ToolUseBlock):
                    print(f"\n  [tool] {block.name}", flush=True)
        elif isinstance(msg, ResultMessage):
            print(
                f"\n\n— done (turns: {msg.num_turns}, "
                f"cost: ${msg.total_cost_usd:.4f})"
                if msg.total_cost_usd is not None
                else f"\n\n— done (turns: {msg.num_turns})"
            )


async def chat_loop(*, model: str | None = None) -> None:
    """REPL: each user line is sent as a follow-up turn in the same session."""
    options = build_options(model=model)
    print("Super-Agent ready. Type a request, or 'exit' to quit.\n")

    async with ClaudeSDKClient(options=options) as client:
        while True:
            try:
                user_input = input("you> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit", ":q"}:
                break

            await client.query(user_input)
            print("agent> ", end="", flush=True)
            await _render_stream(client)


async def one_shot(prompt: str, *, model: str | None = None) -> None:
    options = build_options(model=model)
    async with ClaudeSDKClient(options=options) as client:
        await client.query(prompt)
        await _render_stream(client)


def cli() -> None:
    args = sys.argv[1:]
    if args and args[0] in {"-h", "--help"}:
        print(
            "Usage:\n"
            "  super-agent                 # interactive chat\n"
            "  super-agent <prompt...>     # one-shot prompt\n"
            "  super-agent -f <file>       # one-shot prompt from a file\n"
        )
        return

    if not args:
        asyncio.run(chat_loop())
        return

    if args[0] == "-f" and len(args) >= 2:
        prompt = Path(args[1]).read_text(encoding="utf-8")
    else:
        prompt = " ".join(args)
    asyncio.run(one_shot(prompt))


if __name__ == "__main__":
    cli()
