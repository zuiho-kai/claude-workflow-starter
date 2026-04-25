#!/usr/bin/env bash
# stop-gate.sh — Stop hook 综合门禁
#   1. 检测本轮有代码改动 → 提醒去远端跑测试
#   2. 检测本轮有错误/失败痕迹 → 提醒把新坑写到 .claude_errors/
#   3. 两者都有 → 一并提醒

input=$(cat)
transcript_path=$(printf '%s' "$input" | grep -oE '"transcript_path"[[:space:]]*:[[:space:]]*"[^"]+"' | sed -E 's/.*"([^"]+)"$/\1/')

if [[ -z "$transcript_path" || ! -f "$transcript_path" ]]; then
    exit 0
fi

last=$(tail -n 400 "$transcript_path" 2>/dev/null)
if [[ -z "$last" ]]; then
    exit 0
fi

has_code_change=false
has_error_pattern=false

if echo "$last" | grep -qE '"name"[[:space:]]*:[[:space:]]*"(Edit|Write|NotebookEdit)"'; then
    has_code_change=true
fi

if echo "$last" | grep -qiE '(error|exception|traceback|failed|denied|timeout|cannot|undefined|not found|permission)'; then
    has_error_pattern=true
fi

if ! $has_code_change && ! $has_error_pattern; then
    exit 0
fi

msg="📡 本轮总结："

if $has_code_change; then
    msg="${msg}\\n• 检测到代码改动 → 建议去远端服务器跑测试验证：按 docs/remote_server.md 走 SSH+tmux+docker，启动前三连（GPU/模型路径/缓存变量），跑完三步释放（pkill→exit 容器→exit srun）。"
fi

if $has_error_pattern; then
    msg="${msg}\\n• 检测到错误/失败痕迹 → 如果是新坑，按 \\\".claude_errors/\\\" 格式追加（症状/根因/解法/对未来的提醒）。重复 ≥2 次的坑 → 升级到 CLAUDE.md 顶部硬规则区。"
fi

msg="${msg}\\n\\n这就是数据飞轮。回 'skip' 跳过本次提醒。"

printf '{"systemMessage": "%s"}\n' "$msg"

exit 0
