# LHAASO AGN QPO Survey 候选名单

日期：2026-05-27

## 目的

基于 [LHAASO-AGN-2026.pptx](/Users/luoji/Documents/projects/QPO/prestation/LHAASO-AGN-2026.pptx) 中截至 2025 年 7 月的 LHAASO AGN 样本，总结一份适合在当前 QPO 项目中继续扩展的候选名单。

这份名单的目标不是覆盖全部已探测 AGN，而是优先挑出：

- 在 LHAASO 中已经有较稳健探测的源；
- 报告中已体现出变异性、flare 或持续监测价值的源；
- 类型上尽量接近当前已开展的 `Mrk 421` 和 `Mrk 501`，便于复用现有 WCDA/Fermi/QPO 工作流；
- 同时保留少量不同类型 AGN 作为对照样本。

## 筛选原则

本次候选排序主要依据以下四点：

1. LHAASO 报告表中的探测显著性是否足够高。
2. 报告是否标注了 variability，或是否单独展示了 flare / rapid variability。
3. 是否属于 HBL / IBL / blazar，便于和 `Mrk 421`、`Mrk 501` 做同类扩样。
4. 是否值得纳入少量 radio galaxy 作为物理对照组。

## 推荐分层

### A 级：第一批主样本，优先开工

这些源最适合作为 `Mrk 421`、`Mrk 501` 之外的第一批 survey 主样本。

| Source | Type | LHAASO Sig(σ) | Variability | 推荐理由 |
|---|---|---:|---|---|
| 1ES 1959+650 | HBL | 11.33 | √ | 亮、已见变异，类型与 `Mrk 421/501` 非常接近，最适合直接复用当前 QPO 管线。 |
| 1ES 1727+502 | HBL | 12.08 | √ | 显著性高，有 variability，适合做同类 HBL 扩样。 |
| 1ES 2344+514 | HBL | 9.33 | √ | 有较稳健探测和变异迹象，适合作为主样本补充。 |
| BL Lacertae | IBL | 7.79 | √ | 报告单独展示了 2024-08-10 的 rapid variability，多波段跟进价值高。 |

### B 级：强烈建议纳入，但更适合作为扩展或对照

这些源很值得做，但在类型或预期时标上，与 `Mrk 421/501` 并不完全同构。

| Source | Type | LHAASO Sig(σ) | Variability | 推荐理由 |
|---|---|---:|---|---|
| 4C +42.22 | BL Lac | 6.90 | √ | 属于 blazar，已见 variability，可作为 blazar 扩样补充。 |
| NGC 1275 | FR I | 4.90 | √ | radio galaxy，LHAASO 已探测且有变异，可作为非 blazar 对照样本。 |
| M 87 | FR I | 8.38 | √ | 报告强调 week-level flaring 与 duty cycle，适合与 blazar 样本作比较。 |

### C 级：值得探索，但第一轮不建议作为主统计样本

| Source | Type | LHAASO Sig(σ) | Variability | 推荐理由 |
|---|---|---:|---|---|
| IC 310 | FR I / BL Lac | - | √ | 报告单页指出 2024 年 3–5 月识别出 5 次 flare，且若干时段谱很硬；很适合做 flare-driven exploratory case，但总表未给出显著性数字。 |

## 推荐 shortlist

如果目标是先做一个可执行、风险较低的 survey，建议采用以下 6 个源作为默认 shortlist：

1. `1ES 1959+650`
2. `1ES 1727+502`
3. `1ES 2344+514`
4. `BL Lacertae`
5. `NGC 1275`
6. `M 87`

如果希望稍微激进一些，可以再加入两项扩展目标：

1. `IC 310`
2. `4C +42.22`

## 建议的样本组织方式

为了兼顾可行性和物理解释，建议把后续 survey 分成三层：

### 1. 主样本

- `Mrk 421`
- `Mrk 501`
- `1ES 1959+650`
- `1ES 1727+502`
- `1ES 2344+514`
- `BL Lacertae`

这一层以 blazar，尤其是 HBL 为主，和当前项目现有工作流最兼容，适合作为第一批系统搜索样本。

### 2. 对照样本

- `NGC 1275`
- `M 87`

这一层用于检验潜在 QPO 或准周期结构是否主要偏向 blazar，而不是所有亮 AGN 都普遍存在。

### 3. 探索样本

- `IC 310`
- `4C +42.22`

这层更适合作为 flare / 特例驱动的补充分析，而不是一开始就和主样本混在一起做统一统计。

## 暂不建议放入第一轮主样本的源

以下源目前不建议作为第一轮 survey 主样本，原因通常是变异证据偏弱、分类不够干净、显著性边缘，或更适合后续补样：

- `HESS J1943+213`
- `1ES 1218+304`
- `RX J0648.7+1516`
- `H 1426+428`
- `RGB J2056+496`
- `1ES 1741+196`
- `TXS 0210+515`
- `VER J0521+211`

## 和当前仓库工作流的关系

当前仓库的周期搜索实现仍主要围绕 `mkn421` 和 `mkn501` 组织，尤其体现在以下入口中：

- [src/pipeline/periodicity_v1.py](/Users/luoji/Documents/projects/QPO/src/pipeline/periodicity_v1.py)
- [src/pipeline/weekly_qpo_local_significance.py](/Users/luoji/Documents/projects/QPO/src/pipeline/weekly_qpo_local_significance.py)

因此，从工程可复用性出发，最自然的下一步仍然是优先扩展与 `Mrk 421`、`Mrk 501` 同类的 HBL 样本，而不是一开始就把全部 LHAASO AGN 混合处理。

## 后续建议

1. 先确认这些候选源是否都能在 IHEP 侧稳定导出周尺度或日尺度 WCDA 光变。
2. 为多源 survey 建一个统一的 `source registry`，把源名、类型、输入文件、输出目录和默认周期搜索参数集中管理。
3. 第一轮先跑周尺度 WWZ/CWT quick-look，筛出值得进一步做 local/global significance 的目标。
