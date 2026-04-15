#!/usr/bin/env python3
"""Backward-compatible entry point for WCDA simulation generation.

Prefer running ``mkn421_lhaaso/simulations/generate_wcda_weekly_sims.py``
directly in batch systems such as Slurm. This wrapper is kept so that older
commands like ``python simulation.py`` continue to work.
"""

from simulations.generate_wcda_weekly_sims import main


if __name__ == "__main__":
    main()
