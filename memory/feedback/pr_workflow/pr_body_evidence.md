# PR Workflow · PR body 与证据 provenance

## 6. vLLM-Omni PR 描述必须按仓库模板写

**症状**：给用户的 PR body 用了通用 GitHub 结构：
```markdown
## Summary
## Testing
```
用户指出"不符合 vllm-omni pr 格式"。

**根因**：没先打开 `.github/PULL_REQUEST_TEMPLATE.md`，直接套通用模板。vLLM-Omni 的模板只有：
```markdown
## Purpose
## Test Plan
## Test Result
```
并且 checklist 要求 Test Plan 放测试脚本/命令，Test Result 放 e2e 结果或前后对比。

**怎么避免**：
1. 写 PR 描述前必先读：
   ```bash
   cat .github/PULL_REQUEST_TEMPLATE.md
   ```
2. 输出给用户的 PR body 保持模板标题原样：`Purpose / Test Plan / Test Result`。
3. "Test Plan" 写命令，不写结果；"Test Result" 写 metric / pytest summary。
4. 如果补充额外验证（CUDA graph、accuracy PR），也放在 `Test Result`，不要另起通用 `Additional validation` 大标题。
5. 小 bugfix / reviewer-followup PR 不要机械填写模板里的 `vLLM Version` / `vLLM-Omni Commit`，也不要列 `DCO`、`build (3.11)`、`pre-commit`、ReadTheDocs、current head SHA、旧 validation SHA 这类机器账本。PR 描述要像 reviewer-facing 说明：`Purpose` 讲行为问题和修复边界，`Test Plan` 讲怎么覆盖，`Test Result` 讲实际验证了什么。只有用户明确要求 provenance 表，或性能/精度/图片证据必须绑定来源时，才写 commit / artifact / run metadata。

## 6.1 PR body 是交付物：必须渲染级验收

**触发条件**：
- 开 PR / 更新 PR 描述 / 用户要求贴测试结果或图片。
- 用户问的是 e2e、精度、性能、复现方式，而不是 UT 覆盖。

**不要做**：
- 不要把工作日志式覆盖清单塞进 Test Plan，例如“验证 scheduler admission / request release / unit coverage”。reviewer 需要的是怎么复现。
- 不要用 `tmpfiles` / `0x0` / `transfer.sh` 这类临时图床做 PR 图片；GitHub 预览容易裂，链接也会过期。
- 不要在 PowerShell 双引号 here-string 里直接写 Markdown 三反引号。PowerShell 会把反引号当 escape，代码块会变成 `` `b + ash `` / tab + `ext` 这类乱码。

**正确写法**：
1. PR body 一律写到 no-BOM UTF-8 临时文件。PowerShell 用单引号 here-string：
   ````powershell
   $body = @'
   ## Purpose
   ...
   ```bash
   command
   ```
   '@
   $tmp = [System.IO.Path]::GetTempFileName()
   $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
   [System.IO.File]::WriteAllText($tmp, $body, $utf8NoBom)
   gh pr edit <PR> --body-file $tmp
   Remove-Item $tmp
   ````
2. 更新后必须读回验收：
   ```powershell
   $view = gh pr view <PR> --repo vllm-project/vllm-omni --json body,url,isDraft | ConvertFrom-Json
   $view.body.Contains('```bash')
   $view.body.Contains('```yaml')
   $view.body.Contains('```python')
   $view.body -match "[\x00-\x08\x0B\x0C\x0E-\x1F]"  # 必须 False
   ```
3. 图片必须使用稳定可渲染 URL：
   - 优先单独 artifact branch + `raw.githubusercontent.com/.../artifact.png`。
   - 上传后先验证：
     ```powershell
     Invoke-WebRequest -Uri $url -Method Head -UseBasicParsing
     ```
     必须是 `200` 且 `Content-Type: image/png`。
   - 不要把 artifact branch 开成 PR；它只承载 PR 描述图片，不进入业务 diff。
4. e2e Test Plan 写成 reviewer 可以复制的复现路径：
   - 机器 / cwd / venv / env vars。
   - 运行命令或脚本路径。
   - YAML 路径和关键字段（只贴关键字段，长配置放折叠块或缩减）。
   - 请求怎么构造（prompt、图片、sampling params、`Omni.generate` 调用）。
   - 指标怎么计算、reference 是哪个文件。
   - Test Result 放日志证据、输出路径、指标表、图片。

**格式建议**：
```markdown
## Purpose

