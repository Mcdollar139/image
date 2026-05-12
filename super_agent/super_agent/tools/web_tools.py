"""Web search + fetch MCP server.

`web_search` prefers Tavily (set TAVILY_API_KEY for higher-quality results),
falls back to DuckDuckGo when no key is present.
`web_fetch` fetches a URL and returns cleaned text via BeautifulSoup.
"""

from __future__ import annotations

import os

import httpx
from bs4 import BeautifulSoup
from claude_agent_sdk import create_sdk_mcp_server, tool


def _has_tavily() -> bool:
    return bool(os.environ.get("TAVILY_API_KEY"))


async def _search_tavily(query: str, max_results: int) -> str:
    key = os.environ["TAVILY_API_KEY"]
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": key,
                "query": query,
                "max_results": max_results,
                "search_depth": "advanced",
                "include_answer": True,
            },
        )
        r.raise_for_status()
        data = r.json()
    parts: list[str] = []
    if data.get("answer"):
        parts.append(f"**TL;DR (Tavily):** {data['answer']}\n")
    for item in data.get("results", [])[:max_results]:
        parts.append(
            f"- **{item.get('title', '')}**\n"
            f"  {item.get('url', '')}\n"
            f"  {item.get('content', '')[:400]}"
        )
    return "\n\n".join(parts) if parts else "No results."


async def _search_ddg(query: str, max_results: int) -> str:
    from duckduckgo_search import DDGS  # lazy

    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append(
                f"- **{r.get('title', '')}**\n"
                f"  {r.get('href', '')}\n"
                f"  {r.get('body', '')}"
            )
    return "\n\n".join(results) if results else "No results."


@tool(
    "web_search",
    "Search the web. Uses Tavily if TAVILY_API_KEY is set (recommended for "
    "trading / crypto / market intel), else DuckDuckGo. Returns up to "
    "`max_results` (default 5) titled snippets with URLs.",
    {"query": str, "max_results": int},
)
async def web_search(args: dict) -> dict:
    max_results = int(args.get("max_results") or 5)
    query = args["query"]
    if _has_tavily():
        text = await _search_tavily(query, max_results)
    else:
        text = await _search_ddg(query, max_results)
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
        headers={"User-Agent": "super-agent/0.2 (+https://example.local)"},
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
    version="1.1.0",
    tools=[web_search, web_fetch],
)
