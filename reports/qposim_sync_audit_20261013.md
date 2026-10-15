---
title: qposim：Git 与 Mac 轻量同步核查
subtitle: 2026-10-13 · PDC 实机检查与 GitHub 实时 refs 核对
template: doc
theme: paper
lang: zh
---

PDC 已建立独立 Git 仓库，也曾推送到 GitHub；但 GitHub 没有保存当前完整工作状态。Mac 可以保存约 GB 级的代码与报告副本，模拟快照继续保留在 PDC。

## A Git 跟踪与推送现状

| 检查项 | 实测结果 |
|---|---|
| PDC 工作区 | `/home/luoji/qposim`，符号链接到 `/mnt/mydisk/qposim` |
| 独立仓库 | 是；origin 为 `git@github.com:Pluto235/qposim.git` |
| 当前分支 | `codex/kmonty-pump-fix` |
| 当前 HEAD | `36d9eb358ea4877e12b7472f02e15aa587d01220`，提交日期 2026-10-09 |
| GitHub 实时分支 | `codex/kmonty-pump-fix` → `d52abddb23427137decd431954a3fc53f40b3cc1` |
| GitHub 另一分支 | `codex/kmonty-stable` → `1055a6f9d44ded83ab58524eb878b36ea20a47d1` |
| 当前分支差异 | 相对实时 GitHub 分支落后 0、领先 14 个提交 |
| 已跟踪路径 | 763；主要是 kmonty 相关文件，不代表全项目已纳入 Git |
| 工作区状态 | 9 修改、4 类型变化、60 删除状态、54,579 未跟踪文件 |
| Mac 现有副本 | 约 341 MiB；没有独立 `.git`，父仓库 QPO 的 `.gitignore` 第 46 行忽略 `/qposim/` |

GitHub 的两个分支已用 Mac 上 `git ls-remote --heads` 实时验证。PDC 的缓存远程 refs 与此一致，随后用 `git rev-list --left-right --count origin/codex/kmonty-pump-fix...HEAD` 得到 `0 14`。

未跟踪文件包含源码、报告和生成产物，不能把 54,579 个文件都视为应提交源码。部分删除和类型变化与目录整理、兼容链接有关，需按迁移清单审阅。

PDC 上读取 GitHub 失败：`Permission denied (publickey)`。Mac 可以读取远程；本轮没有测试写入权限，也没有推送任何内容。

## B 存储体量与同步预算

| 内容 | 实测体量 | 本地处理建议 |
|---|---|---|
| `hxf_toroidal_fig/` | `du` 约 2.3 T | 选择代码、报告及依赖附件 |
| 模拟 `.dbl` 文件 | 约 2.43 TB，1,266 个 | 留在 PDC |
| `.git/` | 约 75 G | 不直接 rsync |
| Git 有效 pack | 6.60 GiB，另有约 210 MiB 松散对象 | 完整历史并不轻量 |
| Git 临时对象 | 183 个，67.51 GiB | 本轮未清理；需先检查活动 Git 进程和完整性 |
| 初筛代码、配置、文档、图表 | 14,172 个普通文件，801,928,149 字节 | 约 0.80 GB，排除 `tools/` 与缓存 |
| 加入 TSV 汇总表 | 14,894 个普通文件，1,500,447,321 字节 | 约 1.50 GB；还需确认必要附件 |

以上是按文件类型得到的候选范围，不是已经批准或验证完备的传输清单。未跟随符号链接；未计 Git、缓存和 `tools/`。候选包含生成文件，后续可进一步压缩。

初筛含 TSV 的主要目录体量：`hxf_toroidal_fig/` 1.33 GB、`gpluto-lab/` 56.6 MB、`RTI/` 47.6 MB、`initial_setup_gpluto/` 40.0 MB、`documents/` 13.3 MB、`tutorial/` 8.6 MB。

## C Mac 应保留什么

