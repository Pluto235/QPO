# QPO Toolkit

一个面向光变曲线的周期性分析工具包：给它一份标准 CSV，它会完成质量检查、
CWT、WWZ、显著性分析、候选峰汇总和整合图生成。

```text
CSV light curve → QC → CWT + WWZ → significance → candidates + figure
```

## 快速开始

### 1. 准备环境

```bash
conda env create -f environment-py310.yml
conda activate py310
```

### 2. 准备 CSV

输入必须包含三列：

```csv
time,flux,flux_err
58000.0,1.23,0.10
58001.0,1.18,0.10
58002.0,1.31,0.11
```

约定：`time` 默认是 MJD；`flux` 和 `flux_err` 使用相同单位；误差必须为正。

### 3. 运行一条命令

```bash
PYTHONPATH=src python -m qpo.cli analyze input.csv \
  --outdir results/my_source \
  --label "My source" \
  --n-surrogates 1000
```

示例输入和运行脚本位于 [`examples/`](examples/)。

## 输出结果

每次运行写入一个独立目录：

```text
results/my_source/
├── integrated.png       # LC、CWT、WWZ 和 global spectrum 整合图
├── candidates.csv       # CWT/WWZ 候选峰
├── significance.csv     # WWZ surrogate 显著性结果
├── qc.json              # 输入清洗和采样质量统计
├── manifest.json        # 输入、参数、seed 和版本记录
├── cwt.npz              # CWT 时频矩阵、周期轴和 global spectrum
└── wwz.npz              # WWZ 时频矩阵、周期轴和 global spectrum
```

`integrated.png` 包含光变曲线、运行摘要、CWT 时频图、WWZ 时频图、CWT global
spectrum 和 WWZ global spectrum。

## 分析流程

### CWT

- 在中位采样间隔建立规则网格；
- 最多两个中位 cadence 的短缺口进行线性插值；
- 长缺口在 `qc.json` 中记录，并在 CWT 后端计算时用序列均值填充；
- 使用 Morlet wavelet 和 PyCWT AR(1) 理论参考。

### WWZ

- 使用原始观测时间，不对整条光变曲线做全局插值；
- 默认 `time divisions=80`、`frequency step factor=0.5`；
- 通过 AR(1) Gaussian Monte Carlo surrogate 计算 pointwise、local-window 和 global FAP。

显著性结果只针对当前输入、方法和搜索范围。不同源、不同方法或不同窗口之间的
trial correction 不会自动合并，使用者应在科学结论中明确比较范围。

## 常用参数

```text
--period-min FLOAT              搜索周期下限，默认自动估计
--period-max FLOAT              搜索周期上限，默认自动估计
--n-periods INT                 对数周期网格点数，默认 400
--n-surrogates INT              WWZ surrogate 数量，默认 1000
--seed INT                      默认 20260922
--workers INT                   surrogate 并行线程数
--wwz-time-divisions INT        默认 80
--wwz-freq-step-factor FLOAT    默认 0.5
```

## Python API

命令行调用的是同一个公开 API：

```python
from qpo.pipeline import analyze_lightcurve

result = analyze_lightcurve(
    "input.csv",
    "results/my_source",
    label="My source",
    n_surrogates=1000,
)
print(result.output_dir)
print(result.candidates)
```

## 代码结构

```text
src/qpo/
├── io.py             CSV 读取、字段检查、重复时间合并和 QC
├── sampling.py       CWT 网格、缺口处理和周期网格
├── analysis.py       CWT/WWZ 统一调用
├── significance.py   AR(1) surrogate 和 FAP
├── plotting.py       整合图
├── pipeline.py       Python API 和端到端流程
└── cli.py            命令行入口
```

仓库中保留的其他代码用于方法和计算环境支持：

```text
src/methods/       CWT/WWZ 基础实现及 Emmanoulopoulos 方法
src/pipeline/      原项目的 Fermi/WCDA 专用入口
src/simulation/    模拟生成脚本
src/utils/         项目路径和数据辅助函数
examples/          示例 CSV
tests/             toolkit 测试
docs/              使用说明和方法参考
work/slurm/        toolkit Slurm 模板
```

## 测试

```bash
PYTHONPATH=src python -m pytest -q tests/test_qpo_toolkit.py
```

## Slurm

```bash
sbatch work/slurm/qpo_toolkit.sbatch \
  examples/mkn421_example.csv results/mkn421_slurm \
  --n-surrogates 1000
```

模板默认使用集群环境中的 `python`；也可以设置 `QPO_PYTHON` 指定解释器。

## 当前边界

第一版只接受 CSV，不自动读取 FITS，也不自动识别任意列名。Emmanoulopoulos
代码保留在 `src/methods/` 供后续扩展；当前通用 CLI 默认使用 CWT 的 AR(1) 理论
参考和 WWZ 的 AR(1) Monte Carlo 流程。
