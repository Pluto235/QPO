#!/usr/bin/env python3
"""Build the single-file, base64-embedded HTML status report for the
Mrk 421 / Mrk 501 WCDA QPO search (advisor/collaborator deliverable).

Run: python3 reports/build_mkn421_mkn501_status_report.py
Output: reports/mkn421_mkn501_qpo_status_report.html
"""
import base64
import csv
import html
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed" / "periodicity"
SURVEY = DATA / "agn_wcda_weekly_flux_survey"
FIG_DIR = ROOT / "reports" / "assets" / "status_report_figures"
OUT = ROOT / "reports" / "mkn421_mkn501_qpo_status_report.html"

SOURCE_NAMES = {
    "mkn421": "Mrk 421",
    "mkn501": "Mrk 501",
    "1es1959p650": "1ES 1959+650",
    "1es1727p502": "1ES 1727+502",
    "1es2344p514": "1ES 2344+514",
    "bllac": "BL Lacertae",
    "ngc1275": "NGC 1275",
    "m87": "M 87",
    "4c_p42d22": "4C +42.22",
    "ic310": "IC 310",
}

# Detection-quality tiers, transcribed from reports/agn_wcda_weekly_survey_report.md
# (Tier A if median TS >= 9 or TS>=9 fraction >= 50%; Tier C otherwise; no Tier B present here).
TIERS = {
    "mkn421": ("Tier A — timing-grade", 137.90, "218/229 (95.2%)"),
    "mkn501": ("Tier A — timing-grade", 22.27, "165/229 (72.1%)"),
    "1es1959p650": ("Tier C — diagnostic only", 0.49, "20/229 (8.7%)"),
    "1es1727p502": ("Tier C — diagnostic only", 1.35, "18/229 (7.9%)"),
    "1es2344p514": ("Tier C — diagnostic only", 0.39, "11/229 (4.8%)"),
    "bllac": ("Tier C — diagnostic only", 0.06, "6/229 (2.6%)"),
    "ngc1275": ("Tier C — diagnostic only", 0.06, "9/229 (3.9%)"),
    "m87": ("Tier C — diagnostic only", 0.24, "3/229 (1.3%)"),
    "4c_p42d22": ("Tier C — diagnostic only", 0.00, "2/229 (0.9%)"),
    "ic310": ("Tier C — diagnostic only", 0.21, "14/229 (6.1%)"),
}

SECONDARY_ORDER = [
    "1es1959p650", "1es1727p502", "1es2344p514", "bllac",
    "ngc1275", "m87", "4c_p42d22", "ic310",
]


