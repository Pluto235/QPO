# WCDA Cod v1.0 官方光变曲线：复现、生产与接手指南

更新：2026-10-15（Asia/Shanghai）。本次更新只修改教程；没有修改 pipeline、运行拟合、提交或重试任务。
本指南以当天 IHEP 脚本和公共配置的只读核查为依据；配置存在不代表其 ROOT 输入已全部验证可读。

## 0. 接手前先选路线

| 目的 | 入口 | 当前可做什么 |
| --- | --- | --- |
| 阅读/分析既有光变 | 20260817 handoff 数据包 | 核验校验和、模型和质量标志，追踪一个 bin，无需重拟合 |
| 复现 20260817 发布 | 路线 A：冻结旧版本 | 对齐旧代码、模型、逐 bin 配置、程序和环境后，在新目录复现 |
| 用扩展到 2026-01-31 的数据生成新光变 | 路线 B：新版生产 | 先修复版本选择与验证缺口；当前不能直接去掉 `--ids` 跑全量 |
| 新增源或改变模型 | 路线 B 的模型校准步骤 | 先校准模型并验证配置/输出一致性，不能自动套统一 Gamma=2.6 |
| IC443 等已有专用流程的复杂源 | 专用脚本及其操作记录 | 不绕过专用校准、TS 和 spool 检查 |

当前用户指令是“先不要跑任务”。接手本次工作的 agent 仅做文档和只读核查；
以下运行阶段是后续操作规范，不构成本次拟合、prepare、merge、提交、重试或清理授权。

## 1. Pipeline 做什么

```text
官方预合并 ROOT 天图 + 同 bin DataConfig/仪器响应/模拟输入
                          + 已验证的源及背景模型
                                      ↓
                        每源、每 bin 的 Fit.yaml / ParInit.yaml
                                      ↓
                         Src_Main（批量通过 HTCondor）
                                      ↓
                         out/ParRes.yaml + fit.log
                                      ↓
                      带质量标志和来源路径的光变 CSV
                                      ↓
                        Mac / ETO 上的周期与显著性分析
```

`Data_LC_XXXX.yaml` 是配置，不是天图；其 `Mapfile` 指向已经合并的 1/2/8/32 天 ROOT 天图。
生成光变时直接拟合这些天图，不重新做 DI merge，也不必回到探测器 raw。
同一时间 bin 的天图可供不同源拟合，但每个源需要相应的模型、ROI 和响应分支。
计数率 `excess/Tobs` 不等于物理通量；最终 N0 是指定谱模型和枢轴能量下的差分谱归一化。
本流程不自动生成可靠目标源 TS、profile likelihood、上限、系统误差或 QPO 结论。

## 2. 文件地图与权威入口

下列相对路径均相对于 IHEP `/home/lhaaso/liushijie/QPO`。

| 文件/目录 | 作用 |
| --- | --- |
| `MakeLC/standard_flux_lc.py` | 当前通用包装脚本：准备、分块执行、验证和合并；有第 5 节列出的限制 |
| `results/WCDA_official_LC_2day_8day_20260817_handoff/README.md` | 旧发布的使用说明、模型、字段和异常解释，接手首先阅读 |
| handoff 下 `code/standard_flux_lc.py` | 发布时脚本快照；不等于当前 MakeLC 版本 |
| handoff 下 `metadata/SOURCE_MODELS.csv`、`QUALITY_FLAGS.csv` | 旧发布的源模型摘要与异常行 |
| handoff 下 `metadata/fit_manifest_2day.csv`、`fit_manifest_8day.csv` | 旧发布逐 bin 来源、配置和结果路径 |
| handoff 下 `metadata/official_lc_20260817_summary.json`、`production_run_note.md` | 旧发布规模、状态和生产记录 |
| handoff 下 `CHECKSUMS.sha256` | 数据包完整性校验清单；不涵盖未打包的外部 ROOT 依赖 |
| `JOBs_official_lc_20260817_{2day,8day}/` | 旧生产任务目录，不覆盖；包含 fit_jobs.csv、提交文件、配置、结果及日志 |
| `results/official_lc_20260817_{2day,8day}/` | 旧生产最终 CSV |
| `/home/lhaaso/hushicong/public/v1.0/` | 持续变化的公共软件/配置目录，不是不可变 release |
| `MakeLC/ic443_lc.py` | IC443 专用校准、spool、收集流程 |
| `/workfs2/lhaaso/liushijie/QPO/JOBs_ic443_official_2day_20260922/IMPLEMENTATION.md` | IC443 历史后端和 TS 政策记录；不是新任务目录 |
| `data/config/official_qpo_source_models*.yaml` | 源模型/DGE 试验链记录；不能误称为已用于 20260817 固定谱形发布 |

