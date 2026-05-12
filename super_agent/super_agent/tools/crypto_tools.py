"""Crypto / on-chain MCP server.

Tools:
  - coingecko_price          : current price + market cap + 24h change
  - coingecko_search         : resolve coin name → coingecko id
  - defillama_protocol       : protocol TVL, chains, category
  - defillama_chains         : top chains by TVL
  - etherscan_balance        : ETH balance for an address
  - etherscan_token_balance  : ERC20 token balance
  - solscan_account          : Solana account summary
  - binance_ohlcv            : Binance OHLCV K-lines (backtest fuel)

Public endpoints by default. ETHERSCAN_API_KEY / SOLSCAN_API_KEY recommended
for higher rate limits.
"""

from __future__ import annotations

import os

import httpx
from claude_agent_sdk import create_sdk_mcp_server, tool

_TIMEOUT = httpx.Timeout(20.0, connect=5.0)
_UA = {"User-Agent": "super-agent/0.2"}


async def _get(url: str, params: dict | None = None, headers: dict | None = None) -> dict | list:
    h = {**_UA, **(headers or {})}
    async with httpx.AsyncClient(timeout=_TIMEOUT, headers=h) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        return r.json()


def _text(payload: str) -> dict:
    return {"content": [{"type": "text", "text": payload}]}


# ─── CoinGecko ────────────────────────────────────────────────────────────────

@tool(
    "coingecko_price",
    "Get current USD price, market cap, 24h change, and 7d change for a coin. "
    "`coin_id` is the CoinGecko id (e.g. 'bitcoin', 'ethereum', 'solana'). "
    "Use `coingecko_search` first if you only have a ticker or name.",
    {"coin_id": str},
)
async def coingecko_price(args: dict) -> dict:
    coin_id = args["coin_id"].lower()
    data = await _get(
        f"https://api.coingecko.com/api/v3/coins/{coin_id}",
        params={
            "localization": "false",
            "tickers": "false",
            "community_data": "false",
            "developer_data": "false",
        },
    )
    if "error" in data:
        return _text(f"CoinGecko error: {data['error']}")
    md = data.get("market_data", {})
    price = md.get("current_price", {}).get("usd")
    mc = md.get("market_cap", {}).get("usd")
    ch24 = md.get("price_change_percentage_24h")
    ch7 = md.get("price_change_percentage_7d")
    ath = md.get("ath", {}).get("usd")
    ath_dt = md.get("ath_date", {}).get("usd")
    lines = [f"**{data.get('name')} ({data.get('symbol', '').upper()})**"]
    if price is not None:
        lines.append(f"- Price: ${price:,.6g}")
    if mc is not None:
        lines.append(f"- Market cap: ${mc:,.0f}")
    if ch24 is not None:
        lines.append(f"- 24h: {ch24:+.2f}%")
    if ch7 is not None:
        lines.append(f"- 7d:  {ch7:+.2f}%")
    if ath is not None:
        lines.append(f"- ATH: ${ath:,.6g} ({ath_dt})")
    return _text("\n".join(lines))


@tool(
    "coingecko_search",
    "Search CoinGecko by name/ticker. Returns top 5 matching coin IDs.",
    {"query": str},
)
async def coingecko_search(args: dict) -> dict:
    data = await _get(
        "https://api.coingecko.com/api/v3/search",
        params={"query": args["query"]},
    )
    coins = (data.get("coins") or [])[:5]
    if not coins:
        return _text(f"No coins found for '{args['query']}'.")
    lines = [
        f"- `{c['id']}` — {c['name']} ({c['symbol'].upper()}), rank {c.get('market_cap_rank')}"
        for c in coins
    ]
    return _text("\n".join(lines))


# ─── DefiLlama ────────────────────────────────────────────────────────────────

@tool(
    "defillama_protocol",
    "Get TVL, chains, category, and 1d/7d/30d TVL change for a DeFi protocol. "
    "`slug` is the DefiLlama slug (e.g. 'aave', 'lido', 'uniswap').",
    {"slug": str},
)
async def defillama_protocol(args: dict) -> dict:
    slug = args["slug"].lower()
    data = await _get(f"https://api.llama.fi/protocol/{slug}")
    if "message" in data and not data.get("name"):
        return _text(f"DefiLlama error: {data['message']}")
    tvl = data.get("currentChainTvls", {})
    total_tvl = sum(v for v in tvl.values() if isinstance(v, (int, float)))
    ch1d = data.get("change_1d")
    ch7d = data.get("change_7d")
    ch30d = data.get("change_30d")
    lines = [
        f"**{data.get('name')}** ({data.get('category')})",
        f"- TVL: ${total_tvl:,.0f}",
        f"- Chains: {', '.join(list(tvl.keys())[:8])}",
    ]
    if ch1d is not None:
        lines.append(f"- 1d: {ch1d:+.2f}%")
    if ch7d is not None:
        lines.append(f"- 7d: {ch7d:+.2f}%")
    if ch30d is not None:
        lines.append(f"- 30d: {ch30d:+.2f}%")
    if data.get("url"):
        lines.append(f"- URL: {data['url']}")
    if data.get("twitter"):
        lines.append(f"- Twitter: @{data['twitter']}")
    return _text("\n".join(lines))


