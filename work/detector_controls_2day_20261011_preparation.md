# 四源 WCDA 2day LC：下载与周期检测准备

记录日期：2026-10-12（Asia/Shanghai）。本次只下载、校验、整理数据及检查已有代码；未运行 CWT、WWZ、显著性模拟或提交远端任务。

## 数据位置与校验

- 远端包：`ihep:/workfs2/lhaaso/liushijie/QPO/exports/detector_controls_2day_four_sources_20261011.zip`。
- 原包和完整解压内容：`data/raw/wcda/detector_controls_2day_four_sources_20261011/`，共保留 ZIP 与 14 个包内文件，包括四份标准化 LC、四份 `_original.csv`、README、manifest、校验表及 J1952 模型文件。
- 标准化 LC 工作副本：`data/processed/wcda_2day/detector_controls_20261011/{Crab,IC443,Blank175,J1952}_2day.csv`。
- 本地清单：同目录 `inventory.csv` 与 `import_manifest.json`；后者记录远端来源、校验结果、每份 LC 的 SHA256 和未运行分析的状态。
- ZIP SHA256：`a8eb5aa92293dcc7feaa269e90ce0ae65f5fe655a19067b8a0bb65407554744f`，与远端一致；ZIP CRC、包内 13 个文件的 SHA256、四份原始 CSV 的 manifest SHA256 均通过。
- 所有路径由 `src/utils/project_paths.py` 的 `WCDA_RAW_DIR`、`WCDA_2DAY_DIR` 派生；现有路径模块已经定义 2day 目录，本次无需修改。

工作副本与包内标准化 CSV 字节一致，保留全部时间箱、缺失值和质量标记；未改名、重采样、插值、去趋势、补零或重新拟合。

| 源 | 总箱数 | basic valid_fit | 无效箱 | at_boundary=True 的有效箱 | E0 (TeV) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Crab | 803 | 800 | 3 | 1 | 10 |
| IC443 | 803 | 797 | 6 | 121 | 3 |
| Blank175 | 803 | 791 | 12 | 479 | 10 |
| J1952 | 803 | 802 | 1 | 259 | 3 |

四源时间坐标完全一致，MJD 59281.66666667–60885.66666667，严格每 2 天一个箱，无重复时间。`valid_fit` 只表示导出时的基础有效条件，不代表已经完成科学质量筛选。无效箱的 `flux/flux_err` 为空，`raw_flux/raw_flux_err` 保留导出前的值。

## 已找到的周期检测代码

| 位置 / 函数 | 功能及后续复用方式 |
| --- | --- |
| `src/methods/periodicity.py:163` `run_cwt` | PyCWT Morlet(6) CWT；内部标准化 flux，返回 power、period、COI、全局谱 gws；传入时间、flux 与周期上下限。 |
| `src/methods/periodicity.py:211` `clean_and_merge_weighted` | WWZ 前清理时间/flux/error，并按逆方差合并重复时间。 |
| `src/methods/periodicity.py:239` `run_wwz` | 调用 libwwz.wwt，返回时频图、全局平均谱及 ridge；可设置时间格点、频率步长和 decay constant。 |
| `src/pipeline/official_lc_qpo_analysis.py:124` `run_source` | 最接近本批数据的现有 2day/8day 编排：保存 aligned CSV、CWT/WWZ NPZ、图及显著性表。 |
| `src/pipeline/official_lc_qpo_analysis.py:297` `_assess_cwt` | PyCWT AR(1) 时间平均谱 95%/99% 参考；当前不输出 CWT local/global FAP。 |
| `src/pipeline/official_lc_qpo_analysis.py:353` `_assess_wwz` | AR(1) surrogate，同网格 WWZ、逐周期 95%/99% 参考及候选 ±10% 窗口 local FAP、全搜索频段 global FAP。默认 1000 次、固定随机种子。 |
| `src/pipeline/periodicity_v1.py` `_save_cwt/_save_wwz/_plot_cwt/_plot_wwz/_plot_periodicity_summary` | 可复用的结果保存与出图工具；入口本身主要面向旧 daily/weekly 数据。 |
| `src/pipeline/official_lc_xgm_window_qpo_analysis.py` | 子窗口分析参考，现有输入目录仍指向旧 official release。 |
| `src/pipeline/strict_flux_weekly_significance.py`、`src/pipeline/weekly_qpo_local_significance.py` | 旧 weekly 显著性实现参考，不能直接当成本批 2day 入口。 |
| `work/run_official_lc_qpo_wwz80_slurm.sh` | ETO 作业参数参考；固定旧源列表，本次未运行。 |

现有 official 流程的 2day 默认周期范围是 10–600 d，WWZ 时间分割默认 80，频率步长系数 0.5。这里只记录既有设置，尚未为本次四源确定搜索范围和检验方案。

## 后续接入时需要处理的事项

1. 新标准化文件使用 `mjd,flux,flux_err,valid_fit,...`；旧 official 清理器要求 `source,cadence,mjd,N0,N0_err,fit_status,response_period`。旧 CLI 还固定拼接 `wcda_2day/official_20260817/`，按 `LHAASO-WCDA_*_*_2day_flux.csv` 搜索。后续应增加独立的数据读取适配与四源入口，保留原数据及 provenance；直接给旧 CLI 改 `--input-root` 不足以接入本包。
2. 四源共有规则的完整时间网格，但筛去无效箱后存在缺口。当前 CWT 使用中位 cadence、按连续数组计算，未处理缺失箱间隔；正式运行前须明确规则网格/缺口处理，并使模拟采用一致采样。不能只删除无效行后默认当成连续 2day 数据。
3. `run_wwz` 的 flux_err 用于清理和重复时间合并；当前 `libwwz.wwt` 调用并未传入逐点测量误差，不能称为按误差加权的 WWZ。后续噪声模型须核对这一点。
4. 包内 README 明确：边界拟合误差不是普通高斯误差；Blank175 采用非负 flux 且大量箱落在零边界。`low_exposure/extreme_flux` 不自动剔除；Crab 的空 `error_reliable` 表示未知。后续应明确边界与质量标记策略，不能将 basic valid_fit 等同最终科学样本。
5. J1952 全部行标记 `diagnostic_unresolved_roi_residual`；随包 calibration gate 为 failed，存在 7 个相邻 ≥5σ ROI 残差像素。此 LC 为原全区间模型冻结、每箱仅 F0 自由的诊断数据；周期检验结果须保留这一限定。
6. flux 为差分归一化，单位 TeV^-1 cm^-2 s^-1；Crab/Blank175 的 E0=10 TeV，IC443/J1952 的 E0=3 TeV，不能直接比较绝对 flux。原始 TS 的定义因源而异，不应统一套 TS 阈值。
7. 后续 aligned 与周期产品分别使用 `ALIGNED_DIR / 'detector_controls_20261011' / <source_id>`、`PERIODICITY_DIR / 'detector_controls_20261011' / <source_id>`，大批显著性模拟优先 ETO。以上输出目录本次未生成。

## 环境检查

使用 `/Users/luoji/miniconda3/envs/py310/bin/python` 成功导入 numpy 1.26.4、pandas 2.3.3、matplotlib 3.9.2、scipy 1.15.3、pycwt 0.3.0a22、libwwz、`methods.periodicity` 与 `pipeline.official_lc_qpo_analysis`。仅检查 import，没有调用任何变换、显著性或流水线主函数。