<原理，短表格说明核心 hook / data flow>

## Test Plan

### Environment
### Run Command
### Temporary YAML
### Request Construction
### Metric Comparison

## Test Result

### E2E Evidence
### Run Metadata
### Accuracy Metrics
### Artifacts
```

**验收标准**：PR 页面读起来像复现说明，不像聊天记录；任何人能按 Test Plan 找到脚本/YAML/请求/指标路径。

## 6.2 PR 里的每个性能 / 精度 / 图片证据都必须绑定来源，smoke 不能冒充 e2e

**触发条件**：
- PR 里要写 performance / accuracy / CLIP / SSIM / PSNR / throughput / speedup。
- PR 里要贴输出图片。
- 同一轮验证里同时存在 DiT-only smoke、official accuracy、full AR-to-DiT e2e、临时 debug 脚本等多种结果。

**症状**：2026-05-21 PR #3766 HunyuanImage3 DiT grouped batching 中，我先把一组 DiT-only 临时性能表写成主性能结论：

```text
Baseline max_num_seqs=1 diffusion_batch_size=1 elapsed=51.118s
Grouped  max_num_seqs=2 diffusion_batch_size=2 elapsed=47.426s
speedup=1.078x
```

这组数据来源是临时脚本 + 两条英文 T2I prompt，只能证明 DiT-only grouped path 有功能性收益；它不是官方 IT2I prompt / 官方 demo input images / AR-to-DiT full pipeline 的性能结果。用户指出后，用官方 IT2I 两请求重跑，同口径结果是：

```text
Baseline DiT max_num_seqs=1 diffusion_batch_size=1 elapsed=188.042s
Grouped  DiT max_num_seqs=2 diffusion_batch_size=2 elapsed=182.690s
speedup=1.029x
```

同轮还把英文 DiT-only smoke 的差图贴进 PR，进一步造成误导。那些图只适合作为“不同 prompt token 长度可以 padding 后组 batch”的 smoke 证据，不适合作为质量 / 精度 / 官方输入证据。

**根因**：
- 把“这条路径能跑通”的 smoke 结果和“官方输入下的质量 / 性能结论”混在一起。
- PR body 写表时没有给每个数字绑定：输入、请求数、脚本、配置差异、是否包含初始化、指标 reference。
- 先写结论再补来源，导致临时实验数据进入主结论。

**正确做法**：
1. PR Test Result 里的每张表前必须写清楚 evidence provenance：
   - input：官方 fixture / 用户指定输入 / 临时 smoke prompt。
   - request shape：单请求 / 双请求 / 多请求；T2I / IT2I / AR-to-DiT / DiT-only。
   - config delta：只列 baseline vs grouped 不同的 knobs。
   - timing scope：是否只包 `omni.generate(...)`，是否排除模型初始化。
   - metric reference：CLIP/SSIM/PSNR 对哪个 reference image。
2. Smoke 只写 smoke，不写成主质量结论：
   - DiT-only variable-token smoke 可以证明 padding / grouping 行为。
   - 官方质量、精度、性能必须用 official fixture 或用户指定输入。
   - 如果 smoke 图质量差，不贴图；贴日志证据即可。
3. 官方输入优先级高于“看起来更容易跑”的临时 prompt。用户要求“官方提示词 / 官方输入”时，不能拿自写 prompt 数据替代。
4. 如果已经写过错误口径，必须撤掉而不是补一句解释；PR 只保留当前可 defend 的主结论。

**PR Evidence Matrix gate**：

写 PR body 前先在草稿里填矩阵；没有矩阵，不许写性能 / 精度 / 图片结论。

```markdown
| ID | Purpose | Input Source | Path | Requests | Batch Knobs | Timing Scope | Result | PR Placement |
| --- | --- | --- | --- | ---: | --- | --- | --- | --- |
| E1 | Compatibility smoke | Temporary prompt | DiT-only | 2 | max_num_seqs=2, diffusion_batch_size=2 | N/A | logs only | Test Result / smoke |
| E2 | Official accuracy | Official fixture | AR-to-DiT | 2 | DiT max_num_seqs=2, diffusion_batch_size=2 | N/A | CLIP/SSIM/PSNR + image | Test Result / accuracy |
| E3 | Official performance | Official fixture | AR-to-DiT | 2 | baseline 1/1 vs grouped 2/2 | omni.generate only | elapsed / throughput | Test Result / performance |
```

PR body 写法必须按矩阵顺序落地：
- `Test Plan` 写 E1/E2/E3 如何复现。
- `Test Result` 写 E1/E2/E3 的实际日志、表格、图片。
- `Purpose` 只能引用 E1/E2/E3 支撑得住的范围，不提前吹性能。
- 如果某行是 smoke，标题必须包含 `smoke` 或 `compatibility`，不能叫 `accuracy` / `performance`。

**PR body evidence audit gate**（更新 PR 前手动过一遍）：

```text
For each table/image:
- What exact script or command produced it?
- What input and prompt did it use?
- Is it official/user-specified input, or only a smoke prompt?
- What request count and batching knobs were used?
- Is model initialization excluded from elapsed time?
- Does the conclusion say exactly what this evidence proves, and no more?
```

**验收标准**：reviewer 不看聊天上下文，也能从表格附近判断这组数据代表的是 full e2e、official accuracy、performance comparison，还是 only a smoke.

### 6.2.1 PR comment / PR body 贴测试图片前，先做 evidence provenance gate

**触发条件**：
- 用户要求“贴图 / 补 output image / paste output image / 更新 Test Result / rebase 后再跑”。
- PR comment 或 PR body 要包含 accuracy/perf metrics、测试图片、raw artifact URL。
- 当前 PR head 可能已经被 reviewer / rebase / force-push 更新。

**事故**：2026-05-29 PR #3626 中，用户要求补 online accuracy 输出图。我只验证了远端旧 artifact 是 `PNG 1280x720`，但没有把图片、metrics、PR head 绑定成同一组证据。旧 run 是 `9e218143...`，PR 当前 head 后来已是 `7aa78999...` / rebase 后 `342a298a...`。我还把内部远端路径 `Artifact source: /data/.../image_online.png` 贴进公开 PR comment，污染 reviewer-facing artifact。

**根因**：
- 把“补贴一张图”当成文件上传任务，没有当成 PR evidence 更新任务。
- 只做 artifact provenance（图片能打开、尺寸正确），没做 PR evidence provenance（图片/metrics/commit/base 是否同一轮）。
- 把内部追踪信息混进公开评论；远端路径对 reviewer 没复现价值，且暴露执行环境噪音。

**硬规则**：
1. 贴任何测试图/指标前，先确认当前 PR head：
   ```powershell
   gh pr view <PR> --repo vllm-project/vllm-omni --json headRefOid,headRefName,headRepositoryOwner
   ```
2. 再确认 run status/log 里的 checkout SHA：
   ```bash
   cat <status-file>      # 必须包含 WT=<sha> 或 HEAD=<sha>
   grep -E 'HEAD=|WT=|1 passed|EXIT_STATUS|\\[ONLINE\\]' <log-file>
   ```
3. `headRefOid`、run `WT/HEAD`、图片 mtime 必须属于同一轮。任一不一致：
   - 不贴旧图。
   - 如果用户说“rebase 后 / latest / current PR”，先 rebase/sync 到 current head 再重跑。
   - 如果确实要引用历史结果，标题必须写明历史 head，不能让 reviewer 以为是 current head。
4. 图片证据必须过四件套：
   ```powershell
   python -c "from PIL import Image; import sys; im=Image.open(sys.argv[1]); print(im.format, im.size, im.mode)" <image>
   Get-FileHash -Algorithm SHA256 <image>
   Invoke-WebRequest -Uri <raw-url> -Method Head -UseBasicParsing
   ```
   还要实际打开看一眼，确认不是旧图/裂图/空图。
5. 公开 PR comment/body 只放 reviewer 需要的信息：
   - result、PR head、case、runtime、metrics、stable image URL、必要复现命令。
   - 禁止放内部远端路径、`/tmp` 路径、本地 `%TEMP%` 路径、status 文件路径、“Artifact source: /data/...” 这类流水账。
6. comment body 发出前先本地预览一遍，删掉 internal path 和执行噪音。发出后用 `gh pr view` / comment URL 读回，确认图片渲染和 Markdown 干净。

**验收标准**：reviewer 不看聊天上下文，也能知道这张图和这组 metrics 对应哪个 PR head；评论里没有内部路径；如果 PR head 变了，证据也必须重跑或明确标成历史结果。

## 6.3 新模型 PR body：source parity / stub smoke / real checkpoint 必须分开

**触发条件**：
- 新增 model / pipeline / backend / checkpoint adapter。
- PR body 想写 “weights load clean / smoke passed / shape correct / no NaN”。
- 同一轮里既有 stub input，又有 real checkpoint 尝试，或者真实 tokenizer / processor 尚未完全加载。

**PR #3474 GO-1-Air 教训**：`0 missing / 0 unexpected`、stub smoke、shape check 都成立时，仍可能有 scheduler、embedding order、activation、token order、attention mask 等上游语义偏差。PR body 如果把这些 smoke 写成“模型已验证”，reviewer 会被误导。

**正确写法**：

```markdown
### Source parity
- Scheduler / denoising: <upstream file:line or "source inference">
- Embedding order: <upstream file:line>
- Activation: <upstream file:line>
- Token order: <upstream file:line>
- Attention mask / pad-eos: <upstream file:line or explicit deviation>

