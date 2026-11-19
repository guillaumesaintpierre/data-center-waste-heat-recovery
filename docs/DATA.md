> **2025 actual electricity + DMI station weather import:** See [OBSERVED_DATA_2025.md](OBSERVED_DATA_2025.md). The older price-only importer described here is retained for standalone checks.

# Data and timestamp protocol

The included example (`config.json`) uses 8,760 hourly UTC timestamps in 2025, with deterministic synthetic boundary conditions. All numbers in `results/` come from that example. This is the only data policy that can be independently reproduced with no network connection.

## Optional observed Danish electricity prices

Energinet's `DayAheadPrices` dataset publishes day-ahead prices for Danish bidding zones. Since 1 October 2025, quarter-hourly observations must be aggregated for an hourly simulation. The importer takes the arithmetic mean of **four** equal-duration 15-minute prices to obtain EUR/MWh for that UTC hour; it does not interpolate missing records. Timezone conversion is performed in UTC to avoid daylight-saving ambiguity.

To download one period (requires internet, availability and provider API continuity):

```bash
python scripts/fetch_danish_prices.py --start 2026-03-01 --end 2026-04-01 \
  --area DK2 --out data/real_prices_march_2026.csv
```

This downloads the original provider records **and records the exact request URL** in a sibling `.metadata.json`. The routine has not been executed in this packaged study; there are no claimed downloaded historical observations.

The main simulation requires complete price coverage for its chosen time index. For a complete 2026 run, use a full year of provider observations **after the period is available**; do not silently fill gaps. Change `time.year` in `config.json` to 2026, and `profiles.observed_electricity_csv` to the full-year file path. The physical IT load, temperature and demand remain synthetic unless separately measured and imported.

**Do not run a single-month file against a full-year scenario**: it correctly raises a coverage error. To combine monthly downloads, concatenate and sort the original records, check duplication, then set the complete-year CSV path.

## Data dictionary (selected)

| Field | Unit | Meaning |
|---|---|---|
| `it_mw` | MW electric | Server-side IT electrical input |
| `facility_electricity_mw_ref` | MW electric | IT input multiplied by assumed PUE, descriptive only |
| `available_source_heat_mw` | MW thermal | Capturable thermal energy in IT cooling loop |
| `source_heat_used_mw` | MW thermal | Actual evaporator heat taken from IT loop |
| `compressor_electricity_mw` | MW electric | Heat pump compressor input |
| `condenser_heat_mw` | MW thermal | Evaporator heat + compressor input |
| `pumping_electricity_mw` | MW electric | Auxiliary pumping assumption, extra to compressor input |
| `network_loss_mw` | MW thermal | Condenser energy not reaching customers |
| `district_heat_delivered_mw` | MW thermal | Useful heat displaced at the boiler boundary |
| `district_demand_mw` | MW thermal | Synthetic district customer heat demand |
| `electricity_eur_mwh` | EUR/MWh electric | Price for purchased electrical energy |
| `hourly_net_savings_eur` | EUR | Fuel purchase avoided minus added electricity and variable O&M (fixed O&M not included) |

An hourly row corresponds to one UTC hour; power in MW therefore equals energy in MWh over the 1-hour interval. Changes to simulation time step must be paired with a time-series frequency change; the bundled generator is hourly.
