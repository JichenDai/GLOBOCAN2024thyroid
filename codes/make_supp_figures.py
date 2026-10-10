#!/usr/bin/env python3
"""Supplementary Figures 1 and 2, GLOBOCAN 2024 thyroid cancer.

    Supp_Figure1  age-specific ASIR curves (world male/female, Eastern Asia female)
    Supp_Figure2  projected cases and deaths 2024-2050 by HDI tier

Adapted from New/code/make_supplementary_figures_mainstyle.py (functions
make_s1 and make_s3) so it runs from this bundle: data are read from ./data and
outputs are written to ../figures/ under the final delivery names.
"""
from __future__ import annotations

from pathlib import Path

import json, csv

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans', 'sans-serif'],
    'svg.fonttype': 'none',
    'pdf.fonttype': 42,
    'axes.spines.right': False,
    'axes.spines.top': False,
    'axes.linewidth': 0.8,
    'axes.edgecolor': '#333333',
    'axes.labelcolor': '#333333',
    'xtick.color': '#333333',
    'ytick.color': '#333333',
    'legend.frameon': False,
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'savefig.facecolor': 'white',
})

CF = (150 / 255, 30 / 255, 30 / 255)
CM = (70 / 255, 120 / 255, 165 / 255)
HDI_COLORS = {'Low HDI': '#B4C0E4', 'Medium HDI': '#7FA8D9',
              'High HDI': '#3775BA', 'Very high HDI': '#1F4E79'}

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUT = HERE.parent / "figures"


def export_pub(fig, outpath, dpi=600):
    fig.savefig(f"{outpath}.png", dpi=dpi, bbox_inches='tight')
    fig.savefig(f"{outpath}.pdf", bbox_inches='tight')
    fig.savefig(f"{outpath}.svg", bbox_inches='tight')


def make_s1():
    age = json.loads((DATA / "s1_age_asir_2024.json").read_text())
    x = np.arange(18)
    labels = [a['age_band'] for a in age['M']]
    fig, ax = plt.subplots(figsize=(9, 4.5), constrained_layout=True)
    ax.plot(x, [a['asr'] if a['asr'] is not None else np.nan for a in age['M']],
            marker='o', ms=3.5, color=CM, lw=1.6, label='World, male')
    ax.plot(x, [a['asr'] if a['asr'] is not None else np.nan for a in age['F']],
            marker='o', ms=3.5, color=CF, lw=1.6, label='World, female')
    ax.plot(x, [a['asr'] if a['asr'] is not None else np.nan for a in age['EA_F']],
            marker='s', ms=3.5, color='#7FA8D9', lw=1.6, ls='--', label='Eastern Asia, female')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=90, fontsize=6.5)
    ax.set_xlabel('Age group (years)', fontsize=9)
    ax.set_ylabel('ASIR per 100,000', fontsize=9)
    ax.set_title('Supplementary Figure S1. Age-specific thyroid cancer incidence, GLOBOCAN 2024',
                 fontsize=11, fontweight='bold', loc='left')
    ax.legend(fontsize=8, loc='upper left')
    ax.grid(alpha=0.3, linestyle='--')
    export_pub(fig, OUT / "Supp_Figure1")
    plt.close(fig)


def make_s3():
    rows = list(csv.DictReader((DATA / "supp_figure_s3_data.csv").open()))
    proj = {}
    for r in rows:
        proj.setdefault((r['hdi_label'], r['type']), []).append(
            (int(r['year']), float(r['predicted_count_apc0'])))

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), constrained_layout=True)
    for ai, tname in enumerate(['cases', 'deaths']):
        ax = axes[ai]
        for label in ['Low HDI', 'Medium HDI', 'High HDI', 'Very high HDI']:
            pts = sorted(proj.get((label, tname), []))
            if not pts:
                continue
            yrs = [p[0] for p in pts]
            vals = [p[1] for p in pts]
            ax.plot(yrs, vals, '-o', color=HDI_COLORS[label], lw=1.8, ms=4, label=label)
            base = dict(pts)
            for apc in (2, -2):
                env = [base[y] * (1 + apc / 100) ** (y - 2024) for y in yrs]
                ax.plot(yrs, env, '--', color=HDI_COLORS[label], lw=0.9, alpha=0.45)
        ax.set_xlabel('Year', fontsize=9)
        ax.set_ylabel(f'Projected {tname}', fontsize=9)
        ax.set_title(f"{'A' if ai == 0 else 'B'}. Projected {tname} by HDI tier",
                     fontsize=10, fontweight='bold', loc='left')
        ax.legend(fontsize=7, loc='upper left')
        ax.grid(alpha=0.3, linestyle='--')
        ax.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
    fig.suptitle('Supplementary Figure S3. Projected thyroid cancer burden 2024-2050 by HDI tier, GLOBOCAN 2024',
                 fontsize=12, fontweight='bold')
    export_pub(fig, OUT / "Supp_Figure2")
    plt.close(fig)


if __name__ == '__main__':
    make_s1()
    make_s3()
    print("Supplementary figures written to", OUT)
