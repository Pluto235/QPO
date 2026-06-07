#!/usr/bin/env python3
"""Build the 10-source AGN WCDA weekly quick-look survey report."""

from __future__ import annotations

import html
import sys
from datetime import date
from pathlib import Path

import pandas as pd


SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.project_paths import ALIGNED_DIR, PERIODICITY_DIR, PROJECT_ROOT  # noqa: E402
from utils.source_registry import WCDA_STRICT_FLUX_SOURCE_IDS, WCDA_WEEK_SURVEY_SOURCE_IDS, get_source  # noqa: E402


SURVEY_ALIGNED_DIR = ALIGNED_DIR / "agn_wcda_weekly_survey"
SURVEY_PERIODICITY_DIR = PERIODICITY_DIR / "agn_wcda_weekly_survey"
FLUX_SURVEY_ALIGNED_DIR = ALIGNED_DIR / "agn_wcda_weekly_flux_survey"
FLUX_SURVEY_PERIODICITY_DIR = PERIODICITY_DIR / "agn_wcda_weekly_flux_survey"
REPORT_MD = PROJECT_ROOT / "reports" / "agn_wcda_weekly_survey_report.md"
REPORT_HTML = PROJECT_ROOT / "reports" / "agn_wcda_weekly_survey_report.html"
SUMMARY_CSV = SURVEY_PERIODICITY_DIR / "agn_wcda_weekly_survey_summary.csv"
SIGNIFICANCE_SUMMARY_CSV = SURVEY_PERIODICITY_DIR / "agn_wcda_weekly_significance_summary.csv"
FLUX_SUMMARY_CSV = FLUX_SURVEY_PERIODICITY_DIR / "agn_wcda_weekly_flux_survey_summary.csv"
FLUX_SIGNIFICANCE_SUMMARY_CSV = FLUX_SURVEY_PERIODICITY_DIR / "agn_wcda_weekly_flux_significance_summary.csv"
REQUIRED_IMAGES = ("wcda_weekly_counts.png", "wcda_weekly_periodicity.png")
SIGNIFICANCE_IMAGES = ("wcda_weekly_cwt_global_significance.png", "wcda_weekly_wwz_global_significance.png")
FLUX_IMAGES = ("wcda_strict_flux_weekly_lightcurve.png", "wcda_strict_flux_weekly_periodicity.png")
FLUX_SIGNIFICANCE_IMAGES = (
    "wcda_strict_flux_weekly_cwt_global_significance.png",
    "wcda_strict_flux_weekly_wwz_global_significance.png",
)
TIER_A_MEDIAN_TS = 9.0
TIER_A_FRAC_TS9 = 0.50
TIER_B_FRAC_TS9 = 0.10
TIER_B_FRAC_TS4 = 0.25
FERMI_QPO_SURVEY_URL = "https://pluto235.github.io/any-reports/qpo-fermi-lat-detections.html"
FERMI_QPO_PRIOR_CONTEXT = {
    "mkn421": {
        "status": "Reported Fermi-LAT QPO prior",
        "class": "reported",
        "summary": (
            "The prior Fermi-LAT survey highlights Mrk 421 as a key LHAASO follow-up target: "
            "Ren+22 reports a CWT candidate at 300 +/- 64 d in 30 d bins (>5 sigma, 3 fitted "
            "cycles) and 300 +/- 65 d in 7 d bins (>5 sigma). The same survey lists Mrk 421 as "
            "one of only two direct Fermi-QPO / 1LHAASO catalog matches."
        ),
        "interpretation": (
            "This is the strongest external GeV prior in the current sample and supports treating "
            "Mrk 421 as the primary timing-grade WCDA target."
        ),
    },
    "mkn501": {
        "status": "Reported Fermi-LAT QPO prior",
        "class": "reported",
        "summary": (
            "The prior Fermi-LAT survey lists Mrk 501 as the second direct Fermi-QPO / 1LHAASO "
            "catalog match. Ren+22 reports 326 +/- 76 d in 7 d bins (>5 sigma, 7 fitted cycles) "
            "and 315 +/- 98 d in 30 d bins (2.9 sigma)."
        ),
        "interpretation": (
            "This is a useful GeV prior, but the 30 d versus 7 d difference flags binning "
            "sensitivity; WCDA results should be interpreted with that caveat."
        ),
    },
    "1es1959p650": {
        "status": "No exact-source Fermi-LAT QPO prior in the survey",
        "class": "none",
        "summary": (
            "The prior Fermi-LAT QPO survey does not list 1ES 1959+650 as an exact-source QPO "
            "candidate in its compiled 2020-2025 sample."
        ),
        "interpretation": (
            "Use the WCDA strict-flux detection tier and internal CWT/WWZ checks as the main "
            "screening evidence; there is no supporting GeV-QPO prior from that survey."
        ),
    },
    "1es1727p502": {
        "status": "No exact-source Fermi-LAT QPO prior in the survey",
        "class": "none",
        "summary": (
            "The prior Fermi-LAT report mentions 1ES 1727+502 in the reverse LHAASO catalog "
            "cross-match context, but explicitly not as a member of the compiled Fermi-QPO sample."
        ),
        "interpretation": (
            "Treat this as a WCDA-driven exploratory target rather than a GeV-prior target."
        ),
    },
    "1es2344p514": {
        "status": "No exact-source Fermi-LAT QPO prior in the survey",
        "class": "none",
        "summary": (
            "The prior Fermi-LAT report only brings 1ES 2344+514 into positional cross-match "
            "context; it is not listed as an exact-source Fermi-QPO candidate."
        ),
        "interpretation": (
            "Any WCDA periodicity feature should stand on the WCDA detection quality and "
            "significance checks, not on a prior Fermi-LAT QPO claim."
        ),
    },
    "bllac": {
        "status": "No exact-source Fermi-LAT QPO prior in the survey",
        "class": "none",
        "summary": (
            "The prior Fermi-LAT report contains many BL Lac class objects, but it does not list "
            "BL Lacertae itself as an exact-source QPO candidate in the compiled sample."
        ),
        "interpretation": (
            "Do not infer a Fermi-QPO prior from class-level BL Lac mentions; interpret this "
            "source from its own WCDA strict-flux statistics."
        ),
    },
    "ngc1275": {
        "status": "Mixed / weak external prior",
        "class": "mixed",
        "summary": (
            "The prior Fermi-LAT survey lists NGC 1275 as a Ren+22 CWT candidate in the LHAASO "
            "field of view, with a 92 +/- 33 d 7 d-bin feature (>5 sigma, 4 cycles). The same "
            "report places it outside the direct 1LHAASO catalog-match tier and notes weak TeV "
            "status compared with Mrk 421/501."
        ),
        "interpretation": (
            "This is not a strong WCDA timing prior. Combined with low weekly strict-flux TS here, "
            "NGC 1275 should remain a diagnostic/control case unless stronger VHE detection "
            "quality is established."
        ),
    },
    "m87": {
        "status": "No exact-source Fermi-LAT QPO prior in the survey",
        "class": "none",
        "summary": (
            "The prior Fermi-LAT QPO survey does not list M 87 as an exact-source QPO candidate "
            "in the compiled 2020-2025 sample."
        ),
        "interpretation": (
            "Use this source mainly as a radio-galaxy comparison/control target in the WCDA survey."
        ),
    },
    "4c_p42d22": {
        "status": "No exact-source Fermi-LAT QPO prior in the survey",
        "class": "none",
        "summary": (
            "The prior Fermi-LAT QPO survey does not list 4C +42.22 as an exact-source QPO "
            "candidate in its compiled sample."
        ),
        "interpretation": (
            "Treat any WCDA periodicity feature as exploratory and require WCDA-side robustness "
            "before assigning physical weight."
        ),
    },
    "ic310": {
        "status": "No exact-source Fermi-LAT QPO prior in the survey",
        "class": "none",
        "summary": (
            "The prior Fermi-LAT QPO survey does not list IC 310 as an exact-source QPO candidate "
            "in the compiled 2020-2025 sample."
        ),
        "interpretation": (
            "This remains a WCDA-driven exploratory/flaring target rather than a Fermi-prior QPO "
            "target."
        ),
    },
}


