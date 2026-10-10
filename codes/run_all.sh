#!/usr/bin/env bash
# Reproduce every delivered figure and table in Final_res.
set -euo pipefail
cd "$(dirname "$0")"

echo "[1/6] Figures 3 & 4 constituent panels"
python3 make_caya039_figures.py
echo "[2/6] Figure 1 panels d-e (all-ages world maps)"
python3 make_figure1b_world_maps_allages.py
echo "[3/6] Figure 1 composite"
python3 make_figure1.py
echo "[4/6] Figure 2"
python3 make_figure2.py
echo "[5/6] Supplementary Figures 1-2"
python3 make_supp_figures.py
echo "[6/6] Figures 3 & 4 composites and all tables"
python3 make_figure3.py
python3 make_figure4.py
python3 make_tables.py
echo "Done. Outputs in ../figures and ../tables"
