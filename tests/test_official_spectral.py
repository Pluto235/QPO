from __future__ import annotations

import pytest

from utils.official_spectral import parse_validated_pl_spectrum, spectrum_registry_record


LOG = "STATUS : OK\nTS = 12.0, BIC = 30.0, AIC = 22.0\n"
PARRES = """SRC:
  Src0:
    Epiv: 3
    SEDModel:
      type: PL
      F0: [1.2, 0.0, 500.0, 0, 1.e-12, 0.1]
      alpha: [2.4, 1.0, 4.0, 0, 0.2]
"""


def test_parse_validated_pl_spectrum_and_normalize_registry_record() -> None:
    spectrum = parse_validated_pl_spectrum(LOG, PARRES)

    assert spectrum.f0 == 1.2
    assert spectrum.alpha == 2.4
    record = spectrum_registry_record(
        spectrum,
        provenance={"log_sha256": "abc"},
        dge_active=False,
        dge_decision="disabled_by_user_accepted_public_src_main_high_latitude_guard",
    )
    assert record["validation_status"] == "VERIFIED"
    assert record["parameters"]["F0"][:4] == [1.2, 0.0, 500.0, 1]
    assert float(record["parameters"]["F0"][4]) == 1e-12
    assert record["dge_configuration"]["active"] is False
    assert "DGE disabled" in record["selection_rule"]


def test_reject_boundary_or_unconstrained_index() -> None:
    bad = PARRES.replace("alpha: [2.4, 1.0, 4.0, 0, 0.2]", "alpha: [1.0, 1.0, 4.0, 0, 0.2]")

    with pytest.raises(ValueError, match="alpha"):
        parse_validated_pl_spectrum(LOG, bad)
