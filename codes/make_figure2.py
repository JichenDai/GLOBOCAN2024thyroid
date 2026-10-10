#!/usr/bin/env python3
"""Figure 2 -- projected thyroid cancer burden worldwide, 2024-2050, GLOBOCAN 2024.

Six panels: cases (top row) and deaths (bottom row) for both sexes (left),
female (middle) and male (right).  Solid = constant-rate (APC 0) baseline from
the GLOBOCAN Tomorrow endpoint; dashed = annual-percent-change sensitivity
scenarios at -3..+3 %/yr computed locally by compounding.

Adapted from New/code/make_figure2_projections.py: runs offline from the
bundled audited baseline (./data/figure2_baseline_2024.csv) by default, writes
../figures/Figure2.{png,pdf,svg}.  Pass --online to re-fetch from the API.
"""
import urllib.request, json, csv, time, argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans', 'sans-serif'], 'svg.fonttype': 'none', 'pdf.fonttype': 42})

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUT = HERE.parent / "figures"
BASE24 = "https://gco.iarc.who.int/gateway_prod/api/globocan/v3/2024"
CANCER = 32
UA = "globocan-2024-thyroid-repro/0.1"
SCENARIOS = [-3, -2, -1, 0, 1, 2, 3]
parser = argparse.ArgumentParser()
parser.add_argument('--online', action='store_true',
                    help='re-fetch the constant-rate baseline from the GLOBOCAN Tomorrow API')
ARGS = parser.parse_args()


def fetch(typ, sex):
    url = (f"{BASE24}/data/prediction/{typ}/{sex}/900/{CANCER}/"
           "?prediction_annual=1&ages_group=0_17")
    req = urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': UA})
    t0 = time.time()
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                d = json.loads(r.read().decode())
            return (typ, sex, d.get('dataset', []), f"{time.time()-t0:.1f}s")
        except Exception as e:
            err = repr(e)[:60]
            if attempt < 4:
                time.sleep(3 * (attempt + 1))
    return (typ, sex, None, f"ERR {err}")


tomorrow = {}
baseline_path = DATA / "figure2_baseline_2024.csv"
if not ARGS.online:
    with baseline_path.open(newline='') as f:
        saved = list(csv.DictReader(f))
    for r in saved:
        key = (int(r['type']), int(r['sex']))
        row = dict(r)
        for k in ('year', 'cases_pred', 'cases_base', 'pop'):
            row[k] = int(float(row[k]))
        tomorrow.setdefault(key, {})[row['year']] = row
    expected = {(t, s) for t in (0, 1) for s in (0, 1, 2)}
    if set(tomorrow) != expected:
        raise RuntimeError(f"Offline baseline missing combinations: {sorted(expected - set(tomorrow))}")
    years_check = {tuple(sorted(v)) for v in tomorrow.values()}
    if len(years_check) != 1 or not next(iter(years_check)):
        raise RuntimeError("Offline baseline year grids are incomplete or inconsistent")
    print(f"Loaded offline baseline: {baseline_path} ({len(saved)} rows)")
else:
    print("Fetching Tomorrow constant-rate projections 2024-2050 ...")
    t0 = time.time()
    jobs = [(t, s) for t in (0, 1) for s in (0, 1, 2)]
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(fetch, *j): j for j in jobs}
        for f in as_completed(futs):
            typ, sex, ds, info = f.result()
            print(f"  type={typ} sex={sex} -> {info}")
            if ds:
                tomorrow[(typ, sex)] = {r['year']: r for r in ds}
    expected = {(t, s) for t in (0, 1) for s in (0, 1, 2)}
    if set(tomorrow) != expected:
        raise RuntimeError(f"API projection missing combinations: {sorted(expected - set(tomorrow))}")
    print(f"Total fetch time: {time.time()-t0:.1f}s")

rows_src = []
for (typ, sex), ymap in tomorrow.items():
    for y, r in ymap.items():
        rows_src.append({'type': typ, 'sex': sex, 'year': y,
                         'cases_pred': r.get('cases_pred'), 'cases_base': r.get('cases_base'),
                         'pop': r.get('pop'), 'percent': r.get('percent'),
                         'population_change': r.get('population', {}).get('change'),
                         'population_percent': r.get('population', {}).get('percent'),
                         'risk_change': r.get('risk', {}).get('change'),
                         'risk_percent': r.get('risk', {}).get('percent'),
                         'APC': r.get('APC')})
rows_src.sort(key=lambda r: (r['type'], r['sex'], r['year']))
with baseline_path.open("w", newline='') as f:
    w = csv.DictWriter(f, fieldnames=['type', 'sex', 'year', 'cases_pred', 'cases_base', 'pop',
                                      'percent', 'population_change', 'population_percent',
                                      'risk_change', 'risk_percent', 'APC'])
    w.writeheader(); w.writerows(rows_src)
