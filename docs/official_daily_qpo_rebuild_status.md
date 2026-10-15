# WCDA Cod 官方日图 QPO 重算状态

更新日期：2026-08-04

## Material Passport

- Schema：ARS 9（项目内简化记录）
- Verification Status：`VERIFIED`（官方 v1.0 2-day LC 的三 period 接口复现）
- 数据来源：官方 Cod DailySkyMap，以及 v1.0 发布的 LC DataConfig
- 软件来源：`/home/lhaaso/hushicong/public/v1.0`；其 `Src_Main` 与 v0.99 的 SHA256 相同
- 运行证据：`JOBs_official_lc_smoke/summary.json`、三份 `fit.log` 和 `ParRes.yaml`
- 结果产物：`results/official_lc_smoke/LHAASO-WCDA_Mkn421_2021-03-08_2025-07-29_2day_flux.csv`
- 使用限制：仅完成三 bin 的接口复现，尚未完成全样本流强、QPO 统计或最终报告

## 当前结论

用户已确认 `periodXXX` 日图可直接使用公开合并响应；公共 v1.0 将这一约定落实为 803 个正式的 2-day LC DataConfig。每个配置绑定对应 Mapfile、`T001` 至 `T083` 的 response period、Group1/Group2 response slot 和模拟文件。因此，全量 2-day 重算可以开始准备并通过 HTCondor 提交。

这不等于 QPO 检出已经成立。后续仍须完成全样本拟合、Crab 稳定性、红噪声模拟、窗口函数和全局 trials 校正。

## 已核验资源

- 官方日图：`/eos/lhaaso/rec/wcda/publish/skymap/Cod/DailySkyMap/`
- 覆盖范围：2021-03-08 至 2025-07-31
- 日图数量：1592；相对完整自然日缺 15 天
- period 数量：83
- 官方逐期 MC：`/eos/lhaaso/rec/wcda/publish/simulation/Cod/MCGammaPeriod/`
- 每个 period 均有一份 `corsika.root` 和一份 `rec.root`
- 公开程序：`/home/lhaaso/hushicong/public/v0.99`
- 当前用户副本：`/home/lhaaso/liushijie/software/Space_energy_Joint_fitting/v0.99`
- 公开 DGE：`/home/lhaaso/hushicong/public/DGE_Template`
- 当前 DataConfig：`config/Data/WCDA/Cod/Data_20210305_20250731.yaml`

抽查的早、中、晚日图均含 `hon/hbkg/hoff_0..6`、`hSide`、`hltime_eachbin`、`hFOV` 和 `map_header`。`Src_Main` 当前源码不读取 DataConfig 的 `Livetime` 字段，而是从日图 `hSide` 计算目标方向的 `Tobs`；smoke test 必须从日志回收并核对这个值。

## 历史日图接口 smoke

`MakeLC/standard_flux_lc.py prepare-official-daily-smoke` 直接使用官方日图，不再从旧私有背景目录合并天图。默认选择首日、中间日和末日，最多允许三天，并在 `fit_jobs.csv` 中记录：

- 日期和 `YYYYDDD`
- `periodXXX`
- 官方日图路径
- 同 period 的 rec/corsika 文件路径
- 当前 `Src_Main` 实际会选用的公开合并响应
- 当时的响应契约审计标记（历史记录；现已由 v1.0 LC DataConfig 替代）

默认工作目录为 `JOBs_official_daily_smoke/`，默认结果目录为 `results/official_daily_smoke/`。这是 login 节点允许的小规模检查；全量任务仍必须使用 HTCondor。

2026-08-04 的三日结果均生成非空 `ParRes.yaml`，且拟合日志为 `STATUS: OK`：

| 日期 | period | Tobs (s) | TS | F0 (1e-12 TeV^-1 cm^-2 s^-1) |
|---|---:|---:|---:|---:|
| 2021-03-08 | 001 | 11291.8 | 0.07 | 0.09360 +/- 0.35443 |
| 2023-05-17 | 048 | 32265.8 | 350.79 | 3.15981 +/- 0.23057 |
| 2025-07-31 | 083 | 32008.8 | 12.11 | 0.44737 +/- 0.15086 |

这些数值仅保留为日图格式接口检查。生产链不再使用这套自行生成的 v0.99 DataConfig，而使用下面的官方 v1.0 LC DataConfig。

