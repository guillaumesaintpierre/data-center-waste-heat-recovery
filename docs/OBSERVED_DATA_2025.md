# Historical electricity prices and meteorological observations (2025)

## Purpose and status

The source code supports two verified external inputs: DK2 day-ahead wholesale prices and Copenhagen-region DMI station temperature. **The reference benchmark is synthetic.** A second, explicitly conditional study was executed with downloaded 2025 observations on 19 November 2026. It used 8,760 DK2 hourly market prices and a 8,760-hour DMI weather series, including 13 flagged interpolations (0.15%). Source files, checksums and results must be committed from the data-collection machine before other readers can reproduce the exact historical run offline. Downloading the sources again requires internet access.

## Sources

1. **Energinet / Energi Data Service**: `Elspotprices` (through the market's 1 October 2025 transition) and `DayAheadPrices` afterwards. Spot prices are **EUR/MWh electrical**, not the retail cost faced by a data center and not the effective tariff of a heat-pump owner. Credit: Energinet, https://www.energidataservice.dk/, CC BY 4.0.
2. **Danish Meteorological Institute (DMI)**: `metObs` station `06180` (Copenhagen Airport/Kastrup), parameter `temp_mean_past1h` (previous hour's mean 2-m air temperature in °C). Credit: DMI, https://opendataapi.dmi.dk/, CC BY 4.0. Station data represent the airport rather than a specified heat-network site; station availability and quality must be checked for the chosen year. **DMI explicitly warns that metObs raw observations are not quality-controlled.** The importer checks physical bounds and hour-to-hour jumps but this is NOT equivalent to DMI quality-controlled climate data.

Data endpoint specifications: https://www.energidataservice.dk/guides/api-guides and https://www.dmi.dk/friedata/dokumentation/meteorological-observation-api.

## Technical procedure

**Alignment**: every resulting timestamp denotes the *start* of its 1-hour UTC interval. Prices through 30 September 2025 (Danish market time) are hourly; from 1 October local time, prices are quarter-hourly. The transition is 2025-09-30 22:00 UTC. Hourly market prices from the new regime are arithmetic averages of **exactly four** observed quarter-hour prices (not imputed, no dropped quarters). Negative prices are retained. Any incomplete market hour is rejected.

`temp_mean_past1h` is reported at the *end* of its averaging period, so it is shifted back one hour to align with the market. The station record's `observed` property must represent the actual hour-ending timestamp. Weather series must contain the full year's hourly UTC grid. If a very small number of observations are missing, the fetcher allows **at most 1% missing weather hours and no uninterrupted gap longer than 3 hours**. The importer requests extra actual station observations immediately before and after the calendar year to handle year-boundary gaps with **two-sided interpolation only**. Missing hours are filled linearly in UTC and labelled `quality=interpolated` in the output CSV. An unbracketed boundary, a longer gap, or excessive missing data triggers an exception; no extrapolation or synthetic substitution. Temperatures outside -50 to 50 °C or jumps above 12 °C in one hour also trigger a manual-review error; these checks are heuristic and do not prove measurement quality. These are *data-cleaning choices*, not measurements.

Data are downloaded *before* a simulation can run. Both csv files contain exactly 8,760 rows for 2025; a leap year would have 8,784. Provider URLs, retrieval timestamp, a count of interpolated temperatures, and SHA-256 fingerprints are stored in `data/observed/observed_2025.metadata.json`. Only after validation does the script write the data CSVs. With incomplete inputs it fails and tells the user why.

## Reproduction from repository root

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Requires public internet access to Energinet and DMI:
python scripts/fetch_real_inputs.py --year 2025

# Run with two observed covariates and otherwise hypothetical technical inputs:
python run.py --config config.real-2025.json --out results/real-2025
python scripts/plot_observed_inputs.py --year 2025
python scripts/compare_runs.py --reference results/summary.json --observed results/real-2025/summary.json

# Reproducible baseline and independent software tests:
python run.py --config config.json --out results
PYTHONPATH=src python -m pytest -q
```

For public reproducibility, commit the downloaded `data/observed/*.csv` and the metadata file **only after reviewing the files, quality flags and the recorded provider attribution**. The two CSVs are small; the documented CC BY 4.0 attribution must be preserved. Never commit API credentials or large raw API dumps.

## Executed 2025 run (observed boundary conditions; other assumptions unchanged)

| Result | Synthetic benchmark | Observed 2025 prices and DMI temperatures |
|---|---:|---:|
| Modelled annual heat demand | 7,301.522 MWh | 6,466.512 MWh |
| Useful heat delivered | 5,047.711 MWh | 4,860.612 MWh |
| Mean running COP | 4.005 | 4.064 |
| Modelled demand coverage | 69.1% | 75.2% |
| Electricity cost | EUR 125,570.60/year | EUR 114,568.24/year |
| NPV under assumed gas-boiler counterfactual | EUR 1,318,960 | EUR 1,300,896 |

The 2025 run used 8,747 directly observed DMI hours and 13 explicitly interpolated hours. The prices cover 8,760 hourly UTC intervals, with quarter-hour aggregation after the market transition. Source temperatures, IT load and district heating demand are **not observed**. The NPV represents an assumed system-wide savings calculation, not the revenues of a heat-sale investor. No manufacturer performance map or bank financing model has been validated.

## What actually becomes data-driven?

- Directly observed: market prices in DK2 and weather-station temperature, subject to explicitly recorded interpolation flags.
- Weather-derived but **modelled**: district heat demand, weather-compensated district-supply temperature and an assumed coolant-temperature relation. These are **not measured** demand or heat-pump inlet temperatures.
- Still hypothetical: IT load profile, PUE, capture fraction, COP efficiency, system rating, network losses, capital costs, tariffs, gas counterfactual, operational carbon factors and investment return.

The central claim is therefore *historical boundary-condition sensitivity*, **not** plant validation or real-world bankability.

## Assumptions requiring stronger validation

- Hourly market wholesale prices exclude taxes, network charges and contract risk; substituting them directly as the project's electricity tariff is a screening approximation.
- DMI airport temperature may differ from conditions at a specific data center or heat district; the raw metObs API is *not* quality-controlled. A later phase should cross-check DMI climateData quality-controlled hourly means where available.
- Weather-dependent heat demand is a simplified degree-day regression with uncalibrated coefficients.
- Source-side water temperature is based on a weak assumed correlation with ambient air, not a measured data-center cooling loop.
- The financial comparison is an avoided-gas cost for the thermal network, **not** an investor heat-sale revenue contract.
