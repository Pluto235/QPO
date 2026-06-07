# LHAASO AGN QPO Survey 数据可获得性检查表

日期：2026-05-27

## 用途

这份检查表面向下一步 IHEP 侧拉数和本地接入，用来回答两个问题：

1. 每个候选源当前在本地仓库里已经有哪些数据产物。
2. 下一步去 IHEP 时，优先应该补哪些 WCDA / Fermi 输入。

状态说明：

- `present`：本地已经存在对应文件或目录。
- `missing`：按当前命名约定尚未发现对应文件。
- `n/a`：当前不作为该源默认输入要求。

## 汇总表

| Source ID | Label | Priority | WCDA week | WCDA day | Fermi week | aligned | periodicity | 下一步建议 |
|---|---|---|---|---|---|---|---|---|
| mkn421 | Mrk 421 | active | present | present | present | present | present | 可直接进入 survey 分析 |
| mkn501 | Mrk 501 | active | present | n/a | n/a | present | present | 可直接进入 survey 分析 |
| 1es1959p650 | 1ES 1959+650 | A | missing | n/a | n/a | missing | missing | 从 IHEP 补拉 WCDA 周光变 |
| 1es1727p502 | 1ES 1727+502 | A | missing | n/a | n/a | missing | missing | 从 IHEP 补拉 WCDA 周光变 |
| 1es2344p514 | 1ES 2344+514 | A | missing | n/a | n/a | missing | missing | 从 IHEP 补拉 WCDA 周光变 |
| bllac | BL Lacertae | A | missing | n/a | n/a | missing | missing | 从 IHEP 补拉 WCDA 周光变 |
| ngc1275 | NGC 1275 | B | missing | n/a | n/a | missing | missing | 从 IHEP 补拉 WCDA 周光变 |
| m87 | M 87 | B | missing | n/a | n/a | missing | missing | 从 IHEP 补拉 WCDA 周光变 |

## 分源检查

### Mrk 421 (`mkn421`)

- LHAASO 名称：`Markarian 421`
- 类型：`HBL`
- 优先级：`active`
- LHAASO 显著性：`221.38σ`；variability：`yes`
- 备注：Current main source with WCDA daily, WCDA weekly, Fermi weekly, aligned, and periodicity products.

| 项目 | 状态 | 期望路径 |
|---|---|---|
| WCDA weekly | present | `data/processed/wcda_week/LHAASO-WCDA_Mkn421_2021-03-08_2026-03-29_week.csv` |
| WCDA daily | present | `data/processed/wcda_day/LHAASO-WCDA_Mkn421_2025-03-29_2026-03-29_day.csv` |
| Fermi weekly | present | `data/processed/fermi_week/Mrk421_Fermi_weekly_TSge9_MJD.csv` |
| aligned weekly | present | `data/processed/aligned/mkn421/wcda_weekly_aligned.csv` |
| periodicity summary | present | `data/processed/periodicity/mkn421/periodicity_v1_summary.csv` |

建议动作：

- 本地输入已经到位，可以直接进入周期搜索和显著性评估。

### Mrk 501 (`mkn501`)

- LHAASO 名称：`Markarian 501`
- 类型：`HBL`
- 优先级：`active`
- LHAASO 显著性：`92.54σ`；variability：`yes`
- 备注：Current secondary source with WCDA weekly, aligned weekly, and periodicity products.

| 项目 | 状态 | 期望路径 |
|---|---|---|
| WCDA weekly | present | `data/processed/wcda_week/LHAASO-WCDA_Mkn501_2021-03-08_2026-03-29_week.csv` |
| WCDA daily | n/a | - |
| Fermi weekly | n/a | - |
| aligned weekly | present | `data/processed/aligned/mkn501/wcda_weekly_aligned.csv` |
| periodicity summary | present | `data/processed/periodicity/mkn501/periodicity_v1_summary.csv` |

建议动作：

- 本地输入已经到位，可以直接进入周期搜索和显著性评估。

### 1ES 1959+650 (`1es1959p650`)

- LHAASO 名称：`1ES 1959+650`
- 类型：`HBL`
- 优先级：`A`
- LHAASO 显著性：`11.33σ`；variability：`yes`
- 备注：Best first-wave HBL expansion target after Mrk 421/501.

| 项目 | 状态 | 期望路径 |
|---|---|---|
| WCDA weekly | missing | `data/processed/wcda_week/LHAASO-WCDA_1ES1959p650_2021-03-08_2026-03-29_week.csv` |
| WCDA daily | n/a | - |
| Fermi weekly | n/a | - |
| aligned weekly | missing | `data/processed/aligned/1es1959p650/wcda_weekly_aligned.csv` |
| periodicity summary | missing | `data/processed/periodicity/1es1959p650/periodicity_v1_summary.csv` |

建议动作：

