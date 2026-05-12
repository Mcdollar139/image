# Super-Agent

一个用 **Claude Agent SDK** 搭建的"超级智能体"，方法论按视频《打造你的 AI 超级智能体》的 AIM 框架 + 导航员模式实现，底层针对 **trader / web3 / AI 板块** 这种 use case 做了完整工具栈集成。

## 现在能直接干什么

```bash
# 1) 第一次：建立你的个人画像（已预填了你的资料）
#    若以后想覆盖：super-agent --onboard

# 2) 日常对话（自动加载 background.md）
super-agent

# 3) 直接跑预置 playbook
super-agent --playbook crypto-daily-brief ""
super-agent --playbook strategy-research "刚看到一个 funding rate arb 的帖子..."
super-agent --playbook web3-due-diligence "https://app.aave.com"
super-agent --playbook investor-update "本月 +18.4%, max DD 6.2%, AUM 2.3M"
super-agent --playbook task-handoff "帮我做一个 dashboard 显示所有钱包余额"
super-agent --playbook ai-tool-scan "交易日志自动化"
super-agent --playbook strategy-postmortem "[贴 trade log]"
super-agent --playbook restaurant-ops-report "[贴销售数据]"

super-agent --list-playbooks
```

## 8 个预置 Playbook

| Slug | 干什么 | 主力 subagent |
|---|---|---|
| `strategy-research` | 把策略 idea → 实施 brief | `trader` |
| `strategy-postmortem` | 业绩复盘（内部版 + LP 版） | `trader` + `marketer` |
| `web3-due-diligence` | 项目尽调 + ape/pass 判断 | `dd` |
| `crypto-daily-brief` | 每日市场 + AI 板块情报 | `analyst` |
| `investor-update` | LP / 投资人沟通 | `marketer` |
| `task-handoff` | 派活给技术团队 | `pm` |
| `ai-tool-scan` | 工具栈调研 | `researcher` |
| `restaurant-ops-report` | 餐厅运营分析 | `analyst` |

## 11 个 Subagent（按职责）

**方法论类**：`interviewer` / `planner` / `researcher` / `coder` / `critic` / `crystallizer`
**业务类**：`trader` / `analyst` / `dd` / `pm` / `marketer`

模型分配（混合策略，省 70%+ 成本）：

| Subagent | Model | 理由 |
|---|---|---|
| `trader` / `dd` / `coder` | opus-4-7 | 高 stakes / 复杂分析 |
| 其他 | sonnet-4-6 | 量大 / 结构化 / 速度优先 |

可用 `SUPER_AGENT_SUBAGENT_MODEL_SONNET` / `_HAIKU` 环境变量调。

## 4 个 MCP Server

| Server | 工具 |
|---|---|
| **memory** | `memory_remember` / `recall` / `list_keys` / `forget`；`note_save` / `list` / `read` / `search` |
| **web** | `web_search`（Tavily 优先，DDG 回退）/ `web_fetch`（HTML → 文本）|
| **crypto** | `coingecko_price` / `search`；`defillama_protocol` / `chains`；`etherscan_balance` / `token_balance`；`solscan_account`；`binance_ohlcv` |

加上内置 Claude Agent SDK：`Read` / `Write` / `Edit` / `Bash` / `Glob` / `Grep` / `Task`。

## 安装

```bash
cd super_agent
pip install -e .                       # 基础
pip install -e ".[trading]"            # 额外 tavily-python（可选，纯 REST 也能工作）

# Claude Agent SDK 底层依赖 Claude Code CLI
npm install -g @anthropic-ai/claude-code

cp .env.example .env
# 编辑 .env：
#   - ANTHROPIC_API_KEY（必填）
#   - TAVILY_API_KEY（强烈推荐，免费 1000/月，对市场情报质量影响巨大）
#   - ETHERSCAN_API_KEY（免费，提速链上查询）
#   - SOLSCAN_API_KEY（免费，Solana 查询）
```

## 视频方法论 → 项目实现 映射

| 视频里的步骤 | 实现 |
|---|---|
| 1. 背景提示词 | `--onboard` → `interviewer` → `background.md` 自动加载 |
| 2. AIM 框架 | 写进主 system prompt，每个任务前内部对齐 |
| 3. 导航员模式 | 复杂任务先反问 3–5 个关键问题再动手 |
| 4. 固化为系统提示词 | `crystallizer` → `playbook-<slug>.md`；`--playbook <slug>` 一键复用 |
| 灵魂（价值观/想象力/关怀）| 写进 system prompt 基线，具体偏好以 `background.md` 覆盖 |

## 文件结构

```
super_agent/
├── pyproject.toml
├── .env.example
├── README.md
├── memory_store/notes/
│   ├── background.md                  # 你的个人画像
│   ├── playbook-strategy-research.md
│   ├── playbook-strategy-postmortem.md
│   ├── playbook-web3-due-diligence.md
│   ├── playbook-crypto-daily-brief.md
│   ├── playbook-investor-update.md
│   ├── playbook-task-handoff.md
│   ├── playbook-ai-tool-scan.md
│   └── playbook-restaurant-ops-report.md
└── super_agent/
    ├── main.py                        # CLI
    ├── memory.py                      # 文件型记忆存储
    ├── prompts/__init__.py            # AIM + Navigator + Soul system prompt
    ├── tools/
    │   ├── memory_tools.py            # MCP server: memory
    │   ├── web_tools.py               # MCP server: web (Tavily / DDG)
    │   └── crypto_tools.py            # MCP server: crypto / on-chain
    ├── subagents/__init__.py          # 11 个 AgentDefinition
    └── playbooks/                     # 通用 prompt 模板（AIM / 导航员 / 固化）
```

## 注意事项

- `permission_mode="acceptEdits"`：自动接受文件编辑。生产改 `"default"`。
- 涉及钱的判断必须用 crypto MCP 拉真实数据，agent 已被指示不准凭空生成价格 / TVL。
- DDG 速率限制比较紧；强烈建议配 Tavily。
- 单进程记忆，多实例并发写有竞态。规模化改 SQLite / Redis。
- 没装 `tavily-python` 但设了 `TAVILY_API_KEY` 也能跑——会通过 httpx 直接调 Tavily REST。