def main() -> None:
    summary = _load_summary()
    significance = _load_significance_summary()
    flux_summary = _load_flux_summary()
    flux_significance = _load_flux_significance_summary()
    _validate_report_inputs(summary, significance, flux_summary, flux_significance)
    flux_quality = _load_flux_quality(flux_summary)
    md = _build_markdown(summary, significance, flux_summary, flux_significance, flux_quality)
    html_text = _build_html(summary, significance, flux_summary, flux_significance, flux_quality)
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(md, encoding="utf-8")
    REPORT_HTML.write_text(html_text, encoding="utf-8")
    print(f"[OK] wrote {REPORT_MD.relative_to(PROJECT_ROOT)}")
    print(f"[OK] wrote {REPORT_HTML.relative_to(PROJECT_ROOT)}")


def _load_summary() -> pd.DataFrame:
    if not SUMMARY_CSV.exists():
        raise FileNotFoundError(f"Missing survey summary: {SUMMARY_CSV}")
    summary = pd.read_csv(SUMMARY_CSV)
    expected = set(WCDA_WEEK_SURVEY_SOURCE_IDS)
    observed = set(summary["source_id"]) if "source_id" in summary.columns else set()
    missing = sorted(expected - observed)
    extra = sorted(observed - expected)
    if missing or extra:
        raise ValueError(f"Unexpected source coverage in {SUMMARY_CSV}: missing={missing}, extra={extra}")
    return summary


def _load_significance_summary() -> pd.DataFrame | None:
    if not SIGNIFICANCE_SUMMARY_CSV.exists():
        return None
    significance = pd.read_csv(SIGNIFICANCE_SUMMARY_CSV)
    expected = set(WCDA_WEEK_SURVEY_SOURCE_IDS)
    observed = set(significance["source_id"]) if "source_id" in significance.columns else set()
    missing = sorted(expected - observed)
    extra = sorted(observed - expected)
    if missing or extra:
        raise ValueError(
            f"Unexpected source coverage in {SIGNIFICANCE_SUMMARY_CSV}: missing={missing}, extra={extra}"
        )
    return significance


def _load_flux_summary() -> pd.DataFrame | None:
    if not FLUX_SUMMARY_CSV.exists():
        return None
    flux_summary = pd.read_csv(FLUX_SUMMARY_CSV)
    expected = set(WCDA_STRICT_FLUX_SOURCE_IDS)
    observed = set(flux_summary["source_id"]) if "source_id" in flux_summary.columns else set()
    missing = sorted(expected - observed)
    extra = sorted(observed - expected)
    if missing or extra:
        raise ValueError(f"Unexpected source coverage in {FLUX_SUMMARY_CSV}: missing={missing}, extra={extra}")
    return flux_summary


def _load_flux_significance_summary() -> pd.DataFrame | None:
    if not FLUX_SIGNIFICANCE_SUMMARY_CSV.exists():
        return None
    flux_significance = pd.read_csv(FLUX_SIGNIFICANCE_SUMMARY_CSV)
    expected = set(WCDA_STRICT_FLUX_SOURCE_IDS)
    observed = set(flux_significance["source_id"]) if "source_id" in flux_significance.columns else set()
    extra = sorted(observed - expected)
    if extra:
        raise ValueError(f"Unexpected source ids in {FLUX_SIGNIFICANCE_SUMMARY_CSV}: extra={extra}")
    return flux_significance


def _load_flux_quality(flux_summary: pd.DataFrame | None) -> pd.DataFrame | None:
    if flux_summary is None:
        return None
    rows = []
    for source_id in WCDA_STRICT_FLUX_SOURCE_IDS:
        aligned_path = FLUX_SURVEY_ALIGNED_DIR / source_id / "wcda_strict_flux_weekly_aligned.csv"
        if not aligned_path.exists():
            raise FileNotFoundError(f"Missing strict flux aligned CSV for quality tiering: {aligned_path}")
        aligned = pd.read_csv(aligned_path)
        if "TS" not in aligned.columns:
            raise ValueError(f"{aligned_path} is missing TS; cannot build detection-quality tiers.")
        ts = pd.to_numeric(aligned["TS"], errors="coerce")
        valid_ts = ts.dropna()
        if valid_ts.empty:
            raise ValueError(f"{aligned_path} has no finite TS values; cannot build detection-quality tiers.")
        n_rows = int(len(ts))
        n_ts_ge_4 = int((valid_ts >= 4.0).sum())
        n_ts_ge_9 = int((valid_ts >= 9.0).sum())
        n_ts_ge_25 = int((valid_ts >= 25.0).sum())
        frac_ts_ge_4 = n_ts_ge_4 / n_rows
        frac_ts_ge_9 = n_ts_ge_9 / n_rows
        tier, tier_label, interpretation = _detection_quality_tier(float(valid_ts.median()), frac_ts_ge_9, frac_ts_ge_4)
        rows.append(
            {
                "source_id": source_id,
                "source": get_source(source_id).label,
                "n_ts_rows": n_rows,
                "ts_median": float(valid_ts.median()),
                "ts_mean": float(valid_ts.mean()),
                "ts_p75": float(valid_ts.quantile(0.75)),
                "ts_max": float(valid_ts.max()),
                "n_ts_ge_4": n_ts_ge_4,
                "n_ts_ge_9": n_ts_ge_9,
                "n_ts_ge_25": n_ts_ge_25,
                "frac_ts_ge_4": frac_ts_ge_4,
                "frac_ts_ge_9": frac_ts_ge_9,
                "detection_tier": tier,
                "detection_tier_label": tier_label,
                "interpretation": interpretation,
            }
        )
    return pd.DataFrame(rows)


def _detection_quality_tier(median_ts: float, frac_ts_ge_9: float, frac_ts_ge_4: float) -> tuple[str, str, str]:
    if median_ts >= TIER_A_MEDIAN_TS or frac_ts_ge_9 >= TIER_A_FRAC_TS9:
        return (
            "A",
            "Tier A: timing-grade",
            "weekly WCDA detection quality is high enough for flux-timing interpretation",
        )
    if frac_ts_ge_9 >= TIER_B_FRAC_TS9 or frac_ts_ge_4 >= TIER_B_FRAC_TS4:
        return (
            "B",
            "Tier B: exploratory",
            "some weekly detections exist, but timing claims require stronger checks",
        )
    return (
        "C",
        "Tier C: diagnostic only",
        "low weekly TS; periodicity peaks are diagnostics, not LHAASO QPO evidence",
    )