@tool(
    "defillama_chains",
    "Top chains by TVL. Returns top `limit` (default 15) chains with their current TVL.",
    {"limit": int},
)
async def defillama_chains(args: dict) -> dict:
    limit = int(args.get("limit") or 15)
    data = await _get("https://api.llama.fi/v2/chains")
    rows = sorted(data, key=lambda x: x.get("tvl", 0) or 0, reverse=True)[:limit]
    lines = ["| # | Chain | TVL | Token |", "|---|---|---|---|"]
    for i, c in enumerate(rows, 1):
        lines.append(f"| {i} | {c.get('name')} | ${c.get('tvl', 0):,.0f} | {c.get('tokenSymbol') or '-'} |")
    return _text("\n".join(lines))


# ─── Etherscan ────────────────────────────────────────────────────────────────

def _etherscan_key() -> str:
    return os.environ.get("ETHERSCAN_API_KEY", "")


@tool(
    "etherscan_balance",
    "Get ETH balance (in ether) for an Ethereum address.",
    {"address": str},
)
async def etherscan_balance(args: dict) -> dict:
    data = await _get(
        "https://api.etherscan.io/api",
        params={
            "module": "account",
            "action": "balance",
            "address": args["address"],
            "tag": "latest",
            "apikey": _etherscan_key(),
        },
    )
    if data.get("status") != "1":
        return _text(f"Etherscan error: {data.get('message')} — {data.get('result')}")
    wei = int(data["result"])
    return _text(f"{args['address']}: {wei / 1e18:.6f} ETH")


@tool(
    "etherscan_token_balance",
    "Get ERC20 token balance for an address. `contract` = token contract address.",
    {"address": str, "contract": str},
)
async def etherscan_token_balance(args: dict) -> dict:
    data = await _get(
        "https://api.etherscan.io/api",
        params={
            "module": "account",
            "action": "tokenbalance",
            "contractaddress": args["contract"],
            "address": args["address"],
            "tag": "latest",
            "apikey": _etherscan_key(),
        },
    )
    if data.get("status") != "1":
        return _text(f"Etherscan error: {data.get('message')} — {data.get('result')}")
    return _text(f"{args['address']} / token {args['contract']}: raw balance = {data['result']}")


# ─── Solscan ──────────────────────────────────────────────────────────────────

@tool(
    "solscan_account",
    "Get Solana account summary (SOL balance + token holdings count).",
    {"address": str},
)
async def solscan_account(args: dict) -> dict:
    key = os.environ.get("SOLSCAN_API_KEY", "")
    headers = {"token": key} if key else {}
    try:
        data = await _get(
            f"https://public-api.solscan.io/account/{args['address']}",
            headers=headers,
        )
    except httpx.HTTPStatusError as e:
        return _text(f"Solscan error: {e.response.status_code}")
    lamports = data.get("lamports", 0)
    sol = lamports / 1e9 if isinstance(lamports, (int, float)) else 0
    return _text(
        f"{args['address']}\n"
        f"- SOL balance: {sol:.4f}\n"
        f"- Type: {data.get('type')}\n"
        f"- Executable: {data.get('executable')}\n"
        f"- Rent epoch: {data.get('rentEpoch')}"
    )


# ─── Binance OHLCV ────────────────────────────────────────────────────────────

_VALID_TF = {"1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"}


@tool(
    "binance_ohlcv",
    "Fetch Binance spot OHLCV (K-lines). `symbol` = e.g. 'BTCUSDT'. "
    "`timeframe` ∈ {1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w}. `limit` ≤ 1000.",
    {"symbol": str, "timeframe": str, "limit": int},
)
async def binance_ohlcv(args: dict) -> dict:
    symbol = args["symbol"].upper()
    tf = args["timeframe"]
    if tf not in _VALID_TF:
        return _text(f"Invalid timeframe '{tf}'. Use one of: {', '.join(sorted(_VALID_TF))}.")
    limit = max(1, min(int(args.get("limit") or 100), 1000))
    data = await _get(
        "https://api.binance.com/api/v3/klines",
        params={"symbol": symbol, "interval": tf, "limit": limit},
    )
    if isinstance(data, dict) and data.get("code"):
        return _text(f"Binance error: {data.get('msg')}")
    if not isinstance(data, list) or not data:
        return _text("No data returned.")
    # Summary stats — agent rarely needs every candle.
    closes = [float(k[4]) for k in data]
    highs = [float(k[2]) for k in data]
    lows = [float(k[3]) for k in data]
    vols = [float(k[5]) for k in data]
    first = closes[0]
    last = closes[-1]
    change = (last - first) / first * 100 if first else 0
    lines = [
        f"**{symbol}** {tf} × {len(data)} bars",
        f"- First close: {first:.6g}",
        f"- Last close:  {last:.6g}  ({change:+.2f}%)",
        f"- High:        {max(highs):.6g}",
        f"- Low:         {min(lows):.6g}",
        f"- Avg vol:     {sum(vols) / len(vols):,.2f}",
        "",
        "Last 5 bars (open, high, low, close, vol):",
    ]
    for k in data[-5:]:
        lines.append(f"- {k[0]}: O={float(k[1]):.6g} H={float(k[2]):.6g} L={float(k[3]):.6g} C={float(k[4]):.6g} V={float(k[5]):,.2f}")
    return _text("\n".join(lines))


crypto_server = create_sdk_mcp_server(
    name="crypto",
    version="1.0.0",
    tools=[
        coingecko_price,
        coingecko_search,
        defillama_protocol,
        defillama_chains,
        etherscan_balance,
        etherscan_token_balance,
        solscan_account,
        binance_ohlcv,
    ],
)
