#!/bin/bash
#SBATCH --job-name=qpo_flux_sig_collect
#SBATCH --partition=main
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --output=work/slurm/logs/strict_flux_significance_collect_%j.out
#SBATCH --error=work/slurm/logs/strict_flux_significance_collect_%j.err

set -euo pipefail

cd /mnt/mydisk/server/projects/QPO
mkdir -p work/slurm/logs

echo "[INFO] start=$(date -Is)"
/opt/anaconda3/bin/python3 src/pipeline/strict_flux_weekly_significance.py \
  --all-strict-flux-sources \
  --collect-summary-only
/opt/anaconda3/bin/python3 src/pipeline/build_agn_wcda_weekly_survey_report.py
echo "[INFO] end=$(date -Is)"
