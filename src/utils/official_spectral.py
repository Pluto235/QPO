"""Validation helpers for full-interval public ``Src_Main`` spectral fits."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

import yaml

try:
    from utils.official_profile import parse_src_main_fit_summary
except ModuleNotFoundError:
    from official_profile import parse_src_main_fit_summary


@dataclass(frozen=True)
class ValidatedPLSpectrum:
    f0: float
    f0_order: str
    alpha: float
    alpha_error: float
    epiv_tev: float
    aic: float
    bic: float
    ts: float


def parse_validated_pl_spectrum(log_text: str, parres_text: str) -> ValidatedPLSpectrum:
    """Accept only finite interior PL fit parameters from a successful run."""

    summary = parse_src_main_fit_summary(log_text)
    if summary.status != "OK":
        raise ValueError(f"Src_Main fit status is not OK: {summary.status}")
    data = yaml.safe_load(parres_text)
    try:
        source = data["SRC"]["Src0"]
        sed = source["SEDModel"]
        if sed["type"] != "PL":
            raise ValueError(f"Expected PL, received {sed['type']!r}")
        f0, f0_low, f0_high, _, f0_order, _ = sed["F0"]
        alpha, alpha_low, alpha_high, _, alpha_error = sed["alpha"]
        epiv = source["Epiv"]
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        raise ValueError("ParRes.yaml lacks the expected fitted PL schema") from exc
    values = (f0, f0_low, f0_high, alpha, alpha_low, alpha_high, alpha_error, epiv)
    if not all(math.isfinite(float(value)) for value in values):
        raise ValueError("Full-interval PL fit has non-finite parameters")
    f0, f0_low, f0_high = map(float, (f0, f0_low, f0_high))
    alpha, alpha_low, alpha_high, alpha_error, epiv = map(float, (alpha, alpha_low, alpha_high, alpha_error, epiv))
    if f0 <= f0_low or f0 >= f0_high:
        raise ValueError("Full-interval F0 touches its fit boundary")
    if alpha <= alpha_low or alpha >= alpha_high or alpha_error <= 0:
        raise ValueError("Full-interval alpha is unconstrained or touches its fit boundary")
    return ValidatedPLSpectrum(f0, str(f0_order), alpha, alpha_error, epiv, summary.aic, summary.bic, summary.ts)


def spectrum_registry_record(
    spectrum: ValidatedPLSpectrum,
    *,
    provenance: dict[str, Any],
    dge_active: bool,
    dge_decision: str,
) -> dict[str, Any]:
    """Return the normalized registry record used by profile/LC generators."""

    return {
        "validation_status": "VERIFIED",
        "selection_rule": (
            "full-interval public-v1.0 Src_Main PL fit with active public DGE"
            if dge_active
            else "full-interval public-v1.0 Src_Main PL fit with DGE disabled by the accepted high-latitude guard"
        ),
        "current_action": "use this fixed spectrum for profile-likelihood light curves",
        "model_type": "PL",
        "parameters": {
            "F0": [spectrum.f0, 0.0, 500.0, 1, spectrum.f0_order],
            "alpha": [spectrum.alpha, 1.0, 4.0, 1],
            "Epiv_TeV": spectrum.epiv_tev,
        },
        "fit_summary": {"aic": spectrum.aic, "bic": spectrum.bic, "ts": spectrum.ts, "alpha_error": spectrum.alpha_error},
        "dge_configuration": {"active": dge_active, "decision": dge_decision},
        "provenance": provenance,
    }
