# Super-Agent

一个用 **Claude Agent SDK** 搭建的"超级智能体"骨架，具备：

- 🛠 **代码生成与执行**（Read / Write / Edit / Bash 内置工具）
- 🌐 **联网能力**：自定义 MCP 工具 `web_search`（DuckDuckGo）+ `web_fetch`（HTTP + 文本提取）
- 🧠 **长期记忆**：基于文件的 KV 存储 + Markdown 笔记本（自定义 MCP 服务器 `memory`）
- 👥 **多智能体协作**：4 个内置 subagent —— `planner`、`researcher`、`coder`、`critic`，通过 `Task` 工具协同

## 安装

```bash
cd super_agent
pip install -e .
cp .env.example .env  # 然后填入 ANTHROPIC_API_KEY
```

> 依赖 Anthropic 官方 [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python)，
> 该 SDK 在底层会调用 Claude Code CLI，请先安装：
> ```bash
> npm install -g @anthropic-ai/claude-code
> ```

## 使用

**交互式对话：**
```bash
super-agent
```

**一次性提问：**
```bash
super-agent "帮我研究一下 2026 年最流行的开源 LLM 框架，输出对比表格"
```

**从文件读取 prompt：**
```bash
super-agent -f task.md
```

## 架构

```
你的请求
    │
    ▼
┌──────────────────┐
│   Super-Agent    │  ← 主智能体（claude-opus-4-7）
│   (main loop)    │
└────────┬─────────┘
         │
         ├─ 内置工具：Read / Write / Edit / Bash / Grep / Glob
         │
         ├─ MCP "memory"：memory_remember / recall / note_save / note_search …
         │
         ├─ MCP "web"：web_search / web_fetch
         │
         └─ Task 工具委派给 subagent：
              ├─ planner（分解目标 → 待办清单）
              ├─ researcher（联网调研）
              ├─ coder（写代码、跑代码）
              └─ critic（评审最终产出）
```

## 工作流示例

让超级智能体写一个项目：

```
you> 帮我写一个用 FastAPI 实现的 URL 短链服务，包含测试
```

它会自动：
1. 调用 `planner` 拆解出 5–8 步骤
2. `researcher` 查最新 FastAPI 最佳实践（可选）
3. `coder` 创建文件 → 写代码 → 跑 pytest
4. `critic` 审查代码与测试覆盖
5. 把项目摘要写入长期记忆（`note_save`）

下次启动时，它能通过 `memory_recall` 或 `note_search` 回忆起这些信息。

## 文件结构

```
super_agent/
├── pyproject.toml
├── README.md
├── .env.example
├── memory_store/            # 持久化记忆（自动创建）
└── super_agent/
    ├── main.py              # 入口 / REPL
    ├── memory.py            # 文件型记忆存储
    ├── tools/
    │   ├── memory_tools.py  # MCP server：长期记忆工具
    │   └── web_tools.py     # MCP server：搜索 + 抓取
    └── subagents/
        └── __init__.py      # planner / researcher / coder / critic
```

## 扩展

- **添加新的 subagent**：编辑 `super_agent/subagents/__init__.py`，再写一个 `AgentDefinition`，加入 `AGENTS` 字典即可。
- **添加新的 MCP 工具**：参考 `tools/memory_tools.py` 用 `@tool` 装饰函数，挂到 `create_sdk_mcp_server`。
- **替换模型**：设置环境变量 `SUPER_AGENT_MODEL=claude-sonnet-4-6` 或在调用时传 `model=`。
- **收紧权限**：在 `build_options()` 里改 `permission_mode` 为 `"default"`（每次工具调用前询问）或 `"plan"`（只规划，不执行）。

## 注意事项

- 默认 `permission_mode="acceptEdits"` —— 自动接受文件编辑。生产环境建议改为 `"default"`。
- `web_search` 用 DuckDuckGo 无需 API key，但有速率限制。生产可换 SerpAPI / Tavily。
- 记忆存储是单进程文件，多实例并发写有竞态风险。如需扩展请改成 SQLite 或 Redis。
