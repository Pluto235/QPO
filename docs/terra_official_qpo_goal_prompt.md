# Terra Goal Prompt: Official WCDA QPO Rebuild

## How To Use

On ETO, start the persistent session from the canonical repository:

```bash
tmux new -s qpo-official-lc
cd /home/server/projects/QPO
codex
```

Select the requested Terra model, then paste the prompt below. Do not add a token budget to
the Goal unless you intentionally want to cap it.

## Prompt To Paste

```text
你现在常驻在 ETO 服务器，工作目录是 /home/server/projects/QPO。请创建一个持久 Goal，并持续工作直到目标真正完成。

Goal objective：严格执行 docs/official_daily_qpo_execution_plan.md，完成官方 WCDA Cod 2/8/32-day 响应一致的 10 源探索性 QPO survey：从 IHEP 选择性同步必要代码与轻量产物，补齐 source-specific spectrum、官方 DGE、逐 bin profile likelihood、Crab/空天区/response-boundary 控制；在 IHEP 通过 HTCondor 生成并验证全部官方光变，在 ETO 通过 Slurm 完成 likelihood periodogram、CWT、WWZ、三类复合红噪声模型和每组合 10,000 次模拟；最后交付经过数字与引用完整性审查的中文单文件 HTML、英文摘要、CSV/JSON 和可复现记录。

立即执行以下规则：

1. 先完整阅读 AGENTS.md、CLAUDE.md、docs/official_daily_qpo_execution_plan.md，以及可访问的 IHEP /home/lhaaso/liushijie/QPO/docs/official_daily_qpo_rebuild_status.md。计划文件是科学协议和 Definition of Done 的唯一权威；旧 weekly 报告只是历史基线。
2. 调用 Goal 工具创建上述 objective，不设置 token_budget。随后建立并持续更新 work/official_daily_qpo_goal_status.md。每个阶段开始、提交、完成、失败诊断、合并和决策点都要增量记录，不得最后一次性补写。
3. 先检查 git status，保留现有未跟踪或未提交内容。当前已知存在 periodicity_v2 生成图，禁止回滚、覆盖或清理与本任务无关的用户文件。
4. Agent 本身和 canonical repo 始终在 ETO。ETO 负责代码、测试、QPO 统计、Slurm 模拟和报告；依赖官方 EOS、Src_Main、DGE、响应和 ROOT 的工作必须由你从 ETO 远程编排到 IHEP HTCondor。禁止在 IHEP login 节点批跑，禁止把整套天图搬到 ETO。
5. 首先验证 ETO 到 IHEP 的真实连接。若 Codex 沙箱内 DNS/SSH 失败，分层检查主机 DNS、已有 SSH/隧道配置和 tmux 环境；不要因一次嵌套探针失败就宣称连接不可用。记录成功命令和远端 hostname。确实需要用户改变网络/凭据时再升级。
6. 先做只读审计和轻量同步。IHEP 端以 /home/lhaaso/liushijie/QPO/MakeLC/standard_flux_lc.py 和官方 rebuild status 为起点；ETO 端复用现有 src/methods/periodicity.py、AGN strict-flux pipeline、significance pipeline、report builder、source registry 和 Emmanoulopoulos 代码。旧代码中的 weekly 固定行数、TS 过滤、AR(1)-only、1000 surrogate、对称误差假设不得直接沿用。
7. 严格遵守所有冻结选择：10 源；8-day 主分析；2-day 和 32-day 都做完整辅助扫描；2/8-day 搜索 50-600 d，32-day 搜索 128-600 d；所有官方 bin 保留；7 nhit 联合；源特异固定谱；DGE 开启；单目标 ROI；完整 profile likelihood；三种方法分别报告；PL PSD、bending PSD、CARMA(1,0)；每组合固定 10,000 模拟；不做方法间或 10 源校正；不写 detection/candidate/hint；控制样本只呈现不修正。
8. profile likelihood 是硬闸门。先查明 public Src_Main 的官方接口；优先官方 profile/scan 能力，否则实现确定性的 fixed-F0 scan wrapper。只允许 1-3 个 IHEP 本地 smoke。3/3 早中晚响应 profile 未通过前，不得提交全量光变，也不得退化为 N0/N0_err Gaussian 方案。
9. 大任务必须批处理：IHEP ROOT/拟合/profile 用 HTCondor；ETO 统计模拟用 Slurm。提交前生成 immutable manifest，提交后监控 held/failed/missing outputs，诊断后只重跑明确失败行。不要用 sleep 长时间阻塞；使用产品提供的 wait/monitor 机制并持续向用户报告有变化的状态。
10. 实现按计划分阶段通过硬闸门：环境与传输、配置冻结、profile、Condor pilot、8-day、32-day、2-day、ETO 分析包、三 null 模拟、controls/robustness、report/integrity。任何硬闸门未过，不得宣布下一阶段成功。
11. 每次 Python 改动至少运行 compileall 和相关 pytest；每次数据合并检查期望行数、schema、hash、响应 period/slot、profile coverage 和失败 ledger。所有随机 seed 必须由固定 master seed 和 source/cadence/null/index 确定并写入 manifest。
12. 发现普通实现问题时自主解决，并至少尝试两个独立的安全方案。只有在需要改变冻结科学决定、需要新权限/凭据、需要破坏性操作、或经过充分诊断仍无法继续时才询问我。不得用环境问题掩盖未验证的实现问题。
13. 不要创建或使用 sub-agent，除非我之后明确授权。不要擅自 commit、push、publish、删除 ROOT/日志/结果或修改官方公共软件。需要改造时在用户目录/本仓库实现 wrapper 和配置。
14. 工作期间给出短而有信息量的进度更新；我询问状态时先汇报当前 phase、活动 job ID、完成/预期数量、held/failed、最新验证和下一步，然后继续工作，除非我明确要求暂停。
15. 只有 docs/official_daily_qpo_execution_plan.md 的 Definition of Done 十项全部满足、最终报告通过数字/引用完整性审查、且没有必要的生产或监控进程仍在运行时，才调用 Goal complete。不能因为代码写完、任务已提交或报告骨架生成就提前完成。

现在开始：先创建 Goal，读取规范，检查现有工作树，建立状态 ledger，并执行 Phase 0 的只读环境与连接验证。不要先提交生产任务。
```

## Expected First Status Update

Terra 的第一次状态更新应至少包含：

- Goal 是否成功创建；
- 当前 ETO branch 和 dirty files；
- 实际读取到的指令/计划文件；
- ETO 到 IHEP 的连接验证结果和 hostname；
- Phase 0 尚缺什么；
- 下一条准备执行的只读命令。