- IHEP 侧优先导出或同步 WCDA 周尺度光变到 `data/processed/wcda_week/`。

### 1ES 1727+502 (`1es1727p502`)

- LHAASO 名称：`1ES 1727+502`
- 类型：`HBL`
- 优先级：`A`
- LHAASO 显著性：`12.08σ`；variability：`yes`
- 备注：High-significance HBL with reported variability; strong candidate for weekly-first survey.

| 项目 | 状态 | 期望路径 |
|---|---|---|
| WCDA weekly | missing | `data/processed/wcda_week/LHAASO-WCDA_1ES1727p502_2021-03-08_2026-03-29_week.csv` |
| WCDA daily | n/a | - |
| Fermi weekly | n/a | - |
| aligned weekly | missing | `data/processed/aligned/1es1727p502/wcda_weekly_aligned.csv` |
| periodicity summary | missing | `data/processed/periodicity/1es1727p502/periodicity_v1_summary.csv` |

建议动作：

- IHEP 侧优先导出或同步 WCDA 周尺度光变到 `data/processed/wcda_week/`。

### 1ES 2344+514 (`1es2344p514`)

- LHAASO 名称：`1ES 2344+514`
- 类型：`HBL`
- 优先级：`A`
- LHAASO 显著性：`9.33σ`；variability：`yes`
- 备注：Good HBL supplement with enough significance for first-pass WWZ/CWT checks.

| 项目 | 状态 | 期望路径 |
|---|---|---|
| WCDA weekly | missing | `data/processed/wcda_week/LHAASO-WCDA_1ES2344p514_2021-03-08_2026-03-29_week.csv` |
| WCDA daily | n/a | - |
| Fermi weekly | n/a | - |
| aligned weekly | missing | `data/processed/aligned/1es2344p514/wcda_weekly_aligned.csv` |
| periodicity summary | missing | `data/processed/periodicity/1es2344p514/periodicity_v1_summary.csv` |

建议动作：

- IHEP 侧优先导出或同步 WCDA 周尺度光变到 `data/processed/wcda_week/`。

### BL Lacertae (`bllac`)

- LHAASO 名称：`BL Lacertae`
- 类型：`IBL`
- 优先级：`A`
- LHAASO 显著性：`7.79σ`；variability：`yes`
- 备注：Includes rapid variability case reported on 2024-08-10 in the LHAASO AGN report.

| 项目 | 状态 | 期望路径 |
|---|---|---|
| WCDA weekly | missing | `data/processed/wcda_week/LHAASO-WCDA_BLLacertae_2021-03-08_2026-03-29_week.csv` |
| WCDA daily | n/a | - |
| Fermi weekly | n/a | - |
| aligned weekly | missing | `data/processed/aligned/bllac/wcda_weekly_aligned.csv` |
| periodicity summary | missing | `data/processed/periodicity/bllac/periodicity_v1_summary.csv` |

建议动作：

- IHEP 侧优先导出或同步 WCDA 周尺度光变到 `data/processed/wcda_week/`。

### NGC 1275 (`ngc1275`)

- LHAASO 名称：`NGC 1275`
- 类型：`FR I`
- 优先级：`B`
- LHAASO 显著性：`4.90σ`；variability：`yes`
- 备注：Radio-galaxy control target; also appears in the existing Fermi QPO literature notes.

| 项目 | 状态 | 期望路径 |
|---|---|---|
| WCDA weekly | missing | `data/processed/wcda_week/LHAASO-WCDA_NGC1275_2021-03-08_2026-03-29_week.csv` |
| WCDA daily | n/a | - |
| Fermi weekly | n/a | - |
| aligned weekly | missing | `data/processed/aligned/ngc1275/wcda_weekly_aligned.csv` |
| periodicity summary | missing | `data/processed/periodicity/ngc1275/periodicity_v1_summary.csv` |

建议动作：

- IHEP 侧优先导出或同步 WCDA 周尺度光变到 `data/processed/wcda_week/`。

### M 87 (`m87`)

- LHAASO 名称：`M 87`
- 类型：`FR I`
- 优先级：`B`
- LHAASO 显著性：`8.38σ`；variability：`yes`
- 备注：Week-level flare and duty-cycle case; useful as a non-blazar comparison source.

| 项目 | 状态 | 期望路径 |
|---|---|---|
| WCDA weekly | missing | `data/processed/wcda_week/LHAASO-WCDA_M87_2021-03-08_2026-03-29_week.csv` |
| WCDA daily | n/a | - |
| Fermi weekly | n/a | - |
| aligned weekly | missing | `data/processed/aligned/m87/wcda_weekly_aligned.csv` |
| periodicity summary | missing | `data/processed/periodicity/m87/periodicity_v1_summary.csv` |

建议动作：

- IHEP 侧优先导出或同步 WCDA 周尺度光变到 `data/processed/wcda_week/`。