逐 bin 示例：
`JOBs_official_lc_20260817_2day/fits/Mkn421/2days/LC0001/`。
先从 manifest 找到 `Fit.yaml`（数据、ROI、拟合选项）、`ParInit.yaml`（模型和自由参数），
再读 `out/ParRes.yaml`、`fit.log`，最后核对 CSV 的 LC0001 行。

## 3. 路线 A：复现 20260817 旧发布

### 冻结范围与模型

- 旧主配置：`config/Data/WCDA/Cod/LCData_20210305_20250731.yaml`。
- 主配置日期范围：2021-03-08 至 2025-07-31，83 个 response periods。
- 旧配置集合 1/2/8/32 天分别为 1607/803/200/50；20260817 发布只有 2/8 天结果。
- 发布含 10 个 AGN 加 Crab：每源 803 个 2-day bin、200 个 8-day bin。
- 10 个 AGN：单目标点源，PL，Gamma=2.6、E0=3 TeV，位置/谱形固定，仅归一化自由，DGE/KM2A 关闭。
- Crab：官方三分量模型，本体 LP、E0=10 TeV，仅本体归一化自由，两个 halo 固定。
- 这套固定模型是历史发布的定义，不是新源生产的通用默认；NGC1275/IC310 的单目标 ROI 结果还需考虑近邻混淆。

### 复现步骤

1. 先检查 handoff 的 CHECKSUMS，读取模型、质量标志、manifest 和发布脚本快照。
2. 保存逐 bin YAML、Fit/ParInit、程序/脚本/模型/配置哈希和环境信息，逐项与历史记录对照。
   handoff 并不包含所有天图、所有逐 bin 配置和全部日志；依 manifest 到原作业及公共资源补齐证据。
3. 使用独立的旧版本运行快照和新工作目录。只指定旧主配置文件名并不能冻结输入；
   仅限制旧 ID 也不能证明公共目录中同 ID 的 YAML 内容未变，必须比对冻结内容或哈希。
4. 后续获准运行时，先复现少量源/bin，覆盖首、中、尾及响应边界；Mrk421 的旧 2-day 例子是 LC0001/LC0402/LC0803。
   比较模型、响应、MJD、曝光、归一化、误差和日志状态，再决定是否全量重拟合。
5. 若无法恢复匹配的程序/配置/响应版本，应标记为“新版本重算”，不要宣称严格复现旧发布。

### 旧发布的验收基线

| cadence | 预期行数 | OK | NotOK | 输入失败 |
| --- | ---: | ---: | ---: | ---: |
| 2-day，11 源 | 8833 | 8800 | 22 | 11 |
| 8-day，11 源 | 2200 | 2199 | 1 | 0 |

旧 2-day LC0687 在 11 源上重复 exit 139，保留空通量及原因；不能要求每行都有成功 ParRes 才算“忠实复现”。
但也不能把旧失败标志自动应用于新输入：新运行应独立检查并记录。
旧 NotOK 多为低信号/边界拟合；保持原始记录，不能把它当可靠高斯测量或无休止重试到 OK。
Crab T014→T015 的历史 2-day 均值阶跃约 24%，不能把统计误差当总误差。

## 4. 路线 B：扩展数据的新生产

### 当前公共配置状态（2026-10-15 只读核查）

新主配置是 `config/Data/WCDA/Cod/LCData_20210305_20260131.yaml`：
`DateRange=[20210308,20260131]`，`Nperiod=91`。

| cadence | 旧集合数量 | 当前公共目录数量 |
| --- | ---: | ---: |
| 1-day | 1607 | 1791 |
| 2-day | 803 | 895 |
| 8-day | 200 | 223 |
| 32-day | 50 | 55 |

末尾 2-day LC0895 和 8-day LC0223 的配置引用 T091 响应。
这些是配置计数，不是成功拟合数量；未逐一验证新增 ROOT 内容或全部输入可访问性。
以后运行必须重新盘点，不能永久把此表当作公共目录的最新状态。

### 当前阻断项：先修复版本选择，再准备生产

当前脚本的 `OFFICIAL_LC_DATA_CONFIG_REL` 仍固定为旧主配置；
`discover_official_lc_bins()` 却扫描 `LC/<N>Days/` 中全部匹配 YAML，
不按主配置 DateRange/Nperiod 限定。直接省略 `--ids` 将把新 bin 纳入任务，
同时在 summary 中记录旧主配置哈希。禁止把这种混合来源的任务当作版本一致的新生产。

以下是待实现/验收要求，不是现有 CLI 功能：

