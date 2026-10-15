---
title: ETO 数据恢复核查
subtitle: 2026-10-13 · 新工作区 /mnt/newdisk/shijie/QPO
template: doc
theme: paper
lang: zh
---

## A 现有 QPO 分析可以继续

```callout ok 大部分光变与时序结果已经保住
本机与新 ETO 的 data/results 共 2,091 个文件 SHA256 一致。
优先恢复配置和拟合记录。仅在需要重新拟合时恢复大型上游输入。
```

不能从光变反推 Fermi 光子事件、spacecraft 文件或仪器响应。
旧盘缺少完整清单，本报告只列已核实的当前缺口。

## B 已经恢复了什么

| 数据 | 新 ETO 现状 | 核对依据 |
| --- | --- | --- |
| WCDA weekly counts | 10 源 × 264 行 | IHEP 有相同内容副本 |
| WCDA strict weekly flux | 10 源 × 229 行 | 保留 strict 版本 |
| 官方 WCDA 2-day/8-day LC | 22 份；每源 803/200 行 | 与 IHEP release 哈希全相同 |
| 四控制源 LC | 4 源 × 803 行 | 完整导出包也在 |
| Fermi 两主目标 2-day/8-day LC | 4 套 CSV/FITS/PNG | 本机与 ETO 哈希一致 |
| 谱指数 A/B/C LC | 1,200 行 | 与 IHEP r2 输出哈希相同 |
| 对齐与周期结果 | 79 份 aligned CSV、191 份周期 NPZ | 已恢复现存产品 |

本机也保留 4 份 WCDA daily CSV 和 Mrk 421 Fermi weekly LC。
文件行数齐全，不代表每个时间箱拟合成功。已有失败标记仍需保留。

## C 当前缺口如何补

| 当前缺少 | 类型 | 恢复方式 |
| --- | --- | --- |
| Fermi PH/FT1、SC/FT2 | 原始科学分析输入 | 找副本或重新下载；不能从 LC 反推 |
| Fermi 两份指定弥散背景模型 | 外部模型 | 恢复匹配版本；标定与星表环境待核查 |
| data/config 下两份 source-model YAML | 配置与来源记录 | IHEP 仍有，直接备份 |
| 官方 handoff、fit manifests、逐 bin 日志 | 拟合记录 | IHEP 仍有，先取回轻量部分 |
| MakeLC 与 J1952 完整 provenance 包 | 代码与过程记录 | IHEP 仍有，直接备份 |
| Fermi monthly、ROI、chunk 缓存 | 派生数据 | 输入齐备后重算 |
| Mrk 501 legacy Fermi weekly LC | 派生数据 | 重新做 7-day 拟合 |
| WCDA HDF5 模拟库 | 派生数据 | 默认输入仍在，可按参数重新生成 |

8-day flux 重采样不等价于重新做 7-day likelihood。
旧 Fermi 脚本和配置仍含旧盘路径。此次没有修改它们。

## D 原始输入与派生数据怎样区分

```flow
探测器原始文件 --> 官方天图: 重建与标定
官方天图 -> countsCSV: 提取计数
官方天图 -> fluxCSV: 官方拟合
响应与谱模型 -> fluxCSV: 标定与模型
countsCSV --> fluxCSV: 对应计数拟合流程
fluxCSV -> 对齐序列
对齐序列 -> CWT与WWZ
CWT与WWZ -> 显著性与报告
```

官方天图已是重建后的观测数据。MC、响应和背景模板属于独立输入。
它们都不能仅靠最终 LC 生成。
data/raw 中的 CSV 和 original.csv 是原始导出副本，不是探测器事件。

## E IHEP 仍保留哪些资源

| 资源 | 已核实的数量或状态 |
| --- | --- |
| 探测器 raw | 抽查 2022/0101 目录，可列出 23 项 |
| 官方 DailySkyMap | 1,592 个 ROOT 文件名 |
| 用户周合并天图 | 264 个 ROOT 文件名 |
| 2/8/32-day Mapfile | 1,052/1,053 个路径存在且可读 |
| MC period 库 | 83 period，166 个 rec/corsika 文件名 |
| 官方 response | 两分支共 166 个路径可读 |
| 配置所用 Simufile | 两分支共 166 个路径可读 |
| Src_Main、DGE 模板 | 可读；Src_Main 与旧 release 哈希相同 |

2-day/8-day 天图体积约 541.5/145.7 GB，采用十进制 GB。
继续 QPO 分析无需先把这些天图全部搬到 ETO。

## F 三个需要保留的区别

```callout warn LC0687 属于已有数据缺口
对应 2-day 天图在 IHEP 当前不存在。
历史 release 已记录这个共同失败 bin。不能归因于本次 ETO 坏盘。
```

1,053 份逐 bin YAML 与 IHEP 相同；master YAML 有版本差异。
恢复时并存版本，避免覆盖原始快照。

J1952 作业链接指向节点本地 tmp，当前 lxlogin002 无法访问。
其 12.83 MB provenance 压缩包仍在，目录检查可打开。

点估计 LC、旧 strict flux 和 profile pilot 属于不同产品。
没有证据证明全样本 profile LC 已完成，不把它列作坏盘丢失。

## G 按工作需求恢复

| 目标 | 先做什么 |
| --- | --- |
| 保住可追溯性 | 备份两份模型 YAML、handoff、manifests、ParRes/log、脚本及 J1952 包 |
| 继续已有 QPO 分析 | 使用现成 LC；仅按新需求重做模拟 |
| 重做 Fermi 光变 | 恢复 PH、SC、背景和环境，再重建 ROI 与分箱结果 |
| 重做 WCDA 光变 | 在 IHEP 使用已有天图、response 和官方程序拟合 |
| 改变探测器重建方案 | 才需要回到 raw，并使用集群调度 |

Fermi 事件与姿态可从 [NASA FSSC](https://fermi.gsfc.nasa.gov/ssc/data/) 重新检索。
背景文件见 [LAT 官方背景模型](https://fermi.gsfc.nasa.gov/ssc/data/access/lat/BackgroundModels.html)。

## H 核查边界与详细证据

核查包括本机/ETO 文件哈希、LC 行数、IHEP 文件内容匹配和资源路径。
抽查 9 个拟合的 Fit、ParInit、ParRes 和日志，文件均可读。
没有全量校验 ROOT 内部对象、所有拟合或全时段探测器 raw。
没有传输业务数据、重新拟合或提交任务。

[完整清单与具体路径](README.md)

[本机与 ETO 差异记录](local_eto_comparison.json)

[IHEP 上游资源核查](ihep_public_dependencies.json)
