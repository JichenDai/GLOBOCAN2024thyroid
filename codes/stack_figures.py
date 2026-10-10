#!/usr/bin/env python3
"""Faithful vertical concatenation of reviewed figure images.

The composites Figure 3 and Figure 4 are defined by the author as "stack the
two reviewed originals vertically".  This helper does exactly that at native
resolution, with no rescaling of either source, and writes PNG plus a 600-dpi
PDF built from the composed raster.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image


def stack_vertical(paths, out_stem, background: str = "white", gap: int = 60):
    ims = [Image.open(p).convert("RGB") for p in paths]
    width = max(im.width for im in ims)
    height = sum(im.height for im in ims) + gap * (len(ims) - 1)

    canvas = Image.new("RGB", (width, height), background)
    y = 0
    for im in ims:
        x = (width - im.width) // 2
        canvas.paste(im, (x, y))
        y += im.height + gap

    out_stem = Path(out_stem)
    canvas.save(f"{out_stem}.png", dpi=(600, 600))
    canvas.save(f"{out_stem}.pdf", "PDF", resolution=600.0)
    return out_stem
