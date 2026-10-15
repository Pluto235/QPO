#!/bin/bash
#SBATCH --job-name=poster_crab_highres
#SBATCH --partition=main
#SBATCH --cpus-per-task=2
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=work/poster_crab_highres_20261014/slurm-%j.out

set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
export PYTHONPATH="$PWD/work/poster_mrk421_ar1_1000_20261014/python_deps:$PWD/src"
export MPLBACKEND=Agg
/opt/anaconda3/bin/python3 src/pipeline/detector_controls_2day_qpo.py \
  --sources Crab --workers 2 --n-surrogates 1000 \
  --wwz-time-divisions 240 --wwz-freq-step-factor 0.125 \
  --aligned-dir data/processed/aligned/detector_controls_crab_highres_20261014 \
  --periodicity-dir data/processed/periodicity/detector_controls_crab_highres_20261014 \
  --mark-global-peaks-on-maps --no-report
