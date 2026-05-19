# 项目总览

## 研究目标

本项目用于研究 Mrk 421 在 Fermi-LAT 与 LHAASO-WCDA 光变曲线中是否存在类 QPO 现象，并尽量保持月尺度与周尺度分析链路可复现、可追溯。

## 当前文件结构

```text
QPO/
├─ README.md
├─ AGENTS.md
├─ data/
│  ├─ raw/
│  │  ├─ fermi/
│  │  └─ wcda/
│  ├─ processed/
│  │  ├─ fermi_month/
│  │  ├─ fermi_week/
│  │  └─ wcda_week/
│  └─ simulations/
│     └─ wcda/
├─ src/
│  ├─ pipeline/
│  ├─ simulation/
│  ├─ methods/
│  └─ utils/
├─ notebooks/
├─ work/
└─ archive/
   ├─ compat/
   ├─ docs/
   ├─ legacy_methods/
   ├─ legacy_outputs/
   ├─ notebooks/
   └─ bundles/
```

## 各部分主要内容

### `data/`

- `data/raw/fermi/`：Fermi 月尺度分析所需的原始事件文件、空间文件和周光变输入。
- `data/raw/wcda/`：LHAASO-WCDA 周光变 CSV 原始输入。
- `data/processed/fermi_month/`：Fermi 月尺度 `fermipy` 处理后的 ROI 和光变结果。
- `data/processed/fermi_week/`：已经清洗或筛选后的 Fermi 周尺度产品。
- `data/processed/wcda_week/`：WCDA 周尺度处理中间结果。
- `data/simulations/wcda/`：WCDA 周尺度模拟生成的 HDF5 文件。

### `src/pipeline/`

- `fermi_month.py`：Fermi 月尺度主入口，负责加载配置、完成 ROI 拟合、写出 ROI 文件，并生成月光变。
- `fermi_month_config.yaml`：`fermi_month.py` 使用的分析配置文件。
- `wcda_weekly.py`：WCDA 周尺度模拟的统一命令入口，负责接收 CLI 参数并调用模拟模块。

### `src/simulation/`

- `generate_wcda_weekly_sims.py`：WCDA 周光变模拟的核心脚本，负责读取 CSV、清洗数据、构造观测光变、并行生成 Emmanoulopoulos 模拟并写入 HDF5。

### `src/utils/`

- `project_paths.py`：统一管理项目根目录、数据目录、归档目录等路径常量，避免 notebook 和脚本里散落硬编码路径。

### `src/methods/`

- `emmanoulopoulos/`：移植并封装的 Emmanoulopoulos 光变模拟方法，供 WCDA 周尺度模拟和相关检验调用。

### `notebooks/`

- `mkn421_fermi_month.ipynb`：Fermi 月尺度分析与结果展示。
- `mkn421_fermi_week.ipynb`：Fermi 周尺度光变筛选、时段检查与辅助分析。
- `mkn421_wcda_week.ipynb`：WCDA 周尺度光变构建、模拟检验和时频分析。

### `work/`

- `overview.md`：项目总览与当前工作说明。
- `log.md`：按时间记录的工作日志。

### `archive/`

- `compat/`：已下线的兼容目录与历史入口。
- `docs/`：旧 README、说明文档和历史工作提示。
- `legacy_methods/`：旧方法实现、第三方移植代码和历史实验工程。
- `legacy_outputs/`：早期 Fermi 输出和参数文件等旧结果。
- `notebooks/`：归档的探索性 notebook。
- `bundles/`：历史打包文件。

## 当前推荐工作流

1. 使用 `src/pipeline/fermi_month.py` 运行 Fermi 月尺度主流程。
2. 使用 `notebooks/` 中的周尺度 notebook 检查 Fermi 和 WCDA 的光变与时频结果。
3. 使用 `src/pipeline/wcda_weekly.py` 生成 WCDA 周尺度模拟结果。
4. 将可复用逻辑放在 `src/` 中，将旧实验、旧输出和历史入口移到 `archive/`。

## 代码职责说明

- `src/pipeline/fermi_month.py`：负责月尺度 Fermi 分析的执行顺序，核心动作包括切换到项目根目录、初始化分析目录、运行 `fermipy` 拟合、保存 ROI，再重新载入 ROI 生成月光变。
- `src/pipeline/wcda_weekly.py`：负责把命令行参数传给 WCDA 模拟主脚本，保持对批处理环境和 Slurm 的友好性。
- `src/simulation/generate_wcda_weekly_sims.py`：负责周尺度模拟的完整数据流，从 CSV 读入到观测序列清洗，再到并行生成模拟光变和写入 HDF5。
- `src/utils/project_paths.py`：负责路径收敛，统一定义 `PROJECT_ROOT`、`data/`、`archive/`、`notebooks/` 等常用目录。
- `src/methods/emmanoulopoulos/`：负责提供光变模拟算法本体和其依赖接口，是周尺度模拟与显著性检验的基础方法层。
- `notebooks/`：负责展示、检查和验证，不承载核心可复用计算逻辑。

## 当前状态

- 仓库已经拆分为 `data/`、`src/`、`notebooks/`、`work/` 和 `archive/` 五类主区域。
- 月尺度 Fermi 结果已放在 `data/processed/fermi_month/`。
- Fermi 与 WCDA 的周尺度输入已放入 `data/` 目录下对应位置。
- 原根目录下的兼容目录已经归档到 `archive/compat/`。

## 后续建议

- 继续把 notebook 中的路径硬编码替换为 `src/utils/project_paths.py` 提供的常量。
- 补充少量冒烟测试，覆盖路径解析和 WCDA CSV 解析。
- 旧的 Fermi 输出是否长期保留在 `archive/legacy_outputs/`，可以在后续再单独决定。
