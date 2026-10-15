import numpy as np
import pandas as pd
import pytest

from methods import detector_controls as dc
from methods.periodicity import run_wwz
from utils.project_paths import WCDA_2DAY_DIR


def sample():
    n = 12
    return pd.DataFrame(dict(mjd=100 + 2*np.arange(n), flux=np.arange(n, dtype=float)+1,
        flux_err=np.ones(n), Tobs_s=np.ones(n), valid_fit=True, at_boundary=False,
        error_reliable=pd.Series([None]*n,dtype=object),
        low_exposure=pd.Series([None]*n,dtype=object),
        extreme_flux=pd.Series([None]*n,dtype=object)))


def test_quality_flags_unknowns_and_internal_interpolation():
    raw = sample()
    raw.loc[0, 'at_boundary'] = True
    raw.loc[3, 'error_reliable'] = False
    raw.loc[5, 'low_exposure'] = True
    raw.loc[11, 'extreme_flux'] = True
    audit, observed, grid = dc.prepare_light_curves(raw)
    assert observed.index.tolist() == list(range(8))
    assert audit.retained.sum() == 8
    assert audit.loc[3, 'exclusion_reason'] == 'error_unreliable'
    np.testing.assert_array_equal(observed.mjd, [102,104,108,112,114,116,118,120])
    np.testing.assert_array_equal(np.diff(grid.mjd), 2)
    assert grid.mjd.min() == 102 and grid.mjd.max() == 120
    assert grid.is_interpolated.sum() == 2
    np.testing.assert_allclose(grid.flux, np.arange(2,12))
    assert 'flux_err' not in grid


@pytest.mark.parametrize('source,count', [('Crab',799),('IC443',676),('Blank175',309),('J1952',540)])
def test_release_selection_counts(source, count):
    raw = pd.read_csv(WCDA_2DAY_DIR/'detector_controls_20261011'/f'{source}_2day.csv')
    audit, observed, grid = dc.prepare_light_curves(raw)
    assert len(observed) == count
    assert len(audit) == 803
    np.testing.assert_array_equal(observed.mjd, raw.loc[audit.retained, 'mjd'])
    assert grid.is_interpolated.sum() == len(grid)-count


def test_alpha_only_uses_real_adjacent_two_day_pairs():
    t = np.array([0,2,4,10,12,14,16], dtype=float)
    y = np.array([1,3,2,9,6,8,4], dtype=float)
    alpha, pairs = dc.adjacent_ar1(t,y)
    left=np.array([1,3,9,6,8]); right=np.array([3,2,6,8,4])
    assert pairs == 5
    assert alpha == pytest.approx(np.clip(np.corrcoef(left,right)[0,1],-.95,.95))


def test_surrogates_generate_full_grid_before_mask_and_are_reproducible():
    mask=np.array([True,False,True,True,False,True])
    y=dc.sample_masked_ar1(7,mask,.7,2.,.5)
    np.testing.assert_array_equal(y, dc.sample_masked_ar1(7,mask,.7,2.,.5))
    from pipeline.official_lc_qpo_analysis import _simulate_ar1
    expected=_simulate_ar1(6,.7,2.,.5,np.random.default_rng(7))[mask]
    np.testing.assert_array_equal(y,expected)


@pytest.mark.parametrize('scale',[1.,1e-13])
def test_cached_wwz_preserves_installed_libwwz(scale):
    t=2*np.arange(50,dtype=float)
    t=np.delete(t,[3,7,22])
    y=scale*(2+np.sin(t/10)+np.random.default_rng(3).normal(0,.3,len(t)))
    reference=run_wwz(t,y,np.full(len(t),scale*.1),period_min=10,period_max=60,
        time_divisions=5,freq_step_factor=1)
    operator=dc.CachedWWZ(t,reference['tau_mat'][:,0],reference['freq_mat'][0],.0125)
    actual=operator.power(y)
    np.testing.assert_allclose(actual,reference['wwz_mat'],rtol=2e-8,atol=2e-9)


def test_no_peaks_still_produces_reference_curves_and_fap_bounds():
    periods=np.array([10.,20.,30.,40.])
    sims=np.array([[0,1,2,3],[1,2,3,4],[2,3,4,5]],dtype=float)
    rows,refs=dc.wwz_significance(periods,np.ones(4),sims,alpha=.2,span=100)
    assert rows == []
    np.testing.assert_allclose(refs['q95'],np.percentile(sims,95,axis=0))
    rows,_=dc.wwz_significance(periods,np.array([0.,8.,0.,0.]),sims,alpha=.2,span=100)
    assert rows[0]['local_fap'] == .25
    assert rows[0]['global_fap'] == .25
    assert rows[0]['four_source_fap'] == 1.


def test_cwt_reference_can_use_real_pair_alpha():
    from pipeline.official_lc_qpo_analysis import _assess_cwt
    from methods.periodicity import run_cwt
    t=2*np.arange(50)
    y=2+np.sin(t/8)
    cwt=run_cwt(t,y,period_min=10,period_max=60)
    _,refs=_assess_cwt('test','Test','2day',t,y,cwt,alpha_override=.123)
    assert refs['alpha'] == .123


def test_plot_accepts_independent_cwt_grid_and_marks_clipping(tmp_path):
    from pipeline.periodicity_v1 import _plot_periodicity_summary
    from methods.periodicity import run_cwt
    t=2*np.arange(50)
    y=2+np.sin(t/8)
    cwt=run_cwt(t,y,period_min=10,period_max=60)
    keep=np.arange(50)!=20
    wwz=run_wwz(t[keep],y[keep],np.ones(49)*.1,period_min=10,period_max=60,
                 time_divisions=5,freq_step_factor=1)
    path=tmp_path/'composite.png'
    _plot_periodicity_summary(path,'test',t[keep],y[keep],np.ones(49)*.1,cwt,wwz,
        include_global_row=True,light_curve_ylim=(1.5,2.5),mark_lc_clipping=True)
    assert path.stat().st_size>10000
