---
name: task_as_audit_enumeration
description: TaskCreate should list enumeration steps (what to check), not outcomes (what to fix). After API rename or new producer field, open audit tasks before knowing the answer.
metadata:
  type: feedback
---

TaskCreate 列**枚举步骤**（"该检查的事"），**不是修复目标**（"已知要修的事"）。

**Why:** Task list 本身不消除偏见——偏见在生成 task 那一步。把外部 review 的 action list 直接当 task list 等于把"找问题"完全外包给一个有 framing 的子 agent（见 [review_delegation_framing](review_delegation_framing.md)），它的盲点 100% 继承。task 列在**还不知道答案**之前开，才能逼自己走完审查面。

**实测**：我开的 task 全是 outcome 级（抄自第一轮 review 的 action list），结果独立的第二轮 review 抓到两个我 task list 里压根没有的盲区（API rename 残留、producer→consumer signature 完整性）。

**How to apply:**

❌ outcome 级（已知答案）：
- `#1 Replace old_api_name in module_A`
- `#2 Delete duplicate assignment`

✅ enumeration 级（强制走完审查面）：
- `For each API rename, grep repo-wide for **all** old-name cross-product`
- `For each new field added to producer, grep its consumer and verify the consumer reads it`
- `For each commit in PR chain, list touched files and re-grep stale identifiers introduced before the rename`
- `For each enum exposed at API surface, verify the corresponding override/custom field is also exposed`

**Concrete trigger templates:**

| 触发场景 | 必开的 audit task |
|---------|------------------|
| API rename / enum 拆轴 | `Cross-product grep all old-name combinations across tests + examples + config` |
| 加 producer 新字段 | `Trace field from producer write site to consumer read site, verify signature accepts it` |
| Merge main 进 feature branch | `git log A..B; for each file changed in both branches, manual diff resolve quality` |
| Sub-agent review 返回 action list | `Open ONE meta-task: "verify action list coverage" — re-enumerate the audit surface independently before treating list as ground truth` |
