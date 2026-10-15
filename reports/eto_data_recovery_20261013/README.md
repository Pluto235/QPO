# ETO 数据缺口与恢复核查

核查日期：2026-10-13（Asia/Shanghai）。ETO 项目：`/mnt/newdisk/shijie/QPO`。本次只核查、编写报告，没有恢复业务数据、重算分析或提交作业。

## 结论

**继续做已有光变的 QPO 分析所需数据大部分已经保住；从事件或天图重新拟合所需的输入和过程记录尚不完整。** 本机与新 ETO 的 `data/`、`results/` 共 2,091 个文件、190,389,284 字节逐一 SHA256 一致。这个结论只证明本机现有内容已恢复，不证明旧 ETO 的全部内容都已找回。

缺口分为三类：Fermi 原始分析输入需另找副本或重新下载；IHEP 仍保存的配置、拟合元数据和脚本可以直接取回；ROI、分箱拟合缓存、模拟库等派生数据可以按需重算。官方 WCDA 大型上游资源仍放在 IHEP，不必因 ETO 坏盘就全部复制。

## 已保住的分析数据

| 数据 | 本机及新 ETO 的现状 | IHEP 核对结果 |
| --- | --- | --- |
| WCDA weekly counts | 10 源，每源 264 行 | 8 源位于 `QPO/data/wcda_week/`；Mrk 421/501 位于 `QPO/results/`，内容有本地匹配副本 |
| WCDA strict weekly flux | 10 源，每源 229 行；主目标在 `data/processed/wcda_week/`，另 8 源在 `results/flux_strict_agn_week/` | strict 输出仍保留；另有较早的 `results/flux/` 同名版本，不能按文件名直接覆盖 |
| 官方 WCDA 2-day/8-day LC | 11 源 × 两种分箱，共 22 份；每源分别 803/200 行 | 全部 22 份与 IHEP 官方 release 逐文件 SHA256 相同 |
| 四控制源 2-day LC | Crab、IC443、Blank175、J1952 各 803 行；导出包及原始导出 CSV 也在 | 四源包的 CSV、模型与校验文件均有相同内容副本 |
| WCDA daily 数据 | 4 份，包括两主目标各 1,607 行 daily flux，以及 Mrk 421 的两份 daily counts | 本次保留本机版本；没有把所有历史 daily 产品认定为同一 release |
| Fermi 2-day/8-day LC | Mrk 421/501 共 4 套 CSV/FITS/PNG，分别 803/200 行 | 本机 → ETO 已校验；无需重新拟合就能继续现有时序分析 |
| Fermi weekly | Mrk 421 的 `Mrk421_Fermi_weekly_TSge9_MJD.csv` 存在 | Mrk 501 对应 legacy weekly CSV 当前缺失 |
| 谱指数 A/B/C 实验 | `spectral_abc_20260908/lightcurves.csv` 有 1,200 行及分析结果 | 该 CSV 与 IHEP r2 作业结果 SHA256 相同 |
| 对齐与周期结果 | 79 份 aligned CSV；periodicity 下 191 份 NPZ、114 份 CSV，以及图片 | 已恢复到新 ETO；仅统计现存文件，未宣称每条历史流程的全部产物齐全 |

路径均相对 QPO 项目根目录。counts、flux、对齐序列、周期结果都是派生数据；放在 `data/raw/` 中的 CSV 或 `_original.csv` 表示收到的原始导出版本，并不等于探测器原始事件。

## 当前缺少什么

