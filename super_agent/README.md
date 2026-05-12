# Super-Agent

一个用 **Claude Agent SDK** 搭建的"超级智能体"骨架。底层是工具与多智能体协作，**上层是视频《打造你的 AI 超级智能体》提到的那套方法论**：背景提示词 → AIM 框架 → 导航员模式 → 系统提示词固化 → 灵魂。

## 视频方法论 → 本项目映射

| 视频里讲的 | 本项目里的实现 |
|---|---|
| 第一步：建立背景提示词（让 AI 通过采访了解你）| `super-agent --onboard` → `interviewer` subagent → 把你的"个人使用说明书"存为 `memory_store/notes/background.md`，每次启动自动加载 |
| 第二步：AIM 框架（Act / Input / Mission）| 写进主 system prompt，每个任务前内部对齐 |
| 第三步：导航员模式（让 AI 反过来提问）| 写进主 system prompt 作为**默认行为**：复杂/有歧义的任务先问 3–5 个关键问题，再动手 |
| 第四步：固化为系统提示词 | `crystallizer` subagent → 把磨合好的流程存为 `playbook-<slug>.md`，下次 `super-agent --playbook <slug>` 一键复用 |
| 灵魂：价值观 / 想象力 / 关怀 | 写进主 system prompt 作为创造性任务的基线（具体偏好由 `background.md` 覆盖）|

## 底层能力（基础设施）

- 🛠 **代码生成与执行**：Read / Write / Edit / Bash / Glob / Grep
- 🌐 **联网**：`web_search`（DuckDuckGo）+ `web_fetch`（HTTP + 正文提取）
- 🧠 **长期记忆**：KV 存储 + Markdown 笔记本，全文检索
- 👥 **多智能体协作**：6 个 subagent —— `interviewer` / `planner` / `researcher` / `coder` / `critic` / `crystallizer`

## 安装

```bash
cd super_agent
pip install -e .
cp .env.example .env  # 填入 ANTHROPIC_API_KEY

# Claude Agent SDK 底层依赖 Claude Code CLI
npm install -g @anthropic-ai/claude-code
```

## 使用流程（推荐）

### 1. 第一次启动：建立你的"个人使用说明书"

```bash
super-agent --onboard
```

`interviewer` subagent 会向你提 8–12 个问题（身份、业务、客户痛点、风格偏好、价值观、想自动化的重复任务……），然后把答案合成成 `background.md` 存进长期记忆。**之后每次启动都会自动加载**。

### 2. 日常使用：直接对话

```bash
super-agent                            # 交互式
super-agent "帮我做 XX"                 # 一次性
super-agent -f task.md                 # 从文件读 prompt
```

agent 会：
- 启动时自动读 `background.md` 了解你
- 遇到复杂任务先按 AIM 框架在内部对齐
- 不明确就**反过来问你** 3–5 个关键问题（导航员模式）
- 该联网/写代码/审查时分别委派给对应 subagent

### 3. 磨合成功后：把流程固化成 playbook

任何一次满意的对话结束后，对 agent 说一句（或直接 copy `super_agent/playbooks/crystallize-request.md` 里的提示）：

```
请委派给 crystallizer，把刚才的流程固化成 playbook，slug 叫 marketing-brief。
```

下次只要：

```bash
super-agent --playbook marketing-brief "原料：本月活动……"
```

就能复用同样的逻辑产出同等质量的结果——`background.md` + playbook 双重提示词。

```bash
super-agent --list-playbooks           # 看看有哪些
```

## 现成的 prompt 模板

`super_agent/playbooks/` 目录下有几份可直接复制粘贴的提示词：

- `aim-template.md` — 通用 AIM 任务模板（A/I/M 三段式填空）
- `navigator-kickoff.md` — 启动导航员模式
- `crystallize-request.md` — 让 agent 把当前流程固化

## 架构

```
你的请求
    │
    ▼
┌────────────────────────────────────────────────┐
│   Super-Agent (claude-opus-4-7)                │
│   system prompt = BASE + background.md         │
│                 + AIM + Navigator + Soul       │
└────────┬───────────────────────────────────────┘
         │
         ├─ 内置：Read / Write / Edit / Bash / Grep / Glob
         ├─ MCP "memory"：memory_* / note_*
         ├─ MCP "web"：web_search / web_fetch
         └─ Task → 委派给 subagent
              ├─ interviewer   （onboarding）
              ├─ planner       （拆解目标）
              ├─ researcher    （联网调研）
              ├─ coder         （写代码、跑代码）
              ├─ critic        （评审产出）
              └─ crystallizer  （固化为 playbook）
```

## 文件结构

```
super_agent/
├── pyproject.toml
├── README.md
├── memory_store/                    # 持久化记忆（自动创建）
│   ├── kv.json                      # 短期 KV
│   └── notes/
│       ├── background.md            # 你的个人使用说明书
│       └── playbook-*.md            # 固化的可复用流程
└── super_agent/
    ├── main.py                      # 入口 + CLI
    ├── memory.py                    # 文件型记忆存储
    ├── prompts/__init__.py          # AIM + Navigator + Soul system prompt
    ├── tools/
    │   ├── memory_tools.py          # MCP server：记忆工具
    │   └── web_tools.py             # MCP server：联网工具
    ├── subagents/__init__.py        # 6 个 AgentDefinition
    └── playbooks/                   # 现成的 prompt 模板
```

## 扩展

- **新 subagent**：编辑 `subagents/__init__.py`，加 `AgentDefinition` 到 `AGENTS`。
- **新 MCP 工具**：用 `@tool` 装饰函数，挂到 `create_sdk_mcp_server`。
- **换模型**：`export SUPER_AGENT_MODEL=claude-sonnet-4-6`
- **收紧权限**：`build_options()` 里改 `permission_mode` 为 `"default"`（每次工具调用前询问）。

## 注意

- 默认 `permission_mode="acceptEdits"` —— 自动接受文件编辑。生产环境改 `"default"`。
- `web_search` 用 DuckDuckGo 无 API key，但有速率限制。生产换 Tavily / SerpAPI。
- 记忆是单进程文件，并发写有竞态。规模化改 SQLite。
