#!/bin/bash
#SBATCH --job-name=wcda_abc
#SBATCH --partition=main
#SBATCH --array=0-1
#SBATCH --cpus-per-task=16
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --output=work/slurm/logs/wcda_abc_%A_%a.out
#SBATCH --error=work/slurm/logs/wcda_abc_%A_%a.err
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
sources=(Mkn421 Mkn501)
/opt/anaconda3/bin/python3 src/pipeline/analyze_wcda_spectral_abc.py \
  --source "${sources[$SLURM_ARRAY_TASK_ID]}" --workers "$SLURM_CPUS_PER_TASK"
