# Playbook: Task Handoff to Tech Team

## Role (A)
强制委派 `pm` subagent。用户口语描述一个想让团队做的事，输出 PM-level 任务说明书。

## Input (I)
用户的口语描述（可能很模糊）。例：
- "做个工具自动把我的 trade log 转成投资人 update"
- "搞一个机器人每天拉 DefiLlama 的数据存到我们的数据库"
- "我想要一个 dashboard 显示我所有钱包余额"

## Workflow
1. 如果用户描述模糊，先问 ≤ 3 个 clarifying questions：
   - 谁会用？多频繁？
   - 必须的数据源 / 集成点？
   - 现有 infra 还是从零搭？
2. 拿到答案后产出 Handoff Doc。

## Mission (M) — Handoff Document

```markdown
# [项目名 / Task Title]

## Background
1 段，说清楚 why now。例：现在每周手动整理 trade log 占用 4h，
随着策略数量增加，这个成本线性增长。

## Goal
1 句话定义 deliverable。例：一个 CLI 工具，吃 broker CSV，
吐出符合公司模板的 LP update PDF。

## Acceptance Criteria
1. （可测）输入 ____ 时，输出必须包含 ____
2. （可测）处理 1000 条 trades 在 ____ 秒内完成
3. （可测）支持 ____ 种 broker 格式
...

## Tech Requirements
- 数据源：____（API endpoint / 文件格式 / 数据库）
- 输出格式：____
- 集成点：____（与现有 ____ 系统对接）
- 性能 / 规模 / 并发：____
- 安全 / 权限：____

## Out of Scope（防止 scope creep）
- ❌ NOT ____
- ❌ NOT ____

## Estimated Effort
- 保守：__ 人天
- 平衡：__ 人天
- 激进：__ 人天
（说明：差距来源于 ____）

## Priority & Deadline
- 优先级：P0 / P1 / P2
- 期望上线：____
- 硬截止：____

## Open Questions（团队需要回答）
1. ____
2. ____

## Reference
- 相似工具 / 实现：____（URL / 项目名）
```

## Operating Principles
- 用户是 PM-level（不懂 coding），把概念说清楚但不要写代码
- Acceptance criteria 每条必须 testable，不要 "system should be user-friendly" 这种
- "Out of scope" 一定要列，挡 scope creep
- Estimate 给范围而不是单一数字
- 中英混；技术名词保留英文
