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

from .memory import MemoryStore
from .prompts import build_system_prompt
from .subagents import AGENTS
from .tools import crypto_server, memory_server, web_server


def build_options(
    *,
    model: str | None = None,
    cwd: str | None = None,
    system_prompt: str | None = None,
) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        model=model or os.environ.get("SUPER_AGENT_MODEL", "claude-opus-4-7"),
        system_prompt=system_prompt or build_system_prompt(),
        mcp_servers={
            "memory": memory_server,
            "web": web_server,
            "crypto": crypto_server,
        },
        agents=AGENTS,
        allowed_tools=[
            "Read",
            "Write",
            "Edit",
            "Bash",
            "Glob",
            "Grep",
            "Task",
            # memory
            "mcp__memory__memory_remember",
            "mcp__memory__memory_recall",
            "mcp__memory__memory_list_keys",
            "mcp__memory__memory_forget",
            "mcp__memory__note_save",
            "mcp__memory__note_list",
            "mcp__memory__note_read",
            "mcp__memory__note_search",
            # web
            "mcp__web__web_search",
            "mcp__web__web_fetch",
            # crypto / on-chain
            "mcp__crypto__coingecko_price",
            "mcp__crypto__coingecko_search",
            "mcp__crypto__defillama_protocol",
            "mcp__crypto__defillama_chains",
            "mcp__crypto__etherscan_balance",
            "mcp__crypto__etherscan_token_balance",
            "mcp__crypto__solscan_account",
            "mcp__crypto__binance_ohlcv",
        ],
        permission_mode="acceptEdits",
        cwd=cwd or os.getcwd(),
    )


ONBOARD_KICKOFF = (
    "请委派给 `interviewer` subagent，让它通过采访的方式建立我的 `background.md` "
    "（个人使用说明书）。完成后保存到长期记忆。"
)


async def onboard() -> None:
    """Run the interviewer subagent to build background.md."""
    options = build_options()
    print("启动 onboarding —— interviewer 会向你提问，建立专属背景档案。\n")
    async with ClaudeSDKClient(options=options) as client:
        await client.query(ONBOARD_KICKOFF)
        await _render_stream(client)
        # Subsequent turns let the user answer follow-up questions.
        while True:
            try:
                user_input = input("\nyou> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit", ":q", "done"}:
                break
            await client.query(user_input)
            print("agent> ", end="", flush=True)
            await _render_stream(client)


async def run_playbook(slug: str, user_input: str) -> None:
    """Run a saved playbook (system prompt) with raw user input."""
    store = MemoryStore()
    body = store.read_note(f"playbook-{slug}.md")
    if body is None:
        print(f"未找到 playbook 'playbook-{slug}.md'。可用列表：")
        for name in store.list_notes():
            if name.startswith("playbook-"):
                print(f"  - {name[len('playbook-'):-len('.md')]}")
        return
    options = build_options(system_prompt=body)
    async with ClaudeSDKClient(options=options) as client:
        await client.query(user_input)
        await _render_stream(client)


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
            "  super-agent                          # interactive chat\n"
            "  super-agent <prompt...>              # one-shot prompt\n"
            "  super-agent -f <file>                # one-shot prompt from a file\n"
            "  super-agent --onboard                # interview-driven background.md setup\n"
            "  super-agent --playbook <slug> <...>  # run a saved playbook with given input\n"
            "  super-agent --list-playbooks         # list saved playbooks\n"
        )
        return

    if not args:
        asyncio.run(chat_loop())
        return

    if args[0] == "--onboard":
        asyncio.run(onboard())
        return

    if args[0] == "--list-playbooks":
        store = MemoryStore()
        slugs = [
            n[len("playbook-"):-len(".md")]
            for n in store.list_notes()
            if n.startswith("playbook-") and n.endswith(".md")
        ]
        print("\n".join(f"- {s}" for s in slugs) if slugs else "(no playbooks)")
        return

    if args[0] == "--playbook":
        if len(args) < 3:
            print("用法: super-agent --playbook <slug> <prompt...>")
            return
        slug = args[1]
        prompt = " ".join(args[2:])
        asyncio.run(run_playbook(slug, prompt))
        return

    if args[0] == "-f" and len(args) >= 2:
        prompt = Path(args[1]).read_text(encoding="utf-8")
    else:
        prompt = " ".join(args)
    asyncio.run(one_shot(prompt))


if __name__ == "__main__":
    cli()
