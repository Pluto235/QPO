# Fermi-LAT γ-ray QPO 检测调研 (2020–2025)

> **范围**：2020–2025 年发表在 arXiv 上、利用 Fermi-LAT γ 射线光变曲线搜寻
> blazar / AGN 准周期振荡 (quasi-periodic oscillation, QPO) 的 **11 篇论文**
> （其中 Peñil 系列 3 篇 2022/2024/2025）。不包含 TESS 光学和方法学性质论文。
>
> **数据生成日期**：2026-05-13；**最新修订 2026-05-14**（补 Ren+22 13 源 +
> 全 catalog 位置交叉匹配复核）；**2026-05-14b** 集成 Peñil 系列三篇
> （Peñil+22 / Rico+24 / Peñil+25），样本从 34 → 81 unique 源。

## TL;DR

- **论文数**：11（其中 5 篇大样本：**Peñil+25 扫 1492 jetted AGN**、**Rico+24 扫 494 源**、Chen+24 扫 134 blazars、Ren+22 扫 35 brightest、**Peñil+22 扫 24 selected hint 源**；3 篇小样本：Sharma+25 7 源；其余 5 篇为单源研究）。
- **覆盖源**：去重 **81 个 unique AGN**（Ren+22 24 + Peñil+22 18 new + Rico+24 22 new + Peñil+25 5 new hints + 其余 12）。
- **周期跨度**：~35 d (PKS 2247-131 短周期) 至 ~5 yr (Rico+24 多个 FSRQ ~3–5 yr)，主体集中在 50 d–4 yr。
- **方法演化**：LSP + REDFIT + WWZ → 加 CWT post-trial + Emmanoulopoulos PSD/PDF MC（Ren+22）→ 加 Gaussian Process (DRW / SHO) + MCMC 物理参数拟合（Sharma+25）→ **Singular Spectrum Analysis (SSA)** + 含 upper-limit 的 LC 处理（Peñil+22, Rico+24）→ **9-method ensemble + 全局显著性 trial-factor 修正**（Peñil+25）。
- **物理图像**：短周期 (< 1 yr) 偏好 helical jet / plasma blob helical motion；长周期 (> 1 yr) 偏好 SMBBH 轨道进动 / Lense-Thirring；mildly beamed 与 non-blazar 系统讨论 accretion + lighthouse 效应。
- **发生率（最新校正）**：Chen+24 ~3% (134 源, transient, ≥5 cycles)；Rico+24 SSA 给出 46/494 ≈ 9% 本地 ≥2σ，33/494 ≈ 7% 局域 ≥4σ → 全局 ≥2.2σ；**Peñil+25 在 1492 源（排除 24 hint 源）严格 trial-factor 修正后 0% 全局显著检出** —— 三者一致指向 QPO 几乎完全集中在已识别 hint 源 + 长 baseline 才显现。
- **LHAASO follow-up 候选**：扩样 81 源后仍**仅 Mrk 421 / Mrk 501 与 1LHAASO catalog 直接对应**（角距 0.04°）；新近 hint 中**最接近的非匹配**是 Rico+24 引入的 **3C 66A → 1LHAASO J0216+4237 = 1.22°**（仍远超 PSF，但已是 Mrk 421/501 之外最近的一对）—— 详见末尾 [LHAASO catalog 比对](#lhaaso-catalog-比对vhe-follow-up-候选评估) 节及 [2026-05-14b 81 源扩样本位置交叉匹配复核](#2026-05-14b-81-源扩样本位置交叉匹配复核) 子节。

## 主表 — 每篇论文一览

| # | 论文 | 样本 | 周期范围 / 数量 | 最高 σ | 主要方法 | Fermi 数据 | 物理解释 |
|---|---|---|---|---|---|---|---|
| 1 | Kushwaha+ 2020 | OJ 287 | ~314 d × 1 | ~3σ | LSP, REDFIT, WWZ | 2008-08 → 2018-02 | quasi-stationary radio knots / SMBBH |
| 2 | Zhang+ 2021 | PKS 0521-36 | ~1.1 yr × 1 | ~5σ | LSP, WWZ, REDFIT, GP | 2008-08 → 2021-03 | γ-ray outburst-driven (mildly beamed) |
| 3 | Ren+ 2022 | 35 brightest 4LAC (19 FSRQ + 15 BL Lac + 1 RDG) | 30 d – 1127 d，**36 QPO 候选 in 24 源** | >5σ post-trial | CWT (Morlet) + global wavelet + Emmanoulopoulos MC | 2008-08 → 2021-04 | SMBBH / jet precession / helical |
| 4 | **Peñil+ 2022** | **24 selected blazars (hint sample)** | 1.0 – 4.7 yr | PG 1553+113 **~1.8σ global** 唯一 | LSP + Phase Dispersion Min. + WWZ + ARIMA + Bayesian + 含 UL 点 | 2008-08 → 2020-08 (12 yr) | hint 重确认；trial-factor 后只 PG 1553+113 通过 |
| 5 | Gong+ 2023 | S4 0954+658 | 66 d & 210 d | >5σ (66d) | LSP, WWZ, REDFIT, epoch fold | 2008 → 2022 | plasma blob helical motion |
| 6 | Zhang+ 2023 | S2 0109+22 | ~600 d | 3.5σ | LSP, WWZ, REDFIT, phase fold | 2008-08 → 2023-01 | binary BH + lighthouse |
| 7 | Sharma+ 2023 | PKS 0521-36 | 268 d, 295 d, 806 d | >3σ | LSP, WWZ, GP (SHO + DRW) | 2008-08 → 2023 (15 yr) | first long-term QPO in non-blazar AGN |
| 8 | Chen+ 2024 | 134 blazars (flux-limited) → 6 源 8 QPO | 54 d – 341 d | ~4.3σ (PKS 1510-089) | WWZ + LSP + Emmanoulopoulos MC, 严格 5+ cycles | 2008-08 → ~2021-04 | helical jet (favored) |
| 9 | **Rico+ 2024** | **494 Fermi-LAT 源 (4LAC)** | 1.0 – 4.7 yr，**46 候选, 33 局域 ≥4σ ⇒ 全局 ≥2.2σ, 25 新 γ-ray candidates** | 4.8σ local / 3.3σ global (top) | **Singular Spectrum Analysis (SSA)** + LSP + EM MC | 2008 → ~2020-08 (12 yr) | SSA 隔离趋势 + 噪声后筛大批长周期候选 |
| 10 | Sharma+ 2025 | 7 blazars | ~225 d – ~1449 d | 4σ (PKS 0736+01) | LSP + REDFIT + DRW MC (30k LC) + MCMC SMBBH 拟合 | 2008-08 → 2025-04 (15+ yr) | SMBBH 主导 + jet precession |
| 11 | **Peñil+ 2025** | **1492 jetted AGN (4FGL, 排除 24 hint 源)** | **— (null result：trial-factor 后全局 ≈0σ)** | 10 源局域 ≥2σ → 全局 0σ | **9 种方法 ensemble** (LSP + PDM + WWZ + Wavelet + ARIMA/ARFIMA + CARMA + Bayesian + z-DCF + autoregressive) | 2008-08 → 2020-08 (12 yr) | QPO 不是 jetted AGN 普适特征 |

## 完整 QPO 候选列表（每行 = 一个源 × 一个 QPO 信号）

按发表年份-论文-显著性排序。同一源出现在不同论文里时多次列出，便于对比。

| # | Source | 4FGL / 类型 | 周期 (d) | Cycles | σ | 方法 | 论文 |
|---|---|---|---|---|---|---|---|
| 1 | OJ 287 | J0854.8+2006 / BL Lac | 314 | — | ~3σ | LSP+REDFIT+WWZ | Kushwaha+ 2020 |
| 2 | PKS 0521-36 | J0522.9-3628 / non-blazar AGN | ~400 (~1.1 yr) | — | ~5σ | LSP+WWZ+REDFIT+GP | Zhang+ 2021 |
| 3 | 4C +01.02 | J0108.6+0134 / FSRQ | 268±55 | 4 | >5σ | CWT 30d | Ren+ 2022 |
| 4 | 4C +01.02 | FSRQ | 123±26 (∼122±26 7d) | 5 | 4.7σ / >5σ | CWT | Ren+ 2022 |
| 5 | PKS 0537-441 | J0538.8-4405 / BL Lac | 285±67 (∼286±73 7d) | 4 | >5σ | CWT | Ren+ 2022 |
| 6 | **S5 1044+71** | J1048.4+7143 / FSRQ | **1127±226** (~3 yr) | 3 | 4.6σ post-trial（首报） | CWT | Ren+ 2022 |
| 7 | S5 1044+71 | FSRQ | 117±38 | 4 | >5σ | CWT | Ren+ 2022 |
| 8 | B2 1520+31 | J1522.1+3144 / FSRQ | 179±42 | 6 | >5σ | CWT | Ren+ 2022 |
| 9 | B2 1520+31 | FSRQ | 71±15 | 14 | >5σ | CWT 7d | Ren+ 2022 |
| 10 | B2 1520+31 | FSRQ | 39±11 | 17 | >5σ | CWT 7d | Ren+ 2022 |
| 11 | PKS 2247-131 | J2250.0-1250 / BL Lac | 214±43 | 6 | >5σ | CWT | Ren+ 2022 |
| 12 | PKS 2247-131 | BL Lac | **34±13** (~1 month) | 10 | >5σ | CWT 7d | Ren+ 2022 |
| 13 | NGC 1275 | J0319.8+4130 / RDG | 92±33 (7d) | 4 | >5σ | CWT | Ren+ 2022 |
| 14 | 4C +28.07 | J0237.8+2848 / FSRQ | 244±88 (7d) | 3 | >5σ | CWT | Ren+ 2022 |
| 14a | PKS 0426-380 | J0428.6-3756 / BL Lac | 85±26 (7d) | 8 | >5σ | CWT | Ren+ 2022 |
| 14b | PKS 0447-439 | J0449.4-4350 / BL Lac | 111±42 (7d) | 7 | >5σ | CWT | Ren+ 2022 |
| 14c | PKS 0454-234 | J0457.0-2324 / FSRQ | 69±21 (7d) | 4 | >5σ | CWT | Ren+ 2022 |
| 14d | S5 0716+714 | J0721.9+7120 / BL Lac | 324±77 (7d) | 5 | 3.2σ | CWT | Ren+ 2022 |
| 14e | Mrk 421 | J1104.4+3812 / BL Lac | 300±65 (7d) | 3 | >5σ | CWT | Ren+ 2022 |
| 14f | 1H 1013+498 | J1015.0+4926 / BL Lac | 264±59 / 100±25 / 52±15 | 4 / 4 / 12 | 4.9σ / >5σ / >5σ | CWT | Ren+ 2022 |
| 14g | 4C +21.35 | J1224.9+2122 / FSRQ | 66±17 (7d) | 6 | >5σ | CWT | Ren+ 2022 |
| 14h | 3C 273 | J1229.0+0202 / FSRQ | 177±38 / 97±25 (7d) | 4 / 3 | >5σ / >5σ | CWT | Ren+ 2022 |
| 14i | 3C 279 | J1256.1-0547 / FSRQ | 101±27 / 40±8 (7d) | 6 / 4 | >5σ / >5σ | CWT | Ren+ 2022 |
| 14j | Mrk 501 | J1653.8+3945 / BL Lac | 326±76 (7d) | 7 | >5σ | CWT | Ren+ 2022 |
| 14k | PKS 2155-304 | J2158.8-3013 / BL Lac | 341±106 (7d) | 4 | 3.5σ | CWT | Ren+ 2022 |
| 14l | CTA 102 | J2232.6+1143 / FSRQ | 366±81 / 178±40 (7d) | 3 / 5 | >5σ / >5σ | CWT | Ren+ 2022 |
| 14m | 3C 454.3 | J2253.9+1609 / FSRQ | 120±27 (7d) | 4 | >5σ | CWT | Ren+ 2022 |
| 14n | PMN J2345-1555 | J2345.2-1555 / FSRQ | 191±44 (7d) | 4 | >5σ | CWT | Ren+ 2022 |
| 15 | S4 0954+658 | / BL Lac | 66 ± 4.8 | 9 | >5σ | LSP+WWZ+REDFIT+epoch fold | Gong+ 2023 |
| 16 | S4 0954+658 | BL Lac | 210 ± 43 | 4 | ~3.5σ | 同上 | Gong+ 2023 |
| 17 | S2 0109+22 | J0112.1+2245 / BL Lac | ~600 | 5.6 | ~3.5σ | LSP+WWZ+REDFIT+phase fold | Zhang+ 2023 |
| 18 | PKS 0521-36 | non-blazar AGN | 268 | — | >3σ | LSP+WWZ+GP(SHO+DRW) | Sharma+ 2023 |
| 19 | PKS 0521-36 | non-blazar AGN | 295 / 283 (PSD) | — | >3σ | 同上 | Sharma+ 2023 |
| 20 | PKS 0521-36 | non-blazar AGN | **806 / 886 (PSD)** — 268 d 的第三谐波 | — | >3σ | 同上 | Sharma+ 2023 |
| 21 | 4C +01.02 | FSRQ | 253.2 ± 20.0 | 6 | ~2.7σ | WWZ+LSP | Chen+ 2024 |
| 22 | **PKS 0336-01** | / FSRQ | **94.6 ± 6.8** ★新发现 | 6 | ~3.4σ | WWZ+LSP | Chen+ 2024 |
| 23 | PKS 0402-362 | FSRQ | 103.9 ± 6.7 | 5 | ~2.6σ | WWZ+LSP | Chen+ 2024 |
| 24 | **PKS 0537-441** | BL Lac | **55.0 ± 3.3 (QPO I)** ★新 | 7 | ~4.1σ | WWZ+LSP | Chen+ 2024 |
| 25 | **PKS 0537-441** | BL Lac | **54.7 ± 3.3 (QPO II)** ★新（重复 transient） | 7 | ~4.0σ | WWZ+LSP | Chen+ 2024 |
| 26 | **PKS 1424-41** | FSRQ | **57.1 ± 4.5 (QPO I)** ★新（嵌套） | 6 | ~3.2σ | WWZ+LSP | Chen+ 2024 |
| 27 | PKS 1424-41 | FSRQ | 341 ± 25.8 (QPO II) | 6 | ~3.7σ | WWZ+LSP | Chen+ 2024 |
| 28 | PKS 1510-089 | J1512.8-0906 / FSRQ | 92.3 ± 5.2 | 8 | ~4.3σ | WWZ+LSP | Chen+ 2024 |
| 29 | PKS 0736+01 | J0739.2+0137 / FSRQ | ~1449 (~4 yr) | — | 4σ | LSP+REDFIT+DRW | Sharma+ 2025 |
| 30 | PKS 1424-41 | FSRQ | ~357 | — | 3σ | LSP+REDFIT+DRW | Sharma+ 2025 |
| 31 | S2 0109+22 | BL Lac | ~667 | — | 3σ | LSP+REDFIT+DRW | Sharma+ 2025 |
| 32 | PKS 0244-470 | FSRQ | ~227 | — | 3σ | LSP+REDFIT+DRW | Sharma+ 2025 |
| 33 | PKS 0405-385 | FSRQ | ~1000 | — | 2.9σ | LSP+REDFIT+DRW | Sharma+ 2025 |
| 34 | PKS 0208-512 | FSRQ | ~909 | — | 2.85σ | LSP+REDFIT+DRW | Sharma+ 2025 |
| 35 | PKS 0035-252 | FSRQ | ~357 | — | 2.8σ | LSP+REDFIT+DRW | Sharma+ 2025 |

★ = 该源在该周期/方法下的首次报告。
注：Ren+ 2022 共给 24 源 36 候选；本表展开列入主要单候选（同源多周期保留首选/示例值），完整列表见原文 Table 2。

## Peñil 系列三篇大样本扩样（2026-05-14b 加入）

Peñil 课题组 2022–2025 跨度的三篇系统性扫描带来 **45 个本报告原先未列出的
新 QPO/hint 源**（去重；与已有 34 源相加 → **81 unique 源**）。三篇在
"候选 vs 显著" 这条轴上代表三种态度：

- **Peñil+22**（24 hint 源精挑）：保守，只 PG 1553+113 一个全局 1.8σ
- **Rico+24**（494 源 + SSA）：相对宽松的方法学（SSA），出 46 candidates，
  33 个 local ≥4σ ↔ global ≥2.2σ，**25 个标记为「新 γ-ray candidate」**
- **Peñil+25**（1492 源 9-method ensemble）：最严格，trial-factor 修正后
  **0 个 globally significant** QPO；10 源 ≥2σ local 但 global ≈ 0σ

### Peñil+22 新源（18 个，按 global σ 降序，最高 1.8σ）

PG 1553+113 是 Peñil 系列中迄今**唯一通过全局显著性 ≥1σ 的源**。

| Source | 4FGL | Type | z | 周期 (yr) | Global σ | Dec | FoV |
|---|---|---|---|---|---|---|---|
| **PG 1553+113** ★ | J1555.7+1111 | BL Lac | 0.433 | 2.2±0.2 | **≈1.8σ** | +11.19° | ✅ |
| OJ 014 | J0811.3+0146 | BL Lac | 1.148 | 4.1 | ≈0σ | +1.77° | ✅ |
| GB6 J0043+3426 | J0043.8+3425 | FSRQ | 0.966 | 1.9 | ≈0σ | +34.43° | ✅ |
| TXS 0518+211 | J0521.7+2113 | BL Lac | 0.108 | 3.1 | ≈0σ | +21.21° | ✅ |
| 87GB 164812.2+524023 | J1649.4+5238 | BL Lac | — | 2.8 | ≈0σ | +52.58° | ✅ |
| PKS 0301-243 | J0303.4-2407 | BL Lac | 0.266 | 2.1 | ≈0σ | −24.12° | ❌ |
| S4 1144+40 | J1146.8+3958 | FSRQ | 1.089 | 3.3 | ≈0σ | +39.97° | ✅ |
| PG 1246+586 | J1248.2+5820 | BL Lac | — | 2.1 | ≈0σ | +58.35° | ✅ |
| PKS 0250-225 | J0252.8-2218 | FSRQ | 1.419 | 1.2 | ≈0σ | −22.32° | ❌ |
| PKS 2255-282 | J2258.0-2759 | FSRQ | 0.926 | 1.4 | ≈0σ | −27.98° | ❌ |
| TXS 1902+556 | J1903.2+5541 | BL Lac | — | 3.3 | ≈0σ | +55.68° | ✅ |
| S3 0458-02 | J0501.2-0157 | FSRQ | 2.291 | 3.8 | ≈0σ | −1.98° | ✅ |
| MG2 J130304+2434 | J1303.0+2435 | BL Lac | 0.993 | 2.1 | ≈0σ | +24.57° | ✅ |
| PKS 2052-47 | J2056.2-4714 | FSRQ | 1.489 | 1.7 | ≈0σ | −47.23° | ❌ |
| S4 0814+42 | J0818.2+4223 | BL Lac | 0.530 | 2.2 | ≈0σ | +42.38° | ✅ |
| MG1 J021114+1051 | J0211.2+1051 | BL Lac | 0.2 | 2.9 | ≈0σ | +10.86° | ✅ |
| TXS 0059+581 | J0102.8+5825 | FSRQ | 0.644 | 4.0 | ≈0σ | +58.42° | ✅ |
| TXS 1452+516 | J1454.5+5124 | BL Lac | — | 2.1 | ≈0σ | +51.41° | ✅ |

★ = 唯一全局 ≥1σ。FoV = 是否在 LHAASO 视场（Dec > −20°）。

### Rico+24 新源（22 个 starred「new γ-ray candidates」，去 3 个与现有重叠）

按 local σ 降序排列。`*` 表 Rico+24 原表标的 "无既有 γ-ray QPO 证据"。

| Source | 4FGL | Type | z | 周期 (yr) | Local σ | Global σ | Dec | FoV |
|---|---|---|---|---|---|---|---|---|
| OC 457 | J0137.0+4751 | FSRQ | 0.859 | 1.79±0.22 | 4.8σ | 3.3σ | +47.86° | ✅ |
| 4C +47.44 | J1637.7+4717 | FSRQ | 0.735 | 3.17±0.58 | 4.8σ | 3.3σ | +47.29° | ✅ |
| 4C +48.41 | J1657.7+4808 | FSRQ | 1.669 | 1.47±0.08 | 4.8σ | 3.3σ | +48.14° | ✅ |
| **3C 66A** | J0222.6+4302 | BL Lac | 0.444 | 2.31±0.20 | 4.6σ | 3.1σ | +43.04° | ✅ |
| PKS B1310-041 | J1312.8-0425 | FSRQ | 0.825 | 2.37±0.22 | 4.6σ | 3.1σ | −4.42° | ✅ |
| PKS 0524-485 | J0526.2-4830 | FSRQ | 1.300 | 2.07±0.20 | 4.8σ | 3.3σ | −48.52° | ❌ |
| PKS 1005-333 | J1007.6-3332 | FSRQ | 1.837 | 2.61±0.34 | 4.8σ | 3.3σ | −33.54° | ❌ |
| TXS 1530-131 | J1532.7-1319 | BCU | — | 1.37±0.07 | 4.8σ | 3.3σ | −13.33° | ✅ |
| PKS 1903-80 | J1913.0-8009 | FSRQ | 1.756 | 2.41±0.22 | 4.8σ | 3.3σ | −80.16° | ❌ |
| PKS 2155-83 | J2201.5-8339 | FSRQ | 1.865 | 4.73±0.94 | 4.8σ | 3.3σ | −83.66° | ❌ |
| MH 2136-428 | J2139.4-4235 | BL Lac | — | 1.81±0.18 | 4.8σ | 3.3σ | −42.59° | ❌ |
| 7C 2010+4619 | J2012.0+4629 | BL Lac | — | 3.23±0.46 | 4.2σ | 2.5σ | +46.49° | ✅ |
| B2 2234+28A | J2236.3+2828 | FSRQ | 0.790 | 2.19±0.15 | 4.1σ | 2.3σ | +28.48° | ✅ |
| TXS 1318+225 | J1321.1+2216 | FSRQ | 0.943 | 1.21±0.06 | 3.8σ | 1.8σ | +22.28° | ✅ |
| S5 1221+80 | J1223.8+8039 | BL Lac | — | 2.67±0.27 | 3.5σ | 1.2σ | +80.66° | ✅ |
| PKS 1424-328 | J1427.6-3305 | BL Lac | — | 1.27±0.08 | 2.9σ | <1.0σ | −33.09° | ❌ |
| 4C +04.42 | J1222.5+0414 | FSRQ | 0.964 | 2.21±0.19 | 2.7σ | <1.0σ | +4.24° | ✅ |
| PKS 1716-771 | J1723.6-7714 | BCU | — | 2.27±0.20 | 2.9σ | <1.0σ | −77.24° | ❌ |
| S4 1250+53 | J1253.2+5301 | BL Lac | — | 2.31±0.21 | 2.6σ | <1.0σ | +53.02° | ✅ |
| PKS 0403-13 | J0405.6-1308 | FSRQ | 0.571 | 1.69±0.12 | 2.3σ | <1.0σ | −13.14° | ✅ |
| B2 0716+33 | J0719.3+3307 | FSRQ | 0.779 | 2.29±0.18 | 2.2σ | <1.0σ | +33.12° | ✅ |
| S4 1030+41 | J1033.1+4115 | FSRQ | 1.117 | 2.29±0.21 | 2.0σ | <1.0σ | +41.26° | ✅ |
| PMN J0427-3900 | J0427.3-3900 | BCU | — | 2.79±0.31 | 3.9σ | 2.0σ | −39.01° | ❌ |

注：原文 Table A.1 共 46 行，其中 25 行带 `*` (= 新 γ-ray 候选)；本表只列
22 个不与现有 34 源重叠的（另 3 个 *-标记的 3C 66A、PKS 1424+240、S2 0109+22
属于「之前在他文 sample 内但 Rico+24 视为首次 SSA 检出」）。

### Peñil+25 新源（5 个 local ≥2σ hint，**全部 global ≈0σ**）

Peñil+25 主样本 1492，扫完后没有全局显著源；下列 5 个仅作 hint（local σ 在
trial-factor 修正后归零）。其余 5 个表 1 源（S5 1044+71, S2 0109+22, PG 1553+113,
OJ 014, S5 0716+714, GB6 J0043+3426, TXS 0518+211, 87GB 164812.2+524023）
已出现在 Peñil+22 / Ren+22 中，本表略。

| Source | 4FGL | Type | z | 周期 (yr) | Local σ | Global σ | Dec | FoV |
|---|---|---|---|---|---|---|---|---|
| PKS 0215+015 | J0217.8+0144 | FSRQ | 1.715 | 3.4±0.4 | 2.2σ | ≈0σ | +1.73° | ✅ |
| PMN J0533-5549 | J0533.3+4823 | BCU | — | — | — | ≈0σ | −55.82° | ❌ |
| OP 313 | J1310.5+3221 | FSRQ | 0.997 | 5.7±0.8 | 2.0σ | ≈0σ | +32.35° | ✅ |
| S4 1030+61 | J1033.9+6050 | FSRQ | 1.401 | 2.9±0.4 | 2.0σ | ≈0σ | +60.85° | ✅ |
| S5 1039+81 | J1044.6+8053 | FSRQ | 1.254 | 3.5±0.4 | 2.0σ | ≈0σ | +80.89° | ✅ |

PKS 0405-385 与 MH 2136-428 在 Peñil+25 表 1 中 local σ 最高 (2.5σ) 但
分别已在 Sharma+25 / Rico+24 列入，故不重复。

## 逐篇细读

### 1. Kushwaha+ 2020 — OJ 287 [arXiv:2009.13754]

- **源**：OJ 287 (BL Lac，z=0.306)，最经典的 SMBBH 候选体（光学 12-yr QPO）。
- **检测**：γ-ray 月度 binned 光变曲线中识别 ~314 d 周期 (~3σ)。
- **方法**：LSP、REDFIT、WWZ 三件套，无 GP。
- **解释**：与 quasi-stationary radio knot 位置漂移和 γ-ray–mm radio 强相关一致 — 信号可能与喷流内静止结节相关，而非 SMBBH 12-yr 主周期。
- **数据**：Fermi-LAT 2008-08 → ~2018-02 (约 9.5 yr)。

### 2. Zhang+ 2021 — PKS 0521-36 [arXiv:2106.10040]

- **源**：PKS 0521-36 — 4LAC 中分类为 BL Lac / 中间态非典型 blazar，**mildly beamed jet**。
- **检测**：在两次 outburst（2012-10 和 2019-05）之间的 ~5.8 yr 窗口（MJD 56317–58447）内识别 **~1.1 yr 周期 (~5σ)**。
- **方法**：LSP + WWZ + REDFIT 三种 + Gaussian Process 模型四种独立验证。
- **解释**：首例 γ-ray QPO in mildly beamed jet；推测 γ-ray outburst 在 QPO 形成中起关键作用。
- **数据**：~12.6 yr LAT 全数据，但 QPO 仅在 5.8 yr 窗口内。

### 3. Ren, Cerruti & Sahakyan 2022 — 35 brightest AGN [arXiv:2204.13051]

- **样本**：4LAC 中最亮 34 个 + 手工加入 PKS 2247-131，共 35 个（19 FSRQ + 15 BL Lac + 1 radio galaxy NGC 1275）。
- **方法**：Continuous Wavelet Transform (Morlet, via `PyCWT`) + global wavelet spectrum + **post-trial look-elsewhere correction** (Auchère 2016) + Emmanoulopoulos PSD/PDF Monte Carlo（10⁴ artificial LC × 每源 × 每 binning）。
- **时间 binning**：30 d 与 7 d 两套，独立比对。
- **能段**：100 MeV – 500 GeV。**数据跨度** Aug 2008 → Apr 2021 (MJD 54686-59308)。
- **结果**：**36 QPO 候选 in 24/35 源**（post-trial σ > 3，至少 3 cycles）。
  - 长周期 (>1 yr) 出现在 5 源：**S5 0716+714, S5 1044+71, Mrk 421, PKS 2155-304, CTA 102**。
  - 月周期 (<300 d) 出现在 20 源。
  - 摘要 5 个最显著：4C +01.02, PKS 0537-441, **S5 1044+71** (1127 d 首报), B2 1520+31, PKS 2247-131。
- **结论**：**所有候选均为 transient**（在分析窗口内出现/消失）。S5 1044+71 ~3 yr 周期作为最长多年 QPO 首次报告。
- **解释**：与 SMBBH 在 SMBH 演化中的存在关联，但保持开放，认为 jet 内/外多种几何机制都可解释。

### 5. Gong+ 2023 — S4 0954+658 [arXiv:2304.03085]

- **源**：S4 0954+658 (BL Lac, z=0.367)。
- **检测**：两个分段 transient QPO：
  - **66 ± 4.8 d (>5σ)**，MJD 57145–57745（2015–2016），**9 cycles** — blazar γ-ray QPO 中观测到的最多 cycle 之一。
  - **210 ± 43 d (~3.5σ)**，MJD 59035–59915（2020–2022），4 cycles。
- **方法**：LSP + WWZ + REDFIT + epoch folding。
- **解释**：plasma blob 沿 helical 路径运动 + jet 几何模型 — 与短周期一致。

### 6. Zhang+ 2023 — S2 0109+22 [arXiv:2306.11579]

- **源**：S2 0109+22 (BL Lac, z~0.36)。射电、毫米波已知 ~657 d 周期。
- **检测**：**~600 d (3.5σ)**，2013-11 至 2023-01，~9 yr / **5.6 cycles**。
- **方法**：WWZ + LSP + REDFIT + phase-folded LC。Baluev 假警报修正 + Emmanoulopoulos MC (10⁵ LCs)。
- **数据**：Fermi-LAT 2008-08-04 → 2023-01-16，7-day binned, TS>9。
- **解释**：与已知 radio 周期一致 → binary BH 系统的 accretion + lighthouse 效应。

### 7. Sharma, Prince & Bose 2023 — PKS 0521-36 [arXiv:2312.12623]

- **源**：PKS 0521-36（与 Zhang+ 2021 同源）。**non-blazar AGN**，弱 beamed jet。
- **检测**：3 个周期：**268 d, 295 d, 806 d (>3σ)**；其中 806 d 是 268 d 的 **第三谐波**。GP（SHO + DRW）模型 PSD 显示 ~283 d 和 ~886 d 两个峰。
- **方法**：LSP + WWZ + GP（SHO/DRW）。
- **数据**：Fermi-LAT 15 yr 全数据。
- **意义**：首例长周期 (>800 d) γ-ray QPO in non-blazar AGN。
- **与 Zhang+ 2021 对比**：Zhang+ 2021 在更短窗口给出 ~1.1 yr (~400 d)；Sharma+ 2023 在 15 yr 全数据给出多个周期且都更短/更长。说明在 5.8 yr vs 15 yr 窗口内，主导信号不同。

### 8. Chen+ 2024 — 134 blazars systematic search [arXiv:2401.10658]

- **样本**：134 blazars（Monitored Source List 中 peak flux > 1×10⁻⁶ ph cm⁻²s⁻¹，7 BCU + 31 BL Lac + 95 FSRQ）。
- **方法**：WWZ 全光变曲线扫描 → LSP 独立验证 → Emmanoulopoulos PSD/PDF MC 给出 σ。
- **筛选标准**（比 Ren+ 2022 严格）：
  1. cycles ≥ 5
  2. 缺数据 < 60%
  3. 肉眼可识 QPO
- **结果**：8 个 transient QPOs in 6 sources，全为 FSRQ 或 BL Lac：
  - PKS 0537-441 (2 个 QPO，重复 transient)
  - PKS 1424-41 (2 个 QPO，嵌套 — 短周期叠在长周期上)
  - 4C +01.02, PKS 0336-01, PKS 0402-362, PKS 1510-089 各 1 个
- **新发现 4 个**（首报）：PKS 0336-01 94 d、PKS 0537-441 55 d & 54 d、PKS 1424-41 57 d。
- **发生率估算**：~3%。
- **解释**：helical jet motion 模型 best fit；同时讨论磁岛 / 磁重联，但 helical jet 仍最优。

### 4. Peñil+ 2022 — 24 selected blazars hint sample [arXiv:2211.01894]

> 注：按时间顺序此节应放在 §3 (Ren+22) 后、§5 (Gong+23) 前；本文档为简化
> 编辑，把 Peñil 系列三篇 (§4/§9/§11) 集中在 §3-§8 后阅读，主表已按时间排序。

- **作者**：P. Peñil, M. Ajello, S. Buson, A. Domínguez, J. R. Westernacher-Schneider, A. Rico, S. Adhikari, J. Zrake；2022-11-03。
- **样本**：24 个 γ-ray blazars，来自 Peñil+2020 的更早期 hint 列表，扩展时长。
- **数据**：Fermi-LAT 12 yr (≈2008-08 → 2020-08)，能段 >0.1 GeV，28 d binning。
- **方法链条**：
  1. **保留 upper-limit (UL) 点**：把 UL 数据作为信号下限纳入分析（>0% blazars 有 UL；过去常 discard）—— 防止 LC 出现假 gap
  2. LSP + Phase Dispersion Min. (PDM) + WWZ + ARIMA + Bayesian periodicity 5 种独立验证
  3. **Trial-factor 全局显著性修正**：local σ 经 ≥4σ 时配 P × B 试验 → global σ ≈ local 经验函数。这是 Peñil 系列方法学的核心创新。
- **结果**：
  - **PG 1553+113** 给出 2.2±0.2 yr，local 4.5σ → **global ≈1.8σ** —— 唯一通过 ≥1σ 全局门槛的
  - 其余 23 源 global ≈ 0σ（包含 PKS 2155−304、OJ 014、PKS 0454−234、S5 0716+714 等知名 VHE 源）
- **意义**：在 hint 重分析中只有 PG 1553+113 保留为 robust QPO 候选 —— 与 Ait Benkhali+20、HESS 等独立分析一致。
- **后续**：直接对接 Rico+24（SSA 重测得 PG 1553+113 local 4.8σ）和 Peñil+25 全 sample 大扫描。

### 9. Rico+ 2024 — SSA × 494 Fermi-LAT 源 [arXiv:2412.05812]

- **作者**：A. Rico, A. Domínguez, P. Peñil, M. Ajello, S. Buson, S. Adhikari, M. Movahedifar；2024-12-08，DOI 10.1051/0004-6361/202452495。
- **样本**：4LAC 中 494 个 Fermi-LAT 源（jetted AGN + Sy1，含 nlSy1）。
- **数据**：Fermi-LAT ~12 yr，28 d binning，>0.1 GeV。
- **方法**：**Singular Spectrum Analysis (SSA)** —— 把时间序列分解为 oscillatory + trend + noise 三个 component，**剥离趋势和噪声后单独做 LSP**。优势：长 baseline 下红噪声不再压死信号。
- **统计**：
  - Local σ：Emmanoulopoulos PSD/PDF MC + Vaughan red-noise 模型，从 4σ 到 4.8σ 离散级
  - Global σ：用 Gross & Vitells 2010 trial-factor 公式，4.8σ local → 3.3σ global
- **结果**：
  - **46 candidates** with local ≥2σ；其中
  - **33 candidates** local ≥4σ ⇒ global ≥2.2σ（**8 个 global ≥3.0σ**）
  - **25 个 `*` 标 "new γ-ray candidates"**（无既有 γ-ray QPO 文献）—— Mass-add 到 LHAASO 比对样本
- **代表性新源**：
  - OC 457 (FSRQ, z=0.859, 1.79 yr, global 3.3σ)
  - 4C +47.44, 4C +48.41（高纬 FSRQ, > 4σ local）
  - **3C 66A** (BL Lac, z=0.444, 2.31 yr, local 4.6σ / global 3.1σ) —— 已知 VHE 源 + 长期 γ-ray hint，首次有 SSA QPO 显著性
- **方法学贡献**：把 SSA 从原本生物/经济学时间序列工具引入 blazar 周期搜寻，**与 Ren+22 CWT 形成互补**。后续 Peñil+25 把 SSA 集成进 9-method ensemble。

### 11. Peñil+ 2025 — 1492 jetted AGN, 9-method ensemble, NULL result [arXiv:2509.14013]

- **作者**：P. Peñil, A. Domínguez, S. Buson, M. Ajello, S. Adhikari, A. Rico；2025-09-17 (v1) / 2025-10-22 (v2)。
- **样本**：从 4FGL DR2 选 **1492 个 jetted AGN**（占 catalog 45.1%）；**显式排除 24 个 hint 源**（已在 Peñil+22 单独再分析）。这是迄今为止最大的 GeV blazar QPO 搜寻样本。
- **数据**：Fermi-LAT 12 yr (2008-08 → 2020-08)，28 d binning，>0.1 GeV，含 UL 点。
- **流水线**：四阶段
  1. **变量性筛**：1492 → 453（30.6%）保留 <50% upper-limit
  2. **10 established methods**（LSP, PDM, WWZ, CWT, ARIMA, ARFIMA, CARMA, Bayesian QPO, Markov Chain Monte Carlo sine fits, …），**REDFIT 已剔除**（AR(1) 不当模型）
  3. **2 new methods** (§3.5)：z-DCF (autocorrelation) + autoregressive 模型 → 算 **9-method ensemble**
  4. **同一 period 必须 ≥3 method 检出，最少 4 个 method ≥4σ** —— 极严标准
- **统计**：
  - local σ：Timmer & Koenig (TK) artificial LC + Emmanoulopoulos MC 修正
  - global σ：**look-elsewhere** trial factor P × B = 24 × 1492 = 35,808 → 把 local 4.5σ 压到 global ≈0σ
- **结果**：
  - **0 sources with global σ > 0**
  - **10 sources** 给 local ≥2σ hint（**全部 global ≈0σ**）—— Table 1：S5 1044+71 (2.5σ local, top), S2 0109+22, PKS 0215+015, PMN J0533-5549, OP 313, S4 1030+61, S5 1039+81 + 重叠的 PG 1553+113 等
  - **PKS 0405-385** local 2.5σ 与 S5 1044+71 并列；但都被全局修正掉
- **核心物理结论**：
  - **QPO 不是 jetted AGN 的普适特征** —— 否则 1492 源里应至少出几十个 global ≥3σ
  - 现有所有 robust γ-ray QPO（Mrk 421/501 周期、PG 1553+113 2.2 yr、Ren+22 CTA 102/CB2 1520+31 等）应被视为**少数特殊源的几何/动力学产物**，不能外推
  - 把 Chen+24 ~3% 发生率上限进一步压到 < 0.5%（在排除 hint 源后）
- **方法学意义**：这是目前最严格 trial-factor 修正后的 null result —— **后续任何 γ-ray QPO 论文必须通过这套 9-method ensemble + 全局修正才算 robust**。

### 10. Sharma+ 2025 — 7 blazars + SMBBH 拟合 [arXiv:2505.23697]

- **样本**：7 blazars (PKS 1424-41, PKS 0736+01, S2 0109+22, PKS 0244-470, PKS 0405-385, PKS 0208-512, PKS 0035-252)。
- **数据**：Fermi-LAT 2008-08-05 → 2025-04-01 (MJD 54683–60766)，weekly binned，TS ≥ 9。
- **方法链条**：
  1. LSP + REDFIT 找候选峰
  2. DRW (Damped Random Walk) 模型 + **30,000 个 synthetic LC** 评估显著性
  3. MCMC 拟合 SMBBH 物理参数（Lorentz factor Γ、视角 ψ）
- **检测**（7 源全部检出，σ 不同）：
  - PKS 0736+01 ~1449 d / 4σ（**首次报告**该源 QPO）
  - PKS 1424-41 ~357 d / 3σ
  - S2 0109+22 ~667 d / 3σ
  - PKS 0244-470 ~227 d / 3σ
  - PKS 0405-385 ~1000 d / 2.9σ
  - PKS 0208-512 ~909 d / 2.85σ
  - PKS 0035-252 ~357 d / 2.8σ
- **物理解释**：长周期 (>1 yr) 在 SMBBH 框架下 — 约束 Γ ~ 10–20，ψ 几度量级；助攻 SMBBH + 喷流方向相关性研究。

## 跨论文交叉

### 同一源在多篇里出现

| 源 | 论文 | 周期 / σ |
|---|---|---|
| PKS 0521-36 (non-blazar AGN) | Zhang+ 2021 | ~1.1 yr / ~5σ |
|  | Sharma+ 2023 | 268 / 295 / 806 d / >3σ |
| PKS 1424-41 (FSRQ) | Ren+ 2022 | 90±22, 92±25 d, >5σ |
|  | Chen+ 2024 | 57 / 341 d / 3.2σ / 3.7σ |
|  | Sharma+ 2025 | ~357 d / 3σ |
| S2 0109+22 (BL Lac) | Zhang+ 2023 | ~600 d / 3.5σ |
|  | Sharma+ 2025 | ~667 d / 3σ |
| PKS 0537-441 (BL Lac) | Ren+ 2022 | 285 d (~5σ) |
|  | Chen+ 2024 | 55 / 54 d (~4σ) — 双 transient |
| PKS 0402-362 (FSRQ) | Ren+ 2022 | 221±56 d, 122±42 d |
|  | Chen+ 2024 | 103.9 d / 2.6σ |
| 4C +01.02 (FSRQ, z=2.099) | Ren+ 2022 | 268, 123 d / >5σ |
|  | Chen+ 2024 | 253 d / 2.7σ |
| PKS 1510-089 (FSRQ) | Ren+ 2022 | 119±31, 120±36 d |
|  | Chen+ 2024 | 92.3 d / 4.3σ |
| OJ 287 (BL Lac) | Kushwaha+ 2020 | 314 d / ~3σ |
|  | Ren+ 2022 | ∼300 d 量级（未在最显著 5 名内）|

观察：
- **方法越严格、周期估计往往越短**：Chen+ 2024 用严格 ≥5 cycles 筛选，发现的周期 (54–341 d) 比 Ren+ 2022 (含 long-period) 更窄。
- **数据窗口决定主导信号**：PKS 0521-36 在 5.8 yr vs 15 yr 给出不同周期组（说明 transient QPO 在不同时段切换）。

### 方法使用频率

| 方法 | 使用论文数 / 11 |
|---|---|
| LSP (Lomb-Scargle) | 11 |
| WWZ (Weighted Wavelet Z-transform) | 9 |
| REDFIT | 6 |
| Emmanoulopoulos PSD/PDF MC | 5 |
| Gaussian Process (DRW / SHO) | 3 |
| Phase fold / epoch fold | 3 |
| CWT (Morlet, post-trial corrected) | 2 (Ren+ 2022, Peñil+ 2025) |
| MCMC 物理参数拟合 | 1 (Sharma+ 2025) |
| **SSA (Singular Spectrum Analysis)** | **2 (Rico+ 2024, Peñil+ 2025)** |
| **z-DCF (autocorrelation)** | **1 (Peñil+ 2025)** |
| **ARIMA / ARFIMA / CARMA** | **3 (Peñil+ 2022/2025, Rico+ 2024)** |
| **Bayesian QPO / MCMC sine fits** | **2 (Peñil+ 2022, Peñil+ 2025)** |
| **Trial-factor 全局显著性修正** | **3 (Peñil+ 2022, Rico+ 2024, Peñil+ 2025)** |
| **保留 upper-limit (UL) 点** | **3 (Peñil 系列)** |

### 物理解释优先级

| 解释模型 | 用于哪类周期 | 出现频次 |
|---|---|---|
| Helical jet / plasma blob helical motion | 短周期 (< 1 yr) | 5 篇 |
| SMBBH orbital / precession | 长周期 (> 1 yr) | 4 篇 |
| Lense-Thirring precession | 长周期 | 2 篇 |
| Accretion disk instability + lighthouse | non-blazar / mildly beamed | 3 篇 |
| Magnetic islands / reconnection | 短周期 alternative | 1 篇 (Chen+ 2024 讨论) |

## 显著性 σ 分布

|  σ 范围 | 候选数（含重复源） |
|---|---|
| > 5σ (post-trial) | ~20+（主要来自 Ren+ 2022） |
| 4–5σ | ~5 |
| 3–4σ | ~10 |
| < 3σ | ~3 (Chen+ 2024 中 4C +01.02 253-d 等) |

## 数据 binning 约定

| 论文 | binning |
|---|---|
| Kushwaha+ 2020 | monthly (~30 d) |
| Zhang+ 2021 | 30 d |
| Ren+ 2022 | 7 d + 30 d 并行 |
| Gong+ 2023 | 7 d |
| Zhang+ 2023 | 7 d (+ 10/30 d 验证) |
| Sharma+ 2023 | weekly |
| Chen+ 2024 | weekly |
| Sharma+ 2025 | weekly |

7-day binned 已成 2022 年后的实际标准（短周期 < 1 yr 几乎必须）。

## LHAASO catalog 比对（VHE follow-up 候选评估）

> 本节面向**下一步工作**：用 LHAASO 数据搜寻上述 Fermi QPO 源在 VHE 段的
> QPO 信号。比对依据为 1LHAASO catalog (Cao et al. 2024, [arXiv:2305.17030](https://arxiv.org/abs/2305.17030))。

### LHAASO 观测窗与 1LHAASO catalog

- 海拔 4410 m（中国四川稻城）；WCDA 1–25 TeV (508 d, 2021-03 → 2022-09)、KM2A >25 TeV (933 d, 2020-01 → 2022-09)
- **天区覆盖**：Dec −20° 至 +80°
- 1LHAASO 总数 ~90 源（绝大多数为 Galactic：SNR / PWN / pulsar / UNID）
- **Extragalactic 仅 3 源**：

| 1LHAASO ID | 对应天体 | 类型 | RA, Dec | TS (≈σ²) | 备注 |
|---|---|---|---|---|---|
| J1104+3810 | **Mrk 421** | BL Lac (z=0.030) | 166.07°, +38.18° | 5343.6 (~73σ) | WCDA only；KM2A 无 >25 TeV (EBL 吸收) |
| J1653+3943 | **Mrk 501** | BL Lac (z=0.034) | 253.43°, +39.73° | 4121.6 (~64σ) | WCDA only |
| J1219+2915 | NGC 4278 (候选) | LINER AGN (z=0.002) | 184.98°, +29.25° | 50.4 (~7σ) | 高 Galactic latitude，likely extragalactic |

### Fermi QPO 源 × LHAASO 状态三档分类

把本报告 8 篇论文里出现的 **34 个 unique Fermi QPO 源** 按 LHAASO 视场/检出状态分三档（2026-05-14 修订：原 21 源扩为 34 源，补 Ren+22 Table 2 中前版未单列的 13 源）。

#### A 档：在 1LHAASO catalog 内（2 源）

| Source | Dec | 类型 | Fermi QPO（Ren+22 Table 2） | 1LHAASO ID | LHAASO 显著性 |
|---|---|---|---|---|---|
| **Mrk 421** | +38.18° | BL Lac (z=0.030) | 30d LC: 300±64 d (>5σ, 3 cycles)；7d LC: 300±65 d (>5σ) | J1104+3810 | ~73σ |
| **Mrk 501** | +39.73° | BL Lac (z=0.034) | 30d LC: 315±98 d (2.9σ)；7d LC: 326±76 d (>5σ, 7 cycles) | J1653+3943 | ~64σ |

⚠️ 上轮报告主表的「完整 QPO 候选列表」里这两个源被归入 Ren+22「其余 ~18 源」未单独列出 — 本节把它们提升为 LHAASO follow-up 关键目标。

#### B 档：LHAASO 视场内但未在 1LHAASO catalog 检出（20 源）

| Source | Dec | 类型 | Fermi QPO 来源 | VHE 现状 / 评注 |
|---|---|---|---|---|
| OJ 287 | +20.10° | BL Lac (z=0.306) | Kushwaha+20 (314 d); Ren+22 (~300 d) | MAGIC/VERITAS 偶检；VHE 流强弱 |
| S2 0109+22 | +22.74° | BL Lac (z=0.36) | Zhang+23 (~600 d); Sharma+25 (~667 d) | VHE 暗源 |
| 4C +01.02 | +01.58° | FSRQ (z=2.099) | Ren+22 (268, 123 d); Chen+24 (253 d) | 高 z FSRQ，VHE 段 EBL 吸收强 |
| 4C +28.07 | +28.80° | FSRQ (z=1.206) | Ren+22 (244±88 d, 3 cycles >5σ) | 高 z FSRQ |
| NGC 1275 | +41.51° | RDG (z=0.0176) | Ren+22 (92 d, 4 cycles, >5σ) | MAGIC 在 ~50 GeV 检出但 TeV 弱 |
| PKS 0336-01 | −01.78° | FSRQ (z=0.852) | Chen+24 (**94 d ★新发现**) | 高 z FSRQ |
| S5 0716+714 | +71.34° | BL Lac (z=0.300) | Ren+22 (324±77 d, 3.2σ) | MAGIC 已检 VHE；高纬度低海拔可观测时间不长 |
| PKS 0736+01 | +01.62° | FSRQ (z=0.189) | Sharma+25 (~1449 d, 4σ ★首报) | 低 z FSRQ，VHE 候选潜在 |
| S4 0954+658 | +65.57° | BL Lac (z=0.367) | Gong+23 (**66 d 9 cycles >5σ**; 210 d) | 已被 IACT 探到；LHAASO marginal |
| 1H 1013+498 | +49.43° | BL Lac (z=0.212) | Ren+22 (264 / 100 / 52 d, 多 cycles >5σ) | HBL，潜在 VHE 候选 |
| S5 1044+71 | +71.71° | FSRQ (z=1.15) | Ren+22 (**1127 d ★首报**, 117 d) | 高 z + 高纬度 |
| 4C +21.35 | +21.38° | FSRQ (z=0.434) | Ren+22 (66±17 d, 6 cycles >5σ) | MAGIC 已检；VHE 偶发 |
| 3C 273 | +02.05° | FSRQ (z=0.158) | Ren+22 (177 / 97 d, 多 cycles >5σ) | 距 LHAASO 1LHAASO J1219+2915 27.3°；最近 quasar，VHE 段弱 |
| 3C 279 | −05.79° | FSRQ (z=0.536) | Ren+22 (101 / 40 d, 多 cycles >5σ) | MAGIC 已检 VHE；强 BLR/EBL 吸收 |
| PKS 1510-089 | −09.10° | FSRQ (z=0.36) | Ren+22 (~120 d); Chen+24 (92 d, 4.3σ) | HESS/MAGIC 偶检 |
| B2 1520+31 | +31.74° | FSRQ (z=1.489) | Ren+22 (179, 71, 39 d) | 高 z FSRQ |
| CTA 102 | +11.73° | FSRQ (z=1.037) | Ren+22 (366 / 178 d, 多 cycles >5σ) | 高 z FSRQ，VHE 段 EBL |
| PKS 2247-131 | −12.81° | BL Lac (z=0.22) | Ren+22 (214, 34 d) | 视场内（Dec > −20）；中等 z BL Lac，潜在 VHE 候选 |
| 3C 454.3 | +16.15° | FSRQ (z=0.859) | Ren+22 (120±27 d, 4 cycles >5σ) | 极亮 GeV，VHE 暂未确认 |
| PMN J2345-1555 | −15.92° | FSRQ (z=0.621) | Ren+22 (191±44 d, 4 cycles >5σ) | 视场边缘，VHE 暗 |

#### C 档：超出 LHAASO 视场（Dec < −20°，12 源）

| Source | Dec | 类型 | Fermi QPO 来源 |
|---|---|---|---|
| PKS 0521-36 | −36.55° | non-blazar AGN (z=0.056) | Zhang+21 (~1.1 yr); Sharma+23 (268, 295, **806 d**) |
| PKS 0537-441 | −44.08° | BL Lac (z=0.892) | Ren+22 (~286 d); Chen+24 (**55, 54 d ★新双 transient**) |
| PKS 0402-362 | −36.09° | FSRQ (z=1.417) | Chen+24 (103.9 d) |
| PKS 0426-380 | −37.94° | BL Lac (z=1.11) | Ren+22 (85±26 d, 8 cycles >5σ) |
| PKS 0447-439 | −43.84° | BL Lac (z=0.205) | Ren+22 (111±42 d, 7 cycles >5σ); HESS 已检 VHE |
| PKS 0454-234 | −23.41° | FSRQ (z=1.003) | Ren+22 (69±21 d, 4 cycles >5σ) |
| PKS 1424-41 | −42.10° | FSRQ (z=1.522) | Chen+24 (**57 d ★新**, 341 d); Sharma+25 (~357 d) |
| PKS 0244-470 | −46.84° | FSRQ (z=1.385) | Sharma+25 (~225 d) |
| PKS 0405-385 | −38.43° | FSRQ (z=1.285) | Sharma+25 (~1000 d) |
| PKS 0208-512 | −51.02° | FSRQ (z=1.003) | Sharma+25 (~909 d) |
| PKS 0035-252 | −24.99° | FSRQ (z=0.49) | Sharma+25 (~357 d) |
| PKS 2155-304 | −30.23° | BL Lac (z=0.116) | Ren+22 (341±106 d, 3.5σ); HESS 已检 VHE |

C 档多数为 z > 1 的 FSRQ，VHE 段会被 BLR / EBL 吸收 — 即使在视场内也不必然探到。真正合适的后续阵列是规划中的南天高海拔 **SWGO**。

### 重点候选：Mrk 421 / Mrk 501 — Fermi QPO 周期 vs LHAASO 预期可探性

#### Mrk 421（首选候选）

| 维度 | 数据 |
|---|---|
| Fermi QPO 周期 | 300 ± 64 d (Ren+22, 30d binning, >5σ, **3 fitted cycles**) |
| | 300 ± 65 d (Ren+22, 7d binning, >5σ) — 7d/30d 完全一致 |
| LHAASO 流强 | 1LHAASO TS=5343.6 (~73σ)，flux ~3.68 Crab unit (WCDA) — **最亮 extragalactic** |
| LHAASO 数据时长 | ~5 yr 已积累 (2021-03 → 2026 当前)，比 1LHAASO 公开版多 ~3 yr |
| 周期 vs 数据量 | 300 d × 5 yr ≈ **6 cycles 可期** |
| binning 可行性 | WCDA 流强足以做 weekly LC（与 IACT 监测兼容） |

**结论**：数据量、显著性、binning 三方面都最利好。LHAASO QPO 搜寻**首选目标**。

#### Mrk 501（次选候选）

| 维度 | 数据 |
|---|---|
| Fermi QPO 周期 | 326 ± 76 d (Ren+22, 7d binning, >5σ, **7 fitted cycles**) |
| | 315 ± 98 d (Ren+22, 30d binning, **2.9σ**) — ⚠️ binning 敏感 |
| LHAASO 流强 | 1LHAASO TS=4121.6 (~64σ)，flux ~3.77 Crab unit |
| LHAASO 数据时长 | ~5 yr 已积累 |
| 周期 vs 数据量 | 326 d × 5 yr ≈ **5–6 cycles** |
| binning 可行性 | weekly LC 可行但 SNR 弱于 Mrk 421 |

**结论**：值得做，但**marginal**。Mrk 501 在 Fermi 数据里 30d vs 7d binning 显著性差异（2.9σ → >5σ）警示 binning 选择对 QPO 显著性敏感 — 在 LHAASO 端也需多种 binning 验证。

#### LHAASO QPO 搜寻执行建议

1. **优先 Mrk 421**：weekly + monthly 两种 binning 并行
2. **Mrk 501 作为 binning 敏感性对照源**同时跑
3. NGC 4278 (1LHAASO 候选 extragalactic, z=0.002, ~7σ) 流强弱，仅作 stacked / long-term check
4. B 档源待 LHAASO 公开数据扩展后再考虑 stacked analysis

### 比对统计

**2026-05-14（前 Peñil 系列）—— 34 源**：

| 档位 | 数量 | 占比 |
|---|---|---|
| A 档 (in 1LHAASO catalog) | 2 / 34 | ~6% |
| B 档 (视场内未检出) | 20 / 34 | ~59% |
| C 档 (超出视场) | 12 / 34 | ~35% |

**2026-05-14b（含 Peñil 系列扩样）—— 81 源**：

| 档位 | 数量 | 占比 |
|---|---|---|
| A 档 (in 1LHAASO catalog) | 2 / 81 | ~2.5% |
| B 档 (视场内未检出) | 54 / 81 | ~67% |
| C 档 (超出视场) | 25 / 81 | ~31% |

A 档**仍然只有 Mrk 421 / Mrk 501**（其余 79 个源到任何 1LHAASO 源的最近角距均 > 1.2°）。
B 档扩到 54 主要源于 Rico+24 22 新源 + Peñil+22 14 in-FoV 源 + Peñil+25 4 in-FoV 源。

注：1LHAASO catalog 数据截至 2022-09；本节赤纬比对采用 4FGL DR4 J2000 坐标。

### 2026-05-14 全 catalog 位置交叉匹配复核

> **复核动机**：上一版只显式列了 Mrk 421 / Mrk 501 两个 1LHAASO 直接对应，
> 并把其余 in-FoV 源标为「未检出」，未给出实际角距，留下「是否有位置很接近、
> 还没被明确证认的近邻」的疑问。本节用 4FGL DR4 J2000 + 从 1LHAASO catalog
> PDF 抽出的 90 源真实表列 RA/Dec，按 great-circle 角距做正反两向全量交叉
> 匹配，给出可复算的最近邻表。

#### 方法

- Fermi QPO 源 34 个（21 原列 + Ren+22 Table 2 补 13），位置取 4FGL DR4，
  非 blazar 类源（NGC 1275, PKS 0521-36）补充 NED 主名解析。
- 1LHAASO catalog 90 源全部加入（含 KM2A-only Galactic 源），位置取
  `lhaaso_cao2024_1lhaaso_catalog.pdf` 公开 Table 表列 RA/Dec。
- 角距用经典 great-circle 公式
  cos θ = sin δ₁ sin δ₂ + cos δ₁ cos δ₂ cos(α₁−α₂)。

#### 表 1 — Forward 方向：FoV 内 22 个 Fermi QPO 源到最近 1LHAASO 源的角距

按角距升序。**完整列表**，便于复算。

| Fermi QPO | 4FGL RA / Dec (°) | 最近 1LHAASO | 角距 (°) | 该 1LHAASO 既有关联 |
|---|---|---|---|---|
| **Mrk 421** | 166.114 / +38.209 | J1104+3810 | **0.04** | Mrk 421 (确认) |
| **Mrk 501** | 253.468 / +39.760 | J1653+3943 | **0.04** | Mrk 501 (确认) |
| 4C +21.35 | 186.227 / +21.380 | J1219+2915 | 7.95 | (无强关联；曾建议 NGC 4278) |
| NGC 1275 | 49.951 / +41.512 | J0216+4237 | 11.80 | (Perseus 区 UNID) |
| 1H 1013+498 | 153.767 / +49.434 | J1104+3810 | 14.30 | Mrk 421 |
| 4C +28.07 | 39.463 / +28.806 | J0216+4237 | 14.49 | (UNID) |
| PKS 0736+01 | 114.827 / +1.618 | J0703+1405 | 15.33 | 2HWC J0700+143 |
| B2 1520+31 | 230.542 / +31.739 | J1653+3943 | 20.15 | Mrk 501 |
| S2 0109+22 | 18.024 / +22.744 | J0206+4302 | 23.26 | (UNID) |
| S5 0716+714 | 110.473 / +71.340 | J0428+5531 | 24.08 | (UNID) |
| OJ 287 | 133.704 / +20.109 | J0703+1405 | 27.27 | 2HWC J0700+143 |
| 3C 273 | 187.278 / +2.052 | J1219+2915 | 27.29 | (UNID) |
| S4 0954+658 | 149.697 / +65.565 | J1104+3810 | 28.99 | Mrk 421 |
| S5 1044+71 | 162.119 / +71.712 | J1104+3810 | 33.59 | Mrk 421 |
| CTA 102 | 338.152 / +11.731 | J2028+3352 | 35.85 | (Cygnus UNID) |
| 3C 279 | 194.047 / −5.789 | J1219+2915 | 36.11 | (UNID) |
| PKS 0336-01 | 54.879 / −1.776 | J0534+2200 | 36.79 | Crab |
| 3C 454.3 | 343.491 / +16.148 | J2346+5138 | 37.02 | 1ES 2344+514 |
| PKS 1510-089 | 228.211 / −9.100 | J1740+0948 | 41.24 | (Galactic) |
| 4C +01.02 | 17.161 / +1.584 | J0206+4302 | 43.45 | (UNID) |
| PKS 2247-131 | 342.516 / −12.834 | J1959+1129 | 48.85 | (UNID) |
| PMN J2345-1555 | 356.302 / −15.918 | J1959+1129 | 62.24 | (UNID) |

#### 表 2 — Reverse 方向：1LHAASO 高 Galactic latitude (|b|>10°) 源到最近 Fermi QPO 源的角距

只列 |b| > 10° 的 1LHAASO 源（VHE extragalactic 候选区），10 条。

| 1LHAASO | RA / Dec (°) | Gal. b (°) | 既有关联 | 最近 Fermi QPO | 角距 (°) |
|---|---|---|---|---|---|
| J1104+3810 | 166.070 / +38.180 | +65.0 | Mrk 421 | **Mrk 421** | **0.04** |
| J1653+3943 | 253.430 / +39.730 | +38.9 | Mrk 501 | **Mrk 501** | **0.04** |
| J1219+2915 | 184.980 / +29.250 | +82.7 | (NGC 4278 弱候选) | 4C +21.35 | 7.95 |
| J1727+5016 | 261.890 / +50.280 | +33.7 | 1ES 1727+502 | Mrk 501 | 12.07 |
| J0216+4237 | 34.100 / +42.630 | −17.5 | (UNID) | NGC 1275 | 11.80 |
| J0212+4254 | 33.010 / +42.910 | −17.5 | (UNID) | NGC 1275 | 12.60 |
| J0206+4302 | 31.700 / +43.050 | −17.7 | (UNID) | NGC 1275 | 13.56 |
| J0007+7303 | 1.910 / +73.070 | +10.5 | CTA 1 (PWN/SNR) | S5 0716+714 | 28.75 |
| J0622+3754 | 95.500 / +37.900 | +11.0 | LHAASO J0621+3755 | S5 0716+714 | 34.32 |
| J1740+0948 | 265.030 / +9.810 | +20.3 | (UNID) | Mrk 501 | 31.67 |

#### 结论

1. **1LHAASO catalog (截至 2022-09) 内只有 Mrk 421 / Mrk 501 与本调研 Fermi QPO
   样本直接对应**（角距 < 0.1°，比 LHAASO 位置不确定度 0.05–0.4° 还小）。
2. 余下 20 个 FoV 内 Fermi QPO 源到任意 1LHAASO 源的最近邻角距均 **≥ 7.95°**
   （4C +21.35 ↔ J1219+2915），**远超 LHAASO PSF**。位置一致性的「未证认近邻」
   候选 **不存在**。
3. 反向看，1LHAASO 中 3 个 high-|b| 未证认源：
   - **J1219+2915**（|b|=+82.7°，原文建议 NGC 4278，关联弱）— 与所有 34 个
     Fermi QPO 源最小角距 7.95°（4C +21.35）—— **不是任何 Fermi QPO 源的
     合理对应**。
   - **J1727+5016**（|b|=+33.7°，关联 1ES 1727+502，一个 BL Lac）— 1ES 1727+502
     不在本调研覆盖的 Fermi QPO 样本里，但作为 VHE 已证认 BL Lac 可单独被
     检验是否在 GeV 段有 QPO（**留作未来工作的潜在目标**）。
   - **J0206+4302 / J0212+4254 / J0216+4237**（Perseus 区 3 个 KM2A UNID，
     |b|=−17.5°）— 距 NGC 1275 都在 11–14°，**不是位置匹配**；这片区域的
     UHE 起源仍是 LHAASO 内部待解课题，与 Fermi blazar QPO 无关。
4. **任何"位置非常接近、可能还没完全证认"的 Fermi-QPO × LHAASO 候选体在
   1LHAASO catalog 内不存在**。下一步要扩展候选必须等：
   (a) 2022-09 后的 LHAASO 后续公开（>1500 d 累计数据）形成的更新 catalog；
   (b) LHAASO 对单个 blazar 的专文 / ATels（如 2024 后已出现的 NGC 4278
       论文级别报告）；
   (c) 把 Sharma+25 等论文的 C 档 (Dec < −20°) 源留给规划中的 **SWGO**。

> **可复算**：该交叉匹配的具体脚本逻辑写在 plan 文档里；catalog 提取自
> `data/papers/lhaaso_cao2024_1lhaaso_catalog.pdf` Table 1。

### 2026-05-14b 81 源扩样本位置交叉匹配复核

> **复核动机**：Peñil 系列 3 篇加 45 个新 hint/candidate 源进来。重新跑
> 全 81 × 90 great-circle 角距，验证 A 档是否仍是 Mrk 421/501 二件套。

#### 方法

- Fermi QPO 源 **81 个**：34 (原列) + 18 (Peñil+22 new) + 22 (Rico+24 ★ new) +
  5 (Peñil+25 hint new) + 2 (Rico+24 ★ 3C 66A、PKS 1424+240 视为新探测，但
  4FGL 名已在 Ren+22 表中)。位置全部用 4FGL DR4 / Peñil+22 Table 1 / Rico+24
  Table A.1 的 J2000 直接表列。
- 1LHAASO 仍 90 源，与 2026-05-14 节同。

#### 表 — 81 源扩样本 forward match 角距分布

| 角距区间 (°) | Fermi QPO 源数 | 标志源 |
|---|---|---|
| **< 0.1°** | **2** | Mrk 421, Mrk 501 |
| 0.1 – 2.0° | 1 | 3C 66A → J0216+4237 (1.22°) |
| 2.0 – 5.0° | 1 | TXS 0518+211 → J0534+2200 (3.06° Crab 区) |
| 5.0 – 10.0° | 9 | 4C +48.41, TXS 0059+581, 7C 2010+4619, 87GB 164812.2+524023, S4 1030+41, OC 457, 4C +21.35, 4C +47.44, S4 1144+40 |
| 10.0 – 20.0° | 9 | MG2 J130304+2434, OP 313, NGC 1275, B2 0716+33, 1H 1013+498, 4C +28.07, TXS 1902+556, PKS 0736+01, TXS 1318+225 |
| > 20.0° | 34 | 其余 |
| **总计 FoV 内** | **56** | (Dec > −20°) |

#### 「最接近 Mrk 421/501 以外」的近邻候选简评

##### 3C 66A → 1LHAASO J0216+4237 = 1.22°

**最有趣的"近邻但不匹配"案例**：

- 3C 66A：BL Lac, z=0.444, RA 35.67°, Dec +43.04°
- 1LHAASO J0216+4237：UNID, RA 34.10°, Dec +42.63°, KM2A 检出，位置不确定度 0.10°
- 角距 1.22° **远超 PSF (0.10°)**，因此**不是位置匹配**
- 但 3C 66A 是 known VERITAS VHE BL Lac + 长期 γ-ray hint，Rico+24 SSA 给 2.31 yr local 4.6σ / global 3.1σ —— 在所有 79 个非 Mrk421/501 源中**离 1LHAASO 最近**
- Perseus cluster 周围有 3 个相关 1LHAASO UNID (J0206+4302, J0212+4254, J0216+4237)，归因更可能是该区域的 KM2A 系统效应或未知 Galactic 起源，与 3C 66A 高纬位置不直接关联

结论：**仍不存在 < PSF 的 Fermi QPO × 1LHAASO 新对应**；3C 66A 作为「最接近 LHAASO 视野的非配对源」值得在 LHAASO 后续 catalog 公开时优先复核。

##### 5–10° 近邻：9 个源全部是 Galactic 1LHAASO 邻居

落在 5–10° 的 9 对绝大多数来自高 |b| Fermi QPO 源 × 银道面附近 1LHAASO Galactic
UNID（Crab、Cygnus 区、Galactic anticenter）—— 不是物理关联，只是角度限制。

#### 结论

1. **A 档仍是 2 源**（Mrk 421 / Mrk 501）—— 81 源样本下保持不变
2. **没有任何 < PSF 的新对应**；最近的非配对 (3C 66A → J0216+4237 = 1.22°)
   是 PSF 的 12 倍
3. Peñil+25 1492 → 0 全局显著的 null result 与 LHAASO 位置 null 一致暗示：
   **GeV QPO × VHE QPO 关联在现有数据下极稀缺，Mrk 421 / Mrk 501 是仅有的
   两个 robust 标的**
4. 未来扩展候选必须等：
   - LHAASO post-2022-09 公开数据
   - LHAASO 对 PG 1553+113 / 3C 66A 等的专项搜寻（这些 BL Lac 在视场内且
     是 Peñil/Rico 系列的最佳候选）

> **可复算**：cross-match 脚本同 2026-05-14 节，sample 列表参见上节
> "Peñil 系列三篇大样本扩样" 三张表。

## 参考文献

1. **Kushwaha P., Sarkar A., Gupta A. C., Tripathi A., Wiita P. J.**, 2020, *MNRAS*, 499, 653. *A Possible γ-ray Quasi-periodic Oscillation of ~314 days in the Blazar OJ 287.* [arXiv:2009.13754](https://arxiv.org/abs/2009.13754) · [DOI 10.1093/mnras/staa2899](https://doi.org/10.1093/mnras/staa2899)
2. **Zhang H., Yan D., Zhang P., Yang S., Zhang L.**, 2021, *ApJ*, 919, 58. *A Quasi-periodic Oscillation in the γ-ray Emission from the Non-blazar Active Galactic Nucleus PKS 0521-36.* [arXiv:2106.10040](https://arxiv.org/abs/2106.10040) · [DOI 10.3847/1538-4357/ac0cf0](https://doi.org/10.3847/1538-4357/ac0cf0)
3. **Ren H. X., Cerruti M., Sahakyan N.**, 2023, *A&A* (submitted Feb 2023). *Quasi-periodic oscillations in the γ-ray light curves of bright active galactic nuclei.* [arXiv:2204.13051](https://arxiv.org/abs/2204.13051)
4. **Gong Y., Tian S., Zhou L., Yi T., Fang J.**, 2023, *ApJ*, 949, 39. *Two Transient Quasi-periodic Oscillations in γ-Ray Emission from the Blazar S4 0954+658.* [arXiv:2304.03085](https://arxiv.org/abs/2304.03085) · [DOI 10.3847/1538-4357/acca7b](https://doi.org/10.3847/1538-4357/acca7b)
5. **Zhang H., Wu F., Dai B.**, 2023, *PASP*, 135, 074101. *The detection of possible γ-ray quasi-periodic modulation with ~600 days from the blazar S2 0109+22.* [arXiv:2306.11579](https://arxiv.org/abs/2306.11579) · [DOI 10.1088/1538-3873/acdf1f](https://doi.org/10.1088/1538-3873/acdf1f)
6. **Sharma A., Prince R., Bose D.**, 2023, *MNRAS* (submitted). *Detection of gamma-ray quasi-periodic oscillations in non-blazar AGN PKS 0521-36.* [arXiv:2312.12623](https://arxiv.org/abs/2312.12623)
7. **Chen J., Yu J., Huang W., Ding N.**, 2024, *MNRAS*, 528, 6807. *Transient quasi-periodic oscillations in the gamma-ray light curves of bright blazars.* [arXiv:2401.10658](https://arxiv.org/abs/2401.10658) · [DOI 10.1093/mnras/stae416](https://doi.org/10.1093/mnras/stae416)
8. **Sharma A., Chaudhary S., Sarath A., Bose D.**, 2025, preprint. *Exploring Year-timescale Gamma-ray Quasi-Periodic Oscillations in Blazars: Evidence for Supermassive Binary Black Holes Scenario.* [arXiv:2505.23697](https://arxiv.org/abs/2505.23697)
9. **Peñil P., Ajello M., Buson S., Domínguez A., Westernacher-Schneider J. R., Rico A., Adhikari S., Zrake J.**, 2022, preprint. *Search for Periodic Variability in γ-ray Blazars Using Fermi-LAT.* [arXiv:2211.01894](https://arxiv.org/abs/2211.01894) — 24 hint blazars, 12 yr; PG 1553+113 global ≈1.8σ 唯一通过
10. **Rico A., Domínguez A., Peñil P., Ajello M., Buson S., Adhikari S., Movahedifar M.**, 2024, *A&A* (in press). *Singular Spectrum Analysis of Fermi-LAT Blazar Light Curves: A Systematic Search for Periodicity and Trends in the Time Domain.* [arXiv:2412.05812](https://arxiv.org/abs/2412.05812) · [DOI 10.1051/0004-6361/202452495](https://doi.org/10.1051/0004-6361/202452495) — 494 源 SSA，46 candidates (25 new γ-ray)
11. **Peñil P., Domínguez A., Buson S., Ajello M., Adhikari S., Rico A.**, 2025, preprint (v2). *Extensive Analysis of γ-Ray Periodicity in Jetted AGN from the 4FGL Catalog Using Fermi-LAT Observations.* [arXiv:2509.14013](https://arxiv.org/abs/2509.14013) — 1492 jetted AGN (排除 24 hint 源)，9-method ensemble，**0 global-significant QPO**
12. **Cao Z. et al.** (LHAASO Collaboration), 2024, *ApJS*, 271, 25. *The First LHAASO Catalog of Gamma-Ray Sources.* [arXiv:2305.17030](https://arxiv.org/abs/2305.17030) · [DOI 10.3847/1538-4365/acfd29](https://doi.org/10.3847/1538-4365/acfd29) — LHAASO catalog 比对节的数据源

---

*报告生成：2026-05-13 · 修订：2026-05-13 加入 LHAASO catalog 比对节 · 2026-05-14 补 Ren+22 13 源 + 全 catalog 位置交叉匹配复核 · **2026-05-14b 集成 Peñil 系列三篇（Peñil+22 + Rico+24 + Peñil+25），样本从 34 扩到 81 unique 源** · 数据来源：上述 11 篇 Fermi 论文 + 1LHAASO catalog（保存在 `/mnt/mydisk/server/projects/QPO/data/papers/`）· 数字与论文原表/正文对应；同一源在不同论文给出不一致周期时，原值保留 — 不在本报告中合并。*
