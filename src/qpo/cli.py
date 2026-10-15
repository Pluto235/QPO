from __future__ import annotations
import argparse
from .pipeline import analyze_lightcurve

def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m qpo.cli"); sub = parser.add_subparsers(dest="command", required=True); p = sub.add_parser("analyze")
    p.add_argument("input"); p.add_argument("--outdir", required=True); p.add_argument("--label"); p.add_argument("--flux-unit", default=""); p.add_argument("--period-min", type=float); p.add_argument("--period-max", type=float); p.add_argument("--n-periods", type=int, default=400); p.add_argument("--n-surrogates", type=int, default=1000); p.add_argument("--seed", type=int, default=20260922); p.add_argument("--workers", type=int, default=1); p.add_argument("--wwz-time-divisions", type=int, default=80); p.add_argument("--wwz-freq-step-factor", type=float, default=0.5)
    args = parser.parse_args(argv)
    if args.command == "analyze":
        analyze_lightcurve(args.input, args.outdir, label=args.label, flux_unit=args.flux_unit, period_min=args.period_min, period_max=args.period_max, n_periods=args.n_periods, n_surrogates=args.n_surrogates, seed=args.seed, workers=args.workers, time_divisions=args.wwz_time_divisions, freq_step_factor=args.wwz_freq_step_factor)

if __name__ == "__main__":
    main()