### Stub plumbing smoke
- Command:
- Inputs:
- Allowed conclusion: model wiring / tensor shapes only

### Real checkpoint validation
- Checkpoint:
- Tokenizer / processor status:
- Strict load:
- Command:
- Allowed conclusion:
```

**硬规则**：
- stub smoke 不能支撑 real checkpoint / quality / e2e 结论。
- `load_state_dict` clean 只能写在 plumbing evidence 下，不能单独当 correctness。
- 真实 checkpoint 缺 tokenizer / processor / config 时必须写 fail-fast 或 blocker，不能 silent fallback。
- 更新 PR body 后必须 `gh pr view` 读回，确认 code fence、source parity 表和 allowed conclusion 没错位。

## 6.4 PR body 禁止暴露本地 / 远端内部环境细节

**触发条件**：
- 开 PR / 更新 PR 描述 / 更新 PR comment。
- Test Plan / Test Result 要写本地测试、远端验证、benchmark、model cache、环境探针。
- 当前验证是在个人 Windows、共享远端、临时 worktree、临时 cache 或内部路径上完成。

**事故模式**：
- 把“本地 Windows 环境缺依赖，无法执行完整导入测试”写进公开 Test Result。
- 把远端机器别名、用户路径、venv 路径、cache 路径、host/port、模型缓存是否存在这类内部侦察信息写进 PR body。
- 远端只做了 import/cache 探针，却在 PR 里用探针失败替代真实模型验证。

**根因**：
- 把面向用户的工作日志当成 reviewer-facing Test Result。
- 没区分“内部排查细节”和“公开可复现证据”。
- 没有先跑远端真实路径，就用本地环境 blocker 填 PR 测试结果。

**硬规则**：
1. 公开 PR body / comment 只写 reviewer 需要的可复现证据：
   - PR head SHA / run checkout SHA。
   - public model id 或公开 snapshot revision。
   - workload：prompt 来源、尺寸、帧数、step、guidance、run count、是否 warmup。
   - 命令或 repo 内脚本路径。
   - 结果表：latency、memory、accuracy、pass/fail。
2. 禁止写入公开 PR：
   - Windows 用户目录、本地绝对路径、远端用户路径、venv 路径、cache 路径、`/tmp` 路径。
   - 远端机器别名、host、port、账号、内部工作目录。
   - “cache not found / 缺某个本地包 / 本地没装 vllm”这类内部侦察噪音。
3. 本地环境无法跑时，不能把它作为主要 Test Result；必须优先尝试远端真实验证。
4. 远端只做 import/cache 探针时，只能作为内部排查，不写进公开 Test Result；PR 至少要有真实功能 smoke 或明确写“validation pending”。
5. 性能 PR 不得写未验证 speedup；必须同一 checkout / 同一机器 / 同一 workload 跑 Omni 和 HF/original baseline。没有提升就写真实结果，不硬凑“提升”。
6. `gh pr edit --body-file` 后必须读回验收，确认没有内部路径或机器信息：
   ```powershell
   gh pr view <PR> --repo vllm-project/vllm-omni --json body |
     Select-String -Pattern "C:\\|D:\\|/home/|/root/|/tmp/|\\.venv|HF_HOME|cache|port|host|Windows|本地"
   ```
   有命中就手动判断是否为公开复现所需；默认删除。

**公开写法示例**：
```markdown
### Remote GPU validation

- PR head: `<sha>`
- Model: `dg845/LTX-2.3-Diffusers@<revision>`
- Workload: 384x512, 25 frames, 20 steps, guidance 4.0, 1 warmup + 3 measured runs.
- Result: `<table>`
```

**验收标准**：PR body 读起来像 reviewer 可复现报告，不像个人机器日志；没有本地/远端私有路径；每个性能结论都有同口径 baseline。