print(f"Saved {baseline_path.name} ({len(rows_src)} rows)")

years = sorted(tomorrow[(0, 0)].keys())
t_base = years[0]


def scenario_series(typ, sex, apc):
    base = tomorrow[(typ, sex)]
    out = {}
    for y in years:
        r = base[y]
        out[y] = r['cases_pred'] if apc == 0 else r['cases_pred'] * (1 + apc / 100) ** (y - t_base)
    return out


sexes_name = {0: "Both", 1: "Male", 2: "Female"}
typ_name = {0: "Incidence (cases)", 1: "Mortality (deaths)"}

rows_all = []
for typ in (0, 1):
    for sex in (0, 1, 2):
        for apc in SCENARIOS:
            for y, v in scenario_series(typ, sex, apc).items():
                rows_all.append({'type': typ, 'sex': sex, 'type_name': typ_name[typ],
                                 'sex_name': sexes_name[sex], 'apc_pct': apc,
                                 'year': y, 'predicted_count': round(v)})
with (DATA / "figure2_all_scenarios_2024.csv").open("w", newline='') as f:
    w = csv.DictWriter(f, fieldnames=['type', 'sex', 'type_name', 'sex_name', 'apc_pct', 'year', 'predicted_count'])
    w.writeheader(); w.writerows(rows_all)
print(f"Saved figure2_all_scenarios_2024.csv ({len(rows_all)} rows)")

series_of = {(typ, sex, apc): scenario_series(typ, sex, apc)
             for typ in (0, 1) for sex in (0, 1, 2) for apc in SCENARIOS}

base_2024, base_2050 = series_of[(0, 0, 0)][2024], series_of[(0, 0, 0)][2050]
mort_2024, mort_2050 = series_of[(1, 0, 0)][2024], series_of[(1, 0, 0)][2050]
print(f"\nConstant-rate (APC=0) projection, both sexes:")
print(f"  Cases:  2024={base_2024:,}  -> 2050={base_2050:,}  ({(base_2050/base_2024-1)*100:+.2f}%)")
print(f"  Deaths: 2024={mort_2024:,}  -> 2050={mort_2050:,}  ({(mort_2050/mort_2024-1)*100:+.2f}%)")

fig, axes = plt.subplots(2, 3, figsize=(15, 8))
M_F_BOTH = [(0, "Both sexes"), (2, "Female"), (1, "Male")]
TYPE_TITLE = {0: "Cases", 1: "Deaths"}
SCN_COLOR = {-3: '#1a3d6d', -2: '#3b6fb5', -1: '#7d9fd6', 0: '#222', 1: '#e9a3c4', 2: '#d4496e', 3: '#a01a4a'}
SCN_WIDTH = {-3: 1, -2: 1, -1: 1, 0: 2.4, 1: 1, 2: 1, 3: 1}
SCN_ALPHA = {-3: 0.6, -2: 0.7, -1: 0.8, 0: 0.9, 1: 0.8, 2: 0.7, 3: 0.6}

for col, (sex, label) in enumerate(M_F_BOTH):
    for row, typ in enumerate([0, 1]):
        ax = axes[row][col]
        for apc in SCENARIOS:
            vals = [series_of[(typ, sex, apc)][y] for y in years]
            ax.plot(years, vals, '-' if apc == 0 else '--', color=SCN_COLOR[apc],
                    lw=SCN_WIDTH[apc], alpha=SCN_ALPHA[apc],
                    label=f'APC={apc:+d}%' if apc != 0 else 'constant rate')
        ax.set_title(f"{'ABCDEF'[row*3+col]}. {TYPE_TITLE[typ]} ({label})", fontsize=11, fontweight='bold')
        ax.set_xlabel('Year'); ax.set_ylabel(TYPE_TITLE[typ])
        ax.grid(True, alpha=0.3, linestyle='--')
        if row == 0 and col == 0:
            ax.legend(loc='upper left', fontsize=8, ncol=2)
        ax.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))

fig.suptitle('GLOBOCAN 2024 projected thyroid-cancer burden 2024-2050 '
             '(constant rate + APC sensitivity, world)', fontsize=13, fontweight='bold', y=0.99)
fig.tight_layout(rect=[0, 0, 1, 0.97])
fig.savefig(OUT / "Figure2.png", dpi=600, bbox_inches='tight')
fig.savefig(OUT / "Figure2.pdf", bbox_inches='tight')
fig.savefig(OUT / "Figure2.svg", bbox_inches='tight')
plt.close(fig)
print(f"\nSaved {OUT}/Figure2.png (600 dpi) + .pdf + .svg")