def b64_img(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def figure(path: Path, caption: str, width_pct: int = 100) -> str:
    data = b64_img(path)
    cap = html.escape(caption)
    return (
        f'<figure style="width:{width_pct}%"><img src="data:image/png;base64,{data}" '
        f'alt="{cap}" loading="lazy"><figcaption>{cap}</figcaption></figure>'
    )


def load_csv(path: Path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def fnum(x, nd=2):
    try:
        return f"{float(x):.{nd}f}"
    except (TypeError, ValueError):
        return "—"


def fpct(x):
    try:
        return f"{float(x) * 100:.1f}%"
    except (TypeError, ValueError):
        return "—"


def yn(x):
    return "yes" if str(x).strip() == "True" else "no"


def significance_table(rows, source_id):
    srows = [r for r in rows if r["source_id"] == source_id]
    out = ['<table class="sig"><thead><tr>',
           "<th>Method</th><th>Period [d]</th><th>Cycles</th><th>Observed</th>",
           "<th>Local FAP</th><th>Global FAP</th><th>&ge;95%</th><th>&ge;99%</th><th>Note</th>",
           "</tr></thead><tbody>"]
    for r in srows:
        method = r["method"]
        local_fap = fpct(r["local_fap"]) if r["local_fap"] else "n/a (AR1 theory)"
        global_fap = fpct(r["global_fap"]) if r["global_fap"] else "n/a (AR1 theory)"
        note = "fewer than 4 cycles" if "Fewer than four" in r.get("note", "") else ""
        out.append(
            f"<tr><td>{method}</td><td>{fnum(r['period_days'], 1)}</td>"
            f"<td>{fnum(r['cycles'], 1)}</td><td>{fnum(r['observed_statistic'], 2)}</td>"
            f"<td>{local_fap}</td><td>{global_fap}</td>"
            f"<td>{yn(r['above_95'])}</td><td>{yn(r['above_99'])}</td><td>{note}</td></tr>"
        )
    out.append("</tbody></table>")
    return "\n".join(out)


def best_candidate(rows, source_id, method):
    srows = [r for r in rows if r["source_id"] == source_id and r["method"] == method]
    if not srows:
        return None
    # "best" = lowest global_fap when available, else first row
    with_fap = [r for r in srows if r["global_fap"]]
    pool = with_fap or srows
    return min(pool, key=lambda r: float(r["global_fap"]) if r["global_fap"] else 1.0)


def main():
    survey_summary = {r["source_id"]: r for r in load_csv(SURVEY / "agn_wcda_weekly_flux_survey_summary.csv")}
    sig_rows = load_csv(SURVEY / "agn_wcda_weekly_flux_significance_summary.csv")

    mkn421_dir = SURVEY / "mkn421"
    mkn501_dir = SURVEY / "mkn501"
    v2_421 = DATA / "periodicity_v2" / "mkn421"
    v2_501 = DATA / "periodicity_v2" / "mkn501"

    # ---- Primary source figure blocks: uniform 5-figure set per cadence, from the ----
    # ---- dedicated reports/assets/status_report_figures/ folder (see              ----
    # ---- src/pipeline/build_status_report_figures.py). Same layout for both        ----
    # ---- cadences: 1) LC+TS  2) CWT summary (global spectrum + 2D map)             ----
    # ----            3) WWZ summary (global WWZ + 2D map)  4) CWT significance      ----
    # ----            5) WWZ significance.                                          ----
    def primary_cadence_block(label, source_id, cadence, n_pts, mjd_range, extra_note=""):
        prefix = FIG_DIR / f"{source_id}_{cadence}"
        cadence_title = cadence.capitalize()
        return (
            '<div class="cadence-block">'
            f'<span class="cadence-label">{cadence_title} cadence</span>'
            f'<p class="caveat">N={n_pts}, {mjd_range}.{extra_note}</p>'
            + figure(Path(f"{prefix}_lc_ts.png"), f"{label} — {cadence} N0 flux light curve and per-bin TS", 100)
            + '<div class="fig-grid">'
            + figure(Path(f"{prefix}_cwt_summary.png"),
                     f"{label} — {cadence} CWT 2D power map (left) and global wavelet spectrum (right)", 50)
            + figure(Path(f"{prefix}_wwz_summary.png"),
                     f"{label} — {cadence} WWZ 2D power map (left) and global WWZ (right)", 50)
            + figure(Path(f"{prefix}_cwt_significance.png"),
                     f"{label} — {cadence} CWT vs. AR(1) 95%/99% reference", 50)
            + figure(Path(f"{prefix}_wwz_significance.png"),
                     f"{label} — {cadence} WWZ vs. AR(1) surrogate 95%/99% reference (1000 realizations)", 50)
            + "</div></div>"
        )

    def fermi_cadence_block(label, source_id, n_pts, mjd_range):
        prefix = FIG_DIR / f"{source_id}_fermi"
        return (
            '<div class="cadence-block">'
            '<span class="cadence-label">Fermi weekly cadence</span>'
            f'<p class="caveat">N={n_pts}, {mjd_range}, re-binned onto the WCDA weekly time axis. '
            "No per-bin TS is retained in this processed product, so no TS panel is shown.</p>"
            + figure(Path(f"{prefix}_lc_ts.png"), f"{label} — Fermi-LAT weekly flux (0.1-300 GeV)", 100)
            + '<div class="fig-grid">'
            + figure(Path(f"{prefix}_cwt_summary.png"),
                     f"{label} — Fermi weekly CWT 2D power map (left) and global wavelet spectrum (right)", 50)
            + figure(Path(f"{prefix}_wwz_summary.png"),
                     f"{label} — Fermi weekly WWZ 2D power map (left) and global WWZ (right)", 50)
            + figure(Path(f"{prefix}_cwt_significance.png"), f"{label} — Fermi weekly CWT vs. AR(1) 95%/99% reference", 50)
            + figure(Path(f"{prefix}_wwz_significance.png"),
                     f"{label} — Fermi weekly WWZ vs. AR(1) surrogate 95%/99% reference (1000 realizations)", 50)
            + "</div></div>"
        )

    mkn421_figs = (
        primary_cadence_block("Mrk 421", "mkn421", "weekly", 229, "2021-03-08 to 2025-07-27, median cadence 7.0&nbsp;d")
        + primary_cadence_block("Mrk 421", "mkn421", "daily", 1570, "MJD 59281.5–60887.5 (2021-06-10 to 2025-07-31)")
        + fermi_cadence_block("Mrk 421", "mkn421", 224, "2021-03-08 to 2025-07-27")
    )

    mkn501_figs = (
        primary_cadence_block("Mrk 501", "mkn501", "weekly", 229, "2021-03-08 to 2025-07-27, median cadence 7.0&nbsp;d")
        + primary_cadence_block("Mrk 501", "mkn501", "daily", 1560, "MJD 59282.5–60887.5 (2021-06-11 to 2025-07-31)")
    )

    # ---- Secondary source table + figure grid ----
    sec_table_rows = []
    sec_figs = []
    for sid in SECONDARY_ORDER:
        name = SOURCE_NAMES[sid]
        tier, med_ts, frac = TIERS[sid]
        best_cwt = best_candidate(sig_rows, sid, "CWT")
        best_wwz = best_candidate(sig_rows, sid, "WWZ")
        cwt_str = (f"{fnum(best_cwt['period_days'], 1)} d "
                   f"(&ge;95%: {yn(best_cwt['above_95'])}, &ge;99%: {yn(best_cwt['above_99'])})") if best_cwt else "—"
        wwz_str = (f"{fnum(best_wwz['period_days'], 1)} d, local FAP {fpct(best_wwz['local_fap'])} "
                   f"(&ge;95%: {yn(best_wwz['above_95'])}, &ge;99%: {yn(best_wwz['above_99'])})") if best_wwz else "—"
        flag = ""
        if sid == "ngc1275":
            flag = ' <span class="flag">† see callout below</span>'
        sec_table_rows.append(
            f"<tr><td>{name}</td><td>{tier}</td><td>{fnum(med_ts, 2)}</td><td>{frac}</td>"
            f"<td>{cwt_str}</td><td>{wwz_str}{flag}</td></tr>"
        )
        src_dir = SURVEY / sid
        group = (
            f'<h4>{name} <span class="caveat">(Tier C, diagnostic only)</span></h4>'
            '<div class="source-fig-row">'
            f'<div class="source-fig-main">{figure(src_dir / "wcda_strict_flux_weekly_periodicity.png", f"{name} — weekly CWT+WWZ composite quicklook", 100)}</div>'
            '<div class="source-fig-side">'
            + figure(src_dir / "wcda_strict_flux_weekly_cwt_global_significance.png",
                     f"{name} — CWT global wavelet spectrum vs. AR(1) 95%/99% reference", 100)
            + figure(src_dir / "wcda_strict_flux_weekly_wwz_global_significance.png",
                     f"{name} — WWZ vs. AR(1) surrogate 95%/99% reference (1000 realizations)", 100)
            + "</div></div>"
        )
        sec_figs.append(group)

    secondary_table_html = (
        '<table class="sig"><thead><tr><th>Source</th><th>Detection tier</th>'
        "<th>Median weekly TS</th><th>Weeks with TS&ge;9</th>"
        "<th>Best CWT candidate</th><th>Best WWZ candidate</th></tr></thead><tbody>"
        + "\n".join(sec_table_rows) + "</tbody></table>"
    )
    secondary_figs_html = "\n".join(sec_figs)

    mkn421_sig_table = significance_table(sig_rows, "mkn421")
    mkn501_sig_table = significance_table(sig_rows, "mkn501")

    daily_sig_rows = load_csv(DATA / "periodicity_v2" / "daily_significance_summary.csv")
    mkn421_daily_sig_table = significance_table(daily_sig_rows, "mkn421")
    mkn501_daily_sig_table = significance_table(daily_sig_rows, "mkn501")

    ren_repro_fig = figure(
        DATA / "ren2022_repro" / "mkn421" / "ren2022_repro_mkn421.png",
        "Mrk 421 Fermi-LAT weekly flux, Ren et al. (2022) baseline (2008-08 to 2021-04, N=650): "
        "light curve, observed CWT global wavelet spectrum, and Emmanoulopoulos MC null distribution "
        "at the 300 d target period", 100,
    )

    xgm_dir = DATA / "periodicity_v2" / "xgm_poster_repro" / "mkn421"
    xgm_wwz_quicklook_fig = figure(
        xgm_dir / "mkn421_daily_flux_60200_60700_wwz_quicklook_with_sig.png",
        "Mrk 421 v2 daily flux, MJD 60200–60700 (xgm poster window): light curve (left), WWZ 2D power "
        "map (middle) with the poster's 51.05 d target marked (red dashed line), and global WWZ with "
        "AR(1) 95%/99% reference (right)", 100,
    )
    xgm_figs = (
        '<div class="fig-grid">'
        + figure(
            xgm_dir / "mkn421_daily_flux_60200_60700_wwz_significance.png",
            "Mrk 421 v2 daily flux, MJD 60200–60700 (xgm poster window): observed WWZ vs. AR(1) "
            "surrogate 95%/99% reference (1000 realizations); red line marks the poster's 51.05 d target, "
            "blue line marks this window's own global WWZ peak (111.0 d) for comparison", 50,
        )
        + figure(
            xgm_dir / "mkn421_daily_flux_60200_60700_cwt_significance.png",
            "Mrk 421 v2 daily flux, MJD 60200–60700 (xgm poster window): observed CWT global wavelet "
            "spectrum vs. AR(1) 95%/99% theoretical reference; red line marks the poster's 51.05 d target, "
            "blue line marks this window's own global CWT peak (124.8 d) for comparison", 50,
        )
        + "</div>"
    )

    generated_date = "2026-07-02"

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>LHAASO-WCDA Flux Periodicity Search in Mrk 421 and Mrk 501 &mdash; Status Report</title>
<style>
  :root {{
    --fg: #1c1f24; --muted: #5b6472; --border: #dfe3e8; --accent: #a6362c;
    --bg-callout: #fdf3f2; --bg-table: #f7f8fa;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: "Georgia", "Times New Roman", serif;
    color: var(--fg); line-height: 1.6; max-width: 960px; margin: 0 auto; padding: 2.5rem 1.5rem 6rem;
    background: #fff;
  }}
  h1 {{ font-size: 1.7rem; margin-bottom: 0.2rem; }}
  h2 {{ font-size: 1.25rem; margin-top: 2.6rem; border-bottom: 2px solid var(--border); padding-bottom: 0.3rem; }}
  h3 {{ font-size: 1.05rem; margin-top: 1.8rem; color: var(--accent); }}
  h4 {{ font-size: 0.95rem; margin-top: 1.2rem; }}
  .subtitle {{ color: var(--muted); font-size: 0.95rem; margin-bottom: 1.6rem; }}
  .exec-summary {{
    background: var(--bg-table); border-left: 4px solid var(--accent);
    padding: 1rem 1.2rem; font-size: 0.97rem; margin: 1.2rem 0 2rem;
  }}
  table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: 0.86rem; font-family: "Helvetica Neue", Arial, sans-serif; }}
  table.sig th, table.sig td {{ border: 1px solid var(--border); padding: 0.35rem 0.5rem; text-align: right; }}
  table.sig th:first-child, table.sig td:first-child,
  table.sig th:nth-child(2), table.sig td:nth-child(2) {{ text-align: left; }}
  table.sig thead {{ background: var(--bg-table); }}
  table.lit th, table.lit td {{ border: 1px solid var(--border); padding: 0.4rem 0.6rem; text-align: left; font-family: "Helvetica Neue", Arial, sans-serif; font-size: 0.86rem; vertical-align: top; }}
  table.lit thead {{ background: var(--bg-table); }}
  figure {{ display: inline-block; vertical-align: top; margin: 0.4rem 0.5% 1rem 0; }}
  figure img {{ width: 100%; border: 1px solid var(--border); border-radius: 3px; display: block; }}
  figcaption {{ font-size: 0.78rem; color: var(--muted); margin-top: 0.3rem; font-family: "Helvetica Neue", Arial, sans-serif; }}
  .fig-grid {{ display: flex; flex-wrap: wrap; gap: 0 1%; }}
  .source-fig-row {{ display: flex; align-items: flex-start; gap: 1.5%; }}
  .source-fig-main {{ width: 56%; }}
  .source-fig-main figure {{ width: 100% !important; margin-right: 0; }}
  .source-fig-side {{ width: 42.5%; display: flex; flex-direction: column; gap: 0.6rem; }}
  .source-fig-side figure {{ width: 100% !important; margin-right: 0; }}
  .cadence-block {{ margin-top: 1.4rem; }}
  .cadence-label {{
    display: inline-block; font-weight: 700; font-family: "Helvetica Neue", Arial, sans-serif;
    font-size: 0.82rem; letter-spacing: 0.04em; text-transform: uppercase; color: #fff;
    background: var(--accent); padding: 0.15rem 0.6rem; border-radius: 3px; margin-bottom: 0.6rem;
  }}
  .callout {{
    background: var(--bg-callout); border: 1px solid #f0c9c4; border-radius: 4px;
    padding: 0.9rem 1.1rem; margin: 1.2rem 0; font-size: 0.92rem;
  }}
  .callout strong {{ color: var(--accent); }}
  .callout.info {{ background: #eef3fa; border-color: #c7d7ec; }}
  .callout.info strong {{ color: #1d4f8f; }}
  .flag {{ color: var(--accent); font-size: 0.78rem; }}
  ul, ol {{ padding-left: 1.4rem; }}
  li {{ margin-bottom: 0.35rem; }}
  code {{ background: var(--bg-table); padding: 0.1rem 0.3rem; border-radius: 3px; font-size: 0.9em; }}
  .caveat {{ color: var(--muted); font-size: 0.88rem; }}
  footer {{ margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--border); color: var(--muted); font-size: 0.8rem; }}
</style>
</head>
<body>

<h1>LHAASO-WCDA Flux Periodicity Search in Mrk 421 and Mrk 501</h1>
<p class="subtitle">Status report &middot; prepared for advisor and collaborator review &middot; {generated_date}<br>
QPO working group &middot; data window 2021-03-08 to 2025-07-27/31 &middot; source: <code>QPO/</code> repository, commit <code>9e07a61</code></p>

<div class="exec-summary">
<strong>Executive summary.</strong> This report summarizes the current state of the quasi-periodic
oscillation (QPO) search in Mrk 421 and Mrk 501 using LHAASO-WCDA weekly <em>and</em> daily flux products,
with eight additional AGN included as detection-quality controls. At <strong>weekly</strong> cadence,
continuous wavelet transform (CWT) and weighted wavelet Z-transform (WWZ) scans find several candidate
periods in both primary sources, but none clear the pre-registered AR(1) surrogate significance threshold.
At <strong>daily</strong> cadence, Mrk 421 shows only a borderline, cadence-dependent hint (WWZ 128&nbsp;d,
local-only 95%), but <strong>Mrk 501 shows a candidate at &sim;152&ndash;157&nbsp;d that formally exceeds
both the 95% and 99% AR(1) reference in both CWT and WWZ</strong> &mdash; the strongest candidate in this
report, though it does not appear at weekly cadence for the same data (a binning-sensitivity split that
directly echoes Ren et al. 2022's own 30-day-vs-7-day disagreement for this source) and carries no
multi-comparison trial correction. Neither primary source's weekly result reproduces the &gt;5&sigma;
GeV-band periodicities Ren et al. (2022) report at ~300&nbsp;d (Mrk 421) and ~326&nbsp;d (Mrk 501). A second
nominally significant candidate appears in the low-detection-quality control source NGC&nbsp;1275; it is
flagged here for discussion, not claimed as a detection. An independent feasibility-scale reproduction of
Ren et al. (2022)'s own GeV-band method on Mrk 421 finds a candidate near their claimed period
(291.5&nbsp;d vs. 300&plusmn;65&nbsp;d) with a suggestive local false-alarm probability (2.3%) but an
unremarkable global one (48.3%) &mdash; well short of their &gt;5&sigma; claim; the equivalent check for
Mrk 501 is still in progress (see &sect;7). The report closes with concrete next steps to extend
statistical power and enable a fair comparison with the GeV literature.
</div>

<h2 id="motivation">1. Motivation</h2>
<p>Quasi-periodic oscillations in blazar &gamma;-ray light curves are usually interpreted through two
physical pictures: (i) a helical or precessing structure within a relativistically boosted jet sweeping
periodically across the line of sight, which favors shorter periods (months); or (ii) orbital motion or
jet precession in a supermassive black hole binary (SMBBH) system, or Lense&ndash;Thirring precession of
the accretion disk, which favors longer periods (years). A confirmed QPO would be a rare, direct probe of
jet geometry or a binary SMBH system &mdash; but robust claims in the blazar population remain contested,
with detection rates and significance highly sensitive to method, sample size, and trial correction.</p>

<table class="lit">
<thead><tr><th>Reference</th><th>Sample</th><th>Method</th><th>Headline result</th></tr></thead>
<tbody>
<tr><td>Ren et al. 2022</td><td>35 brightest 4LAC blazars</td><td>CWT + Emmanoulopoulos Monte Carlo</td>
<td>36 candidates across 24 sources (&gt;5&sigma् post-trial), including <strong>Mrk 421 at 300&plusmn;65&nbsp;d
(7-day bins, &gt;5&sigma, 3 cycles)</strong> and <strong>Mrk 501 at 326&plusmn;76&nbsp;d (7-day bins,
&gt;5&sigma, 7 cycles)</strong></td></tr>
<tr><td>Chen et al. 2024</td><td>134 flux-limited blazars</td><td>WWZ + LSP + Emmanoulopoulos MC</td>
<td>6/134 sources with transient QPO (8 events, 54&ndash;341&nbsp;d), &sim;3% incidence, helical-jet favored</td></tr>
<tr><td>Pe&ntilde;il et al. 2025</td><td>1492 jetted AGN (4FGL)</td><td>9-method ensemble with trial-factor correction</td>
<td><strong>0 globally significant detections</strong> after correction &mdash; the field-level null-result baseline</td></tr>
</tbody>
</table>

<p>Across the compiled Fermi-LAT QPO literature (11 papers, 81 unique AGN), <strong>Mrk 421 and Mrk 501
are the only two sources with a direct positional match (&lt;0.05&deg;) to the 1LHAASO source
catalog</strong> &mdash; i.e. the only two blazars that combine a published GeV periodicity claim with a
robust, independent TeV detection by LHAASO. That makes them the natural targets for an independent,
cross-band QPO consistency check: <strong>this analysis tests, at TeV energies and with a different
instrument and systematics, whether the WCDA weekly/daily flux light curves of Mrk 421 and Mrk 501 show
statistically significant periodicity, and whether any signal found is consistent with the Ren et al.
(2022) GeV-band claims.</strong></p>

<h2 id="method">2. Data &amp; Method</h2>
<p>The analysis uses LHAASO-WCDA strict-batch weekly/daily counts products for Mrk 421, Mrk 501, and
eight additional AGN (1ES 1959+650, 1ES 1727+502, 1ES 2344+514, BL Lacertae, NGC 1275, M 87, 4C&nbsp;+42.22,
IC 310), covering <strong>2021-03-08 to 2025-07-27</strong> at weekly cadence (229 points per source) and
to <strong>2025-07-31</strong> at daily cadence for the two primary sources (1570 / 1560 points). A
Fermi-LAT weekly flux series for Mrk 421, re-binned onto the WCDA weekly time axis, is included for one
direct cross-band comparison.</p>

<h3>Flux extraction (forward folding)</h3>
<p>Raw WCDA <code>nhits</code>-binned counts are converted to physical flux by forward-folding an assumed
power-law spectrum (fixed photon index &Gamma;&nbsp;=&nbsp;2.6) through the period-resolved detector
response library, then fitting the flux normalization <code>N0</code> (at E0&nbsp;=&nbsp;3&nbsp;TeV) via
a Poisson likelihood. This supersedes an earlier photon-count / excess-rate proxy
(<code>(n_on&minus;n_bkg)/t_obs</code>) used in preliminary work, which does not correct for detector
efficiency, effective area, or zenith-angle response and is not a physical flux. Rows with
<code>N0_err</code> greater than 5&times; the per-source/cadence median are excluded as a quality cut
before periodicity analysis (affects &lt;2% of rows; see Appendix).</p>

<h3>Periodicity scan and significance testing</h3>
<p>Both methods decompose the weekly (or daily) flux series into a time&ndash;period map and then collapse it
into a 1-D power spectrum, which is tested against a red-noise null hypothesis. The two methods use different
statistical machinery, so they are treated as independent checks rather than reported as a single combined
number:</p>
<ul>
<li><strong>CWT (global wavelet spectrum, GWS).</strong> A Morlet wavelet transform (via <code>pycwt</code>)
is applied to the flux series, and the time-averaged power at each period &mdash; the global wavelet
spectrum &mdash; is compared against the theoretical power spectrum of a best-fit AR(1) (first-order
autoregressive / "red noise") process, following the standard Torrence &amp; Compo (1998) formalism. The
95%/99% significance thresholds are the analytic <code>&chi;&sup2;</code> quantiles of that theoretical AR(1)
reference spectrum at each period; no Monte Carlo surrogates are drawn for CWT, so no local/global FAP number
is reported for it (shown as "n/a (AR1 theory)" in the candidate tables) &mdash; only whether the observed
GWS curve crosses the 95%/99% reference curve.</li>
<li><strong>WWZ (weighted wavelet Z-transform).</strong> Computed via <code>libwwz</code>
(<code>time_divisions=80</code>, <code>freq_step_factor=0.5</code>). Significance is assessed empirically:
1000 synthetic light curves are generated from an AR(1) Gaussian process fitted to the same source (same
mean, variance, and lag-1 autocorrelation as the real weekly series), each is put through the identical WWZ
pipeline, and the observed WWZ power at a given period is compared to the resulting surrogate distribution.
This gives two false-alarm probabilities (FAP): <strong>local FAP</strong> is the fraction of surrogates
whose maximum WWZ power inside a &plusmn;10% window around the candidate period exceeds the observed value
(tests "is this specific peak unusual compared to nearby periods"); <strong>global FAP</strong> is the same
comparison but against the surrogate maximum over the full 50&ndash;600&nbsp;d search range (tests "is this
the strongest peak I would expect to see anywhere in the search range by chance"). Global FAP is always
&ge; local FAP, and is the more conservative number.</li>
<li>Search range: 50&ndash;600 days, weekly cadence.</li>
<li><strong>No source-, method-, or survey-level trial (look-elsewhere) correction has been applied at this
stage.</strong> Every source and every method is tested independently; with 10 sources &times; 2 methods
&times; a 50&ndash;600&nbsp;d search window, some nominally significant peaks are expected by chance alone
even if no real periodicity exists anywhere in the sample. Quoted FAP values are per-candidate only &mdash;
this is stated explicitly wherever significance numbers are quoted below, and is the reason the NGC 1275
candidate in &sect;5 is flagged rather than claimed.</li>
</ul>
<p class="caveat"><strong>How to read the significance figures below:</strong> in each CWT panel, the solid
curve is the observed global wavelet spectrum and the dashed/dotted curves are the theoretical AR(1) 95%/99%
reference levels &mdash; a genuine detection would cross above the 99% curve. In each WWZ panel, the solid
curve is the observed WWZ power and the shaded band / dashed curves are the 95%/99% levels of the 1000-surrogate
AR(1) distribution at each period &mdash; again, a genuine detection would rise above the 99% level.</p>

<div class="callout">
<strong>Known coverage limitation.</strong> The forward-folding pipeline currently only has detector-response
coverage for periods <code>T001</code>&ndash;<code>T083</code> (&asymp;2021-03-08 to 2025-08-03). Response
files for <code>T084</code>&ndash;<code>T091</code> and the period map beyond 2025-11-05 are not yet
available, so all light curves in this report stop in mid-2025 and do not yet include the most recent
&sim;1&nbsp;year of WCDA data. This is a resource/access gap, not a physics result, and is the single
most direct lever for adding statistical power (see &sect;8).
</div>

<h2 id="mkn421">3. Primary Results &mdash; Mrk 421</h2>
<p>Detection quality: <strong>Tier A, timing-grade</strong> (median weekly TS 137.90; TS&ge;9 in 218/229
weeks, 95.2%). 229 weekly points (2021-03-08 to 2025-07-27, median cadence 7.0&nbsp;d) and 1570 daily points
(MJD 59281.5&ndash;60887.5) pass quality cuts.</p>

{mkn421_figs}

<h3>Weekly candidate periods and significance</h3>
{mkn421_sig_table}
<p class="caveat">No candidate reaches the 95% global threshold in either method. The closest approach is
the WWZ peak at 131.25&nbsp;d, with a <strong>local</strong> FAP of 48.2% &mdash; i.e. not distinguishable
from AR(1) red noise even within its own local search window, let alone globally (global FAP 99.7%).
Because detection quality is high (Tier A), this is a clean non-detection rather than a sensitivity
limitation.</p>

<h3>Daily candidate periods and significance</h3>
{mkn421_daily_sig_table}
<p class="caveat">At daily cadence, the WWZ peak at 128.2&nbsp;d crosses the <strong>local</strong> 95%
threshold (local FAP 6.1%, 32.5 observed cycles) but not the global one (global FAP 19.5%); the CWT peak
at 132.2&nbsp;d falls just short of its own 95% theoretical reference (observed GWS 15.95 vs. 16.82). Both
candidates sit in the same period range as the weekly-cadence non-detection above. This is read as a
borderline, cadence-dependent hint rather than a robust detection &mdash; consistent with, not
independent confirmation of, the weekly result.</p>

<h4>Cross-check: a prior WCDA claim near 51&nbsp;d ("xgm poster")</h4>
<p>A group poster ("xgm poster") previously reported a visually striking &sim;51&nbsp;d periodicity in Mrk 421
WCDA <em>counts</em> data &mdash; a WWZ/PSD-based visual reference display, read there as crossing a 99%
reference, restricted to <strong>MJD 60200&ndash;60700</strong> (a &sim;1.4&nbsp;yr sub-window of the current
baseline). This is independently re-tested here on the <em>same</em> MJD window using the strict-batch
<code>N0</code> flux product and the identical AR(1) surrogate/theory methodology used throughout this
report &mdash; not a reproduction of the poster's own significance calculation, which is not recoverable
from the poster alone.</p>
<table class="sig">
<thead><tr><th>Method</th><th>Target period</th><th>Local peak</th><th>Power</th><th>Local FAP</th><th>Global FAP</th><th>&ge;99%</th></tr></thead>
<tbody>
<tr><td>WWZ</td><td>51.05&nbsp;d</td><td>49.92&nbsp;d</td><td>16.70</td><td>10.1%</td><td>74.6%</td><td>no</td></tr>
<tr><td>CWT</td><td>51.05&nbsp;d</td><td>49.53&nbsp;d</td><td>9.78</td><td>33.2%</td><td>95.4%</td><td>no</td></tr>
</tbody>
</table>
{xgm_wwz_quicklook_fig}
{xgm_figs}
<p class="caveat">Under an AR(1) surrogate/theory null, neither method confirms the poster's visual &gt;99%
reading on this window: local FAP is 10&ndash;33% and global FAP is 75&ndash;95%, both consistent with red
noise. Notably, the <strong>same &sim;50&nbsp;d feature reappears in the full 2021&ndash;2025 daily
baseline</strong> in the candidate table just above (CWT 49.5&nbsp;d, WWZ 50.1&nbsp;d, neither above 95%)
&mdash; so this is a reproducible feature of the WCDA daily flux series across both a narrow window and the
full baseline, not a one-off artifact, but it fails the same significance test both times. Because the
poster's own counts-based method states no explicit null model, this is read as an internal consistency
check against a prior in-group claim, not a formal refutation of the poster on its own terms.</p>

<h4>Fermi-LAT cross-check</h4>
<p>The Fermi-LAT weekly flux series, re-binned onto the WCDA weekly time axis (N=224), was run through the
same CWT/AR(1)-theory and WWZ/AR(1)-surrogate pipeline used throughout this report (see figures above).
The CWT scan's candidate peak is at 206&nbsp;d; the WWZ scan finds candidates at 98.8&nbsp;d and
208.4&nbsp;d. None of these match the Ren et al. (2022) 300&nbsp;d GeV claim, and (as the significance
figures above show) none clear the 95%/99% AR(1) reference in this reduced/aligned dataset; see &sect;6
for a fuller discussion of why a direct comparison with Ren et al.'s original, much longer baseline is not
yet apples-to-apples.</p>
<div class="callout info"><strong>Prior Fermi-LAT literature for Mrk 421.</strong> Ren et al. (2022) is the
<em>only</em> paper, among the 11-paper / 81-source Fermi-LAT QPO literature review compiled for this
project, that reports a periodicity for Mrk 421 &mdash; no other survey in that review lists this source.
Their claim: <strong>300&plusmn;65&nbsp;d</strong> (7-day binning, &gt;5&sigma, 3 fitted cycles) and
300&plusmn;64&nbsp;d (30-day binning, &gt;5&sigma), consistent between binnings. The claim is drawn from
their full analyzed Fermi-LAT baseline, <strong>MJD 54679&ndash;59334 (2008-08 to 2021-04, &sim;12.7&nbsp;yr)</strong>
&mdash; the literature review does not identify a narrower sub-range within that baseline where the
periodicity specifically appears; "3 fitted cycles" for a 300&nbsp;d period implies the coherent signal
spans roughly 900&nbsp;days somewhere within that baseline, not necessarily the full 12.7&nbsp;years. This
baseline is independently re-tested in &sect;7 below.</div>

<h2 id="mkn501">4. Primary Results &mdash; Mrk 501</h2>
<p>Detection quality: <strong>Tier A, timing-grade</strong> (median weekly TS 22.27; TS&ge;9 in 165/229
weeks, 72.1%). 229 weekly points (same window) and 1560 daily points (MJD 59282.5&ndash;60887.5) pass
quality cuts.</p>

{mkn501_figs}

<h3>Weekly candidate periods and significance</h3>
{mkn501_sig_table}
<p class="caveat">As with Mrk 421, no candidate reaches the 95% global threshold. The closest approach is
the WWZ peak at 436.07&nbsp;d, with a local FAP of 34.0% (local confidence 66.0%) &mdash; still short of the
95% local bar, and the associated candidate has fewer than four observed cycles over the current baseline,
which further limits how much weight it should carry.</p>

<h3>Daily candidate periods and significance</h3>
{mkn501_daily_sig_table}
<div class="callout">
<strong>Notable daily-cadence candidate.</strong> Unlike the weekly-cadence scan above, the
<strong>daily</strong>-cadence CWT/WWZ scan for Mrk 501 finds a candidate at
<strong>&sim;152&ndash;157&nbsp;d that formally exceeds both the 95% and 99% AR(1) reference levels in
both methods</strong>: CWT observed GWS 11.07 vs. a 99% theoretical reference of 10.39 (&sim;10.2 cycles);
WWZ observed power 13.58 with global FAP 1.0% (999/1000 surrogates fall below it). This is the single
strongest candidate found anywhere in this report. Three caveats keep this from being a claimed detection:
(i) it is one quick-look candidate among the many source&times;cadence&times;method combinations searched
across this report, with no multi-comparison trial correction applied; (ii) it does <strong>not</strong>
appear in the weekly-cadence analysis of the same underlying WCDA data &mdash; an internal
binning-sensitivity split directly analogous to the one Ren et al. (2022) themselves flagged for Mrk 501's
own Fermi-LAT data (2.9&sigma; at 30-day bins vs. &gt;5&sigma; at 7-day bins); (iii) at &sim;152&ndash;157&nbsp;d
it is close to half of Ren et al.'s 326&plusmn;76&nbsp;d GeV claim, which invites checking for a harmonic
relationship rather than assuming independence. Given detection quality is Tier A and &sim;10.5 cycles are
observed (well above the 4-cycle caution threshold used elsewhere in this report), this is flagged as the
most promising lead for follow-up, not dismissed as boundary noise.
</div>

<h4>Fermi-LAT literature context</h4>
<div class="callout info"><strong>Prior Fermi-LAT literature for Mrk 501.</strong> As with Mrk 421, Ren et al.
(2022) is the only paper in the compiled literature review reporting a periodicity for Mrk 501. Their
claim: <strong>326&plusmn;76&nbsp;d</strong> (7-day binning, &gt;5&sigma, 7 fitted cycles) and
315&plusmn;98&nbsp;d (30-day binning, only 2.9&sigma) &mdash; the two binnings disagree markedly in
significance, which Ren et al. themselves flag as a binning-sensitivity warning specific to this source.
Same analyzed baseline as Mrk 421: <strong>MJD 54679&ndash;59334 (2008-08 to 2021-04)</strong>; "7 fitted
cycles" at 326&nbsp;d implies a coherent span of roughly 2280&nbsp;days (&sim;6.2&nbsp;yr) somewhere within
that baseline. A dedicated Fermi-LAT weekly light curve for Mrk 501 did not exist locally prior to this
report; one is now being computed (see &sect;7) so this source can get the same independent reproduction
treatment as Mrk 421.</div>

<h2 id="secondary">5. Secondary Results &mdash; 8-source AGN survey context</h2>
<p>Eight additional AGN (selected as nearby HBL/FSRQ analogs of Mrk 421/501, already LHAASO-detected with
variability flags) were carried through the identical weekly pipeline as detection-quality controls. All
eight are <strong>Tier C, diagnostic only</strong> &mdash; median weekly TS below 1.4 in every case &mdash;
so any CWT/WWZ peak found here is a pipeline diagnostic, not evidence for or against a real periodicity. The
summary table gives the best candidate per source; the composite quicklook and both significance-test figures
(CWT global wavelet spectrum vs. AR(1) reference, and WWZ vs. AR(1) surrogate reference) are shown for each
source below so the significance curves can be checked directly rather than taken on the table numbers alone.</p>

{secondary_table_html}

<div class="callout">
<strong>NGC 1275 flag.</strong> NGC 1275 is the only source in the full 10-source sample with nominal
<code>above_99%</code> significance flags &mdash; both a CWT peak at 436.8&nbsp;d and a WWZ peak at
505.1&nbsp;d formally clear the 99% AR(1) surrogate threshold. However, NGC 1275 has a <strong>median
weekly TS of only 0.06</strong> (TS&ge;9 in just 9/229 weeks, 3.9%) &mdash; among the lowest detection
quality in the sample &mdash; and both candidate periods have fewer than four observed cycles over the
current baseline. Interestingly, Ren et al. (2022) do report a Fermi-LAT NGC 1275 QPO at
92&plusmn;33&nbsp;d (&gt;5&sigma, 7-day bins) &mdash; a factor of &sim;5 away from the WCDA candidates
found here. Given the very low WCDA detection quality, this is presented as <strong>worth a second look,
not a claim</strong>; it should not be over-interpreted without first improving the source's weekly TS or
extending the baseline.
</div>

{secondary_figs_html}

<h2 id="literature">6. Comparison with Fermi-LAT Literature</h2>
<table class="lit">
<thead><tr><th>Source</th><th>This work (best local WCDA candidate)</th><th>Ren et al. 2022 (Fermi-LAT, GeV)</th><th>Note</th></tr></thead>
<tbody>
<tr><td>Mrk 421</td><td>131.25&nbsp;d (WWZ), local FAP 48.2% &mdash; not significant</td>
<td>300&plusmn;65&nbsp;d (7-day bins, &gt;5&sigma, 3 cycles); 300&plusmn;64&nbsp;d (30-day bins, &gt;5&sigma)</td>
<td>No correspondence in period. Different energy band (TeV vs. GeV); current WCDA coverage stops mid-2025;
no trial correction applied yet on either side for a fully matched comparison.</td></tr>
<tr><td>Mrk 501</td><td>436.07&nbsp;d (WWZ), local FAP 34.0% &mdash; not significant</td>
<td>326&plusmn;76&nbsp;d (7-day bins, &gt;5&sigma, 7 cycles); 315&plusmn;98&nbsp;d (30-day bins, 2.9&sigma)</td>
<td>Same order of magnitude but not a matched value; Ren et al. themselves flag 30-day vs. 7-day binning
sensitivity for this source, which should temper how strongly the GeV claim itself is read.</td></tr>
<tr><td>NGC 1275 <span class="caveat">(context only, Tier C)</span></td>
<td>505.06&nbsp;d (WWZ), nominally &ge;99% &mdash; but source is diagnostic-only</td>
<td>92&plusmn;33&nbsp;d (7-day bins, &gt;5&sigma, 4 cycles)</td>
<td>&gt;5&times; different period; WCDA detection quality (median TS 0.06) is far too low to treat this as
a real cross-band signal.</td></tr>
</tbody>
</table>
<p>None of the WCDA candidate periods found in Mrk 421 or Mrk 501 independently reproduce the corresponding
Ren et al. (2022) GeV-band claims, and none reach internal significance on their own terms. This is
consistent with the broader field-level picture from Pe&ntilde;il et al. (2025) &mdash; after proper trial
correction, most blazar QPO claims in the literature do not survive &mdash; but it is not yet a definitive
cross-band non-confirmation, given the coverage and trial-correction caveats above.</p>

<h2 id="ren-repro">7. Independent Reproduction Attempt &mdash; Ren et al. (2022)</h2>
<p>Rather than only citing Ren et al. (2022), this section attempts an independent reproduction of their
Mrk 421 result using their own method (Morlet CWT global wavelet spectrum, significance from
Emmanoulopoulos Monte Carlo simulations &mdash; not the AR(1) surrogate approach used elsewhere in this
report) applied to this project's own Fermi-LAT weekly (TS&ge;9-filtered) flux light curve, sliced to their
published baseline (<strong>MJD 54679&ndash;59334, 2008-08 to 2021-04, N=650 weekly points</strong>). The Emmanoulopoulos sampler
(vendored in <code>src/methods/emmanoulopoulos/</code>) generates synthetic light curves matching the
observed power spectral density and flux probability distribution; 300 realizations were run here (fewer
than would be needed to resolve a &gt;5&sigma; tail directly &mdash; this is a feasibility-scale
reproduction, not a publication-grade one, and is flagged as such).</p>

{ren_repro_fig}

<table class="sig"><thead><tr><th>Quantity</th><th>Value</th></tr></thead><tbody>
<tr><td>Target period (Ren et al. 2022 claim)</td><td>300&nbsp;d</td></tr>
<tr><td>Observed CWT global wavelet spectrum peak (this reproduction)</td><td>291.5&nbsp;d, power 6.13</td></tr>
<tr><td>Observed GWS at exactly 300&nbsp;d</td><td>5.76</td></tr>
<tr><td>Local FAP at 300&nbsp;d (300 Emmanoulopoulos MC sims)</td><td>2.3%</td></tr>
<tr><td>Global FAP at 300&nbsp;d (max over 50&ndash;600&nbsp;d search range)</td><td>48.3%</td></tr>
</tbody></table>

<p class="caveat"><strong>Interpretation.</strong> The observed CWT spectrum does show a genuine local
peak close to Ren et al.'s claimed period (291.5&nbsp;d vs. their 300&plusmn;65&nbsp;d) &mdash; a modest
local enhancement, with only 2.3% of Emmanoulopoulos MC realizations reaching an equally strong peak at
that specific period. However, once the full 50&ndash;600&nbsp;d search range is accounted for (global FAP),
this level of peak power is unremarkable: 48.3% of simulations produce an equally strong peak <em>somewhere</em>
in that range, i.e. consistent with red-noise variability. This <strong>does not reach anywhere near the
&gt;5&sigma; significance Ren et al. (2022) report</strong>, and with only 300 MC realizations the local
FAP itself is not resolved finely enough to rule out a much smaller true value &mdash; it should be read as
"a candidate at the right location that does not obviously stand out globally," not as either a confirmation
or a refutation of the original GeV claim.</p>

<div class="callout">
<strong>Mrk 501 reproduction &mdash; stalled on data acquisition.</strong> The equivalent Fermi-LAT weekly
flux product for Mrk 501 does not yet exist (see &sect;2 data checklist). A dedicated fermipy weekly
light-curve pipeline was configured and launched on the ETO cluster (full mission baseline, Slurm-managed,
raw Fermi-LAT event data queried fresh from the FSSC LAT Data Server), matching the same TS&ge;9-filtered
weekly convention as the existing Mrk 421 product. The photon-event download completed (7 files), but the
spacecraft-position file download failed after 3 retries and the pipeline halted before ever submitting the
actual light-curve fit job &mdash; so no Mrk 501 Fermi-LAT weekly product exists yet. This needs a retry
(re-querying or re-downloading the spacecraft file) before the light-curve job can even start; once it does,
full completion is still expected to take on the order of half a day to a day of remote compute given the
&sim;18-year baseline and per-bin likelihood fit cost. This report will be updated with the equivalent
Mrk 421-style figure, candidate table, and MC significance result for Mrk 501 once that is resolved.
</div>

<h2 id="conclusions">8. Conclusions</h2>
<ul>
<li>At <strong>weekly</strong> cadence, no statistically significant QPO is found in either Mrk 421 or
Mrk 501 WCDA flux over the current baseline (2021-03-08 to 2025-07-27), under CWT/WWZ scanning with AR(1)
surrogate significance testing. Detection quality for both primary sources is high (Tier A), so this
reflects the data, not a pipeline sensitivity limitation.</li>
<li>At <strong>daily</strong> cadence, Mrk 421 shows only a borderline, cadence-dependent hint (WWZ
128&nbsp;d, local-95% only). <strong>Mrk 501 shows a candidate at &sim;152&ndash;157&nbsp;d that formally
exceeds both the 95% and 99% AR(1) reference in both CWT and WWZ</strong> &mdash; the strongest result in
this report &mdash; but it does not appear at weekly cadence for the same underlying data, has no
multi-comparison trial correction applied, and echoes the binning-sensitivity warning Ren et al. (2022)
themselves raised for this exact source. It is flagged as the most promising lead, not claimed as a
confirmed detection.</li>
<li>An independent reproduction attempt of Ren et al. (2022)'s own GeV-band method (CWT + Emmanoulopoulos
MC) on Mrk 421's Fermi-LAT weekly data over their exact baseline finds a candidate peak close to their
claimed period (291.5&nbsp;d vs. 300&plusmn;65&nbsp;d) with a suggestive local FAP (2.3%) but an
unremarkable global FAP (48.3%) &mdash; nowhere near their reported &gt;5&sigma;. The equivalent check for
Mrk 501 is still in progress (data acquisition stalled, see &sect;7 for status).</li>
<li>NGC 1275, among the 8 diagnostic-only control sources, shows a nominally &ge;99% candidate but at very
low detection quality &mdash; flagged for discussion, not claimed.</li>
<li>The current analysis is <strong>baseline- and coverage-limited</strong> (WCDA stops mid-2025; no trial
correction applied anywhere yet; the Ren+22 reproduction used only 300 MC sims), not method-exhausted
&mdash; there are concrete, identified next steps rather than a dead end.</li>
</ul>

<h2 id="next-steps">9. Proposed Next Steps (for discussion)</h2>
<ol>
<li><strong>Follow up the Mrk 501 &sim;152&ndash;157&nbsp;d daily candidate first</strong> &mdash; it is the
strongest lead in this report. Apply trial correction across the source&times;cadence&times;method
combinations searched, check whether it is stable under alternative CWT/WWZ parameter choices, and reconcile
the weekly/daily binning discrepancy directly (mirroring how Ren et al. 2022 handled their own 30d-vs-7d
split for this source) before treating it as anything more than a lead.</li>
<li><strong>Extend WCDA flux coverage past 2025-07</strong> by resolving the two known gaps: missing detector
response files for periods T084&ndash;T091, and the missing period map beyond 2025-11-05. This is the most
direct way to add roughly one more year of baseline and more observed cycles for the longer-period
candidates.</li>
<li><strong>Apply post-trial / look-elsewhere correction</strong> consistently across sources, cadences, and
methods &mdash; a prerequisite for any future significance claim to be publishable or directly comparable
to the trial-corrected literature (e.g. Pe&ntilde;il et al. 2025).</li>
<li><strong>Finish and scale up the Ren et al. (2022) reproduction</strong>: unblock the stalled Mrk 501
Fermi-LAT spacecraft-file download (see &sect;7) and complete the weekly light-curve pipeline (running on
ETO), then re-run both sources' Emmanoulopoulos MC significance with a much larger simulation count
(thousands, not 300) to properly resolve the low-FAP tail before drawing any firm conclusion about the
Mrk 421 291.5&nbsp;d candidate.</li>
<li><strong>Cross-check with a second method</strong> (e.g. Gaussian Process / damped random walk, following
Sharma et al. 2025) as a robustness check independent of the CWT/WWZ + AR(1)/Emmanoulopoulos frameworks.</li>
<li><strong>Decide whether NGC 1275 warrants dedicated follow-up</strong> &mdash; e.g. a targeted
re-analysis once its weekly TS improves, or an independent check with Fermi-LAT data on the same window.</li>
</ol>

<h2 id="appendix">Appendix</h2>
<h3>A.1 Flux quality-control summary (source: <code>periodicity_v2_report.md</code>)</h3>
<table class="sig">
<thead><tr><th>Source</th><th>Cadence</th><th>OK rows</th><th>Kept</th><th>Rejected</th><th><code>N0_err</code> limit</th></tr></thead>
<tbody>
<tr><td>Mrk 421</td><td>day</td><td>1588</td><td>1570</td><td>18</td><td>8.206&times;10<sup>-13</sup></td></tr>
<tr><td>Mrk 421</td><td>week</td><td>229</td><td>229</td><td>0</td><td>3.142&times;10<sup>-13</sup></td></tr>
<tr><td>Mrk 501</td><td>day</td><td>1591</td><td>1560</td><td>31</td><td>6.963&times;10<sup>-13</sup></td></tr>
<tr><td>Mrk 501</td><td>week</td><td>229</td><td>229</td><td>0</td><td>2.571&times;10<sup>-13</sup></td></tr>
</tbody>
</table>
<p class="caveat">Rows with <code>N0_err</code> above 5&times; the per-source/cadence median are excluded
before periodicity analysis; the rejection rate is under 2% in all four cases.</p>

<footer>
Generated from <code>QPO/reports/build_mkn421_mkn501_status_report.py</code> against data as of commit
<code>9e07a61</code> (2026-06-16). All figures and significance numbers are reproduced directly from
<code>data/processed/periodicity/agn_wcda_weekly_flux_survey/</code> and
<code>data/processed/periodicity/periodicity_v2/</code> without modification.
</footer>

</body>
</html>
"""

    OUT.write_text(html_doc, encoding="utf-8")
    size_mb = OUT.stat().st_size / 1024 / 1024
    print(f"Wrote {OUT} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
