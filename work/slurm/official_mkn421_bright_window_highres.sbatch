#!/bin/bash
#SBATCH --job-name=m421_bw_hr
#SBATCH --partition=main
#SBATCH --cpus-per-task=32
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=work/slurm/logs/official_mkn421_bright_window_highres_%j.out
#SBATCH --error=work/slurm/logs/official_mkn421_bright_window_highres_%j.err

set -euo pipefail

cd /mnt/mydisk/server/projects/QPO
mkdir -p work/slurm/logs

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

echo "[INFO] host=$(hostname) start=$(date -Is)"

/opt/anaconda3/bin/python3 src/pipeline/official_lc_xgm_window_qpo_analysis.py \
  --sources Mkn421 \
  --window-min 59800 \
  --window-max 60500 \
  --period-min 10 \
  --period-max 200 \
  --output-key bright_window_59800_60500_highres \
  --target-period 140 \
  --mark-global-peaks-on-maps \
  --n-surrogates 200 \
  --workers "${SLURM_CPUS_PER_TASK:-32}" \
  --wwz-time-divisions 240 \
  --wwz-freq-step-factor 0.25

echo "[INFO] end=$(date -Is)"
