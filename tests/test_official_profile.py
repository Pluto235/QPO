from __future__ import annotations

import pytest

from utils.official_profile import SrcMainFitSummary, build_fixed_grid_profile, parse_src_main_fit_summary


def test_parse_src_main_final_fit_summary() -> None:
    log = """
STATUS: OK
TS = 12.0, BIC = 31.2, AIC = 24.4
STATUS: OK
TS = 15.5, BIC = 28.2, AIC = 21.4
"""

    summary = parse_src_main_fit_summary(log)

    assert summary == SrcMainFitSummary(aic=21.4, bic=28.2, ts=15.5, status="OK")


def test_fixed_grid_profile_normalizes_aic_and_requires_brackets() -> None:
    summaries = [
        SrcMainFitSummary(aic=30.0, bic=31.0, ts=1.0, status="OK"),
        SrcMainFitSummary(aic=22.0, bic=23.0, ts=4.0, status="OK"),
        SrcMainFitSummary(aic=32.0, bic=33.0, ts=1.0, status="OK"),
    ]

    profile = build_fixed_grid_profile([0.1, 1.0, 10.0], summaries)

    assert [point.delta_log_likelihood for point in profile] == [4.0, 0.0, 5.0]


def test_fixed_grid_profile_rejects_boundary_mle() -> None:
    summaries = [
        SrcMainFitSummary(aic=10.0, bic=11.0, ts=4.0, status="OK"),
        SrcMainFitSummary(aic=12.0, bic=13.0, ts=3.0, status="OK"),
        SrcMainFitSummary(aic=20.0, bic=21.0, ts=1.0, status="OK"),
    ]

    with pytest.raises(ValueError, match="outer F0 grid boundary"):
        build_fixed_grid_profile([0.1, 1.0, 10.0], summaries)

    profile = build_fixed_grid_profile([0.1, 1.0, 10.0], summaries, allow_lower_boundary_mle=True)
    assert profile[0].delta_log_likelihood == 0.0