另一个可审计性问题是：`Src_Main` 日志输入摘要打印配置中的 `Responsefile1`，但 `ReadRespFile` 随后才按 `Ycenter < 28` 选择 Responsefile1/2，且不再打印最终选择。Mrk 421 的 ROI 赤纬大于 28 度，源码实际选择 1.04；任务清单已显式记录该文件，但全量生产前最好让运行日志也能记录最终打开的响应路径。

## 正式 v1.0 LC workflow

官方主配置 `v1.0/config/Data/WCDA/Cod/LCData_20210305_20250731.yaml` 列出 83 个数据时期及支持的 2、8、32 天时窗。QPO 生产选用 2-day：803 个 `Data_LC_XXXX.yaml`，覆盖 MJD 59281.6667 至 60885.6667。

`MakeLC/standard_flux_lc.py prepare-official-lc` 读取这些 DataConfig，而不自行合并 Mapfile。三 bin 的正式 smoke 已覆盖 T001、T048、T083，均为 `STATUS: OK`：

| LC bin | response period | Tobs (s) | TS | F0 (1e-12 TeV^-1 cm^-2 s^-1) |
|---|---:|---:|---:|---:|
| LC0001 | T001 | 42528.1 | 11.31 | 0.41773 +/- 0.14416 |
| LC0402 | T048 | 64420.9 | 211.00 | 1.49252 +/- 0.13069 |
| LC0803 | T083 | 49862.7 | 9.57 | 0.26580 +/- 0.10248 |

对 Mrk 421，ROI 赤纬大于 28 度，源码选择 `Responsefile2`，即官方 Group1 response；任务 CSV 显式记录此选择。`Src_Main` 日志摘要仍只打印 `Responsefile1`，因此生产审计以 CSV 的 `response_slot/response_file` 为准。

## 必须敲定的分析细节

1. 源样本：预先固定源列表和纳入标准，不能根据周期图挑源。
2. 时间采样：主分析使用官方 2-day bin；不把缺失日填零，保留逐 bin `Tobs`、response period 和窗口函数。
3. 流强估计：确定固定谱指数还是逐期拟合；低 TS 日使用带误差的似然估计、profile likelihood 或上限，不能把上限当普通测量值。
4. 响应系统学：period 边界前后做 Crab 稳定性检查，并评估 1.07/1.04 分支、时间标定、效率和水质变化造成的假周期。
5. QPO 统计量：至少使用带测量误差的 generalized Lomb-Scargle，并同步计算采样窗口谱。
6. 零假设：白噪声显著性不够；需预先选定红噪声/弯折幂律 PSD，并用保持采样和误差结构的模拟校准局部与全局显著性。
7. 多重试验：频率范围、源数、能段数、时间尺度数和候选筛选步骤都计入 trials factor。
8. 稳健性：改变时间分箱、能段、质量阈值、低 TS 处理和 period 边界后，候选周期应保持；分段数据需显示相位/频率一致性。
9. 报告措辞：只有通过响应确认、全局显著性和稳健性检验后才能称为 QPO evidence；否则只能称为 candidate 或 periodicity hint。

## 项目闸门

| 阶段 | 状态 | 通过标准 |
|---|---|---|
| 公开资源可访问 | 通过 | 程序、DataConfig、DGE、日图和 83 组 MC 可读 |
| 三日接口 smoke | 通过 | 3/3 生成非空 `ParRes.yaml`，日志有合理 `Tobs`，无输入/响应错误 |
| period 响应契约 | 通过 | 使用 v1.0 每 bin 官方 LC DataConfig 的 T001-T083 response slot |
| Crab 时间稳定性 | 未开始 | period 边界无未建模跳变，系统误差有量化 |
| 全量 2-day 拟合 | 已就绪 | 已生成可追踪 HTCondor 模板；提交前固定源样本 |
| QPO 统计分析 | 未开始 | 红噪声模拟、窗口谱、全局 trials 和稳健性检查齐全 |
| 最终报告 | 未开始 | 方法、数据谱系、失败项、统计限制和可复现元数据完整 |

## 旧结果定位

旧 HTML 报告位于 Mac 的 `/Users/luoji/Documents/projects/QPO/reports/agn_wcda_weekly_survey_report.html`。它是 10 个源、229 个周 bin 的 quick-look survey，不应作为最终 QPO 检测报告引用。新报告应在上述科学闸门全部通过后另行生成，并明确保留旧报告为历史基线。
