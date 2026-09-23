#!/usr/bin/env bash
set -euo pipefail
python -m qpo.cli analyze examples/mkn421_example.csv --outdir results/mkn421_example --label "Mrk 421" --n-surrogates 100
