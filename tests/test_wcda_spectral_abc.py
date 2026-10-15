"""Small contract check: all variants must use the same valid bins."""
import numpy as np
import pandas as pd

from pipeline.analyze_wcda_spectral_abc import common_mask
from pipeline.wcda_spectral_abc import variants


def test_common_bins_and_statistical_index_bracket():
    a = pd.DataFrame({'name': ['LC0001', 'LC0002', 'LC0003'],
                      'fit_status': ['OK', 'OK', 'NotOK'],
                      'N0': [1., 2., 3.], 'N0_err': [.1, .2, .3]})
    b = a.copy()
    b.loc[0, 'N0_err'] = np.nan
    assert common_mask({'A': a, 'B': b}) == {'LC0002'}
    bracket = variants(2.8, .1)
    assert np.allclose(list(bracket.values()), [2.8, 2.7, 2.9])
    try:
        variants(2.8, float('nan'))
    except ValueError:
        pass
    else:
        raise AssertionError('Nonfinite uncertainty accepted')
