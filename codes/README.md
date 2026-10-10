# Final_res/codes — figure and table generation

Every delivered figure and table in `../figures/` and `../tables/` is reproduced
by the scripts in this folder from the bundled inputs in `./data/`. No network
access and no values outside `./data/` are required.

Run everything:

```bash
cd Final_res/codes
bash run_all.sh
```

| Deliverable | Script | Output |
|---|---|---|
| Figure 1 (a–c top-25 + d–e world maps) | `make_figure1.py` | `../figures/Figure1.{png,pdf,svg}` |
| Figure 1 panels d–e (all-ages maps) | `make_figure1b_world_maps_allages.py` | `../figures/original/Figure1b_world_maps_allages.*` |
| Figure 2 (projections 2024–2050) | `make_figure2.py` | `../figures/Figure2.{png,pdf,svg}` |
| Figure 3 (result main + mortality comparison) | `make_figure3.py` | `../figures/Figure3.{png,pdf}` |
| Figure 4 (world maps + HDI associations) | `make_figure4.py` | `../figures/Figure4.{png,pdf}` |
| Figure 3/4 constituent panels | `make_caya039_figures.py` | `../figures/original/Figure3a/3b/4a/4b_*` |
| Supplementary Figure 1 (age-specific ASIR) | `make_supp_figures.py` | `../figures/Supp_Figure1.*` |
| Supplementary Figure 2 (HDI projections) | `make_supp_figures.py` | `../figures/Supp_Figure2.*` |
| All five tables | `make_tables.py` | `../tables/*.csv` |

Helpers: `stack_figures.py` (vertical concatenation for Figures 3 and 4),
`figstyle.py` (house matplotlib style).

`original/` holds each source panel exactly as produced by its own generator,
so the composite Figures 3 and 4 are faithful stacks of reviewed originals.

## Layout of Figure 1

Author-specified composition: top row (a) ASIR, (b) ASMR, (c) MIR top-25
diverging country panels; bottom row (d) all-ages ASIR and (e) all-ages ASMR
world maps. Female bars extend left (burgundy), male bars right (blue).

## Inputs (`./data/`)

- `globocan_allages_2024.json` — GLOBOCAN 2024 all-ages C73 counts/rates (today endpoint)
- `caya039_allages_2024.json` — same, for the map panels
- `populations_metadata_2024.json` — population labels, HDI, area codes
- `caya039_metadata.csv` — population code → ISO3 / is_country
- `caya039_burden_by_population_age_sex.csv` — CAYA 0-39 / 40+ verified table
- `caya039_hdi_correlations.csv`, `caya039_sex_and_adult_comparisons.csv`,
  `caya039_ageband_contributions.csv` — CAYA analysis outputs
- `figure2_baseline_2024.csv`, `figure2_all_scenarios_2024.csv` — Tomorrow projections
- `s1_age_asir_2024.json`, `supp_figure_s3_data.csv` — supplementary figure inputs
- `countries.geojson` — Natural Earth country polygons

## Verification performed

- The five tables reproduce byte-identically to the reviewed versions
  (`diff` clean).
- The regenerated Figure 1b map, Figure 2, Supp Figure 1, Supp Figure 2 and the
  four CAYA constituent panels are pixel-identical (max channel difference 0)
  to the reviewed originals.

## Provenance

These scripts adapt the project's original generators:
`New/code/make_figure2_projections.py`,
`New/code/make_supplementary_figures_mainstyle.py`,
`2024GLOBOCAN/make_supplementary_tables.py`,
`manuscript_2024/reproduce_tables.py`,
`CAYA039/code/make_caya039_figures.py`,
`CAYA039/code/make_caya039_suppl_tables.py`,
`CAYA039/code/make_allages_world_maps.py`,
with paths retargeted to the bundled `./data` so the bundle is self-contained.