def _validate_report_inputs(
    summary: pd.DataFrame,
    significance: pd.DataFrame | None,
    flux_summary: pd.DataFrame | None,
    flux_significance: pd.DataFrame | None,
) -> None:
    required_cols = {
        "source_id",
        "source",
        "series",
        "n_points",
        "mjd_min",
        "mjd_max",
        "median_dt_days",
        "cwt_peak_period_days",
        "cwt_peak_gws",
        "wwz_peak_period_days",
        "wwz_peak_power",
    }
    missing_cols = sorted(required_cols - set(summary.columns))
    if missing_cols:
        raise ValueError(f"{SUMMARY_CSV} is missing required columns: {missing_cols}")
    if len(summary) != len(WCDA_WEEK_SURVEY_SOURCE_IDS):
        raise ValueError(f"Expected {len(WCDA_WEEK_SURVEY_SOURCE_IDS)} summary rows, found {len(summary)}.")
    if set(summary["series"]) != {"wcda_weekly"}:
        raise ValueError("Survey report expects weekly-only rows with series == wcda_weekly.")

    for source_id in WCDA_WEEK_SURVEY_SOURCE_IDS:
        aligned_path = SURVEY_ALIGNED_DIR / source_id / "wcda_weekly_aligned.csv"
        summary_path = SURVEY_PERIODICITY_DIR / source_id / "periodicity_v1_summary.csv"
        missing = [path for path in (aligned_path, summary_path) if not path.exists()]
        missing += [SURVEY_PERIODICITY_DIR / source_id / image for image in REQUIRED_IMAGES if not (SURVEY_PERIODICITY_DIR / source_id / image).exists()]
        if significance is not None:
            missing += [
                SURVEY_PERIODICITY_DIR / source_id / image
                for image in SIGNIFICANCE_IMAGES
                if not (SURVEY_PERIODICITY_DIR / source_id / image).exists()
            ]
        if missing:
            raise FileNotFoundError(f"Missing report inputs for {source_id}: {missing}")

    if significance is not None:
        required_sig_cols = {
            "source_id",
            "source",
            "method",
            "period_days",
            "cycles",
            "observed_statistic",
            "local_fap",
            "global_fap",
            "above_95",
            "above_99",
            "n_surrogates",
            "note",
        }
        missing_sig_cols = sorted(required_sig_cols - set(significance.columns))
        if missing_sig_cols:
            raise ValueError(f"{SIGNIFICANCE_SUMMARY_CSV} is missing required columns: {missing_sig_cols}")

    if flux_summary is not None:
        required_flux_cols = {
            "source_id",
            "source",
            "series",
            "n_rows",
            "n_points",
            "n_bad_fit_rows",
            "mjd_min",
            "mjd_max",
            "date_min",
            "date_max",
            "median_dt_days",
            "flux_min",
            "flux_max",
            "median_flux_err",
            "cwt_peak_period_days",
            "cwt_peak_gws",
            "wwz_peak_period_days",
            "wwz_peak_power",
        }
        missing_flux_cols = sorted(required_flux_cols - set(flux_summary.columns))
        if missing_flux_cols:
            raise ValueError(f"{FLUX_SUMMARY_CSV} is missing required columns: {missing_flux_cols}")
        if len(flux_summary) != len(WCDA_STRICT_FLUX_SOURCE_IDS):
            raise ValueError(f"Expected {len(WCDA_STRICT_FLUX_SOURCE_IDS)} flux rows, found {len(flux_summary)}.")
        if set(flux_summary["series"]) != {"wcda_strict_flux_weekly"}:
            raise ValueError("Flux report expects rows with series == wcda_strict_flux_weekly.")

        for source_id in WCDA_STRICT_FLUX_SOURCE_IDS:
            aligned_path = FLUX_SURVEY_ALIGNED_DIR / source_id / "wcda_strict_flux_weekly_aligned.csv"
            summary_path = FLUX_SURVEY_PERIODICITY_DIR / source_id / "periodicity_flux_summary.csv"
            missing = [path for path in (aligned_path, summary_path) if not path.exists()]
            missing += [
                FLUX_SURVEY_PERIODICITY_DIR / source_id / image
                for image in FLUX_IMAGES
                if not (FLUX_SURVEY_PERIODICITY_DIR / source_id / image).exists()
            ]
            if missing:
                raise FileNotFoundError(f"Missing strict flux report inputs for {source_id}: {missing}")

    if flux_significance is not None:
        required_flux_sig_cols = {
            "source_id",
            "source",
            "series",
            "method",
            "period_days",
            "cycles",
            "observed_statistic",
            "local_fap",
            "global_fap",
            "above_95",
            "above_99",
            "n_surrogates",
            "note",
        }
        missing_flux_sig_cols = sorted(required_flux_sig_cols - set(flux_significance.columns))
        if missing_flux_sig_cols:
            raise ValueError(f"{FLUX_SIGNIFICANCE_SUMMARY_CSV} is missing required columns: {missing_flux_sig_cols}")
        if set(flux_significance["series"]) != {"wcda_strict_flux_weekly"}:
            raise ValueError("Flux significance report expects rows with series == wcda_strict_flux_weekly.")
        for source_id in WCDA_STRICT_FLUX_SOURCE_IDS:
            missing = [
                FLUX_SURVEY_PERIODICITY_DIR / source_id / image
                for image in FLUX_SIGNIFICANCE_IMAGES
                if not (FLUX_SURVEY_PERIODICITY_DIR / source_id / image).exists()
            ]
            per_source_csv = FLUX_SURVEY_PERIODICITY_DIR / source_id / "wcda_strict_flux_weekly_local_significance.csv"
            if not per_source_csv.exists():
                missing.append(per_source_csv)
            if missing:
                raise FileNotFoundError(f"Missing strict flux significance report inputs for {source_id}: {missing}")


def _build_markdown(
    summary: pd.DataFrame,
    significance: pd.DataFrame | None,
    flux_summary: pd.DataFrame | None,
    flux_significance: pd.DataFrame | None,
    flux_quality: pd.DataFrame | None,
) -> str:
    lines = [
        "# AGN WCDA Weekly Periodicity Survey",
        "",
        f"Generated on {date.today().isoformat()} from `data/processed/periodicity/agn_wcda_weekly_survey/`.",
        "",
        "This report applies the same WCDA weekly quick-look pipeline to 10 LHAASO AGN targets: Mrk 421, Mrk 501, and the eight newly pulled IHEP AGN products. It uses strict weekly flux products as the primary source-by-source view, with photon-count/excess-rate products folded below for validation.",
        "",
        "Important scope note: this is not a QPO detection claim. The optional significance section is an AR(1) quick-look only, with no source-level, method-level, or survey-level trial correction. Detection-quality tiers below are based on weekly strict-flux TS, not on CWT/WWZ peak strength. The Fermi-LAT notes are prior context from the earlier survey page and are not recomputed in this report.",
        "",
        "## Data And Method",
        "",
        "- Input products are weekly WCDA count CSVs under `data/processed/wcda_week/`.",
        "- Photon-count diagnostics use `excess_counts = sum(n_on - n_bkg)` plus total `n_on` and `n_bkg` curves.",
        "- Periodicity inputs use the existing v1 excess-rate proxy `wcda_flux_excess = sum(n_on - n_bkg) / tobs` with propagated on/off errors.",
        "- CWT uses a Morlet wavelet through `pycwt`; WWZ uses `libwwz` with `time_divisions=80` and `freq_step_factor=0.5`.",
        "- The weekly period search range is 50-600 days.",
        "- Strict-flux detection tiering: Tier A if median TS >= 9 or TS>=9 fraction >= 50%; Tier B if TS>=9 fraction >= 10% or TS>=4 fraction >= 25%; Tier C otherwise. Tier C peaks are diagnostic/control results only.",
        f"- Per-source Fermi-LAT prior context is summarized from `{FERMI_QPO_SURVEY_URL}` for interpretation only; it is not part of the WCDA CWT/WWZ significance calculation.",
        "",
        "## Strict Flux Weekly Source Results",
        "",
        *_markdown_source_first_flux_sections(summary, significance, flux_summary, flux_significance, flux_quality),
        "## Counts / Excess-Rate Overview",
        "",
        "The original 10-source counts/excess-rate quick-look is kept here as a secondary overview. The detailed counts figures are also available in each source's collapsed validation block above.",
        "",
        _markdown_table(summary),
        "",
        *_markdown_significance_section(significance),
        "## Outputs",
        "",
        "- Survey aligned CSVs: `data/processed/aligned/agn_wcda_weekly_survey/<source_id>/wcda_weekly_aligned.csv`.",
        "- Survey arrays and figures: `data/processed/periodicity/agn_wcda_weekly_survey/<source_id>/`.",
        "- Survey summary CSV: `data/processed/periodicity/agn_wcda_weekly_survey/agn_wcda_weekly_survey_summary.csv`.",
        "- Strict flux aligned CSVs: `data/processed/aligned/agn_wcda_weekly_flux_survey/<source_id>/wcda_strict_flux_weekly_aligned.csv`.",
        "- Strict flux arrays and figures: `data/processed/periodicity/agn_wcda_weekly_flux_survey/<source_id>/`.",
        "- Strict flux summary CSV: `data/processed/periodicity/agn_wcda_weekly_flux_survey/agn_wcda_weekly_flux_survey_summary.csv`.",
        "",
    ]
    return "\n".join(lines)


