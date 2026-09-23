#!/usr/bin/env bash
#SBATCH --job-name=qpo-toolkit
#SBATCH --cpus-per-task=4
#SBATCH --time=04:00:00
#SBATCH --mem=8G

set -euo pipefail

if [ "$#" -lt 2 ]; then
    echo "Usage: sbatch qpo_toolkit.sbatch INPUT.csv OUTPUT_DIR [analysis options]" >&2
    exit 2
fi

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_dir"
python_bin="${QPO_PYTHON:-python}"
input_csv="$1"
output_dir="$2"
shift 2

PYTHONPATH="$repo_dir/src${PYTHONPATH:+:$PYTHONPATH}" \
    "$python_bin" -m qpo.cli analyze "$input_csv" --outdir "$output_dir" \
    --workers "${SLURM_CPUS_PER_TASK:-1}" "$@"
