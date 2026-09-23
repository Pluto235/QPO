# QPO

从一条标准 CSV 光变曲线运行 CWT、WWZ 和显著性分析的工具。项目特定的
Fermi/WCDA 脚本仍在 `src/pipeline/`，通用入口在 `src/qpo/`。

## 从一条 LC 开始

新用户只需要准备一个 CSV：

```csv
time,flux,flux_err
58000.0,1.23,0.10
58001.0,1.18,0.10
```

先根据 `environment-py310.yml` 安装依赖；在项目根目录激活该环境后运行：

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
├── data/                 已有项目数据和分析结果
├── src/
│   ├── qpo/             通用 CSV → CWT/WWZ → 显著性 → 作图工具
│   ├── pipeline/        项目特定的 Fermi、WCDA 和 survey 入口脚本
│   ├── methods/         可复用方法和 vendored Emmanoulopoulos 实现
│   ├── simulation/      模拟生成脚本
│   └── utils/            路径、源注册表和数据辅助函数
├── examples/             最小 CSV 和运行脚本
├── tests/                自动化测试
├── docs/                 输入说明、分析指南和项目参考资料
└── work/slurm/           通用 Slurm 运行模板
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

- CWT 使用规则时间网格；短缺口（最多两个中位 cadence）插值。当前 PyCWT 后端在计算时用序列均值填充长缺口，`qc.json` 记录被填充的 bin；长缺口附近的功率需谨慎解释。
- WWZ 使用原始观测时间，不对整条 LC 做全局插值。
- 默认 CWT 显著性使用 PyCWT AR(1) 理论参考，WWZ 使用 AR(1) Monte Carlo surrogate。
- 默认随机种子为 `20260922`，写入 `manifest.json`，可用 `--seed` 覆盖。
- `pointwise`、`local-window` 和 `global FAP` 分开记录，不自动合并跨方法或跨源的 trial correction。
- 原始大数据和大量生成结果放在 `data/` 或本地输出目录，不放进 toolkit 提交。

## Slurm 模板

激活包含项目依赖的环境后，可把一条 CSV 提交到 Slurm：

```bash
sbatch work/slurm/qpo_toolkit.sbatch examples/mkn421_example.csv \
  results/mkn421_slurm --n-surrogates 1000
```

模板以仓库根目录为工作目录；可用 `QPO_PYTHON` 指向指定环境中的 Python。

## Other project entry points

- `python src/pipeline/fermi_month.py`：Fermi 月尺度 fermipy 流程。
- `python src/pipeline/wcda_weekly.py --output data/simulations/wcda/wcda_weekly_sims_full.h5 --nsim 10000 --ncores 48 --chunk 256 --overwrite`：WCDA 周尺度模拟。
- `PYTHONPATH=src python -m pytest -q tests/test_qpo_toolkit.py`：通用 QPO 工具测试。
- `PYTHONPATH=src python -m pytest -q src/methods/emmanoulopoulos/emmanoulopoulos/test`：Emmanoulopoulos 方法测试。