| 缺口 | 数据性质 | 如何恢复；影响 |
| --- | --- | --- |
| Fermi PH/FT1 事件 FITS | 最底层科学分析输入，已由仪器重建 | 另找副本或按原查询条件重新下载；不能从光变 CSV 反推事件 |
| Fermi SC/FT2 spacecraft FITS | 独立姿态、轨道与时间信息 | 与光子文件分别恢复；不能从 FT1 或 flux CSV 推导 |
| Fermi 两份指定弥散背景模型 | 外部模型 | 当前 ETO `FERMI_DIFFUSE_DIR` 为空；`/opt/anaconda3` 内未找到两个指定背景文件。重新取回匹配版本；IRF、星表及 Fermitools 环境尚未独立核查，不能据此认定缺失 |
| `data/config/` 的两份 source-model YAML | 谱模型、DGE 政策和拟合来源记录 | IHEP 有 `official_qpo_source_models.yaml`（19,530 B）及 `official_qpo_source_models_dge_policy_r5_collected.yaml`（21,837 B）；优先原样备份，保留两者区别 |
| 官方 release 的完整 handoff/metadata | provenance，不是原始观测 | IHEP `results/WCDA_official_LC_2day_8day_20260817_handoff/` 有 SOURCE_MODELS、QUALITY_FLAGS、2/8-day fit manifests 等，本机缺少内容相同副本；直接取回，无需重算 |
| WCDA 的逐 bin Fit/ParInit/ParRes/log | 拟合中间结果及审计证据 | IHEP 的官方 2/8-day、strict flux、谱指数及 profile pilot 作业目录仍在；已抽查 9 个拟合的四类文件可读，未逐一验证所有作业输出 |
| `MakeLC/` 与 IHEP 侧拟合包装代码 | 可复现流程的代码依赖 | 新 ETO 没有 MakeLC；IHEP 有 standard_flux_lc、annual_controls、ic443、merge/read/subjobs 等。仅重做 CWT/WWZ 不需要它；重做光变拟合时应保存版本 |
| J1952 的完整 provenance 压缩包 | 配置、日志及诊断产物 | IHEP exports 有 `J1952_2day_20261011_provenance.tar.gz`，12,826,898 B；可直接备份。本机已有四源 LC 包，但没有这份完整过程包 |
| Fermi 月尺度目录、ROI 与分箱缓存 | 事件分析产生的派生数据 | `data/processed/fermi_month/` 缺失；`fermi_wcda_20260818` 仅保留最终产品及部分 provenance，没有 ROI/chunk 缓存。原始输入和相同环境齐备后可重算；当前不必为现成 LC 的 QPO 分析重算 |
| Mrk 501 legacy Fermi weekly LC | 派生光变 | 当前只有 2/8-day 产品；可从恢复后的事件重新做 7-day likelihood。不能把 8-day flux 直接重采样成等价 7-day 拟合 |
| `data/simulations/wcda/` HDF5 模拟库 | 从观测 LC 和噪声模型生成的派生数据 | 默认输入 CSV 仍在；可用 `src/pipeline/wcda_weekly.py` 重新生成。保存输入、参数、随机种子及软件版本；不能保证所有历史模拟逐字节一致 |

Fermi 当前代码明确期待的路径：

```text
data/raw/fermi/ft1.txt                         # monthly 输入清单，当前不存在
data/raw/fermi/ft2.txt                         # monthly 输入清单，当前不存在
data/raw/fermi_wcda_20260818/mkn421/L260818011233F357373F66_PH*.fits
data/raw/fermi_mkn501/L260703025740F357373F96_PH*.fits
data/raw/fermi_wcda_20260818/shared/L260818011232F357373F77_SC00.fits
```

这些新光变流程所需原始目录当前均不存在。`ft1.txt`/`ft2.txt` 本身是文件列表，可以重建；它们指向的事件和 spacecraft FITS 才是必须找回的输入。现存 `data/raw/fermi/oq334/` 只是另一个目标的 CSV 资料，不能替代 Mrk 421/501 的事件输入。已检查的 IHEP QPO 数据/结果目录没有提供这些 Fermi 原始 FITS；未搜索用户所有其他存储。

