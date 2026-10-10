#!/usr/bin/env python3
"""All-ages world ASIR/ASMR maps (Figure 1, panels d and e).

Uses the identical map code path as the 0-39 maps (draw_world_maps); the only
change is the stratification: the GLOBOCAN 2024 all-ages Both-sex reference
(ASIR 10.33, ASMR 0.44 per 100,000; 959,281 cases, 48,070 deaths) replaces the
0-39 stratum.

Inputs : ./data/globocan_allages_2024.json (or caya039_allages_2024.json),
         ./data/caya039_metadata.csv, ./data/countries.geojson
Output : ../figures/original/Figure1b_world_maps_allages.{png,pdf,svg}
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUT = HERE.parent / "figures" / "original"
import sys
sys.path.insert(0, str(HERE))
from figstyle import use_style
from make_caya039_figures import draw_world_maps


def main():
    use_style()
    src = DATA / "globocan_allages_2024.json"
    allage = json.loads(src.read_text())
    meta = pd.read_csv(DATA / "caya039_metadata.csv", dtype={"pop_code": str, "iso3": str})
    meta = meta[meta.is_country.astype(str).isin(["1", "True", "true"])]
    iso3 = dict(zip(meta.pop_code, meta.iso3))
    inc, mort = allage["0_0"], allage["1_0"]
    rows = [
        {"pop_code": code, "iso3": iso3.get(code), "ASIR": inc[code]["asr"], "ASMR": mort[code]["asr"]}
        for code in inc
        if code in iso3 and iso3.get(code)
    ]
    d = pd.DataFrame(rows)
    assert len(d) == 186, len(d)
    assert d.ASIR.notna().all() and d.ASMR.notna().all()
    draw_world_maps(d, OUT / "Figure1b_world_maps_allages")
    print(f"wrote Figure1b_world_maps_allages (countries={len(d)})")
    print("world", {"ASIR": inc["900"]["asr"], "ASMR": mort["900"]["asr"],
                    "cases": inc["900"]["total"], "deaths": mort["900"]["total"]})


if __name__ == "__main__":
    main()
