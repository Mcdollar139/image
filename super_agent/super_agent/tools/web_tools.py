"""Web search + fetch MCP server.

`web_search` uses DuckDuckGo (no API key required).
`web_fetch` fetches a URL and returns cleaned text via BeautifulSoup.
"""

from __future__ import annotations

import httpx
from bs4 import BeautifulSoup
from claude_agent_sdk import create_sdk_mcp_server, tool


@tool(
    "web_search",
    "Search the web via DuckDuckGo. Returns up to `max_results` (default 5) titled snippets with URLs.",
    {"query": str, "max_results": int},
)
async def web_search(args: dict) -> dict:
    from duckduckgo_search import DDGS  # lazy import; heavy dep

    query = args["query"]
    max_results = int(args.get("max_results") or 5)
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append(
                f"- **{r.get('title', '')}**\n  {r.get('href', '')}\n  {r.get('body', '')}"
            )
    text = "\n\n".join(results) if results else "No results."
    return {"content": [{"type": "text", "text": text}]}


@tool(
    "web_fetch",
    "Fetch a URL and return its readable text (HTML stripped, scripts removed). Truncates to ~8000 chars.",
    {"url": str},
)
async def web_fetch(args: dict) -> dict:
    url = args["url"]
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=20.0,
        headers={"User-Agent": "super-agent/0.1 (+https://example.local)"},
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        ctype = resp.headers.get("content-type", "")
        body = resp.text

    if "html" in ctype.lower():
        soup = BeautifulSoup(body, "html.parser")
        for tag in soup(["script", "style", "noscript", "iframe"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
    else:
        text = body

    if len(text) > 8000:
        text = text[:8000] + "\n\n…(truncated)"
    return {"content": [{"type": "text", "text": f"URL: {url}\n\n{text}"}]}


web_server = create_sdk_mcp_server(
    name="web",
    version="1.0.0",
    tools=[web_search, web_fetch],
)