Fermi 光子和 spacecraft 数据可按位置、时间、能量重新检索：[NASA FSSC 数据入口](https://fermi.gsfc.nasa.gov/ssc/data/)。指定的 `gll_iem_v07.fits`、`iso_P8R3_SOURCE_V3_v1.txt` 应从匹配的官方模型来源恢复：[LAT 背景模型](https://fermi.gsfc.nasa.gov/ssc/data/access/lat/BackgroundModels.html)。重新查询可能得到不同文件名，现有严格文件名匹配也需适配。

## IHEP 上的原始数据与上游资源

| 层级 | 已核实的位置或内容 | 能否仅凭下游 LC 生成 |
| --- | --- | --- |
| 探测器原始文件 | `/eos/lhaaso/ai/wcda/raw/2022/0101/` 可列出 23 项，样例 `Esg20220101_00.root`；未审计全时段 | 不能。也未证明 QPO 当前所需全时段的探测器 raw 均齐全 |
| 官方重建日天图 | `/eos/lhaaso/rec/wcda/publish/skymap/Cod/DailySkyMap/`，列出 1,592 个 ROOT 文件名 | 不能由 LC 反推；属于重建后的高层观测输入，不是探测器 raw |
| 已合并周天图 | `/eos/user/l/liushijie/Skymap/2021-03-08_2026-03-29_week/`，264 个 ROOT 文件名 | 可从匹配的上游天图重做 merge；当前可直接复用 |
| 官方 LC 分箱天图 | 1,053 份 2/8/32-day YAML 所引用的 Mapfile | 1,052/1,053 个路径存在且可读；可用它们重做流强拟合，无需回到探测器 raw |
| 仪器 MC | `/eos/lhaaso/rec/wcda/publish/simulation/Cod/MCGammaPeriod/`，83 period、166 个 rec/corsika ROOT 文件名 | 不能从观测数据本身推导，应保存官方模拟与标定版本 |
| 官方 response/Simufile | 配置引用 83×2 个 Responsefile、83×2 个 Simufile，路径均存在且可读 | 属于仪器标定/模拟输入；光变不能替代它们 |
| 软件与 DGE 模板 | `public/v1.0/Src_Main`、`public/DGE_Template/gll_dust_process_Eqm.root` 可读 | 需要单独保存；当前 Src_Main SHA256 与 20260817 release 一致 |

本次对 1,385 个“配置字段—资源 URI”组合做挂载路径存在/读取权限检查：1,053 Mapfile + 166 Responsefile + 166 Simufile。没有对大型 ROOT 内部对象、物理质量或全部内容做读取校验。2-day/8-day 分箱天图的文件体积分别约 541.5/145.7 GB（十进制），响应两分支合计约 359.5 MB；应先恢复轻量配置与过程记录，不必立即搬运所有天图。

数据链路是：探测器 raw 经重建和标定成为官方天图；counts 从天图提取；flux 由天图或 counts 配合响应、曝光和谱模型拟合得到；aligned、CWT/WWZ、显著性与报告再从光变生成。**只有 raw 目录并不自动满足重新生成物理 flux 的全部条件，响应、模型和曝光同样必要。**

## 不能误判为本次坏盘丢失的事项

- `LC0687` 的 2-day `Dura0687_73_bkgJ2000.root` 目前在 IHEP 不存在。20260817 summary 已记录共同失败 bin LC0687 和 `Src_Main_exit_139_reproduced`；本次只能证明目前路径缺失，不能证明当年 exit 139 的唯一原因。保留失败标记，不擅自补零。
- 1,053 份逐 bin YAML 与 IHEP 当前版本全相同；master `LCData_20210305_20250731.yaml` 的本机旧快照和当前官方文件 SHA256 不同。当前官方 master 与 20260817 summary 记录一致。恢复时应并存版本，不能静默覆盖旧快照。
- J1952 作业目录是指向 `/tmp/liushijie_QPO_J1952_2day_20261011` 的符号链接；在本次 `lxlogin002` 上目标不存在。`/tmp` 可能依赖登录节点，不能据此判定所有节点都已丢失；已确认完整 provenance 压缩包仍可打开并列出 11,180 个成员。
- 20260817 点估计 LC、早期 strict flux、另一条 source-specific/DGE-policy/profile pilot 链路并非同一数据产品。IHEP 的 profile pilot 仍在，但未发现可据以宣称“全样本 profile LC 已完成”的证据；不把未完成工作列作坏盘丢失。
- 旧 Fermi runner、Slurm 文件和现存 `fermipy_config.yaml` 中仍有 `/mnt/mydisk/...` 路径。它们属于迁移适配问题，和数据文件缺失分别处理。本次没有修改。

## 恢复顺序

1. **先保全不可由最终 LC 反推的轻量记录**：两份 source-model YAML、官方 release handoff、拟合 manifests、ParRes/log、MakeLC 版本和 J1952 provenance 包。直接从 IHEP 备份，比重算更可靠。
2. **若继续现有 QPO 分析**：复用已恢复的 WCDA/Fermi LC、aligned 和周期产物；仅对新需求生成模拟，不为恢复工作全量重新拟合。
3. **若重做 Fermi 光变**：先恢复 PH/FT1、SC/FT2、背景模型和环境，再生成文件列表、ROI、chunk/LC；同时处理旧绝对路径和严格文件名匹配。
4. **若重做 WCDA 光变**：优先在 IHEP 用已有官方 DataConfig、天图、response 和 Src_Main 拟合，再向 ETO 输出小型 LC/provenance；对 LC0687 单独审计。
5. **只有改变重建方案时才回到探测器 raw**。批量重建/merge/拟合应通过 IHEP 调度，不能在登录节点运行。

## 证据与边界

- `local_inventory.json`、`eto_inventory.json`、`local_eto_comparison.json`：两端 data/results 完整文件哈希与差异。
- `eto_missing_inputs.json`：新 ETO 上九个所需输入/目录的缺失状态及 FERMI_DIFFUSE_DIR。
- `local_series_summary.json`：现存光变的行数、列名及已有状态字段统计。
- `ihep_inventory.json`、`ihep_local_content_matches.json`：IHEP 189 个文件记录、28 个作业目录状态及与本机的内容匹配。
- `ihep_public_dependencies.json`：1,054 份配置文件、1,385 个资源引用和软件/DGE 状态。
- `ihep_resource_samples.json`：日图、MC、周图文件名统计，9 个拟合样本的配置/结果/日志哈希，J1952 压缩包目录检查。
- 历史依据：`work/cross_environment_sync_2026-06-12.md` 曾记录旧 ETO 约 24 GB，包含未入 Git 的 FITS/月尺度产品；`work/log.md`、`work/ihep_official_lc_handoff.json` 和 IHEP release summary 提供产品谱系。

旧盘不可读取且没有损坏前的完整文件清单，因此本报告是“已验证的当前缺口及可恢复来源”，不是全部丢失文件的逐项盘点。IHEP 全作业递归体积扫描因元数据开销在 240 秒超时，改用轻量 manifests、目录检查和抽样；未全量验证每个 ParRes/日志、全时段 raw、ROOT 对象或科学结果。没有下载安装依赖、启动分析、传输大数据或提交作业。
