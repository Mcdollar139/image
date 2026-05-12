"""In-process MCP server exposing the long-term memory store to the agent."""

from __future__ import annotations

from claude_agent_sdk import create_sdk_mcp_server, tool

from ..memory import MemoryStore

_store = MemoryStore()


@tool(
    "memory_remember",
    "Save a key/value note to long-term memory. Overwrites any existing value at `key`.",
    {"key": str, "value": str},
)
async def memory_remember(args: dict) -> dict:
    _store.remember(args["key"], args["value"])
    return {
        "content": [
            {"type": "text", "text": f"Stored '{args['key']}' in long-term memory."}
        ]
    }


@tool(
    "memory_recall",
    "Read the value previously stored under `key`. Returns 'not found' if missing.",
    {"key": str},
)
async def memory_recall(args: dict) -> dict:
    value = _store.recall(args["key"])
    text = value if value is not None else f"No memory found for key '{args['key']}'."
    return {"content": [{"type": "text", "text": text}]}


@tool(
    "memory_list_keys",
    "List all keys currently stored in long-term memory.",
    {},
)
async def memory_list_keys(args: dict) -> dict:
    keys = _store.list_keys()
    text = "\n".join(f"- {k}" for k in keys) if keys else "(empty)"
    return {"content": [{"type": "text", "text": text}]}


@tool(
    "memory_forget",
    "Delete the memory entry stored under `key`.",
    {"key": str},
)
async def memory_forget(args: dict) -> dict:
    removed = _store.forget(args["key"])
    text = (
        f"Deleted key '{args['key']}'."
        if removed
        else f"No memory found for key '{args['key']}'."
    )
    return {"content": [{"type": "text", "text": text}]}


@tool(
    "note_save",
    "Save a markdown note with a title. Use this for longer findings, research summaries, or working artifacts.",
    {"title": str, "content": str},
)
async def note_save(args: dict) -> dict:
    rel = _store.save_note(args["title"], args["content"])
    return {"content": [{"type": "text", "text": f"Saved note: {rel}"}]}


@tool(
    "note_list",
    "List all saved markdown notes by filename.",
    {},
)
async def note_list(args: dict) -> dict:
    notes = _store.list_notes()
    text = "\n".join(f"- {n}" for n in notes) if notes else "(no notes)"
    return {"content": [{"type": "text", "text": text}]}


@tool(
    "note_read",
    "Read a saved markdown note by filename (as listed by `note_list`).",
    {"filename": str},
)
async def note_read(args: dict) -> dict:
    body = _store.read_note(args["filename"])
    text = body if body is not None else f"Note '{args['filename']}' not found."
    return {"content": [{"type": "text", "text": text}]}


@tool(
    "note_search",
    "Search saved markdown notes for a substring (case-insensitive). Returns up to 5 snippets.",
    {"query": str},
)
async def note_search(args: dict) -> dict:
    hits = _store.search_notes(args["query"])
    if not hits:
        text = f"No notes contain '{args['query']}'."
    else:
        text = "\n\n".join(f"## {fname}\n{snippet}" for fname, snippet in hits)
    return {"content": [{"type": "text", "text": text}]}


memory_server = create_sdk_mcp_server(
    name="memory",
    version="1.0.0",
    tools=[
        memory_remember,
        memory_recall,
        memory_list_keys,
        memory_forget,
        note_save,
        note_list,
        note_read,
        note_search,
    ],
)
