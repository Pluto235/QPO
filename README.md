# QPO

Mrk 421、Mrk 501 以及其他 AGN 的光变曲线和 QPO 分析项目。仓库同时包含
Fermi/WCDA 数据处理、周期性分析、模拟、报告和一个可以单独给师弟师妹使用的
通用 CWT/WWZ 工具。

## 从一条 LC 开始

新用户只需要准备一个 CSV：

```csv
time,flux,flux_err
58000.0,1.23,0.10
58001.0,1.18,0.10
```

在项目根目录、`py310` 环境中运行：

```bash
PYTHONPATH=src python -m qpo.cli analyze input.csv \
  --outdir results/my_source \
  --label "My source" \
  --n-surrogates 1000
```

命令会完成 QC、CWT、WWZ、AR(1) 显著性和整合图，并写出：

```text
results/my_source/
├── integrated.png       # LC、CWT、WWZ、两个 global spectrum 的整合图
├── candidates.csv       # 候选峰和 FAP
├── significance.csv     # WWZ surrogate 显著性结果
├── qc.json              # 清洗、缺测和采样统计
├── manifest.json        # 完整参数、seed 和软件版本
├── cwt.npz              # CWT 时频矩阵和 global spectrum
└── wwz.npz              # WWZ 时频矩阵和 global spectrum
```

完整说明见 [`docs/qpo_toolkit_quickstart.md`](docs/qpo_toolkit_quickstart.md)，
可直接运行的样例在 [`examples/`](examples/)。

## 仓库结构

```text
QPO/
├── data/
│   ├── raw/             原始 Fermi/WCDA 数据（通常不随代码分发）
│   ├── processed/       光变、对齐、周期性和报告中间结果
│   └── simulations/     WCDA 等模拟结果
├── src/
│   ├── qpo/             通用 CSV → CWT/WWZ → 显著性 → 作图工具
│   ├── pipeline/        项目特定的 Fermi、WCDA 和 survey 入口脚本
│   ├── methods/         可复用方法和 vendored Emmanoulopoulos 实现
│   ├── simulation/      模拟生成脚本
│   └── utils/            路径、源注册表和数据辅助函数
├── examples/             通用工具的最小 CSV 和运行脚本
├── tests/                 自动化测试
├── docs/                  分析说明、数据约定和论文资料
├── reports/               HTML/Markdown 分析报告和导出图片
├── notebooks/             探索、检查和展示；核心逻辑不放在这里
├── work/                  运行日志、Slurm/Condor 脚本和交接记录
├── prestation/            PPT、Keynote 和演示素材
├── qposim/                喷流/QPO 模拟及相关论文资料
└── archive/               旧入口、兼容代码和历史产物
```

通用工具内部结构：

```text
src/qpo/
├── io.py             CSV 读取、字段检查、重复时间合并和 QC
├── sampling.py       CWT 规则网格、短缺口插值和周期网格
├── analysis.py       CWT/WWZ 调用层
├── significance.py   AR(1) surrogate 和 FAP
├── plotting.py       5 面板整合图
├── pipeline.py       Python API 和端到端流程
└── cli.py            命令行入口
```

## 重要约定

- CWT 使用规则时间网格；不超过两个中位 cadence 的短缺口插值，长缺口保留屏蔽记录。
- WWZ 使用原始观测时间，不对整条 LC 做全局插值。
- 默认 CWT 显著性使用 PyCWT AR(1) 理论参考，WWZ 使用 AR(1) Monte Carlo surrogate。
- 默认随机种子为 `20260922`，写入 `manifest.json`，可用 `--seed` 覆盖。
- `pointwise`、`local-window` 和 `global FAP` 分开记录，不自动合并跨方法或跨源的 trial correction。
- 原始大数据和大量生成结果应放在 `data/`，代码、配置、文档和少量示例结果才进入 Git。

## Other project entry points

- `python src/pipeline/fermi_month.py`：Fermi 月尺度 fermipy 流程。
- `python src/pipeline/wcda_weekly.py --output data/simulations/wcda/wcda_weekly_sims_full.h5 --nsim 10000 --ncores 48 --chunk 256 --overwrite`：WCDA 周尺度模拟。
- `PYTHONPATH=src python -m pytest -q tests/test_qpo_toolkit.py`：通用 QPO 工具测试。
- `PYTHONPATH=src python -m pytest -q src/methods/emmanoulopoulos/emmanoulopoulos/test`：Emmanoulopoulos 方法测试。

Legacy compatibility directories have been archived under `archive/compat/`.