| 类别 | 具体内容 |
|---|---|
| 项目说明 | 各级 `AGENTS.md`、README、devlog、`hxf_toroidal_fig/docs/`、`paper/` |
| 模拟代码 | `HD/`、`MHD1-2D/`、`MHD1/`、`MHD2/`、`MHD3/`、`MHD2w/` 的源码、makefile、`configs/`、`scripts/`；共享 `common/` |
| 后处理与测试 | `postprocess/src/`、`tests/`、`visualization/`、各辐射管线的维护源码、配置、测试和路径清单 |
| 正式分析成果 | 报告 Markdown/HTML/PDF、引用的 PNG/SVG、必要 CSV/TSV/JSON 汇总、manifest 与校验信息 |
| 其他子案例 | `initial_setup_gpluto/`、`hd2d_overpressured_jet/`、`RTI/`、`gpluto-lab/` 中的维护代码、输入与报告 |
| 环境与来源 | requirements、环境说明、求解器版本、作业命令、数据路径、随机种子、输入/输出校验值 |
| 外部代码 | `tools/RaptorP` 等独立仓库的远程 URL、commit 和未提交补丁；需要离线阅读时另选源码 |

报告入口优先看 `hxf_toroidal_fig/docs/results.md`。例如 t=400 辐射图位于 `MHD3/runs/116705/postprocess/raptorp_t400/figures/`，多频光变汇总位于 `MHD3/runs/116836/postprocess/raptorp_lc/`；不能只复制 `docs/`。

不默认同步模拟快照、重启文件、大型 HDF5/FITS、原始光子与响应数据、编译产物、Python 环境、缓存及所有动画。少量复现必需的小型 NPZ/DAT 或测试输入，应按报告与测试依赖显式补入清单。

## D 同步的实际难点

| 难点 | 影响与处理 |
|---|---|
| Git 覆盖不足 | 维护源码和报告大量未提交；只 clone GitHub 会漏掉当前工作 |
| 数据和成果混放 | `runs/` 里既有快照，也有报告、配置和图；不能整目录排除 |
| 忽略规则不等于同步规则 | 子目录 `.gitignore` 忽略 `runs/`、figures、tables 等，但这些目录可包含需要带回的报告附件 |
| 符号链接 | 兼容源码链接应保留；数据链接可能在 Mac 悬空。不要使用 rsync `-L`，否则可能复制 TB 级目标 |
| 嵌套仓库与 worktree | RaptorP 独立源码和未提交状态不由主仓库自动备份；worktree 的 `.git` 文件可能指回 PDC |
| 历史含大文件 | 全部本地分支的可达历史有 14 个超过 50 MiB 的 blob，最大 FITS 约 1.245 GB；工作树变小不代表历史变小 |
| 本地已有内容 | Mac 有自己的旧代码和动画；首次同步先比对冲突、保留本地独有文件，避免直接覆盖或 `--delete` |
| 本机可读与可运行不同 | Linux/CUDA/MPI、`PLUTO_DIR=/home/luoji/opt/gPLUTO-870aa807` 和远程数据路径不适用于 Mac；本地先保证阅读和轻量后处理 |

PDC 的 `/mnt/mydisk` 是本次实际确认的有效路径，与 ETO 已失效的同名路径属于不同服务器，不能套用 ETO 的迁移结论。

## E 建议落地顺序

先建立文件清单：代码与配置、报告及其附件、少量必要输入。对 Mac 已有同名文件比较哈希，冲突单列，保留本地独有文件。

首次把选定的 PDC 当前工作文件同步到临时目录，执行 rsync dry-run，核对候选总量，再校验 SHA-256 和报告链接。该路径不依赖 PDC 的 GitHub 写入认证，也不需要复制 75 G 的 `.git`。

长期建议继续把 qposim 作为独立仓库，让 QPO 父项目保留 `/qposim/` 忽略。整理维护源码的 Git 跟踪，逐项审阅搬移与链接；代码和小型文档走 Git，报告附件与派生汇总走独立 rsync 清单，模拟数据留在 PDC。

如 Mac 需要完整独立 Git 工作区，可从 GitHub 浅克隆到临时目录，再显式带入当前未推送提交与未提交文件；先检查其他本地分支的成果归属。当前分支以外还有 author、stable、mkn421、pks1510 等本地分支，单个分支的副本不覆盖它们全部工作。

完整历史迁移和历史清理应单独处理，不能把删除 pack 临时文件、历史重写或直接 `git add -A` 当作本轮同步的前置操作。

## F 本轮边界与验证

本轮读取 PDC Git、目录、符号链接、对象大小和项目索引，实时读取 GitHub 分支；只生成本地检查报告并追加 QPO 工作日志。

没有执行同步、push、Git 历史重写、远程清理、模拟作业或逐文件内容校验。约 1.50 GB 是初筛估计；最终清单仍须核对报告附件、嵌套源码和 Mac 同名冲突。
