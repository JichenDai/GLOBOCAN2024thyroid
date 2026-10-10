#!/usr/bin/env python3
"""CAYA 0-39 / 40+ publication panels, GLOBOCAN 2024 (thyroid, C73).

Produces the four constituent panels used by the composite Figures 3 and 4:
    Figure3a_caya039_result_main              (age-band ASIR; regional ASIR;
                                                HDI ASIR 0-39 and 40+)
    Figure3b_caya039_mortality_adult_comparison (ASMR and MIR, world/HDI,
                                                0-39 vs 40+)
    Figure4a_caya039_world_maps               (0-39 both-sex ASIR / ASMR maps)
    Figure4b_caya039_hdi_associations         (country HDI vs ASIR / ASMR / MIR)
plus caya039_ageband_patterns (auxiliary).

Adapted from CAYA039/code/make_caya039_figures.py so it runs from this bundle:
data are read from ./data, geometry from ./data/countries.geojson, and the
outputs are written to ../figures/original/ under the names the composite
Figures 3 and 4 consume.  Values come only from the verified CAYA tables;
nothing is imputed.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import pandas as pd
from matplotlib.colors import Normalize
from matplotlib.patches import Patch, Polygon
from matplotlib.collections import PatchCollection

HERE = Path(__file__).resolve().parent
TABLE = HERE / "data"
OUT = HERE.parent / "figures" / "original"
GEOJSON = HERE / "data" / "countries.geojson"
import sys
sys.path.insert(0, str(HERE))
from figstyle import WIDE, PALETTE, figure_grid, panel_labels, save, use_style

FEMALE = "#961E1E"
MALE = "#4678A5"
BOTH = "#595959"
MISSING = "#D0D0D0"
REGION_CODES = ["906", "910", "911", "912", "913", "914", "915", "916", "920",
                "921", "922", "923", "924", "925", "926", "927", "928", "931", "954", "957"]
BANDS = ["0-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39"]
HDI = ["984", "983", "982", "981", "900"]
HDI_LAB = ["Low", "Med", "High", "Very high", "World"]


def read(name):
    return pd.read_csv(TABLE / name, dtype={'pop_code': str}, low_memory=False)


def save_fig(fig, stem):
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(f"{stem}.png", dpi=600, facecolor="white")
    save(fig, str(stem), formats=("pdf", "svg"), close=True)


def draw_age_specific_panel(ax, b):
    """World female and male incidence over the eight CAYA age bands."""
    world = b[(b.pop_code == "900") & b.stratum.isin(BANDS)]
    for sex, color, marker in (("Female", FEMALE, "o"), ("Male", MALE, "s")):
        q = world[world.sex == sex].set_index("stratum").reindex(BANDS)
        ax.plot(BANDS, q.ASIR.values, color=color, marker=marker, lw=1.6, ms=4, label=sex)
    ax.set_ylabel("ASIR per 100,000")
    ax.set_xlabel("Age group (years)")
    ax.tick_params(axis="x", rotation=45)
    ax.legend(loc="upper left")
    ax.grid(axis="y", alpha=0.35)


def draw_regional_panel(ax, b):
    """Diverging sex-specific ASIR for the leading 0-39 regions."""
    reg = b[(b.pop_code.isin(REGION_CODES)) & (b.stratum == "0-39")]
    base = reg[reg.sex == "Both"].copy()
    base["ASIR"] = pd.to_numeric(base.ASIR, errors="coerce")
    top = base.sort_values("ASIR", ascending=False).head(15).pop_code.tolist()[::-1]
    names = [base[base.pop_code == c].population.iloc[0] for c in top]
    fem = [float(reg[(reg.pop_code == c) & (reg.sex == "Female")].ASIR.iloc[0]) for c in top]
    mal = [float(reg[(reg.pop_code == c) & (reg.sex == "Male")].ASIR.iloc[0]) for c in top]
    y = np.arange(len(top))
    ax.barh(y, -np.array(fem), color=FEMALE, height=0.65)
    ax.barh(y, np.array(mal), color=MALE, height=0.65)
    lim = max(max(fem), max(mal)) * 1.25
    ax.set_xlim(-lim, lim)
    ax.axvline(0, color="#333333", lw=0.8)
    ax.set_yticks(y, names, fontsize=6.5)
    ax.xaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda x, p: f"{abs(x):g}"))
    ax.set_xlabel("ASIR per 100,000")
    ax.grid(axis="x", alpha=0.35)


def draw_hdi_bars(ax, b, metric, age_group, legend_loc="upper right"):
    """Apply one geometry and text style to every Figure 3 HDI bar panel."""
    x = np.arange(len(HDI))
    width = 0.25
    for j, (sex, color) in enumerate((("Male", MALE), ("Female", FEMALE), ("Both", BOTH))):
        values = [
            float(b[(b.pop_code == code) & (b.stratum == age_group) & (b.sex == sex)][metric].iloc[0])
            for code in HDI
        ]
        ax.bar(x + (j - 1) * width, values, width, color=color, label=sex)
    ax.set_xticks(x, HDI_LAB, rotation=45, ha="right", fontsize=5.5)
    ax.set_ylabel("ASIR per 100,000" if metric == "ASIR" else
                  "ASMR per 100,000" if metric == "ASMR" else "Mortality:incidence")
    ax.grid(axis="y", alpha=0.35)
    ax.set_ylim(bottom=0)
    ax.legend(fontsize=5.5, loc=legend_loc, title=age_group, title_fontsize=5.5)


def draw_composite_figure3(b, stem):
    """Render Figure 3 on one eight-panel canvas so all columns align."""
    use_style()
    b = b.copy()
    b["pop_code"] = b.pop_code.astype(str)
    fig, axes = figure_grid(4, 2, width=WIDE, ratio=1.64,
                            gridspec_kw={"width_ratios": [1.0, 1.0]})
    draw_age_specific_panel(axes[0, 0], b)
    draw_regional_panel(axes[0, 1], b)
    for ax, metric, age_group in (
        (axes[1, 0], "ASIR", "0-39"),
        (axes[1, 1], "ASIR", "40+"),
        (axes[2, 0], "ASMR", "0-39"),
        (axes[2, 1], "ASMR", "40+"),
        (axes[3, 0], "MIR", "0-39"),
        (axes[3, 1], "MIR", "40+"),
    ):
        draw_hdi_bars(ax, b, metric, age_group)
    panel_labels(axes)
    fig.suptitle("Thyroid cancer burden by age group (0–39 vs ≥40 years), GLOBOCAN 2024",
                 fontsize=10, fontweight="bold")
    fig.canvas.draw()
    save_fig(fig, stem)


def draw_world_maps(d, stem):
    """Draw the shared 1x2 country ASIR/ASMR map. `d` needs iso3, ASIR, ASMR."""
    if not GEOJSON.exists():
        raise FileNotFoundError(f"missing map geometry: {GEOJSON}")
    geo = json.loads(GEOJSON.read_text())
    fig, axes = figure_grid(1, 2, width=WIDE, ratio=.43)
    for ax, metric in zip(axes, ["ASIR", "ASMR"]):
        v = d[["iso3", metric]].dropna(subset=["iso3"]).drop_duplicates("iso3")
        values = dict(zip(v.iso3, pd.to_numeric(v[metric], errors="coerce")))
        finite = pd.Series(list(values.values())).replace([np.inf, -np.inf], np.nan).dropna()
        vmax = float(finite.quantile(.98)) if len(finite) else 1.0
        vmax = max(vmax, float(finite.max()) if len(finite) else 1.0)
        norm = Normalize(0, vmax)
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
        pc = PatchCollection(patches, cmap="viridis", norm=norm, linewidth=.18, edgecolor="white")
        pc.set_facecolor([plt.get_cmap("viridis")(norm(x)) if np.isfinite(x) else MISSING for x in colors])
        pc.set_array(np.array([x if np.isfinite(x) else 0 for x in colors]))
        ax.add_collection(pc)
        sm = mpl.cm.ScalarMappable(norm=norm, cmap="viridis"); sm.set_array([])
        cb = fig.colorbar(sm, ax=ax, fraction=.035, pad=.015)
        cb.set_label(f"{metric} per 100,000")
        ax.set_xlim(-180, 180); ax.set_ylim(-60, 90); ax.set_aspect("equal")
        ax.set_xticks([]); ax.set_yticks([]); ax.set_frame_on(False)
        ax.set_xlabel("Longitude (°)"); ax.set_ylabel("Latitude (°)")
    fig.legend(handles=[Patch(facecolor=MISSING, edgecolor="none", label="No country value")],
               loc="lower center", ncol=1, fontsize=7, bbox_to_anchor=(.5, -.01))
    panel_labels(axes)
    save_fig(fig, stem)


def main():
    use_style()
    b = read("caya039_burden_by_population_age_sex.csv")
    ordl = read("caya039_sex_and_adult_comparisons.csv")
    corr = read("caya039_hdi_correlations.csv")
    age = read("caya039_ageband_contributions.csv")
    b["pop_code"] = b.pop_code.astype(str)

    # ---------------- main result figure (Figure 3a) ----------------
    fig, axes = figure_grid(2, 2, width=WIDE, ratio=0.82,
                            gridspec_kw={"width_ratios": [1.0, 1.0]})
    world = b[(b.pop_code == "900") & b.stratum.isin(BANDS)]
    draw_age_specific_panel(axes[0, 0], b)
    draw_regional_panel(axes[0, 1], b)
    draw_hdi_bars(axes[1, 0], b, "ASIR", "0-39", legend_loc="upper right")
    draw_hdi_bars(axes[1, 1], b, "ASIR", "40+", legend_loc="upper right")
    panel_labels(axes)
    fig.suptitle("Thyroid cancer incidence by age group (0–39 vs ≥40 years), GLOBOCAN 2024",
                 fontsize=10, fontweight="bold")
    fig.canvas.draw()
    widths = [a.get_position().width * fig.get_figwidth() for a in axes[1]]
    assert abs(widths[0] - widths[1]) < 1e-8, widths
    save_fig(fig, OUT / "Figure3a_caya039_result_main")

    # ---------------- HDI associations (Figure 4b) ----------------
    fig, axes = figure_grid(2, 3, width=WIDE, ratio=0.70)
    metrics = [("ASIR", "ASIR per 100,000"), ("ASMR", "ASMR per 100,000"), ("MIR", "Mortality:incidence")]
    for r, st in enumerate(["0-39", "40+"]):
        d = b[b.is_country & (b.stratum == st) & (b.sex == "Both")]
        for c, (metric, ylab) in enumerate(metrics):
            ax = axes[r, c]
            q = d[["hdi", metric]].replace([np.inf, -np.inf], np.nan).dropna()
            ax.scatter(q.hdi, q[metric], s=13, color=PALETTE["blue"], alpha=.72, linewidth=.25, edgecolor="white")
            ax.set_xlabel("HDI"); ax.set_ylabel(ylab)
            z = corr[(corr.stratum == st) & (corr.sex == "Both") & (corr.metric == metric) & (corr.scope == "primary")]
            if len(z):
                z = z.iloc[0]
                ax.text(.97, .95, f"ρ={z.rho:.2f}; n={int(z.n)}\nFDR p={z.p_fdr:.3g}",
                        transform=ax.transAxes, ha="right", va="top", fontsize=6,
                        bbox=dict(facecolor="white", edgecolor="none", alpha=.8, pad=1.5))
    panel_labels(axes, labels=["(c)", "(d)", "(e)", "(f)", "(g)", "(h)"])
    save_fig(fig, OUT / "Figure4b_caya039_hdi_associations")

    # ---------------- world maps (Figure 4a) ----------------
    d = b[b.is_country & (b.stratum == "0-39") & (b.sex == "Both")]
    draw_world_maps(d, OUT / "Figure4a_caya039_world_maps")

    # ---------------- age band patterns (auxiliary) ----------------
    fig, axes = figure_grid(1, 2, width=WIDE, ratio=.46)
    for sex, color, marker in (("Female", FEMALE, "o"), ("Male", MALE, "s")):
        q = world[world.sex == sex].set_index("stratum").reindex(BANDS)
        axes[0].plot(BANDS, q.ASIR.values, marker=marker, ms=3, color=color, label=sex)
    axes[0].set_xlabel("Age group (years)"); axes[0].set_ylabel("ASIR per 100,000")
    axes[0].tick_params(axis="x", rotation=45); axes[0].legend(fontsize=6)
    c = age[(age.pop_code == "900") & age.sex.isin(["Female", "Male"])]
    denom = float(b[(b.pop_code == "900") & (b.stratum == "0-39") & (b.sex == "Both")].incidence_cases.iloc[0])
    vals = [float(c[(c.sex == s)].incidence_cases.sum() / denom * 100) for s in ["Female", "Male"]]
    axes[1].bar(["Young (0–39)"], [sum(vals)], color="#E8E8E8", edgecolor="none", label="Total")
    axes[1].bar(["Young (0–39)"], [vals[0]], color=FEMALE, label="Female")
    axes[1].bar(["Young (0–39)"], [vals[1]], bottom=[vals[0]], color=MALE, label="Male")
    axes[1].set_ylim(0, 100); axes[1].set_ylabel("Share of world 0–39 cases (%)")
    axes[1].legend(fontsize=6, loc="upper right")
    panel_labels(axes)
    save_fig(fig, OUT / "caya039_ageband_patterns")

    # ---------------- mortality adult comparison (Figure 3b) ----------------
    fig, axes = figure_grid(2, 2, width=WIDE, ratio=.82,
                            gridspec_kw={"width_ratios": [1.0, 1.0]})
    for r, metric in enumerate(["ASMR", "MIR"]):
        for c, st in enumerate(["0-39", "40+"]):
            # Keep panel (f) at upper left; the other panels use upper right
            # to avoid covering the plotted bars.
            legend_loc = "upper left" if (r, c) == (0, 1) else "upper right"
            draw_hdi_bars(axes[r, c], b, metric, st, legend_loc=legend_loc)
    panel_labels(axes, labels=["(e)", "(f)", "(g)", "(h)"])
    save_fig(fig, OUT / "Figure3b_caya039_mortality_adult_comparison")
    print("Wrote CAYA039 constituent panels to", OUT)


if __name__ == "__main__":
    main()
