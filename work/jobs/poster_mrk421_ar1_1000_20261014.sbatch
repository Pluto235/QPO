#!/bin/bash
#SBATCH --job-name=poster_mrk421_1000
#SBATCH --partition=main
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=02:00:00
#SBATCH --output=work/jobs/poster_mrk421_ar1_1000_%j.log

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PYTHONPATH="$PWD/work/poster_mrk421_ar1_1000_20261014/python_deps${PYTHONPATH:+:$PYTHONPATH}"

# Keep slide 8's sampling, search grid, and seed; only increase Monte Carlo size.
/opt/anaconda3/bin/python3 -u src/pipeline/refine_mrk421_poster_significance.py
