from __future__ import annotations

import numpy as np

from pipeline import official_lc_qpo_analysis as analysis


def test_wwz_surrogate_references_are_computed_without_candidate_peaks(monkeypatch) -> None:
    period = np.array([20.0, 40.0, 80.0, 160.0])
    wwz = {
        "period_axis": period,
        "global_wwz": np.ones_like(period),
        "period_min": 20.0,
        "period_max": 160.0,
        "time_divisions": 20,
        "decay_constant": 0.0125,
        "freq_step": 0.01,
        "t_span": 100.0,
    }
    surrogate = np.array([1.0, 2.0, 3.0, 4.0])
    monkeypatch.setattr(analysis, "_run_wwz_surrogate", lambda _task: surrogate)

    rows, references = analysis._assess_wwz(
        "ic310",
        "IC310",
        "2day",
        np.arange(10, dtype=float),
        np.linspace(0.8, 1.2, 10),
        np.full(10, 0.1),
        wwz,
        n_surrogates=4,
        seed=20260817,
        workers=1,
    )

    assert rows == []
    np.testing.assert_allclose(references["q95"], surrogate)
    np.testing.assert_allclose(references["q99"], surrogate)
    assert np.isfinite(references["alpha"])
