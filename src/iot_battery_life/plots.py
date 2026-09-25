from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import matplotlib.pyplot as plt
import numpy as np

from .core import CellParameters, NodeProfile, service_life


def plot_reporting_curve(cells: Sequence[CellParameters], node: NodeProfile,
                         temperature_c: float = 20.0,
                         events_per_day: Iterable[float] | None = None,
                         output: str | Path | None = None):
    if events_per_day is None:
        events_per_day = np.geomspace(1, 1440, 80)
    xs = np.asarray(list(events_per_day), dtype=float)
    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    for cell in cells:
        ys = []
        for f in xs:
            r = service_life(cell, node, temperature_c, float(f))
            ys.append(r.reported_life_years if r.reported_life_years is not None else np.nan)
        ax.plot(xs, ys, marker="o" if len(xs) <= 15 else None, label=cell.label)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Reporting events per day")
    ax.set_ylabel("Reported service life (years)")
    ax.set_title(f"Battery service life at {temperature_c:g} °C")
    ax.grid(True, which="both", alpha=0.25); ax.legend(); fig.tight_layout()
    if output:
        fig.savefig(output, dpi=300, bbox_inches="tight")
    return fig, ax


def plot_temperature_curve(cells: Sequence[CellParameters], node: NodeProfile,
                           events_per_day: float = 24,
                           temperature_c: Iterable[float] | None = None,
                           output: str | Path | None = None):
    if temperature_c is None:
        temperature_c = np.linspace(-60, 85, 100)
    xs = np.asarray(list(temperature_c), dtype=float)
    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    for cell in cells:
        ys = []
        for t in xs:
            r = service_life(cell, node, float(t), events_per_day)
            ys.append(r.reported_life_years if r.status == "ok" else np.nan)
        ax.plot(xs, ys, label=cell.label)
    ax.set_yscale("log")
    ax.set_xlabel("Cell temperature (°C)")
    ax.set_ylabel("Reported service life (years)")
    ax.set_title(f"Battery service life at {events_per_day:g} events/day")
    ax.grid(True, which="both", alpha=0.25); ax.legend(); fig.tight_layout()
    if output:
        fig.savefig(output, dpi=300, bbox_inches="tight")
    return fig, ax
