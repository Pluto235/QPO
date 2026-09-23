from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def integrated_figure(path: Path, label: str, lc, cwt, wwz, sig, *, flux_unit=""):
    fig, axes = plt.subplots(3, 2, figsize=(16, 11), constrained_layout=True)
    ax = axes[0, 0]; ax.errorbar(lc["time"], lc["flux"], yerr=lc["flux_err"], fmt="o", ms=3, alpha=.75); ax.set_title(f"{label} | light curve"); ax.set_xlabel("Time (MJD)"); ax.set_ylabel(f"Flux {flux_unit}".strip())
    axes[0, 1].axis("off"); axes[0, 1].text(.05, .75, f"{label}\nCWT + WWZ QPO analysis", fontsize=14); axes[0, 1].text(.05, .52, f"N={len(lc)}\nspan={lc['time'].max()-lc['time'].min():.1f} d", transform=axes[0, 1].transAxes)
    extent = [cwt["t_mjd"].min(), cwt["t_mjd"].max(), cwt["period"].min(), cwt["period"].max()]
    axes[1, 0].imshow(cwt["power"], aspect="auto", origin="lower", extent=extent, interpolation="nearest"); axes[1, 0].set_yscale("log"); axes[1, 0].set_title("CWT power"); axes[1, 0].set_xlabel("Time (MJD)"); axes[1, 0].set_ylabel("Period (day)")
    axes[1, 1].pcolormesh(wwz["tau_mat"][:, 0], wwz["period_mat"].T, wwz["wwz_mat"].T, shading="auto"); axes[1, 1].set_yscale("log"); axes[1, 1].set_title("WWZ power"); axes[1, 1].set_xlabel("Time (MJD)"); axes[1, 1].set_ylabel("Period (day)")
    axes[2, 0].plot(cwt["period"], cwt["gws"], color="black", label="Observed"); axes[2, 0].plot(cwt["period"], cwt["signif95"], "--", label="AR(1) 95%"); axes[2, 0].set_xscale("log"); axes[2, 0].set_title("CWT global spectrum"); axes[2, 0].legend()
    axes[2, 1].plot(sig["period"], sig["observed"], color="black", label="Observed"); axes[2, 1].plot(sig["period"], sig["pointwise95"], "--", label="AR(1) surrogate 95%"); axes[2, 1].plot(sig["period"], sig["pointwise99"], ":", label="AR(1) surrogate 99%"); axes[2, 1].set_xscale("log"); axes[2, 1].set_title("WWZ global spectrum"); axes[2, 1].legend()
    fig.savefig(path, dpi=180); plt.close(fig)
