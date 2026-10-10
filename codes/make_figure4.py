#!/usr/bin/env python3
"""Figure 4 -- world distribution of thyroid cancer, GLOBOCAN 2024.

Vertical concatenation of the two constituent panels after the CAYA revision:
    top    : caya039_world_maps        (0-39 both-sex ASIR / ASMR country maps)
    bottom : caya039_hdi_associations  (country HDI vs ASIR/ASMR/MIR, 0-39 and 40+)

The map panel carries labels (a-b), and the HDI panel carries labels (c-h),
giving the requested top-to-bottom, left-to-right sequence (a) through (h).

Inputs : ../figures/original/Figure4a_caya039_world_maps.png
         ../figures/original/Figure4b_caya039_hdi_associations.png
Outputs                       : ../figures/Figure4.png / .pdf
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stack_figures import stack_vertical

HERE = Path(__file__).resolve().parent
ORIG = HERE.parent / "figures" / "original"
OUT = HERE.parent / "figures"

stack_vertical(
    [ORIG / "Figure4a_caya039_world_maps.png",
     ORIG / "Figure4b_caya039_hdi_associations.png"],
    OUT / "Figure4",
)
print("wrote", OUT / "Figure4.png/.pdf")
