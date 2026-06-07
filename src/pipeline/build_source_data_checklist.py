#!/usr/bin/env python3
"""Render a Markdown data-availability checklist for survey source candidates."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.project_paths import PROJECT_ROOT
from utils.source_registry import DEFAULT_SURVEY_SOURCE_IDS, SOURCE_REGISTRY, SourceRecord


DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "lhaaso-agn-qpo-data-checklist.md"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--source-ids",
        nargs="+",
        default=list(DEFAULT_SURVEY_SOURCE_IDS),
        choices=sorted(SOURCE_REGISTRY),
        help="Survey source ids to include in the checklist.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    records = [SOURCE_REGISTRY[source_id] for source_id in args.source_ids]
    content = render_markdown(records)
    args.output.write_text(content, encoding="utf-8")
    print(f"[OK] wrote {args.output.relative_to(PROJECT_ROOT)}")


def render_markdown(records: list[SourceRecord]) -> str:
    lines: list[str] = []
    lines.append("# LHAASO AGN QPO Survey 数据可获得性检查表")
    lines.append("")
    lines.append("日期：2026-05-27")
    lines.append("")
    lines.append("## 用途")
    lines.append("")
    lines.append("这份检查表面向下一步 IHEP 侧拉数和本地接入，用来回答两个问题：")
    lines.append("")
    lines.append("1. 每个候选源当前在本地仓库里已经有哪些数据产物。")
    lines.append("2. 下一步去 IHEP 时，优先应该补哪些 WCDA / Fermi 输入。")
    lines.append("")
    lines.append("状态说明：")
    lines.append("")
    lines.append("- `present`：本地已经存在对应文件或目录。")
    lines.append("- `missing`：按当前命名约定尚未发现对应文件。")
    lines.append("- `n/a`：当前不作为该源默认输入要求。")
    lines.append("")
    lines.append("## 汇总表")
    lines.append("")
    lines.append("| Source ID | Label | Priority | WCDA week | WCDA day | Fermi week | aligned | periodicity | 下一步建议 |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for record in records:
        summary = source_summary(record)
        lines.append(
            "| {source_id} | {label} | {priority} | {wcda_week} | {wcda_day} | {fermi_week} | {aligned} | {periodicity} | {next_step} |".format(
                **summary
            )
        )
    lines.append("")
    lines.append("## 分源检查")
    lines.append("")
    for record in records:
        lines.extend(render_source_section(record))
    return "\n".join(lines) + "\n"


def source_summary(record: SourceRecord) -> dict[str, str]:
    wcda_week = status_tag(record.expected_wcda_week_path())
    wcda_day = status_tag(record.expected_wcda_day_path())
    fermi_week = status_tag(record.expected_fermi_week_path())
    aligned = status_tag(record.expected_aligned_week_path())
    periodicity = status_tag(record.expected_periodicity_summary_path())

    if wcda_week == "missing":
        next_step = "从 IHEP 补拉 WCDA 周光变"
    elif record.default_wcda_day and wcda_day == "missing":
        next_step = "补拉 WCDA 日光变"
    elif record.default_fermi_week and fermi_week == "missing":
        next_step = "补齐 Fermi 周光变"
    elif aligned == "missing":
        next_step = "生成 aligned 周序列"
    elif periodicity == "missing":
        next_step = "运行 periodicity_v1"
    else:
        next_step = "可直接进入 survey 分析"

    return {
        "source_id": record.source_id,
        "label": record.label,
        "priority": record.priority,
        "wcda_week": wcda_week,
        "wcda_day": wcda_day,
        "fermi_week": fermi_week,
        "aligned": aligned,
        "periodicity": periodicity,
        "next_step": next_step,
    }


def render_source_section(record: SourceRecord) -> list[str]:
    lines: list[str] = []
    lines.append(f"### {record.label} (`{record.source_id}`)")
    lines.append("")
    lines.append(f"- LHAASO 名称：`{record.lhaaso_name}`")
    lines.append(f"- 类型：`{record.source_type}`")
    lines.append(f"- 优先级：`{record.priority}`")
    lines.append(
        f"- LHAASO 显著性：`{format_sigma(record.lhaaso_significance_sigma)}`；variability：`{record.variability_flag}`"
    )
    lines.append(f"- 备注：{record.notes}")
    lines.append("")
    lines.append("| 项目 | 状态 | 期望路径 |")
    lines.append("|---|---|---|")
    lines.append(render_row("WCDA weekly", record.expected_wcda_week_path()))
    lines.append(render_row("WCDA daily", record.expected_wcda_day_path()))
    lines.append(render_row("Fermi weekly", record.expected_fermi_week_path()))
    lines.append(render_row("aligned weekly", record.expected_aligned_week_path()))
    lines.append(render_row("periodicity summary", record.expected_periodicity_summary_path()))
    lines.append("")
    lines.append("建议动作：")
    lines.append("")
    for action in suggested_actions(record):
        lines.append(f"- {action}")
    lines.append("")
    return lines


def render_row(label: str, path: Path | None) -> str:
    if path is None:
        return f"| {label} | n/a | - |"
    return f"| {label} | {status_tag(path)} | `{path.relative_to(PROJECT_ROOT)}` |"


def status_tag(path: Path | None) -> str:
    if path is None:
        return "n/a"
    return "present" if path.exists() else "missing"


def format_sigma(value: float | None) -> str:
    if value is None:
        return "not listed"
    return f"{value:.2f}σ"


def suggested_actions(record: SourceRecord) -> list[str]:
    actions: list[str] = []
    wcda_week = record.expected_wcda_week_path()
    wcda_day = record.expected_wcda_day_path()
    fermi_week = record.expected_fermi_week_path()
    aligned = record.expected_aligned_week_path()
    periodicity = record.expected_periodicity_summary_path()

    if not wcda_week.exists():
        actions.append("IHEP 侧优先导出或同步 WCDA 周尺度光变到 `data/processed/wcda_week/`。")
    if wcda_day is not None and not wcda_day.exists():
        actions.append("如果后续要做日尺度 WWZ/CWT，再补拉 WCDA 日尺度光变。")
    if fermi_week is not None and not fermi_week.exists():
        actions.append("补齐该源的 Fermi 周尺度 CSV，便于做多波段对照。")
    if wcda_week.exists() and not aligned.exists():
        actions.append("用统一 survey 流水线生成 `aligned/<source_id>/wcda_weekly_aligned.csv`。")
    if aligned.exists() and not periodicity.exists():
        actions.append("在本地先跑一轮 weekly `periodicity_v1` quick-look。")
    if not actions:
        actions.append("本地输入已经到位，可以直接进入周期搜索和显著性评估。")
    return actions


if __name__ == "__main__":
    main()