def _build_html(
    summary: pd.DataFrame,
    significance: pd.DataFrame | None,
    flux_summary: pd.DataFrame | None,
    flux_significance: pd.DataFrame | None,
    flux_quality: pd.DataFrame | None,
) -> str:
    rows_html = "\n".join(_summary_html_rows(summary))
    significance_section = _significance_html_section(significance)
    source_first_section = _source_first_flux_html_section(summary, significance, flux_summary, flux_significance, flux_quality)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AGN WCDA Weekly Periodicity Survey</title>
  <style>
    :root {{
      --ink: #1f2933;
      --muted: #5f6c7b;
      --line: #d7dee8;
      --panel: #f7f9fc;
      --panel-strong: #eef5f1;
      --accent: #255c99;
      --flux: #1b7f5c;
    }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: var(--ink);
      background: #ffffff;
      line-height: 1.55;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 32px 24px 56px;
    }}
    h1 {{ margin: 0 0 8px; font-size: 30px; }}
    h2 {{
      margin-top: 34px;
      border-bottom: 1px solid var(--line);
      padding-bottom: 6px;
      font-size: 22px;
    }}
    h3 {{ margin-top: 26px; font-size: 18px; }}
    .meta, .note, figcaption {{ color: var(--muted); }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px 18px;
      margin: 18px 0;
    }}
    .source-card {{
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 18px 18px 20px;
      margin: 24px 0;
      background: linear-gradient(180deg, #ffffff 0%, #f9fcfb 100%);
      box-shadow: 0 6px 22px rgba(31, 41, 51, 0.06);
    }}
    .source-card h3 {{
      margin-top: 0;
      font-size: 21px;
    }}
    .flux-badge {{
      display: inline-block;
      border: 1px solid #a9cdbb;
      background: var(--panel-strong);
      color: #145d43;
      border-radius: 999px;
      padding: 3px 10px;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.02em;
      text-transform: uppercase;
    }}
    .tier-badge {{
      display: inline-block;
      border-radius: 999px;
      padding: 3px 10px;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.01em;
      margin-left: 6px;
      white-space: nowrap;
    }}
    .tier-a {{
      background: #e8f5ee;
      border: 1px solid #8bc4a3;
      color: #145d43;
    }}
    .tier-b {{
      background: #fff4dc;
      border: 1px solid #e4bd6a;
      color: #755317;
    }}
    .tier-c {{
      background: #fff0ed;
      border: 1px solid #e2a094;
      color: #8a2f22;
    }}
    .quality-note {{
      color: #334155;
      margin: 8px 0 10px;
    }}
    .quality-warning {{
      border: 1px solid #e2a094;
      background: #fff7f5;
      color: #7f2a1d;
      border-radius: 8px;
      padding: 10px 12px;
      margin: 10px 0 16px;
    }}
    .fermi-prior {{
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 12px 14px;
      margin: 14px 0 18px;
      background: #f8fbff;
    }}
    .fermi-prior h4 {{
      margin: 0 0 8px;
      font-size: 15px;
    }}
    .fermi-prior p {{
      margin: 6px 0;
    }}
    .fermi-prior.reported {{
      border-color: #90b7e0;
      background: #f0f7ff;
    }}
    .fermi-prior.mixed {{
      border-color: #e4bd6a;
      background: #fff9eb;
    }}
    .fermi-prior.none {{
      border-color: #cfd8e3;
      background: #fafcff;
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin: 12px 0 16px;
    }}
    .metric {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px 12px;
      background: #fff;
    }}
    .metric span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
    }}
    .metric strong {{
      display: block;
      margin-top: 2px;
      font-size: 17px;
    }}
    details {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfe;
      margin: 16px 0 4px;
      padding: 0;
    }}
    summary {{
      cursor: pointer;
      padding: 12px 14px;
      font-weight: 700;
      color: var(--accent);
    }}
    .details-body {{
      padding: 0 14px 14px;
    }}
    code {{ background: #eef2f7; padding: 2px 4px; border-radius: 4px; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
      margin: 12px 0 20px;
    }}
    th, td {{
      border: 1px solid var(--line);
      padding: 8px 9px;
      text-align: right;
      vertical-align: top;
    }}
    th:first-child, td:first-child, th:nth-child(2), td:nth-child(2) {{ text-align: left; }}
    th {{ background: #eef3f9; }}
    figure {{ margin: 14px 0 22px; }}
    img {{
      width: 100%;
      height: auto;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: white;
    }}
    figcaption {{ font-size: 13px; margin-top: 6px; }}
    @media (max-width: 820px) {{
      main {{ padding: 22px 14px 40px; }}
      table {{ font-size: 12px; }}
      .metrics {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
    @media (max-width: 520px) {{
      .metrics {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
<main>
  <h1>AGN WCDA Weekly Periodicity Survey</h1>
  <p class="meta">Generated on {date.today().isoformat()} from <code>data/processed/periodicity/agn_wcda_weekly_survey/</code>.</p>
  <section class="panel">
    <strong>Scope.</strong> This report applies the same WCDA weekly quick-look pipeline to 10 LHAASO AGN targets. It shows photon-count diagnostics, CWT maps, WWZ maps, 1D global spectra, optional AR(1) quick-look significance, and strict-flux detection-quality tiers. It does not include source-level, method-level, or survey-level trial correction, forward folding, or daily WCDA. Fermi-LAT entries below are prior context from the earlier survey page, not recomputed comparisons.
  </section>

  <h2>Data And Method</h2>
  <p>Input products are weekly WCDA count CSVs under <code>data/processed/wcda_week/</code>. Photon-count diagnostics use <code>excess_counts = sum(n_on - n_bkg)</code> plus total <code>n_on</code> and <code>n_bkg</code> curves.</p>
  <p>Periodicity inputs use the existing v1 excess-rate proxy <code>wcda_flux_excess = sum(n_on - n_bkg) / tobs</code> with propagated on/off errors. This is not calibrated flux. CWT uses a Morlet wavelet through <code>pycwt</code>; WWZ uses <code>libwwz</code> with <code>time_divisions=80</code> and <code>freq_step_factor=0.5</code>. The weekly period search range is 50-600 days.</p>
  <p>Strict-flux detection tiering is based on weekly TS, not on periodogram strength: Tier A if median TS &ge; 9 or TS&ge;9 fraction &ge; 50%; Tier B if TS&ge;9 fraction &ge; 10% or TS&ge;4 fraction &ge; 25%; Tier C otherwise.</p>
  <p>Per-source Fermi-LAT prior context is summarized from <a href="{html.escape(FERMI_QPO_SURVEY_URL)}">the earlier Fermi-LAT QPO survey</a> for interpretation only; it is not part of the WCDA CWT/WWZ significance calculation.</p>
  <p class="note">The maps, peaks, and AR(1) references below are quick-look summaries only, not QPO detection claims. Tier C peaks are diagnostic/control results only because the source is not significantly detected in most weekly bins.</p>

  <h2>Strict Flux Weekly Source Results</h2>
{source_first_section}

  <h2>Counts / Excess-Rate Overview</h2>
  <p>The original 10-source counts/excess-rate quick-look is kept here as a secondary overview. The detailed counts figures are also available in each source's collapsed validation block above.</p>
  <table>
    <thead>
      <tr><th>Source</th><th>Series</th><th>N</th><th>MJD min</th><th>MJD max</th><th>Median dt [d]</th><th>CWT peak [d]</th><th>CWT GWS</th><th>WWZ peak [d]</th><th>WWZ power</th></tr>
    </thead>
    <tbody>
{rows_html}
    </tbody>
  </table>

{significance_section}

  <h2>Outputs</h2>
  <ul>
    <li>Survey aligned CSVs: <code>data/processed/aligned/agn_wcda_weekly_survey/&lt;source_id&gt;/wcda_weekly_aligned.csv</code></li>
    <li>Survey arrays and figures: <code>data/processed/periodicity/agn_wcda_weekly_survey/&lt;source_id&gt;/</code></li>
    <li>Survey summary CSV: <code>data/processed/periodicity/agn_wcda_weekly_survey/agn_wcda_weekly_survey_summary.csv</code></li>
    <li>Strict flux aligned CSVs: <code>data/processed/aligned/agn_wcda_weekly_flux_survey/&lt;source_id&gt;/wcda_strict_flux_weekly_aligned.csv</code></li>
    <li>Strict flux arrays and figures: <code>data/processed/periodicity/agn_wcda_weekly_flux_survey/&lt;source_id&gt;/</code></li>
    <li>Strict flux summary CSV: <code>data/processed/periodicity/agn_wcda_weekly_flux_survey/agn_wcda_weekly_flux_survey_summary.csv</code></li>
  </ul>
</main>
</body>
</html>
"""


def _markdown_table(summary: pd.DataFrame) -> str:
    lines = [
        "| Source | Series | N | MJD min | MJD max | Median dt [d] | CWT peak [d] | CWT GWS | WWZ peak [d] | WWZ power |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for source_id in WCDA_WEEK_SURVEY_SOURCE_IDS:
        row = _summary_row(summary, source_id)
        lines.append(
            f"| {row.source} | {row.series} | {int(row.n_points)} | {row.mjd_min:.3f} | {row.mjd_max:.3f} | "
            f"{row.median_dt_days:.3f} | {row.cwt_peak_period_days:.2f} | {row.cwt_peak_gws:.3f} | "
            f"{row.wwz_peak_period_days:.2f} | {row.wwz_peak_power:.3f} |"
        )
    return "\n".join(lines)


def _summary_html_rows(summary: pd.DataFrame) -> list[str]:
    rows = []
    for source_id in WCDA_WEEK_SURVEY_SOURCE_IDS:
        row = _summary_row(summary, source_id)
        rows.append(
            "      "
            f"<tr><td>{html.escape(str(row.source))}</td><td>{html.escape(str(row.series))}</td>"
            f"<td>{int(row.n_points)}</td><td>{row.mjd_min:.3f}</td><td>{row.mjd_max:.3f}</td>"
            f"<td>{row.median_dt_days:.3f}</td><td>{row.cwt_peak_period_days:.2f}</td>"
            f"<td>{row.cwt_peak_gws:.3f}</td><td>{row.wwz_peak_period_days:.2f}</td>"
            f"<td>{row.wwz_peak_power:.3f}</td></tr>"
        )
    return rows


def _markdown_significance_section(significance: pd.DataFrame | None) -> list[str]:
    if significance is None:
        return []
    lines = [
        "## Significance Quick Look",
        "",
        "CWT rows use an AR(1) theory reference from PyCWT. WWZ rows use AR(1) Gaussian surrogates on the same weekly sampling and report both local-window and global-search FAP. These are not source-level, method-level, or survey-level trial corrected.",
        "",
        _significance_markdown_table(significance),
        "",
    ]
    return lines


def _significance_markdown_table(significance: pd.DataFrame) -> str:
    lines = [
        "| Source | Method | Period [d] | Cycles | Observed | Local FAP | Global FAP | Above 95% | Above 99% | N sim | Note |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |",
    ]
    for row in _ordered_significance_rows(significance):
        lines.append(
            f"| {row.source} | {row.method} | {row.period_days:.2f} | {row.cycles:.2f} | "
            f"{row.observed_statistic:.3f} | {_format_fap(row.local_fap)} | {_format_fap(row.global_fap)} | "
            f"{_format_bool(row.above_95)} | {_format_bool(row.above_99)} | {int(row.n_surrogates)} | {row.note} |"
        )
    return "\n".join(lines)


def _significance_html_section(significance: pd.DataFrame | None) -> str:
    if significance is None:
        return ""
    rows_html = "\n".join(_significance_html_rows(significance))
    return f"""
  <h2>Significance Quick Look</h2>
  <p>CWT rows use an AR(1) theory reference from PyCWT. WWZ rows use AR(1) Gaussian surrogates on the same weekly sampling and report both local-window and global-search FAP. These are not source-level, method-level, or survey-level trial corrected.</p>
  <table>
    <thead>
      <tr><th>Source</th><th>Method</th><th>Period [d]</th><th>Cycles</th><th>Observed</th><th>Local FAP</th><th>Global FAP</th><th>Above 95%</th><th>Above 99%</th><th>N sim</th><th>Note</th></tr>
    </thead>
    <tbody>
{rows_html}
    </tbody>
  </table>
"""


def _significance_html_rows(significance: pd.DataFrame) -> list[str]:
    rows = []
    for row in _ordered_significance_rows(significance):
        rows.append(
            "      "
            f"<tr><td>{html.escape(str(row.source))}</td><td>{html.escape(str(row.method))}</td>"
            f"<td>{row.period_days:.2f}</td><td>{row.cycles:.2f}</td><td>{row.observed_statistic:.3f}</td>"
            f"<td>{_format_fap(row.local_fap)}</td><td>{_format_fap(row.global_fap)}</td>"
            f"<td>{_format_bool(row.above_95)}</td><td>{_format_bool(row.above_99)}</td>"
            f"<td>{int(row.n_surrogates)}</td><td>{html.escape(str(row.note))}</td></tr>"
        )
    return rows


def _source_significance_markdown_table(significance: pd.DataFrame, source_id: str) -> str:
    rows = _ordered_source_significance_rows(significance, source_id)
    if not rows:
        return "_No strict-flux significance rows found for this source._"
    lines = [
        "| Method | Period [d] | Cycles | Observed | Local FAP | Global FAP | Above 95% | Above 99% | N sim | Note |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row.method} | {row.period_days:.2f} | {row.cycles:.2f} | {row.observed_statistic:.3f} | "
            f"{_format_fap(row.local_fap)} | {_format_fap(row.global_fap)} | "
            f"{_format_bool(row.above_95)} | {_format_bool(row.above_99)} | {int(row.n_surrogates)} | {row.note} |"
        )
    return "\n".join(lines)


def _source_significance_html_table(significance: pd.DataFrame, source_id: str) -> str:
    rows = _ordered_source_significance_rows(significance, source_id)
    if not rows:
        return '<p class="note">No strict-flux significance rows found for this source.</p>'
    row_html = "\n".join(
        "      "
        f"<tr><td>{html.escape(str(row.method))}</td><td>{row.period_days:.2f}</td><td>{row.cycles:.2f}</td>"
        f"<td>{row.observed_statistic:.3f}</td><td>{_format_fap(row.local_fap)}</td>"
        f"<td>{_format_fap(row.global_fap)}</td><td>{_format_bool(row.above_95)}</td>"
        f"<td>{_format_bool(row.above_99)}</td><td>{int(row.n_surrogates)}</td>"
        f"<td>{html.escape(str(row.note))}</td></tr>"
        for row in rows
    )
    return f"""
    <table>
      <thead>
        <tr><th>Method</th><th>Period [d]</th><th>Cycles</th><th>Observed</th><th>Local FAP</th><th>Global FAP</th><th>Above 95%</th><th>Above 99%</th><th>N sim</th><th>Note</th></tr>
      </thead>
      <tbody>
{row_html}
      </tbody>
    </table>
"""


def _ordered_source_significance_rows(significance: pd.DataFrame, source_id: str) -> list[pd.Series]:
    method_order = {"CWT": 0, "WWZ": 1}
    source_rows = significance.loc[significance["source_id"] == source_id].copy()
    if source_rows.empty:
        return []
    source_rows["_method_order"] = source_rows["method"].map(method_order).fillna(99)
    source_rows = source_rows.sort_values(["_method_order", "period_days"])
    return [row for _idx, row in source_rows.iterrows()]


def _fermi_prior_markdown(source_id: str) -> list[str]:
    prior = FERMI_QPO_PRIOR_CONTEXT[source_id]
    return [
        "#### Fermi-LAT prior context",
        "",
        f"- Status: {prior['status']}.",
        f"- Prior result: {prior['summary']}",
        f"- Interpretation for this WCDA report: {prior['interpretation']}",
        f"- Source of context: {FERMI_QPO_SURVEY_URL}",
        "",
    ]


def _fermi_prior_html(source_id: str) -> str:
    prior = FERMI_QPO_PRIOR_CONTEXT[source_id]
    css_class = html.escape(str(prior["class"]))
    status = html.escape(str(prior["status"]))
    summary = html.escape(str(prior["summary"]))
    interpretation = html.escape(str(prior["interpretation"]))
    url = html.escape(FERMI_QPO_SURVEY_URL)
    return f"""
    <div class="fermi-prior {css_class}">
      <h4>Fermi-LAT Prior Context</h4>
      <p><strong>Status:</strong> {status}.</p>
      <p><strong>Prior result:</strong> {summary}</p>
      <p><strong>Interpretation for this WCDA report:</strong> {interpretation}</p>
      <p class="meta">Context source: <a href="{url}">Fermi-LAT QPO detection survey</a>. This report does not recompute those Fermi-LAT results.</p>
    </div>
"""


def _markdown_source_first_flux_sections(
    summary: pd.DataFrame,
    significance: pd.DataFrame | None,
    flux_summary: pd.DataFrame | None,
    flux_significance: pd.DataFrame | None,
    flux_quality: pd.DataFrame | None,
) -> list[str]:
    if flux_summary is None:
        return [
            "Strict flux products are not present yet. Run `src/pipeline/agn_strict_flux_weekly_periodicity.py` to populate this section.",
            "",
        ]

    lines = [
        "This source-first section uses 10 strict weekly flux products: Mrk 421 and Mrk 501 from `data/processed/wcda_week/`, plus the eight IHEP AGN flux products under `results/flux_strict_agn_week/`. Each source starts with strict flux (`N0`, `N0_err`) as the primary result; the older counts/excess-rate products are folded below for validation.",
        "",
        "Detection-quality tiers are based on strict-flux weekly TS. Tier A means timing-grade quick-look input; Tier B is exploratory; Tier C is diagnostic/control only even if CWT/WWZ returns peaks.",
        "",
        _flux_peak_markdown_table(flux_summary, flux_significance, flux_quality),
        "",
    ]
    for source_id in WCDA_STRICT_FLUX_SOURCE_IDS:
        record = get_source(source_id)
        flux_row = _flux_summary_row(flux_summary, source_id)
        counts_row = _summary_row(summary, source_id)
        quality_row = _flux_quality_row(flux_quality, source_id)
        flux_lightcurve = _report_relative_path(
            FLUX_SURVEY_PERIODICITY_DIR / source_id / "wcda_strict_flux_weekly_lightcurve.png",
            REPORT_MD.parent,
        )
        flux_periodicity = _report_relative_path(
            FLUX_SURVEY_PERIODICITY_DIR / source_id / "wcda_strict_flux_weekly_periodicity.png",
            REPORT_MD.parent,
        )
        counts_path = _report_relative_path(SURVEY_PERIODICITY_DIR / source_id / "wcda_weekly_counts.png", REPORT_MD.parent)
        counts_periodicity = _report_relative_path(
            SURVEY_PERIODICITY_DIR / source_id / "wcda_weekly_periodicity.png",
            REPORT_MD.parent,
        )
        lines.extend(
            [
                f"### {record.label}",
                "",
                "`Strict flux primary result`",
                "",
                f"- Detection quality: {quality_row.detection_tier_label}; median TS {quality_row.ts_median:.2f}; TS>=9 weeks {int(quality_row.n_ts_ge_9)} / {int(quality_row.n_ts_rows)} ({100.0 * quality_row.frac_ts_ge_9:.1f}%).",
                f"- Interpretation: {quality_row.interpretation}.",
                f"- Usable strict-flux points: {int(flux_row.n_points)} / {int(flux_row.n_rows)}; excluded fit rows: {int(flux_row.n_bad_fit_rows)}.",
                f"- Date range: {flux_row.date_min} to {flux_row.date_max}; median cadence {flux_row.median_dt_days:.3f} d.",
                f"- Flux CWT global peak: {flux_row.cwt_peak_period_days:.2f} d, GWS {flux_row.cwt_peak_gws:.3f}.",
                f"- Flux WWZ global peak: {flux_row.wwz_peak_period_days:.2f} d, mean WWZ {flux_row.wwz_peak_power:.3f}.",
                "",
                *(
                    [
                        "**Low-TS caveat:** this source is not significantly detected in most weekly strict-flux bins. Treat the periodicity maps and AR(1) quick-look rows as diagnostics only, not as LHAASO QPO evidence.",
                        "",
                    ]
                    if quality_row.detection_tier == "C"
                    else []
                ),
                f"![{record.label} strict weekly flux light curve]({flux_lightcurve})",
                "",
                f"![{record.label} strict weekly flux CWT and WWZ quick-look]({flux_periodicity})",
                "",
                *_fermi_prior_markdown(source_id),
            ]
        )
        if flux_significance is not None:
            cwt_flux_sig_path = _report_relative_path(
                FLUX_SURVEY_PERIODICITY_DIR / source_id / "wcda_strict_flux_weekly_cwt_global_significance.png",
                REPORT_MD.parent,
            )
            wwz_flux_sig_path = _report_relative_path(
                FLUX_SURVEY_PERIODICITY_DIR / source_id / "wcda_strict_flux_weekly_wwz_global_significance.png",
                REPORT_MD.parent,
            )
            lines.extend(
                [
                    "#### Strict flux significance quick look",
                    "",
                    "CWT uses an AR(1) theory reference; WWZ uses AR(1) Gaussian surrogates on the same strict-flux weekly sampling. These are not source-level, method-level, or survey-level trial corrected.",
                    "",
                    _source_significance_markdown_table(flux_significance, source_id),
                    "",
                    f"![{record.label} strict flux CWT AR(1) reference]({cwt_flux_sig_path})",
                    "",
                    f"![{record.label} strict flux WWZ AR(1) surrogate significance]({wwz_flux_sig_path})",
                    "",
                ]
            )
        lines.extend(
            [
                "<details>",
                f"<summary>Counts / excess-rate validation for {record.label}</summary>",
                "",
                f"- Counts/excess-rate points: {int(counts_row.n_points)}; MJD {counts_row.mjd_min:.3f}-{counts_row.mjd_max:.3f}.",
                f"- Counts CWT global peak: {counts_row.cwt_peak_period_days:.2f} d, GWS {counts_row.cwt_peak_gws:.3f}.",
                f"- Counts WWZ global peak: {counts_row.wwz_peak_period_days:.2f} d, mean WWZ {counts_row.wwz_peak_power:.3f}.",
                "",
                f"![{record.label} WCDA weekly photon-count diagnostic]({counts_path})",
                "",
                f"![{record.label} WCDA weekly CWT and WWZ quick-look]({counts_periodicity})",
                "",
            ]
        )
        if significance is not None:
            cwt_sig_path = _report_relative_path(
                SURVEY_PERIODICITY_DIR / source_id / "wcda_weekly_cwt_global_significance.png",
                REPORT_MD.parent,
            )
            wwz_sig_path = _report_relative_path(
                SURVEY_PERIODICITY_DIR / source_id / "wcda_weekly_wwz_global_significance.png",
                REPORT_MD.parent,
            )
            lines.extend(
                [
                    f"![{record.label} counts CWT AR(1) reference]({cwt_sig_path})",
                    "",
                    f"![{record.label} counts WWZ AR(1) surrogate significance]({wwz_sig_path})",
                    "",
                ]
            )
        lines.extend(["</details>", ""])
    return lines


def _source_first_flux_html_section(
    summary: pd.DataFrame,
    significance: pd.DataFrame | None,
    flux_summary: pd.DataFrame | None,
    flux_significance: pd.DataFrame | None,
    flux_quality: pd.DataFrame | None,
) -> str:
    if flux_summary is None:
        return """
  <p class="note">Strict flux products are not present yet. Run <code>src/pipeline/agn_strict_flux_weekly_periodicity.py</code> to populate this section.</p>
"""
    rows_html = "\n".join(_flux_peak_html_rows(flux_summary, flux_significance, flux_quality))
    cards = "\n".join(
        _source_first_flux_html_card(summary, significance, flux_summary, flux_significance, flux_quality, source_id)
        for source_id in WCDA_STRICT_FLUX_SOURCE_IDS
    )
    return f"""
  <p>This source-first section uses 10 strict weekly flux products: Mrk 421 and Mrk 501 from <code>data/processed/wcda_week/</code>, plus the eight IHEP AGN flux products under <code>results/flux_strict_agn_week/</code>. Each source starts with strict flux (<code>N0</code>, <code>N0_err</code>) as the primary result; the older counts/excess-rate products are folded below for validation.</p>
  <p class="note">The strict-flux blocks include AR(1) quick-look references and surrogate FAP where available, but still do not include source-level, method-level, or survey-level trial correction, and they are not QPO detection claims.</p>
  <p class="note">Detection-quality tiers are based on strict-flux weekly TS. Tier A means timing-grade quick-look input; Tier B is exploratory; Tier C is diagnostic/control only even if CWT/WWZ returns peaks.</p>
  <table>
    <thead>
      <tr><th>Source</th><th>Detection tier</th><th>Median TS</th><th>TS&ge;9 weeks</th><th>Method</th><th>Peak period [d]</th><th>Observed</th><th>Local FAP</th><th>Global FAP</th><th>Above 95%</th><th>Above 99%</th><th>Interpretation</th></tr>
    </thead>
    <tbody>
{rows_html}
    </tbody>
  </table>
{cards}
"""


def _source_first_flux_html_card(
    summary: pd.DataFrame,
    significance: pd.DataFrame | None,
    flux_summary: pd.DataFrame,
    flux_significance: pd.DataFrame | None,
    flux_quality: pd.DataFrame | None,
    source_id: str,
) -> str:
    record = get_source(source_id)
    flux_row = _flux_summary_row(flux_summary, source_id)
    counts_row = _summary_row(summary, source_id)
    quality_row = _flux_quality_row(flux_quality, source_id)
    label = html.escape(record.label)
    tier_class = f"tier-{html.escape(str(quality_row.detection_tier).lower())}"
    low_ts_warning = ""
    if quality_row.detection_tier == "C":
        low_ts_warning = """
    <div class="quality-warning">
      <strong>Low-TS caveat.</strong> This source is not significantly detected in most weekly strict-flux bins. Treat the periodicity maps and AR(1) quick-look rows as diagnostics only, not as LHAASO QPO evidence.
    </div>
"""
    flux_lightcurve = _report_relative_path(
        FLUX_SURVEY_PERIODICITY_DIR / source_id / "wcda_strict_flux_weekly_lightcurve.png",
        REPORT_HTML.parent,
    )
    flux_periodicity = _report_relative_path(
        FLUX_SURVEY_PERIODICITY_DIR / source_id / "wcda_strict_flux_weekly_periodicity.png",
        REPORT_HTML.parent,
    )
    counts_path = _report_relative_path(SURVEY_PERIODICITY_DIR / source_id / "wcda_weekly_counts.png", REPORT_HTML.parent)
    counts_periodicity = _report_relative_path(
        SURVEY_PERIODICITY_DIR / source_id / "wcda_weekly_periodicity.png",
        REPORT_HTML.parent,
    )
    flux_significance_section = ""
    if flux_significance is not None:
        cwt_flux_sig_path = _report_relative_path(
            FLUX_SURVEY_PERIODICITY_DIR / source_id / "wcda_strict_flux_weekly_cwt_global_significance.png",
            REPORT_HTML.parent,
        )
        wwz_flux_sig_path = _report_relative_path(
            FLUX_SURVEY_PERIODICITY_DIR / source_id / "wcda_strict_flux_weekly_wwz_global_significance.png",
            REPORT_HTML.parent,
        )
        flux_significance_section = f"""
    <h4>Strict Flux Significance Quick Look</h4>
    <p class="note">CWT uses an AR(1) theory reference. WWZ uses AR(1) Gaussian surrogates on the same strict-flux weekly sampling. These values are not source-level, method-level, or survey-level trial corrected.</p>
    {_source_significance_html_table(flux_significance, source_id)}
    <figure>
      <img src="{html.escape(cwt_flux_sig_path)}" alt="{label} strict flux CWT AR(1) reference">
      <figcaption>Strict-flux CWT global-wavelet-spectrum AR(1) theory reference.</figcaption>
    </figure>
    <figure>
      <img src="{html.escape(wwz_flux_sig_path)}" alt="{label} strict flux WWZ AR(1) surrogate significance">
      <figcaption>Strict-flux WWZ AR(1) surrogate local/global FAP quick look.</figcaption>
    </figure>
"""
    significance_figures = ""
    if significance is not None:
        cwt_sig_path = _report_relative_path(
            SURVEY_PERIODICITY_DIR / source_id / "wcda_weekly_cwt_global_significance.png",
            REPORT_HTML.parent,
        )
        wwz_sig_path = _report_relative_path(
            SURVEY_PERIODICITY_DIR / source_id / "wcda_weekly_wwz_global_significance.png",
            REPORT_HTML.parent,
        )
        significance_figures = f"""
      <figure>
        <img src="{html.escape(cwt_sig_path)}" alt="{label} counts CWT AR(1) reference">
        <figcaption>Counts/excess-rate CWT AR(1) theory reference. This is not a strict-flux significance test.</figcaption>
      </figure>
      <figure>
        <img src="{html.escape(wwz_sig_path)}" alt="{label} counts WWZ AR(1) surrogate significance">
        <figcaption>Counts/excess-rate WWZ AR(1) surrogate quick look. This is not a strict-flux significance test.</figcaption>
      </figure>
"""
    return f"""
  <section class="source-card" id="strict-flux-{html.escape(source_id)}">
    <h3>{label}</h3>
    <span class="flux-badge">Strict Flux Primary</span>
    <span class="tier-badge {tier_class}">{html.escape(str(quality_row.detection_tier_label))}</span>
    <p class="meta">Source type: <code>{html.escape(record.source_type)}</code>; LHAASO token: <code>{html.escape(record.lhaaso_token)}</code>; date range: {html.escape(str(flux_row.date_min))} to {html.escape(str(flux_row.date_max))}.</p>
    <div class="metrics">
      <div class="metric"><span>Median weekly TS</span><strong>{quality_row.ts_median:.2f}</strong></div>
      <div class="metric"><span>TS&ge;9 weeks</span><strong>{int(quality_row.n_ts_ge_9)} / {int(quality_row.n_ts_rows)}</strong></div>
      <div class="metric"><span>Usable flux points</span><strong>{int(flux_row.n_points)} / {int(flux_row.n_rows)}</strong></div>
      <div class="metric"><span>Excluded fit rows</span><strong>{int(flux_row.n_bad_fit_rows)}</strong></div>
      <div class="metric"><span>Flux CWT peak</span><strong>{flux_row.cwt_peak_period_days:.2f} d</strong></div>
      <div class="metric"><span>Flux WWZ peak</span><strong>{flux_row.wwz_peak_period_days:.2f} d</strong></div>
    </div>
    <p class="quality-note">{html.escape(str(quality_row.interpretation))}.</p>
{low_ts_warning}
    <figure>
      <img src="{html.escape(flux_lightcurve)}" alt="{label} strict weekly flux light curve">
      <figcaption>Strict weekly WCDA flux normalization <code>N0</code> at 3 TeV. Excluded fit rows are marked when present.</figcaption>
    </figure>
    <figure>
      <img src="{html.escape(flux_periodicity)}" alt="{label} strict weekly flux CWT and WWZ quick-look">
      <figcaption>Strict weekly flux CWT map, WWZ map, and 1D global spectra. Red dashed lines mark algorithmic global-spectrum peaks only.</figcaption>
    </figure>
{_fermi_prior_html(source_id)}
{flux_significance_section}
    <details>
      <summary>Open counts / excess-rate validation for {label}</summary>
      <div class="details-body">
        <p class="meta">Counts/excess-rate points: {int(counts_row.n_points)}; MJD {counts_row.mjd_min:.3f}-{counts_row.mjd_max:.3f}; CWT peak {counts_row.cwt_peak_period_days:.2f} d; WWZ peak {counts_row.wwz_peak_period_days:.2f} d.</p>
        <figure>
          <img src="{html.escape(counts_path)}" alt="{label} WCDA weekly photon-count diagnostic">
          <figcaption>Weekly photon-count diagnostic using excess counts and total on/background counts.</figcaption>
        </figure>
        <figure>
          <img src="{html.escape(counts_periodicity)}" alt="{label} WCDA weekly CWT and WWZ quick-look">
          <figcaption>WCDA weekly excess-rate light curve, CWT map, WWZ map, and 1D global spectra.</figcaption>
        </figure>
{significance_figures}
      </div>
    </details>
  </section>
"""


def _flux_markdown_table(flux_summary: pd.DataFrame) -> str:
    lines = [
        "| Source | Usable / Rows | Bad fits | Date min | Date max | CWT peak [d] | CWT GWS | WWZ peak [d] | WWZ power |",
        "| --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for source_id in WCDA_STRICT_FLUX_SOURCE_IDS:
        row = _flux_summary_row(flux_summary, source_id)
        lines.append(
            f"| {row.source} | {int(row.n_points)} / {int(row.n_rows)} | {int(row.n_bad_fit_rows)} | "
            f"{row.date_min} | {row.date_max} | {row.cwt_peak_period_days:.2f} | {row.cwt_peak_gws:.3f} | "
            f"{row.wwz_peak_period_days:.2f} | {row.wwz_peak_power:.3f} |"
        )
    return "\n".join(lines)


def _flux_peak_markdown_table(
    flux_summary: pd.DataFrame,
    flux_significance: pd.DataFrame | None,
    flux_quality: pd.DataFrame | None,
) -> str:
    if flux_significance is None:
        return _flux_markdown_table(flux_summary)
    lines = [
        "| Source | Detection tier | Median TS | TS>=9 weeks | Method | Peak period [d] | Observed | Local FAP | Global FAP | Above 95% | Above 99% | Interpretation |",
        "| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for source_id in WCDA_STRICT_FLUX_SOURCE_IDS:
        flux_row = _flux_summary_row(flux_summary, source_id)
        quality_row = _flux_quality_row(flux_quality, source_id)
        sig_rows = _ordered_source_significance_rows(flux_significance, source_id)
        tier_cell = str(quality_row.detection_tier_label)
        ts_cell = f"{quality_row.ts_median:.2f}"
        ts9_cell = f"{int(quality_row.n_ts_ge_9)} / {int(quality_row.n_ts_rows)}"
        interpretation_cell = str(quality_row.interpretation)
        if not sig_rows:
            lines.append(
                f"| {flux_row.source} | {tier_cell} | {ts_cell} | {ts9_cell} | none | - | - | - | - | - | - | {interpretation_cell} |"
            )
            continue
        for idx, sig_row in enumerate(sig_rows):
            source_cell = str(flux_row.source) if idx == 0 else ""
            tier_out = tier_cell if idx == 0 else ""
            ts_out = ts_cell if idx == 0 else ""
            ts9_out = ts9_cell if idx == 0 else ""
            interpretation_out = interpretation_cell if idx == 0 else ""
            lines.append(
                f"| {source_cell} | {tier_out} | {ts_out} | {ts9_out} | {sig_row.method} | "
                f"{sig_row.period_days:.2f} | {sig_row.observed_statistic:.3f} | "
                f"{_format_fap(sig_row.local_fap)} | {_format_fap(sig_row.global_fap)} | "
                f"{_format_bool(sig_row.above_95)} | {_format_bool(sig_row.above_99)} | {interpretation_out} |"
            )
    return "\n".join(lines)


def _flux_html_rows(flux_summary: pd.DataFrame) -> list[str]:
    rows = []
    for source_id in WCDA_STRICT_FLUX_SOURCE_IDS:
        row = _flux_summary_row(flux_summary, source_id)
        rows.append(
            "      "
            f"<tr><td>{html.escape(str(row.source))}</td><td>{int(row.n_points)} / {int(row.n_rows)}</td>"
            f"<td>{int(row.n_bad_fit_rows)}</td><td>{html.escape(str(row.date_min))}</td>"
            f"<td>{html.escape(str(row.date_max))}</td><td>{row.cwt_peak_period_days:.2f}</td>"
            f"<td>{row.cwt_peak_gws:.3f}</td><td>{row.wwz_peak_period_days:.2f}</td>"
            f"<td>{row.wwz_peak_power:.3f}</td></tr>"
        )
    return rows


def _flux_peak_html_rows(
    flux_summary: pd.DataFrame,
    flux_significance: pd.DataFrame | None,
    flux_quality: pd.DataFrame | None,
) -> list[str]:
    if flux_significance is None:
        return _flux_html_rows(flux_summary)
    rows = []
    for source_id in WCDA_STRICT_FLUX_SOURCE_IDS:
        flux_row = _flux_summary_row(flux_summary, source_id)
        quality_row = _flux_quality_row(flux_quality, source_id)
        sig_rows = _ordered_source_significance_rows(flux_significance, source_id)
        tier_class = f"tier-{html.escape(str(quality_row.detection_tier).lower())}"
        tier_cell = f'<span class="tier-badge {tier_class}">{html.escape(str(quality_row.detection_tier_label))}</span>'
        ts9_cell = f"{int(quality_row.n_ts_ge_9)} / {int(quality_row.n_ts_rows)}"
        interpretation = html.escape(str(quality_row.interpretation))
        if not sig_rows:
            rows.append(
                "      "
                f"<tr><td>{html.escape(str(flux_row.source))}</td><td>{tier_cell}</td>"
                f"<td>{quality_row.ts_median:.2f}</td><td>{ts9_cell}</td><td>none</td><td>-</td>"
                f"<td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>{interpretation}</td></tr>"
            )
            continue
        rowspan = len(sig_rows)
        for idx, sig_row in enumerate(sig_rows):
            prefix = ""
            if idx == 0:
                prefix = (
                    f"<td rowspan=\"{rowspan}\">{html.escape(str(flux_row.source))}</td>"
                    f"<td rowspan=\"{rowspan}\">{tier_cell}</td>"
                    f"<td rowspan=\"{rowspan}\">{quality_row.ts_median:.2f}</td>"
                    f"<td rowspan=\"{rowspan}\">{ts9_cell}</td>"
                )
            suffix = f"<td rowspan=\"{rowspan}\">{interpretation}</td>" if idx == 0 else ""
            rows.append(
                "      "
                f"<tr>{prefix}<td>{html.escape(str(sig_row.method))}</td><td>{sig_row.period_days:.2f}</td>"
                f"<td>{sig_row.observed_statistic:.3f}</td><td>{_format_fap(sig_row.local_fap)}</td>"
                f"<td>{_format_fap(sig_row.global_fap)}</td><td>{_format_bool(sig_row.above_95)}</td>"
                f"<td>{_format_bool(sig_row.above_99)}</td>{suffix}</tr>"
            )
    return rows


def _ordered_significance_rows(significance: pd.DataFrame) -> list[pd.Series]:
    rows = []
    method_order = {"CWT": 0, "WWZ": 1}
    for source_id in WCDA_WEEK_SURVEY_SOURCE_IDS:
        source_rows = significance.loc[significance["source_id"] == source_id].copy()
        if source_rows.empty:
            continue
        source_rows["_method_order"] = source_rows["method"].map(method_order).fillna(99)
        source_rows = source_rows.sort_values(["_method_order", "period_days"])
        rows.extend(row for _idx, row in source_rows.iterrows())
    return rows


def _format_fap(value) -> str:
    value = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(value):
        return "-"
    return f"{float(value):.4f}"


def _format_bool(value) -> str:
    if pd.isna(value):
        return "-"
    return "yes" if bool(value) else "no"


def _summary_row(summary: pd.DataFrame, source_id: str) -> pd.Series:
    rows = summary.loc[summary["source_id"] == source_id]
    if len(rows) != 1:
        raise ValueError(f"Expected exactly one summary row for {source_id}, found {len(rows)}.")
    return rows.iloc[0]


def _flux_summary_row(flux_summary: pd.DataFrame, source_id: str) -> pd.Series:
    rows = flux_summary.loc[flux_summary["source_id"] == source_id]
    if len(rows) != 1:
        raise ValueError(f"Expected exactly one strict flux summary row for {source_id}, found {len(rows)}.")
    return rows.iloc[0]


def _flux_quality_row(flux_quality: pd.DataFrame | None, source_id: str) -> pd.Series:
    if flux_quality is None:
        raise ValueError("Strict flux quality table is required for detection-tiered reporting.")
    rows = flux_quality.loc[flux_quality["source_id"] == source_id]
    if len(rows) != 1:
        raise ValueError(f"Expected exactly one strict flux quality row for {source_id}, found {len(rows)}.")
    return rows.iloc[0]


def _report_relative_path(path: Path, report_dir: Path) -> str:
    return Path(path).resolve().relative_to(report_dir.resolve()).as_posix() if path.resolve().is_relative_to(report_dir.resolve()) else Path("..", path.resolve().relative_to(PROJECT_ROOT.resolve())).as_posix()


if __name__ == "__main__":
    main()
