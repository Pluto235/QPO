from argparse import Namespace
import base64
import json

import pandas as pd

from pipeline.build_detector_controls_report import build_report


def test_report_embeds_figures_and_handles_no_candidate(tmp_path):
    out=tmp_path/'periodicity'
    folder=out/'crab'
    folder.mkdir(parents=True)
    png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=')
    (folder/'Crab_strict_2day_cwt_wwz.png').write_bytes(png)
    meta=dict(config=dict(source='Crab',n_surrogates=1000,period_min=10,period_max=600,
        seed=20261012,wwz_time_divisions=80,wwz_freq_step_factor=.5,input_sha256='abc'),
        raw_rows=803,retained_rows=799,cwt_rows=803,interpolated_rows=4,
        mjd_min=59281.66666667,mjd_max=60885.66666667,max_retained_gap_days=4,
        ar1_alpha=.3,ar1_real_pairs=794,pivot_energy_TeV=10,
        flux_min=1e-14,flux_max=2e-13,display_clipped_count=12,
        observed_parity_max_abs=1e-12,null_parity_max_abs=1e-12,
        versions=dict(numpy='1.26.4'),python='py310',completed_at='2026-10-12',
        workers=2,threads_per_worker=1,elapsed_seconds=1,wwz_frequency_bins=317,
        wwz_time_bins=80,model_status='not_specified')
    (folder/'run_metadata.json').write_text(json.dumps(meta))
    pd.DataFrame(columns=['source','method','period_days','local_fap','global_fap','four_source_fap']).to_csv(folder/'candidate_significance.csv',index=False)
    path=build_report(Namespace(sources=['Crab'],periodicity_dir=out,report_path=tmp_path/'report.html'))
    text=path.read_text()
    assert text.count('src="data:image/png;base64,')==1
    assert '未识别到符合规则的内部候选峰' in text
    assert '插值' in text and 'AR(1)' in text and '四源' in text
    assert '<script' in text and '<dialog' in text
    assert (tmp_path/'report.md').exists()
