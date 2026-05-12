# 固化为系统提示词的指令

当你和 super-agent 磨合出一个满意的结果，并希望下次只输入原料就能复用流程：

---

> 刚才我们解决这个问题的逻辑非常棒。请委派给 `crystallizer` subagent，
> 把刚才的对话过程整理成一个**系统提示词**（playbook），要求：
>
> 1. 遵循 AIM 框架（Act / Input / Mission 三段式）。
> 2. 下次我只需要输入"原料"（Input 部分的内容），你就能按这个逻辑自动产出同等质量的结果。
> 3. 给这个 playbook 起一个简短的 slug 名（例如 `marketing-brief` / `weekly-report`）。
> 4. 保存到长期记忆，用 `note_save` 写入 `playbook-<slug>.md`。
> 5. 告诉我下次怎么调用它。
