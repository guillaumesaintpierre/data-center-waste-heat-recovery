# Verification and validation strategy

A convincing numerical result needs more than an attractive plot. I separate three questions:

**Verification:** Does the code solve the stated mathematical model consistently?

**Sensitivity:** Which parameter changes alter its results and by how much?

**Validation:** Does the mathematical model represent a physical installation? **Not yet.** No measured plant or heat pump OEM curve is supplied, so physical validation cannot honestly be claimed.

## Tests and numerical checks

Run `PYTHONPATH=src pytest -q`. The automated test suite covers:

- Carnot upper bound and temperature-lift monotonicity of COP.
- Source-limited and rated-capacity-limited condenser output.
- `Q_source + W_comp = Q_condenser` at every time step.
- `Q_condenser = Q_useful + Q_network_loss` at every time step.
- No heat exported beyond the simultaneous district demand, source heat or installed rating.
- Zero demand, zero IT load and price-driven dispatch shutdown.
- Correct treatment of negative electricity prices.
- Deterministic profile generation and parameter-space exploration.
- Analytical two-year discounted cash-flow check.
- Strict rejection of missing/duplicate market-price hours, and exact four-quarter-hour aggregation.
- Comparative scenarios to ensure lower supply temperatures improve COP.
- Discrete capacity sizing and a calibration check that the reference size reproduces the reference CAPEX.

## Analytical one-hour hand check

For a hypothetical fixed source 30 C, district output 65 C, source-side pinch 4 K, condenser pinch 3 K, and second-law efficiency 0.5:

- Evaporation temperature is 26 C = 299.15 K.
- Condensing temperature is 68 C = 341.15 K.
- Carnot heating COP is 341.15/(341.15-299.15) = **8.1226**.
- Estimated heating COP is **4.0613**.
- If source heat available is 0.600 MW, then source-limited condenser heat is 0.600 x COP/(COP-1) = **0.79599 MW**.
- Compressor electricity is **0.19599 MW**, such that 0.600 + 0.19599 = 0.79599 MW.

These rounded hand values can be checked independently against `physics.py`.

## Important non-intuitive outcome

A **higher COP can produce a smaller condenser thermal output when source-limited**, because a more efficient heat pump requires less compressor electricity per unit of source heat. For fixed evaporator heat, `Q_cond = Q_source * COP/(COP-1)`. Thus, quantity delivered and economic performance should be judged separately.

## What is NOT validated

- No actual coolant temperatures, pipe geometry, part-load performance, thermal storage or heat-demand measurements.
- No measured environmental electricity marginal intensity, district heat cost, installed costs or heat purchase agreements.
- No claim of metrology-grade PUE or ERF compliance.
- No lifecycle or market-dispatch simulation.

**Recommended field validation:** obtain a year of IT electricity, coolant supply/return, hourly district demand and heat-pump manufacturer performance points, then calibrate physical assumptions on one interval and test on a held-out interval.

## Historical-data controls (added)

The 2025 importer is tested using *constructed fixtures*, not copied or claimed 2025 observations: settlement switch at local midnight (22:00 UTC on 30 September), the mean of four quarter-hour spot prices, preservation of negative prices, rejection of missing intervals and duplicate market timestamps, station ID/parameter checks, preceding-hour DMI alignment, and explicit weather imputation flags. The 2025 provider retrieval was completed on 19 November 2026 and produced 8,760 hourly DK2 prices and 8,760 hourly Kastrup temperature values, with 13 flagged weather interpolations. Dataset source URLs, quality statistics and SHA-256 hashes are recorded in `data/observed/observed_2025.metadata.json`. The observed-boundary-condition run is in `results/real-2025/`; numerical agreement is not a substitute for validating heat production against measurements. The manuscript has been updated in `report/technical_report.md` and `report/technical_report.pdf`.
