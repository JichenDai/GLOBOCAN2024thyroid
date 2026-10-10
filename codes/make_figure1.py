#!/usr/bin/env python3
"""Figure 1 -- thyroid cancer (GLOBOCAN 2024, ICD-10 C73).

Layout requested by the author
    top row    : (a) ASIR  |  (b) ASMR  |  (c) MIR   -- top-25 countries, diverging bars
    bottom row : (d) ASIR world map   |   (e) ASMR world map   -- all ages, both sexes

Panel sources
    (a)-(c) GLOBOCAN 2024 all-age estimates (thyroid_raw_allages_2024.json,
            populations_metadata_2024.json); female bars extend left (burgundy),
            male bars extend right (blue); each panel sorted by its own female value.
    (d)-(e) GLOBOCAN 2024 all-age both-sex ASIR/ASMR for 186 countries
            (caya039_allages_2024.json + caya039_metadata.csv) drawn on
            countries.geojson with a linear 0-max colour scale.

Runs fully offline.  Writes Figure1.png (600 dpi) / .pdf / .svg next to
Final_res/figures/.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.collections import PatchCollection
from matplotlib.patches import Patch, Polygon
import numpy as np

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUT = HERE.parent / "figures"

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.8,
    "axes.edgecolor": "#333333",
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
})

CF = (150 / 255, 30 / 255, 30 / 255)     # female -- burgundy
CM = (70 / 255, 120 / 255, 165 / 255)    # male   -- muted blue
GRID_C = "lightgray"
ZERO_C = "#333333"
MISSING = "#D0D0D0"


# --------------------------------------------------------------------------
# top-25 diverging panels
# --------------------------------------------------------------------------
def load_top25():
    allages = json.loads((DATA / "globocan_allages_2024.json").read_text())
    pops = json.loads((DATA / "populations_metadata_2024.json").read_text())
    label_of = {str(r["country_code"]): r.get("short_label") or r.get("label")
                for r in pops}

    def rows(key):
        return [r for k, r in allages[key].items() if int(k) < 900]

    def lookup(key):
        return {int(k): r for k, r in allages[key].items() if int(k) < 900}

    ranked = sorted(rows("0_0"), key=lambda r: r["asr"], reverse=True)[:25]
    inc_m, inc_f = lookup("0_1"), lookup("0_2")
    mor_m, mor_f = lookup("1_1"), lookup("1_2")
    out = []
    for b in ranked:
        cc = b["country_code"]
        im, iw = inc_m.get(cc, {}), inc_f.get(cc, {})
        dm, dw = mor_m.get(cc, {}), mor_f.get(cc, {})
        out.append({
            "country": label_of.get(str(cc), str(cc)),
            "asir_m": im.get("asr", 0) or 0, "asir_f": iw.get("asr", 0) or 0,
            "asmr_m": dm.get("asr", 0) or 0, "asmr_f": dw.get("asr", 0) or 0,
            "mir_m": (dm.get("total", 0) / im.get("total", 1)) if im.get("total", 0) else np.nan,
            "mir_f": (dw.get("total", 0) / iw.get("total", 1)) if iw.get("total", 0) else np.nan,
        })
    return out


def diverging_axis(ax, panel_rows, title, xlabel, n_dec, fkey, mkey):
    n = len(panel_rows)
    y = np.arange(n)
    names = [r["country"] for r in panel_rows][::-1]
    f_plot = np.array([-r[fkey] for r in panel_rows][::-1])
    m_plot = np.array([r[mkey] for r in panel_rows][::-1])

    ax.set_axisbelow(True)
    ax.grid(axis="x", linestyle="-", linewidth=0.6, color=GRID_C, alpha=0.6)
    ax.barh(y, f_plot, height=0.66, color=CF, zorder=3, edgecolor="none")
    ax.barh(y, m_plot, height=0.66, color=CM, zorder=3, edgecolor="none")

    maxv = max(np.nanmax(np.abs(f_plot)), np.nanmax(np.abs(m_plot)))
    ax.set_xlim(-1.20 * maxv, 1.15 * maxv)
    ax.xaxis.set_major_locator(mticker.MaxNLocator(nbins=6))
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"{abs(x):g}"))
    ax.axvline(0, color=ZERO_C, linewidth=1.0, zorder=2)

    lab_off = 0.025 * maxv
    for yi, (ff, mm) in enumerate(zip(f_plot, m_plot)):
        if np.isfinite(ff):
            ax.text(ff - lab_off, yi, f"{abs(ff):.{n_dec}f}", ha="right",
                    va="center", fontsize=6.5, color=CF)
        if np.isfinite(mm):
            ax.text(mm + lab_off, yi, f"{mm:.{n_dec}f}", ha="left",
                    va="center", fontsize=6.5, color=CM)

    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=8)
    ax.set_ylim(-0.7, n - 0.3)
    ax.tick_params(axis="y", pad=6)
    ax.tick_params(axis="x", labelsize=7.5)
    ax.set_title(title, loc="left", fontsize=10, fontweight="bold", pad=14)
    ax.set_xlabel(xlabel, fontsize=8.5)


# --------------------------------------------------------------------------
# all-ages world maps
# --------------------------------------------------------------------------
def map_axis(ax, cax, metric, values, geo, letter):
    finite = np.array([v for v in values.values() if np.isfinite(v)], dtype=float)
    vmax = max(float(np.quantile(finite, 0.98)), float(finite.max())) if len(finite) else 1.0
    norm = mpl.colors.Normalize(0, vmax)

    patches, colors = [], []
    for feature in geo["features"]:
        iso = feature.get("properties", {}).get("ISO3166-1-Alpha-3")
        geom = feature.get("geometry") or {}
        polys = geom.get("coordinates", [])
        if geom.get("type") == "Polygon":
            polys = [polys]
        for poly in polys:
            if not poly:
                continue
            patches.append(Polygon(np.asarray(poly[0], dtype=float), closed=True))
            colors.append(values.get(iso, np.nan))

    pc = PatchCollection(patches, linewidth=0.18, edgecolor="white", rasterized=True)
    pc.set_facecolor([mpl.colormaps["viridis"](norm(x)) if np.isfinite(x) else MISSING
                      for x in colors])
    pc.set_array(np.array([x if np.isfinite(x) else 0 for x in colors]))
    ax.add_collection(pc)

    sm = mpl.cm.ScalarMappable(norm=norm, cmap="viridis")
    sm.set_array([])
    cb = ax.figure.colorbar(sm, cax=cax)
    cb.set_label(f"{metric} per 100,000", fontsize=8)
    cb.ax.tick_params(labelsize=7)

    ax.set_xlim(-170, 180)
    ax.set_ylim(-58, 84)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_frame_on(False)
    ax.set_xlabel("Longitude (\u00b0)", fontsize=7)
    ax.set_ylabel("Latitude (\u00b0)", fontsize=7)
    ax.set_title(f"{letter} {metric} (all ages)", loc="left", fontsize=10,
                 fontweight="bold", pad=8)


def main():
    top25 = load_top25()

    geo = json.loads((DATA / "countries.geojson").read_text())
    meta = json.loads((DATA / "caya039_allages_2024.json").read_text())
    import csv
    iso_by_code = {}
    with (DATA / "caya039_metadata.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            if row.get("iso3") and row["iso3"].strip():
                iso_by_code[str(row["pop_code"])] = row["iso3"].strip()

    def map_values(key):
        return {iso_by_code[c]: r["asr"]
                for c, r in meta[key].items()
                if c in iso_by_code and c != "900" and r.get("asr") is not None}

    fig = plt.figure(figsize=(16, 11))
    outer = fig.add_gridspec(2, 1, height_ratios=[3.0, 1.75], hspace=0.22,
                             left=0.045, right=0.985, top=0.905, bottom=0.035)
    gs_top = outer[0].subgridspec(1, 3, wspace=0.55)
    gs_bot = outer[1].subgridspec(1, 4, width_ratios=[1, 0.016, 1, 0.016],
                                  wspace=0.04)

    panels = [
        ("(a) ASIR", "asir_f", "asir_m", "asir_f", "ASIR per 100,000", 2),
        ("(b) ASMR", "asmr_f", "asmr_m", "asmr_f", "ASMR per 100,000", 2),
        ("(c) MIR",  "mir_f",  "mir_m",  "mir_f",  "MIR",             2),
    ]
    for col, (title, fkey, mkey, sortkey, xlabel, nd) in enumerate(panels):
        ax = fig.add_subplot(gs_top[0, col])
        diverging_axis(ax, sorted(top25, key=lambda r: r[sortkey], reverse=True),
                       title, xlabel, nd, fkey, mkey)

    ax_d = fig.add_subplot(gs_bot[0, 0]); cax_d = fig.add_subplot(gs_bot[0, 1])
    ax_e = fig.add_subplot(gs_bot[0, 2]); cax_e = fig.add_subplot(gs_bot[0, 3])
    map_axis(ax_d, cax_d, "ASIR", map_values("0_0"), geo, "(d)")
    map_axis(ax_e, cax_e, "ASMR", map_values("1_0"), geo, "(e)")

    handles = [Patch(color=CF, label="Female"), Patch(color=CM, label="Male")]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.995),
               ncol=2, frameon=False, fontsize=10, handlelength=1.3,
               handleheight=0.9, columnspacing=2.2, borderaxespad=0.0)

    for ext in ("png", "pdf", "svg"):
        kw = {"dpi": 600} if ext == "png" else {}
        fig.savefig(OUT / f"Figure1.{ext}", bbox_inches="tight", **kw)
    plt.close(fig)
    print("wrote", OUT / "Figure1.png/.pdf/.svg", f"({len(top25)} countries)")


if __name__ == "__main__":
    main()
