#!/bin/bash
#SBATCH --job-name=fermi_wcda_lc
#SBATCH --partition=main
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=7-00:00:00
#SBATCH --output=work/slurm/logs/fermi_wcda_lc_%j.out
#SBATCH --error=work/slurm/logs/fermi_wcda_lc_%j.err

set -eo pipefail

cd /mnt/mydisk/server/projects/QPO
mkdir -p work/slurm/logs
source /home/server/anaconda3/etc/profile.d/conda.sh
conda activate fermipy
set -u

echo "[INFO] host=$(hostname)"
echo "[INFO] start=$(date -Is)"
echo "[INFO] conda=${CONDA_PREFIX}"
echo "[INFO] cpus=${SLURM_CPUS_PER_TASK:-16}"

python src/pipeline/fermi_wcda_lightcurves.py \
  --workers "${SLURM_CPUS_PER_TASK:-16}" \
  "$@"

echo "[INFO] end=$(date -Is)"
