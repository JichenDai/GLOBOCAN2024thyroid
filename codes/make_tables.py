#!/usr/bin/env python3
"""Reproduce the five delivered tables, GLOBOCAN 2024 thyroid cancer (C73).

    Table1_reproduction_2024.csv          all-ages cases/deaths/ASIR/ASMR/MIR,
                                          by UN subregion, HDI tier and world,
                                          males and females
    Table2_reproduction_2024_caya039.csv  both-sex burden by 0-39 (<40) vs 40+
                                          age window, by subregion/HDI/world
    Supp_Table1_by_region_sex.csv         all-ages cases/deaths/rates/MIR by
                                          region x sex (incl. both)
    Supp_Table2_age_strata_men_caya039.csv    men, 0-39 vs 40+
    Supp_Table3_age_strata_women_caya039.csv  women, 0-39 vs 40+

All values are taken from the bundled GLOBOCAN 2024 extracts; nothing is
imputed.  Null cells reproduce the source convention (rate undefined, or a
percentage with a zero denominator).

Adapted from New/table generators (manuscript_2024/reproduce_tables.py,
2024GLOBOCAN/make_supplementary_tables.py, CAYA039/code/make_caya039_suppl_tables.py)
into one self-contained script reading ./data and writing ../tables/.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUT = HERE.parent / "tables"

SUBREGIONS = [
    "Eastern Africa", "Middle Africa", "Northern Africa", "Southern Africa", "Western Africa",
    "Caribbean", "Central America", "South America", "Northern America",
    "Eastern Asia", "South-Eastern Asia", "South Central Asia", "Western Asia",
    "Eastern Europe", "Northern Europe", "Southern Europe", "Western Europe",
    "Australia-New Zealand", "Melanesia", "Micronesia", "Polynesia",
]
CONTINENTS = [
    ("Africa", SUBREGIONS[0:5]),
    ("America", SUBREGIONS[5:9]),
    ("Asia", SUBREGIONS[9:13]),
    ("Europe", SUBREGIONS[13:17]),
    ("Oceania", SUBREGIONS[17:21]),
]
HDI_TIERS = ["Low HDI", "Medium HDI", "High HDI", "Very high HDI"]

# population codes for the UN subregions and HDI tiers
CODES = {
    "Eastern Africa": 910, "Middle Africa": 911, "Northern Africa": 912,
    "Southern Africa": 913, "Western Africa": 914, "Caribbean": 915,
    "Central America": 916, "South America": 931, "Northern America": 905,
    "Eastern Asia": 906, "South-Eastern Asia": 920, "South Central Asia": 921,
    "Western Asia": 922, "Eastern Europe": 923, "Northern Europe": 924,
    "Southern Europe": 925, "Western Europe": 926, "Australia-New Zealand": 927,
    "Melanesia": 928, "Micronesia": 954, "Polynesia": 957,
    "Low HDI": 984, "Medium HDI": 983, "High HDI": 982, "Very high HDI": 981,
    "World": 900,
}


def num(v, nd=2):
    """Format a rate the way the source tables do; None -> empty cell."""
    if v is None:
        return ""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return ""
    if f != f:  # NaN
        return ""
    return f"{f:.{nd}f}".rstrip("0").rstrip(".") if f == int(f) else f"{f:.{nd}f}"


def mir(deaths, cases, nd=2):
    if not cases:
        return ""
    return round(deaths / cases, nd)


def write_csv(name, header, rows):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print("wrote", path.name, f"({len(rows)} rows)")


def build_table1(allage):
    """All-ages cases/deaths/rates/MIR by subregion, HDI and world."""
    header = ["Region", "Inc_M_cases", "Inc_M_ASIR", "Inc_F_cases", "Inc_F_ASIR",
              "Mor_M_deaths", "Mor_M_ASMR", "Mor_F_deaths", "Mor_F_ASMR", "MIR_M", "MIR_F"]

    def cells(pop):
        im, iw = allage["0_1"].get(str(pop)), allage["0_2"].get(str(pop))
        dm, dw = allage["1_1"].get(str(pop)), allage["1_2"].get(str(pop))
        if not (im and iw and dm and dw):
            return [""] * 10
        return [im["total"], im["asr"], iw["total"], iw["asr"],
                dm["total"], dm["asr"], dw["total"], dw["asr"],
                mir(dm["total"], im["total"]), mir(dw["total"], iw["total"])]

    rows = []
    for cont, subs in CONTINENTS:
        rows.append([cont] + [""] * 10)
        for s in subs:
            rows.append([s] + cells(CODES[s]))
    rows.append(["HDI"] + [""] * 10)
    for tier in HDI_TIERS:
        rows.append([tier] + cells(CODES[tier]))
    rows.append(["World"] + cells(900))
    return header, rows


def build_supp_table1(allage):
    header = ["Region", "population_code", "M_cases", "M_ASIR", "F_cases", "F_ASIR",
              "B_cases", "B_ASIR", "M_deaths", "M_ASMR", "F_deaths", "F_ASMR",
              "B_deaths", "B_ASMR", "M_MIR", "F_MIR", "B_MIR"]
    order = SUBREGIONS + HDI_TIERS + ["World"]
    rows = []
    for s in order:
        pop = CODES[s]
        m_c, f_c, b_c = (allage[k][str(pop)]["total"] for k in ("0_1", "0_2", "0_0"))
        m_d, f_d, b_d = (allage[k][str(pop)]["total"] for k in ("1_1", "1_2", "1_0"))
        rows.append([s, pop,
                     m_c, allage["0_1"][str(pop)]["asr"],
                     f_c, allage["0_2"][str(pop)]["asr"],
                     b_c, allage["0_0"][str(pop)]["asr"],
                     m_d, allage["1_1"][str(pop)]["asr"],
                     f_d, allage["1_2"][str(pop)]["asr"],
                     b_d, allage["1_0"][str(pop)]["asr"],
                     mir(m_d, m_c), mir(f_d, f_c), mir(b_d, b_c)])
    return header, rows


def _caya_lookup(b):
    idx = b.set_index(["pop_code", "sex", "stratum"])
    return idx


def _cell(idx, code, sex, stratum, metric, nd=2):
    try:
        v = idx.loc[(str(code), sex, stratum), metric]
    except KeyError:
        return ""
    if pd.isna(v):
        return ""
    if metric in ("incidence_cases", "deaths"):
        return int(round(float(v)))
    return f"{float(v):.{nd}f}"


def _mir(idx, code, sex, stratum):
    try:
        inc = float(idx.loc[(str(code), sex, stratum), "incidence_cases"])
        d = float(idx.loc[(str(code), sex, stratum), "deaths"])
    except KeyError:
        return ""
    if pd.isna(inc) or inc <= 0:
        return ""
    return f"{d / inc:.2f}"


def build_table2(idx):
    """Both-sex 0-39 vs 40+ burden with within-row percentages."""
    header = ["Region", "Y39_cases", "Y39_cases_pct", "Y39_deaths", "Y39_deaths_pct",
              "Y39_ASIR", "Y39_ASMR", "Y39_MIR",
              "O40_cases", "O40_cases_pct", "O40_deaths", "O40_deaths_pct",
              "O40_ASIR", "O40_ASMR", "O40_MIR"]

    def row(label, code):
        yc = _cell(idx, code, "Both", "0-39", "incidence_cases")
        oc = _cell(idx, code, "Both", "40+", "incidence_cases")
        yd = _cell(idx, code, "Both", "0-39", "deaths")
        od = _cell(idx, code, "Both", "40+", "deaths")
        tot = (yc + oc) if isinstance(yc, int) and isinstance(oc, int) else 0
        totd = (yd + od) if isinstance(yd, int) and isinstance(od, int) else 0
        return [label,
                yc, f"{yc/tot*100:.2f}" if tot else "",
                yd, f"{yd/totd*100:.2f}" if totd else "",
                _cell(idx, code, "Both", "0-39", "ASIR"),
                _cell(idx, code, "Both", "0-39", "ASMR"),
                _mir(idx, code, "Both", "0-39"),
                oc, f"{oc/tot*100:.2f}" if tot else "",
                od, f"{od/totd*100:.2f}" if totd else "",
                _cell(idx, code, "Both", "40+", "ASIR"),
                _cell(idx, code, "Both", "40+", "ASMR"),
                _mir(idx, code, "Both", "40+")]

    rows = []
    for cont, subs in CONTINENTS:
        rows.append([cont] + [""] * 14)
        for s in subs:
            rows.append(row(s, CODES[s]))
    rows.append(["HDI"] + [""] * 14)
    for tier in HDI_TIERS:
        rows.append(row(tier, CODES[tier]))
    rows.append(row("World", 900))
    return header, rows


def build_supp_sex(idx, sex):
    header = ["Region", "population_code",
              "Y39_cases", "Y39_ASIR", "Y39_deaths", "Y39_ASMR", "Y39_MIR",
              "O40_cases", "O40_ASIR", "O40_deaths", "O40_ASMR", "O40_MIR"]
    order = SUBREGIONS + HDI_TIERS + ["World"]
    rows = []
    for s in order:
        c = CODES[s]
        rows.append([s, c,
                     _cell(idx, c, sex, "0-39", "incidence_cases"),
                     _cell(idx, c, sex, "0-39", "ASIR"),
                     _cell(idx, c, sex, "0-39", "deaths"),
                     _cell(idx, c, sex, "0-39", "ASMR"),
                     _mir(idx, c, sex, "0-39"),
                     _cell(idx, c, sex, "40+", "incidence_cases"),
                     _cell(idx, c, sex, "40+", "ASIR"),
                     _cell(idx, c, sex, "40+", "deaths"),
                     _cell(idx, c, sex, "40+", "ASMR"),
                     _mir(idx, c, sex, "40+")])
    return header, rows


def main():
    allage = json.loads((DATA / "globocan_allages_2024.json").read_text())
    b = pd.read_csv(DATA / "caya039_burden_by_population_age_sex.csv",
                    dtype={"pop_code": str}, low_memory=False)
    b["pop_code"] = b.pop_code.astype(str)
    idx = _caya_lookup(b)

    h, r = build_table1(allage)
    write_csv("Table1_reproduction_2024.csv", h, r)
    h, r = build_table2(idx)
    write_csv("Table2_reproduction_2024_caya039.csv", h, r)
    h, r = build_supp_table1(allage)
    write_csv("Supp_Table1_by_region_sex.csv", h, r)
    h, r = build_supp_sex(idx, "Male")
    write_csv("Supp_Table2_age_strata_men_caya039.csv", h, r)
    h, r = build_supp_sex(idx, "Female")
    write_csv("Supp_Table3_age_strata_women_caya039.csv", h, r)


if __name__ == "__main__":
    main()