1. 明确选择主配置与对应的冻结逐 bin 集合，验证 ID、时间范围、response period 和数量一致。
2. 确保任务 manifest 和 summary 记录真正使用的主配置、逐 bin YAML、响应及模型版本。
3. 检查新增时期的 Mapfile、两个响应分支和模拟文件可访问，并选择新增时期/边界 bin 做后续 smoke。
4. 对新源先完成全时段模型校准，检查初值稳定性、邻源、DGE、形态和残差；
   每个 LC bin 仅放开目标 F0，其余模型固定，误差属于该固定模型下的条件统计误差。
5. 修复或独立补齐第 5 节的模型元数据、质量和环境检查，验收后才进入分块生产。

只改文档数量、替换文件名、给旧命令去掉 `--ids` 或直接使用 `--program-root`，均不能替代上述检查。
当前 CLI 仅接受 2/8/32 天，1-day 需要另行扩展和测试，不能直接传 `--duration 1`。

## 5. 当前脚本限制：不要误认为已自动保证

| 位置/行为 | 当前实现 | 接手要求 |
| --- | --- | --- |
| 主配置与目录扫描 | 旧主配置常量 + 当前目录全量扫描 | 先修复版本选择和一致性验证；见路线 B |
| `--model-config` | 仅核对 Src0.Name，随后直接复制模型 | 不会自动冻结参数；核对恰有目标 F0 一个自由参数及背景状态 |
| 自定义模型的 CSV 元数据 | spectral_model/gamma/E0_TeV 从 SOURCES 读取，而非实际模型 | 必须与真实 ParInit/ParRes 一致；不能把新谱形或枢轴能量标成默认 PL/2.6/3 TeV |
| 源注册、ROI 与响应选择 | --sources 受 SOURCES 限制；ROI/响应选择依赖登记坐标 | 只换模型文件不足以改变完整源定义；检查登记坐标、ROI 中心和模型位置一致 |
| Crab 模型 | 默认仍从固定公共 OFFICIAL_LC_PROG 读取 | --program-root 不会自动冻结默认 Crab 模型；显式冻结并校验实际模型 |
| IC443 | 通用 prepare 和 merge 显式拒绝；--model-config 帮助文字不代表通用入口可运行 IC443 | 使用 ic443_lc.py，不绕过校准和收集检查 |
| 已有 ParRes | 非空就跳过，不比对代码/模型/配置变化 | 变更输入后用新目录；重提作业不等于重拟合 |
| prepare | 会写配置、manifest、runner；不是只读检查 | 不在旧工作目录重复 prepare，避免改了配置却保留旧结果 |
| merge 的 OK | 能解析 ParRes 即先置 OK，日志明确 NotOK 才降级 | 同时核对日志状态；missing_log/unknown 不能仅因 fit_status=OK 而通过 |
| root:// 输入 | 执行器不做真实远端存在性预检，直接视为可交给程序 | URI 存在于 YAML 不等于数据可读，应独立检查 |
| TS | 从日志 TS_total_W（或回退 TS）提取，仍输出单个 TS 字段 | 不当作已验证的目标源 TS；输出拆分尚待实现 |
| 时间 | 固定 MJD0=59280.6666666667，按编号和 cadence 推算 | 验证版本时间定义和 ID 连续性；不是读取每个 YAML 的真实日期边界 |
| provenance | summary 有程序/主配置哈希，但不覆盖完整模型与全部依赖 | 另存逐 bin/模型/脚本/响应标识、环境和校验清单 |

## 6. CSV 的正确读法与质量规则

- `mjd` 是 bin 中心；当前官方 LC 输出的 `date1/date2` 都是中心 MJD 向下取整对应日期，
  不是起止时间。名义边界可用 `mjd ± cadence_days/2`，不等同实际有效曝光范围。
- `N0=F0×F0_order`、`N0_err=F0_err×F0_order`，单位 TeV^-1 cm^-2 s^-1。
  必须保留 `E0_TeV` 和谱形；Crab 本体 10 TeV 的 N0 不能直接与 AGN 3 TeV 数值比较。
- `Tobs_s` 从日志中的目标方向曝光回收；它不是名义分箱宽度。需检查正值及异常低曝光。
- `response_period/slot/file`、`mapfile`、`lc_data_config`、`parres/log` 是追踪来源的关键字段。
- 可靠点估计至少需：输出可解析、日志明确成功、通量/误差有限、误差和曝光为正，
  并完成边界、自由参数漂移、低曝光高通量和响应期跳变检查。仅“文件存在”或“STATUS: OK”均不足。
