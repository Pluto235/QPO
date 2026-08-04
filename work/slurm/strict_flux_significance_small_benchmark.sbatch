#!/bin/bash
#SBATCH --job-name=qpo_flux_sig_smallbench
#SBATCH --partition=main
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=work/slurm/logs/strict_flux_significance_small_benchmark_%j.out
#SBATCH --error=work/slurm/logs/strict_flux_significance_small_benchmark_%j.err

set -euo pipefail
cd /mnt/mydisk/server/projects/QPO
mkdir -p work/slurm/logs
SOURCE_ID="mkn421"
N_SURROGATES="32"
WORKERS="8"
echo "[INFO] host=ETO"
echo "[INFO] start=2026-06-03T15:00:15+08:00"
echo "[INFO] source= n_surrogates= workers="
/usr/bin/time -v /opt/anaconda3/bin/python3 src/pipeline/strict_flux_weekly_significance.py   --sources ""   --n-surrogates ""   --workers ""
echo "[INFO] end=2026-06-03T15:00:15+08:00"
