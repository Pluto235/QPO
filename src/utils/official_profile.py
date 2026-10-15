"""Profile-likelihood helpers for fixed-F0 ``Src_Main`` scan wrappers.

The public executable prints AIC rather than the total likelihood. For a scan
whose free-parameter set is unchanged at every grid point, its own definition
``AIC = 2*k - logL_total`` makes ``(AIC - min(AIC)) / 2`` the required
Delta-log-likelihood profile up to the common additive convention.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Iterable


_AIC_RE = re.compile(r"\bAIC\s*=\s*([-+0-9.eE]+)")
_BIC_RE = re.compile(r"\bBIC\s*=\s*([-+0-9.eE]+)")
_TS_RE = re.compile(r"\bTS\s*=\s*([-+0-9.eE]+)")
_STATUS_RE = re.compile(r"\bSTATUS\s*[:=]\s*([A-Za-z0-9_]+)")


@dataclass(frozen=True)
class SrcMainFitSummary:
    aic: float
    bic: float
    ts: float
    status: str


@dataclass(frozen=True)
class ProfilePoint:
    f0: float
    aic: float
    delta_log_likelihood: float
    status: str


def parse_src_main_fit_summary(log_text: str) -> SrcMainFitSummary:
    """Parse the final fit statistics emitted by one ``Src_Main`` run."""

    aic_values = _numeric_matches(_AIC_RE, log_text)
    bic_values = _numeric_matches(_BIC_RE, log_text)
    ts_values = _numeric_matches(_TS_RE, log_text)
    statuses = _STATUS_RE.findall(log_text)
    if not aic_values or not bic_values or not ts_values:
        raise ValueError("Src_Main log lacks a finite final AIC, BIC, or TS value")
    return SrcMainFitSummary(
        aic=aic_values[-1],
        bic=bic_values[-1],
        ts=ts_values[-1],
        status=statuses[-1] if statuses else "unknown",
    )


def build_fixed_grid_profile(
    grid_f0: Iterable[float],
    summaries: Iterable[SrcMainFitSummary],
    *,
    required_delta_log_likelihood: float = 4.0,
    allow_lower_boundary_mle: bool = False,
) -> list[ProfilePoint]:
    """Normalize an equal-degree-of-freedom fixed-F0 grid to Delta log L.

    ``required_delta_log_likelihood`` is a predeclared bracket threshold used to
    reject grids which do not extend sufficiently on both sides of their MLE.
    """

    f0_values = list(grid_f0)
    summary_values = list(summaries)
    if len(f0_values) != len(summary_values) or len(f0_values) < 3:
        raise ValueError("A profile requires matching F0/summary values for at least three grid points")
    if any(not math.isfinite(value) or value < 0 for value in f0_values):
        raise ValueError("Profile F0 grid must be finite and non-negative")
    if any(right <= left for left, right in zip(f0_values, f0_values[1:])):
        raise ValueError("Profile F0 grid must be strictly increasing")
    if any(not math.isfinite(item.aic) for item in summary_values):
        raise ValueError("Profile contains a non-finite AIC")

    best_aic = min(item.aic for item in summary_values)
    points = [
        ProfilePoint(
            f0=f0,
            aic=summary.aic,
            delta_log_likelihood=(summary.aic - best_aic) / 2.0,
            status=summary.status,
        )
        for f0, summary in zip(f0_values, summary_values)
    ]
    validate_fixed_grid_profile(
        points,
        required_delta_log_likelihood=required_delta_log_likelihood,
        allow_lower_boundary_mle=allow_lower_boundary_mle,
    )
    return points


def validate_fixed_grid_profile(
    points: Iterable[ProfilePoint],
    *,
    required_delta_log_likelihood: float = 4.0,
    allow_lower_boundary_mle: bool = False,
) -> None:
    """Require a finite profile with the required physical-domain coverage.

    Ordinary fits at the physical F0=0 lower bound may report ``NotOK`` because
    Minuit cannot form a two-sided Hessian there.  A caller may explicitly
    allow that one-sided case, but the upper grid boundary must still cover the
    requested Delta-log-likelihood range.  An upper-boundary MLE is never
    accepted.
    """

    values = list(points)
    if len(values) < 3:
        raise ValueError("A profile requires at least three points")
    if required_delta_log_likelihood <= 0:
        raise ValueError("The required Delta log L threshold must be positive")
    if any(not math.isfinite(point.delta_log_likelihood) or point.delta_log_likelihood < 0 for point in values):
        raise ValueError("Profile has invalid Delta log L values")
    mle_index = min(range(len(values)), key=lambda index: values[index].delta_log_likelihood)
    if mle_index == len(values) - 1:
        raise ValueError("Profile MLE touches an outer F0 grid boundary")
    if mle_index == 0 and not allow_lower_boundary_mle:
        raise ValueError("Profile MLE touches an outer F0 grid boundary")
    if mle_index != 0 and values[0].delta_log_likelihood < required_delta_log_likelihood:
        raise ValueError("Profile lower F0 boundary does not cover the required Delta log L")
    if values[-1].delta_log_likelihood < required_delta_log_likelihood:
        raise ValueError("Profile upper F0 boundary does not cover the required Delta log L")


def _numeric_matches(pattern: re.Pattern[str], text: str) -> list[float]:
    values = [float(match) for match in pattern.findall(text)]
    return [value for value in values if math.isfinite(value)]