- 执行失败、输入缺失、解析失败、NotOK、边界和低曝光应分开标记；保留完整时间网格和失败原因，绝不补零或伪造观测。
- 旧 TS_Src=0 的结果来自主拟合 ROI 统计量；多分量 ROI 尤其不能把它当目标源 TS。
  新交付应分别记录 TS_roi、TS_target、target_ts_status；没有验证过的目标源零假设拟合时 TS_target 留空。
  当前通用 merge 尚未输出这些新字段，不应声称已经实现。
- IC443 历史原版目标源移除拟合存在无自由参数导致的无效 TS；保留原始诊断，
  不把巨大负 TS 当物理结果。目标源 TS 和上限需要独立验证似然流程。
- 在相同时间网格检查 Crab 和 response period；系统学、样本筛选及周期搜索 trials 属于后续分析，
  不因光变成功导出就视为已完成。

## 7. 环境、存储和后续运行阶段

包装脚本目前通过 `bash -lc` 加载：
`/cvmfs/lhaaso.ihep.ac.cn/anysw/slc6_ia64_gcc73/external/envf.sh`。
worker 的 Python 由 `QPO_PYTHON` 指定，默认 `/usr/bin/python`；要在生成 runner 前核对选择和依赖。
冻结 Src_Main 二进制还不够，应记录环境脚本、ROOT/动态库及 Python 依赖版本。
Fit.yaml 的 WorkDir、相对 DataConfig/Outdir 及模型模板路径也必须指向同一冻结环境。

未来获准运行时按阶段执行，不把命令串成无人检查的一条链：

1. 冻结输入、解决第 5 节适用限制，选择新 work/result 目录；模型校准不通过则不生产。
2. 准备少量代表 bin；核查生成的 Fit/ParInit/manifest/runner，确认没有引用旧输出。
3. 少量 smoke 验证后再准备批量；bulk ROOT 拟合必须交 HTCondor，不能在登录节点执行。
4. 选择已验证后端：旧共享目录方案使用 should_transfer_files=NO；
   workfs2 工作节点只读、EOS POSIX 不稳定的历史环境使用 remote spool、节点 scratch 和结果传回。
   不将旧 max_materialize=80 直接套用到 remote spool 作业；参考 IC443 的分波次实现。
5. 核查 schedd、资源、队列状态、退出码、stderr、ParRes 和日志。非空 stderr 需解释，不能只按文件是否为空判定成败。
6. 计算故障单独重试并保留证据；科学边界拟合不反复重跑直到“成功”。
7. 验收后才 merge/collect 到新结果目录；merge 会写 CSV，不是只读验证。
8. 校验行数、ID/MJD/响应一一对应，保存异常清单和发布包，再交付 Mac/ETO。

本版不提供可直接执行的全量提交命令，以免误将旧接口用于扩展数据。
通用步骤对应的既有子命令是 prepare-official-lc、submit fit、validate、merge；
专用源的 prepare/submit/fetch/collect 依其实现。先确认路线和后端，再依据实际 --help 构造命令。

## 8. 新人/agent 的首次接手验收单（当前只读）

- [ ] 说明目标是旧发布分析、旧版复现、新版生产还是新增源；不要混用。
- [ ] 读 handoff README/SOURCE_MODELS/QUALITY_FLAGS/manifest，确认代码快照与当前脚本的区别。
- [ ] 选一个 Mrk421 bin，追踪 DataConfig→Mapfile/response→Fit/ParInit→ParRes/log→CSV。
- [ ] 写明日期、cadence、预期 bin 数、response periods、源模型及软件/配置版本。
- [ ] 清点实际输入与缺口；配置可读、ROOT 可读、拟合成功是三个独立状态。
- [ ] 指出适用的脚本限制及其解决方案；尤其不能遗漏旧主配置扫描新目录的问题。
- [ ] 列出未来新工作/结果目录与后端；不覆盖历史工作，不自动提交/重试/清理。
- [ ] 输出一份接手说明：已核实证据、待修复项、尚未检查的资源和下一步，不把计划写成完成状态。

后续交付至少包含：CSV、字段/模型说明、质量清单、完整 manifest、代码快照、
程序/模型/逐 bin 配置哈希、响应和模拟依赖标识、运行环境、原始日志索引及 CHECKSUMS。
大型 ROOT 可留在 IHEP，但应记录版本与 URI；只有最终 CSV 不能独立重建整条拟合链。

## 9. 版本记录

- 2026-10-15：拆分旧发布复现与扩展数据生产；记录当前 1791/895/223/55 配置、91 periods、
  新主配置日期范围；显式标注版本扫描、自定义模型、CSV 元数据、输出复用、质量、TS、环境和时间字段限制。
  只更新文档，未修复代码、逐一验证 ROOT、运行拟合或提交任务。旧教程保存同目录带时间戳备份。
