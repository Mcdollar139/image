# Playbook: Investor / LP Update

## Role (A)
强制委派 `marketer` subagent。

## Input (I)
- 本期业绩数据（数字）
- 本期关键事件（口语 / bullet）
- 受众：现有 LP / 潜在 LP / 内部 GP
- 期限：周报 / 月报 / 季报
- 渠道：email / WhatsApp / Telegram / PDF

## Mission (M)

### Output 1 — Subject Line（≤ 60 字符）
具体结果（"+18.4% MoM, ETH outperformed"）> 模糊形容（"Strong month"）

### Output 2 — Body

```
TL;DR
- 业绩：____ vs benchmark ____
- 关键事件：____
- 下一步：____

Numbers
| 指标 | 本期 | 上期 | YTD | vs Benchmark |
|---|---|---|---|---|
| Return | __ | __ | __ | __ |
| Sharpe | __ | __ | __ | - |
| Max DD | __ | __ | __ | - |
| AUM | __ | __ | __ | - |

What happened
（1 段，说人话，把数字背后的故事讲清楚。Win 的归因到策略 + 市场，Loss 的归因到具体决策，不甩锅。）

Looking forward
- 接下来 30 天 focus 在 ____
- 风险点：____
- 需要 LP 配合 / 决策的：____
```

### Output 3 — Variants
另外给 3 个版本：
- **Short** (微信 / Telegram，≤ 280 字)
- **Long** (季报 PDF 版本，附详细归因)
- **English** (国际 LP 版)

## Operating Principles
- 不准 spin。亏了就说亏，但要把 context 给到位
- 不写 "感谢您的信任 / 支持"，除非用户明确要求
- 不写 "投资有风险" 类 disclaimer
- 数字一定要 vs benchmark（BTC / ETH / S&P / 同策略指数）
- 用户的风格：详细 + 中英混 + 零套话
- LP 提问历史如果在 `background.md` 里有，主动呼应
