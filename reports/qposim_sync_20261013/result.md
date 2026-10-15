---
title: qposim 已同步到 Mac
subtitle: 2026-10-13 19:29 · 代码、报告与小型分析产品副本
template: doc
theme: paper
lang: zh
---

PDC 当前工作区的代码、配置、测试、论文和报告已同步到 Mac。Git 跟踪以 PDC 为准，Mac 不建立 Git 仓库。

## A 同步结果

| 项目 | 结果 |
|---|---|
| 来源 | `PDC:/home/luoji/qposim/`，真实路径 `/mnt/mydisk/qposim/` |
| Mac 目录 | `/Users/luoji/Documents/projects/QPO/qposim/` |
| 本轮带回 | 28,766 个普通文件，2,210,553,358 字节，约 2.21 GB |
| 校验 | 所有文件 SHA-256、大小、权限与远程清单一致 |
| 符号链接 | 2,510 个；2,387 个服务器内部绝对链接转为 Mac 相对链接 |
| 本地旧文件 | 全部 167 个保留；其中 7 个与远端同名且内容一致，160 个为本地独有文件 |
| 原目录备份 | `/Users/luoji/Documents/projects/QPO/archive/qposim_mac_before_sync_20261013/`，约 341 MiB |
| 最终目录体量 | `du -sh` 约 2.5 G，包含保留的本地旧文件与动画 |
| 本地 Git | 未创建；主目录及嵌套目录均无 `.git` 元数据 |

备份中的全部原文件也已逐项校验。没有发现本地同名内容冲突，没有删除本地独有文件。

## B 已带回的主要内容

| 内容 | Mac 内入口，相对 qposim 根目录 |
|---|---|
| 项目说明与结果索引 | `AGENTS.md`、`devlog.md`、`hxf_toroidal_fig/README.md`、`hxf_toroidal_fig/docs/results.md` |
| 中文研究框架 | `hxf_toroidal_fig/paper/latex/framework.tex`、`framework.pdf`、`framework_reading.pdf` |
| 英文论文项目 | `hxf_toroidal_fig/paper/aa_draft/` 的源码、模板与现有 PDF |
| 喷流模拟代码 | 六个 HD/MHD case、`common/`、各 `configs/`、`scripts/`、makefile、作业提交脚本 |
| 后处理与辐射分析 | `postprocess/src/`、`tests/`、`visualization/`、kmonty 与 RaptorP 管线源码、配置和报告 |
| 外部辐射源码 | `tools/RaptorP*` 的源码副本和已有修改；嵌套仓库的 commit、分支及修改状态另存清单 |
| 其他案例 | `RTI/`、`gpluto-lab/`、`hd2d_overpressured_jet/`、`initial_setup_gpluto/`、`tutorial/` |
| 报告附件 | PNG/SVG/PDF、CSV/TSV/JSON、明确引用的小型附件；保留它们在运行目录中的原路径 |
| 小型输入与配置 | 不超过 5 MiB 的 DAT/NPZ/NPY、XML/XSPEC 配置、LaTeX 样式和轻量快照索引 |

本次在初筛基础上补充了源码头文件、XML 配置、LaTeX bibliography 样式和小型索引。没有重新计算、编译或改变科学结果。

## C Git 权威与同步方式

PDC GitHub SSH 认证已在本轮验证可用。来源工作区为 `codex/kmonty-pump-fix`，HEAD 为 `36d9eb358ea4877e12b7472f02e15aa587d01220`，还包含未提交工作文件。

本次复制的是 PDC 当前磁盘工作文件，包括选定的未跟踪文件，而非仅复制 GitHub 已提交版本。没有切换 PDC 分支、提交、push 或复制服务器的 75 G Git 元数据。PDC 的其他兄弟 worktree 不在此次来源范围内。

执行过程：生成远程文件和 SHA-256 清单，检查 Mac 文件与大小写冲突，rsync 预演，传入临时目录，逐文件校验，保存原 Mac 目录，合入目标目录，再次核验。传输使用文件清单，不跟随数据符号链接，也未使用 `--delete`。

Mac 只作为文件副本。未来修改应以 PDC 工作区为准；本次没有配置自动同步或定时任务。

## D 范围限制与证据

没有带回模拟快照、大型 FITS/HDF5、编译产物、安装的 Python/系统依赖、整套原始观测数据和大多数日志、动画。

1,891 个符号链接在 Mac 可以访问；619 个指向未同步的数据、日志或外部依赖，保留为路径记录。这些目标在 PDC 存在，Mac 上需要远程数据的分析仍应到 PDC 执行。

文档引用的静态扫描另记录 441 个在 PDC 原目录中未解析到文件的引用，包含历史路径与示例，未经逐项人工确认。本次保持原文，没有改写报告结论或历史引用。

核查文件均位于本报告同目录：`remote_manifest.json` 保存原始 SHA-256 和 Git 来源；`final_verification.json` 保存最终校验结果；`rewritten_symlinks.json` 保存链接转换；`unavailable_dependencies.json` 保存未同步目标；`local_before.json` 与 `local_comparison.json` 保存原 Mac 文件状态；`rsync_*.log` 保存传输记录。

未运行模拟、GPU 构建或科学回归测试。本次验收目标是传输完整性和本地文件保护，不能据此认定所有计算管线可在 Mac 独立运行。
