"""Source registry for the LHAASO AGN QPO survey expansion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from utils.project_paths import ALIGNED_DIR, FERMI_WEEK_DIR, PERIODICITY_DIR, WCDA_DAY_DIR, WCDA_WEEK_DIR


@dataclass(frozen=True, slots=True)
class SourceRecord:
    """Canonical metadata and conventional paths for a survey source."""

    source_id: str
    label: str
    lhaaso_name: str
    source_type: str
    priority: str
    in_default_shortlist: bool
    include_in_control_group: bool
    include_in_exploratory_group: bool
    lhaaso_significance_sigma: float | None
    variability_flag: str
    default_wcda_day: bool
    default_fermi_week: bool
    lhaaso_token: str
    fermi_token: str | None = None
    notes: str = ""

    @property
    def aligned_dir(self) -> Path:
        return ALIGNED_DIR / self.source_id

    @property
    def periodicity_dir(self) -> Path:
        return PERIODICITY_DIR / self.source_id

    def expected_wcda_week_path(self) -> Path:
        return WCDA_WEEK_DIR / f"LHAASO-WCDA_{self.lhaaso_token}_2021-03-08_2026-03-29_week.csv"

    def expected_wcda_day_path(self) -> Path | None:
        if not self.default_wcda_day:
            return None
        return WCDA_DAY_DIR / f"LHAASO-WCDA_{self.lhaaso_token}_2025-03-29_2026-03-29_day.csv"

    def expected_fermi_week_path(self) -> Path | None:
        if not self.default_fermi_week or not self.fermi_token:
            return None
        return FERMI_WEEK_DIR / f"{self.fermi_token}_Fermi_weekly_TSge9_MJD.csv"

    def expected_aligned_week_path(self) -> Path:
        return self.aligned_dir / "wcda_weekly_aligned.csv"

    def expected_periodicity_summary_path(self) -> Path:
        return self.periodicity_dir / "periodicity_v1_summary.csv"


SOURCE_REGISTRY: dict[str, SourceRecord] = {
    "mkn421": SourceRecord(
        source_id="mkn421",
        label="Mrk 421",
        lhaaso_name="Markarian 421",
        source_type="HBL",
        priority="active",
        in_default_shortlist=True,
        include_in_control_group=False,
        include_in_exploratory_group=False,
        lhaaso_significance_sigma=221.38,
        variability_flag="yes",
        default_wcda_day=True,
        default_fermi_week=True,
        lhaaso_token="Mkn421",
        fermi_token="Mrk421",
        notes="Current main source with WCDA daily, WCDA weekly, Fermi weekly, aligned, and periodicity products.",
    ),
    "mkn501": SourceRecord(
        source_id="mkn501",
        label="Mrk 501",
        lhaaso_name="Markarian 501",
        source_type="HBL",
        priority="active",
        in_default_shortlist=True,
        include_in_control_group=False,
        include_in_exploratory_group=False,
        lhaaso_significance_sigma=92.54,
        variability_flag="yes",
        default_wcda_day=False,
        default_fermi_week=False,
        lhaaso_token="Mkn501",
        fermi_token="Mrk501",
        notes="Current secondary source with WCDA weekly, aligned weekly, and periodicity products.",
    ),
    "1es1959p650": SourceRecord(
        source_id="1es1959p650",
        label="1ES 1959+650",
        lhaaso_name="1ES 1959+650",
        source_type="HBL",
        priority="A",
        in_default_shortlist=True,
        include_in_control_group=False,
        include_in_exploratory_group=False,
        lhaaso_significance_sigma=11.33,
        variability_flag="yes",
        default_wcda_day=False,
        default_fermi_week=False,
        lhaaso_token="1ES1959p650",
        fermi_token="1ES1959p650",
        notes="Best first-wave HBL expansion target after Mrk 421/501.",
    ),
    "1es1727p502": SourceRecord(
        source_id="1es1727p502",
        label="1ES 1727+502",
        lhaaso_name="1ES 1727+502",
        source_type="HBL",
        priority="A",
        in_default_shortlist=True,
        include_in_control_group=False,
        include_in_exploratory_group=False,
        lhaaso_significance_sigma=12.08,
        variability_flag="yes",
        default_wcda_day=False,
        default_fermi_week=False,
        lhaaso_token="1ES1727p502",
        fermi_token="1ES1727p502",
        notes="High-significance HBL with reported variability; strong candidate for weekly-first survey.",
    ),
    "1es2344p514": SourceRecord(
        source_id="1es2344p514",
        label="1ES 2344+514",
        lhaaso_name="1ES 2344+514",
        source_type="HBL",
        priority="A",
        in_default_shortlist=True,
        include_in_control_group=False,
        include_in_exploratory_group=False,
        lhaaso_significance_sigma=9.33,
        variability_flag="yes",
        default_wcda_day=False,
        default_fermi_week=False,
        lhaaso_token="1ES2344p514",
        fermi_token="1ES2344p514",
        notes="Good HBL supplement with enough significance for first-pass WWZ/CWT checks.",
    ),
    "bllac": SourceRecord(
        source_id="bllac",
        label="BL Lacertae",
        lhaaso_name="BL Lacertae",
        source_type="IBL",
        priority="A",
        in_default_shortlist=True,
        include_in_control_group=False,
        include_in_exploratory_group=False,
        lhaaso_significance_sigma=7.79,
        variability_flag="yes",
        default_wcda_day=False,
        default_fermi_week=False,
        lhaaso_token="BLLacertae",
        fermi_token="BLLacertae",
        notes="Includes rapid variability case reported on 2024-08-10 in the LHAASO AGN report.",
    ),
    "4c_p42d22": SourceRecord(
        source_id="4c_p42d22",
        label="4C +42.22",
        lhaaso_name="4C +42.22",
        source_type="BL Lac",
        priority="B",
        in_default_shortlist=False,
        include_in_control_group=False,
        include_in_exploratory_group=True,
        lhaaso_significance_sigma=6.90,
        variability_flag="yes",
        default_wcda_day=False,
        default_fermi_week=False,
        lhaaso_token="4C_p42d22",
        fermi_token="4C_p42d22",
        notes="Reasonable blazar expansion target, but secondary to the HBL/IBL shortlist.",
    ),
    "ngc1275": SourceRecord(
        source_id="ngc1275",
        label="NGC 1275",
        lhaaso_name="NGC 1275",
        source_type="FR I",
        priority="B",
        in_default_shortlist=True,
        include_in_control_group=True,
        include_in_exploratory_group=False,
        lhaaso_significance_sigma=4.90,
        variability_flag="yes",
        default_wcda_day=False,
        default_fermi_week=False,
        lhaaso_token="NGC1275",
        fermi_token="NGC1275",
        notes="Radio-galaxy control target; also appears in the existing Fermi QPO literature notes.",
    ),
    "m87": SourceRecord(
        source_id="m87",
        label="M 87",
        lhaaso_name="M 87",
        source_type="FR I",
        priority="B",
        in_default_shortlist=True,
        include_in_control_group=True,
        include_in_exploratory_group=False,
        lhaaso_significance_sigma=8.38,
        variability_flag="yes",
        default_wcda_day=False,
        default_fermi_week=False,
        lhaaso_token="M87",
        fermi_token="M87",
        notes="Week-level flare and duty-cycle case; useful as a non-blazar comparison source.",
    ),
    "ic310": SourceRecord(
        source_id="ic310",
        label="IC 310",
        lhaaso_name="IC 310",
        source_type="FR I / BL Lac",
        priority="C",
        in_default_shortlist=False,
        include_in_control_group=False,
        include_in_exploratory_group=True,
        lhaaso_significance_sigma=None,
        variability_flag="yes",
        default_wcda_day=False,
        default_fermi_week=False,
        lhaaso_token="IC310",
        fermi_token="IC310",
        notes="Best treated as a flare-driven exploratory target because the summary table omits a significance value.",
    ),
}

DEFAULT_SURVEY_SOURCE_IDS = tuple(
    source_id
    for source_id, record in SOURCE_REGISTRY.items()
    if record.in_default_shortlist and record.priority in {"active", "A", "B"}
)

WCDA_WEEK_SURVEY_SOURCE_IDS = (
    "mkn421",
    "mkn501",
    "1es1959p650",
    "1es1727p502",
    "1es2344p514",
    "bllac",
    "ngc1275",
    "m87",
    "4c_p42d22",
    "ic310",
)

WCDA_STRICT_FLUX_SOURCE_IDS = (
    "mkn421",
    "mkn501",
    "1es1959p650",
    "1es1727p502",
    "1es2344p514",
    "bllac",
    "ngc1275",
    "m87",
    "4c_p42d22",
    "ic310",
)


def get_source(source_id: str) -> SourceRecord:
    """Return a source record by canonical source id."""

    return SOURCE_REGISTRY[source_id]


def list_sources(*, priorities: set[str] | None = None) -> list[SourceRecord]:
    """Return registry records, optionally filtered by priority."""

    records = list(SOURCE_REGISTRY.values())
    if priorities is not None:
        records = [record for record in records if record.priority in priorities]
    return records
