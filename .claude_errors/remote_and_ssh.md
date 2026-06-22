# Error Book: 远端环境 & SSH

**新增规则**：不要把新的远端事故继续追加到本文件。先按下面类别选择对应文件写入；只有新增/调整分类索引、或一条规则确实横跨所有类别时，才修改本文件。

本文件保留为旧入口索引；具体事故已经按检索场景拆分到下面几个文件。新增远端事故时优先追加到对应主题文件，只有跨主题规则才回到这里补索引。

## 拆分索引

- [远端 SSH / Slurm / 容器基础](remote_ssh_slurm_container.md)：SSH 认证、ControlMaster、srun、sinfo、容器挂载、cache 变量、spawn cwd、释放资源。
- [远端运行时 / GPU / 依赖](remote_runtime_gpu.md)：transformers/vLLM/flashinfer 版本漂移、GPU 占用判断、TP 配置、端到端 smoke 与真实运行路径。
- [远端验证工作流](remote_validation_workflow.md)：何时上远端、`docs/remote_server.md`、跨主机 git 同步、PowerShell→SSH 脚本投递、路径事实、旧 PR/base smoke、新终端接手。
- [远端 venv / 清理](remote_venv_and_cleanup.md)：新建/复用 venv、`--system-site-packages`/`--no-deps` 取舍、保护/删除白名单、大目录清理卡住时的处理。

## 快速规则

1. 远端验证前先读 `docs/remote_server.md`，路径记录以完整 `user@host:port` 为 key。
2. 用户明确说“新建 venv / 装 X / 名字叫 Y”时，做最小冲突检查后按字面执行。
3. 复杂 PowerShell→SSH 命令落 `/tmp/*.sh`，执行前固定 `wc -c` + `sed -n` + `bash -n`。
4. GPU 是否可用不能只看 `memory.used`，还要看 compute-apps 和进程列表。
5. 清理远端目录先列 `KEEP` / `DELETE`，保留项出现在删除列表时直接 abort。
