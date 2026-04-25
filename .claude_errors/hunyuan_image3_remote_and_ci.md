# Error Book: 远端环境 & CI 调试

## 2026-04-21 — 远端节点 — 假设路径 + HF 缓存丢失
> ⚠️ 进任何新节点/容器，第一步必须跑侦察三连，见 CLAUDE.md 规则 4。

**症状**：docker exec 失败、挂载路径为空、HF 缓存消失
**根因**：不同节点布局不同；容器内 `~` 在容器层，非持久
**侦察三连**：
```bash
docker ps && docker inspect <container> --format '{{range .Mounts}}...'
find /home /scratch -maxdepth 5 -name "snapshots" -type d 2>/dev/null
env | grep -iE "cache|hf_home"
```
**提醒**：建容器挂 `/home`，`HF_HOME` 指向持久路径

## 2026-04-22 — TRANSFORMERS_CACHE 覆盖 HF_HOME
> ⚠️ 进容器后必须 `env | grep -i cache` 检查，见 CLAUDE.md 规则 15。

**症状**：模型路径指向 `/models/huggingface/transformers/` 而非 `$HF_HOME/hub/`
**根因**：容器默认设了 `TRANSFORMERS_CACHE`，优先级高于 `HF_HOME`
**关键**：`TRANSFORMERS_CACHE=`（空字符串）≠ `unset`
**解法**：`unset TRANSFORMERS_CACHE`
**提醒**：空字符串仍被 `os.environ.get()` 返回

## 2026-04-22 — GEBench test 未传 --samples-per-type
**症状**：pytest 传了参数但测试函数没透传，跑了全量数据集
**解法**：测试函数接收 fixture 并传给 `gbench_main`
**提醒**：GEBench 每样本 6 张图，smoke test 用 `--samples-per-type 1`

## 2026-04-23 — 没做侦察 + judge 模型未预下载
> ⚠️ accuracy test 前必须过 checklist，见 CLAUDE.md 规则 9/17。

**症状**：跑了 4 小时才跑通；judge 报 `LocalEntryNotFoundError`
**根因**：没做侦察 + `HF_HUB_OFFLINE=1` 下 judge 模型遗漏
**提醒**：accuracy test 涉及 generate + judge 两个模型，都要预下载

## 2026-04-23 — multiprocessing spawn 子进程 cwd PermissionError
**症状**：worker 进程启动即崩，父进程报 `EOFError`
**根因**：spawn 模式 `os.chdir()` 到父进程 cwd（Lustre 目录），容器 root 没权限
**解法**：跑命令前 `cd /tmp`
**排查教训**：前 3 轮只看 EOFError，第 4 轮 `head -60 log` 才看到 worker 端 `PermissionError`
**提醒**：EOFError 时先找 worker 端真正错误；见 CLAUDE.md 规则 19

## 2026-04-23 — 连续跑多配置时 GPU 显存残留 OOM
**症状**：tp4_fp8 跑完立即跑 tp2_sp2，OOM
**根因**：进程退出后 GPU 显存未立即释放
**解法**：每轮之间 `pkill -9 && sleep 5 && nvidia-smi` 确认归零
**提醒**：不能依赖进程正常退出释放显存

## 2026-04-23 — "释放资源"只杀进程没退 srun
**症状**：pkill 后 Slurm job 一直占着节点
**根因**：srun shell 没退出，job 不会释放
**解法**：三步走 pkill → exit 容器 → exit srun → squeue 确认
**提醒**：见 CLAUDE.md 规则 20
## 2026-04-25 19:29 — CI dummy guard 未实际执行导致 property 运行时错误
**症状**：L3 CI 跑 `tests/e2e/offline_inference/test_t2i_model.py::test_hunyuan_image3_instruct_t2i_dummy_forward` 失败，报 `AttributeError: property 'device' of 'HunyuanImage3Pipeline' object has no setter`。
**根因**：新增 dummy guard 后只跑了 `python -m compileall` 和 `git diff --check`，没有让新增测试函数实际执行一次。`object.__new__(HunyuanImage3Pipeline)` 绕过初始化后，测试代码直接 `pipeline.device = torch.device("cpu")`，但 `device` 是只读 property，语法检查无法发现这种运行时错误。
**解法**：不要给实例写只读 property；用 `monkeypatch.setattr(HunyuanImage3Pipeline, "device", property(lambda self: torch.device("cpu")), raising=False)` 让真实 `prepare_model_inputs()` 访问 `self.device` 时返回 CPU。
**对未来的提醒**：写 CI/dummy guard 时，`compileall` 不算行为验证。新增 test function 必须至少执行一次；如果本地 pytest 因缺依赖起不来，要换现有 venv、远端容器、或最小脚本执行核心路径。用 `object.__new__` 构造对象时，先确认要塞的属性不是只读 property。
