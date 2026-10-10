#!/usr/bin/env python3
"""Render Figure 3 as one aligned eight-panel canvas.

Panels (c)-(h) use the same grouped-bar function, so their typography,
tick angle, bar width, legend, grid and column geometry stay identical.
"""
from __future__ import annotations

from pathlib import Path

from make_caya039_figures import draw_composite_figure3, read

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "figures"

draw_composite_figure3(
    read("caya039_burden_by_population_age_sex.csv"),
    OUT / "Figure3",
)
print("wrote", OUT / "Figure3.png/.pdf/.svg")
