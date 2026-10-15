#!/bin/bash
#SBATCH --job-name=fermi_qpo_collect
#SBATCH --partition=main
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:20:00
#SBATCH --output=work/slurm/logs/fermi_wcda_qpo_collect_%j.out
#SBATCH --error=work/slurm/logs/fermi_wcda_qpo_collect_%j.err

set -euo pipefail

cd /mnt/mydisk/server/projects/QPO
mkdir -p work/slurm/logs

/opt/anaconda3/bin/python3 src/pipeline/fermi_wcda_qpo_analysis.py \
  --flux-policy all-successful \
  --collect-only
