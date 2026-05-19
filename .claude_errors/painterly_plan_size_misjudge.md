# Painterly bug — multi-image PR 上的 plan/size 判断错误

painterly fix 之后做 multi-image input PR 时，同会话**两次**踩"input1 驱动下游"——03:45 plan 阶段 IT2I 输出尺寸方向反了，14:30 写 process_image 时 shared-bucket 又来一次。**判断模式相同**：看到下游约束 → 改输入凑合，没问"约束本身 sane 吗"。根因和总览见 [`painterly_root_cause.md`](painterly_root_cause.md)。

---

## 2026-05-08 03:45 — Plan 阶段把 IT2I 输出尺寸逻辑整反了，靠用户截图被打脸

**症状**：写 multi-image input PR 的 plan 时，提议把 `pipeline_hunyuan_image3.py:287-291` 的 `image_list[0]` 裸像素 fallback 改成 `image_processor.reso_group.get_target_size(...)` 桶量化，理由是"对齐官方 `image_size='auto'` + `infer_align_image_size=True`"。用户贴 `postprocess_outputs` 截图反问"是不是先推理出输出 ratio，再匹配输入"——一句话把方向反掉了。

**根因**：读 `hunyuan3.0_ins/image_processor.py:postprocess_outputs` 时只扫到多图分支 "iterate cond images, find ratio match"（line 451-459）就以为"输出尺寸由输入图驱动"，**漏了三处证据**：
1. `output_image_ratio_index = ...get_base_size_and_ratio_index(width=output_image.width, height=output_image.height)`——`output_image.width/height` **已经是 DiT 生成完的尺寸**，说明输出 ratio 在 postprocess 之前就定下来了
2. 没看 `SliceVocabLogitsProcessor`（line 32-58 + `build_img_ratio_slice_logits_processor` line 412-421）——AR 阶段在 ratio token 位置把 vocab 限制成"只能从 ratio tokens 里选"，`image_size="auto"` 的真正含义是**让 AR 自己采样输出桶**，输入图根本不参与
3. 漏看 postprocess 的真实意图——它不是"挑桶"，是"找 ratio 同桶的输入图借 original aspect 做最后精度微调（保持 area ≈ base_size²）"，AR 已经选完桶了

正确数据流：**AR 选桶 → DiT 按桶 denoise → postprocess 用 cond image 的 original aspect 微调**。我把第二步当成了第一步。

**解法**：revert plan §3 的尺寸改动，pre-existing `image_list[0]` 裸像素 fallback 留下不动（pre-existing bug，单独 PR 修，需要把 AR 输出里的 `<img_ratio_X>` token 抽出来塞 ar2diffusion）。最终 PR 只动 AR prompt 多图占位符，责任单一。

**对未来的提醒**：
- 给"size 政策""dispatch 政策""routing 政策"这种需要看完整生命周期的方案前，必须 grep 全调用链：`grep -E "image_size|infer_align|postprocess|ratio_index|<img_ratio_|SliceVocabLogitsProcessor"` 一次性把 AR / DiT / postprocess 所有相关点拉出来对照。**只看一处**就拍方案 = 用半截证据建模
- 看 postprocess 函数时**特别关注 input 参数是哪一阶段产出的**。`output_image.width` 这种字段一看就是上游传进来的，意味着尺寸在更早的阶段就 frozen 了。"看到差异 → 假设差异是 root cause"违反 B16，"看到一处行为 → 反推整个流程意图"是同一类错
- 用户用一句话+截图就把方向纠了——这不是用户特别厉害，是我证据链不完整就 commit 了 plan。下次给 plan 的"决策依据"小节必须列**全部读过的代码点 file:line**，强迫自己把证据链摆出来
- 涉及多 stage 数据流时，画一张 stage A → stage B → stage C 的箭头图（哪怕注释里 ASCII），数据来源能可视化纠错

---

## 2026-05-08 14:30 — 同会话第二次踩"input1 驱动下游"，shared-bucket 又来一次

**症状**：上面 03:45 那条刚 revert 完，两小时后写 `process_image` 的 multi-image stack fix 时，再次让 image1 的 VAE 桶强制驱动 image2/3——`shared_vae_w, shared_vae_h = self.reso_group.get_target_size(images[0].width, images[0].height)` 然后所有图都 resize 到这个 shared bucket。code review 抓出来：image2 1920×1080 被压成 image1 的 1024×1024 方桶，**侧边内容静默丢失**，注释只说"为了让 stack 不炸"，没提画质损失。用户一句"这个问题之前不是出过两次了么"打脸。

**根因（同款）**：碰到 `torch.stack expects equal size` 报错时大脑直接跳"凑成同尺寸最容易让它过"，绕过了"为什么 vllm-omni 这里非要 stack"的根本问题。**真正的约束是 `MultiModalFieldConfig.batched("image")` 选错了**——官方走 ragged（`flat_from_sizes` 等价物，不 stack），vllm-omni 这个 schema 选择是错的，不是输入数据的错。

跟 03:45 那条**完全同款**判断错误：**看到下游报错 → 假设下游是对的 → 改输入数据来满足下游**。正确链：**下游报错 → 问下游为什么这样要求 → 发现 schema 选错 → 改 schema 不改输入**。违反 CLAUDE.md F5（第一性原理：先问根本约束）。

**解法**：本 PR 选 hack 路线（保留 shared bucket + 加 warning），把"改 `MultiModalFieldConfig.batched` → ragged schema"列为 follow-up PR。不是不能修，是 PR 范围控制；但 commit message **必须**列 known limitation，不能说"已支持多图"了事。

**对未来的提醒**：
- 同会话犯同款错两次 ≠ 偶然，是底层模式没改过来。**碰到"下游对输入形状有约束"类报错，第一反应必须是"这个约束 sane 吗、是不是 schema/接口选错了"**，而不是"输入怎么改才能满足下游"
- shared-bucket / forced-equal-shape / pad-to-max 这种"凑齐让它过"的 hack，**永远会丢用户感知不到的画质/语义信息**——必须 commit message 明写、必须 logger.warning，否则就是埋雷
- error book 里的"对未来的提醒"不是写完就完事——下次写代码前必须 `grep` error book 找 keyword（"size"/"input drives"/"ragged"/"shared bucket"）核对，强迫自己跟过往判断对话。这条没跑这个流程是直接原因
- code review subagent 抓得出这种重复错（"P0-1 静默裁切"那条），说明用 subagent 做 review 是必要工序，不是 nice-to-have——本 PR 没让 subagent review 的话三个洞会全部进 prod
