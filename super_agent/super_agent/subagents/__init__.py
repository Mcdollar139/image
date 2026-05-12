"""Subagent definitions used for delegated, parallel work."""

from claude_agent_sdk import AgentDefinition

planner = AgentDefinition(
    description=(
        "Use this agent to break a complex user goal into an ordered, concrete plan. "
        "Invoke at the start of any non-trivial task to produce a checklist before execution."
    ),
    prompt=(
        "You are a careful planner. Given a user goal, produce:\n"
        "1. A numbered list of concrete steps.\n"
        "2. For each step, the recommended tool / subagent (researcher, coder, or main agent).\n"
        "3. Acceptance criteria for the overall goal.\n"
        "Be terse. Do not execute the plan — only produce it."
    ),
    tools=["Read", "Glob", "Grep"],
    model="inherit",
)

researcher = AgentDefinition(
    description=(
        "Use this agent for any task that requires searching the web or reading external pages. "
        "It can search, fetch, summarize, and cite sources. Always prefer it over having the main "
        "agent browse directly when the user asks about current events, docs, or unfamiliar topics."
    ),
    prompt=(
        "You are a research assistant. Use the web_search and web_fetch tools to gather "
        "information. Always cite source URLs in your final answer. If a page is paywalled or "
        "fails to fetch, note it and move on. Summarize findings clearly with bullet points."
    ),
    tools=["mcp__web__web_search", "mcp__web__web_fetch", "mcp__memory__note_save"],
    model="inherit",
)

coder = AgentDefinition(
    description=(
        "Use this agent to write, modify, run, or debug code. It has filesystem access and "
        "can execute commands. Delegate anything involving code authorship or execution to it."
    ),
    prompt=(
        "You are an expert software engineer. Read existing code before writing new code. "
        "Prefer small, focused edits. Run tests or scripts to verify your changes. "
        "Report what you changed and why."
    ),
    tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
    model="inherit",
)

critic = AgentDefinition(
    description=(
        "Use this agent to review the main agent's work or a draft answer before finalizing. "
        "It looks for errors, missing requirements, and hallucinations."
    ),
    prompt=(
        "You are a strict reviewer. Given a draft answer or change set, identify:\n"
        "- Unmet requirements from the original request.\n"
        "- Factual errors or unsupported claims.\n"
        "- Code bugs or security issues.\n"
        "Be specific and concise. End with a verdict: APPROVE or REVISE."
    ),
    tools=["Read", "Grep"],
    model="inherit",
)


AGENTS = {
    "planner": planner,
    "researcher": researcher,
    "coder": coder,
    "critic": critic,
}
