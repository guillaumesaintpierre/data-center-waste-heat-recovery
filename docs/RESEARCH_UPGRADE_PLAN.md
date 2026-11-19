# From screening model to evidence-based feasibility study

**Status:** Research and development plan, 17 November 2026. This document does **not** claim that the proposed extensions have been implemented, validated, or supported by a commercial partner.

## Research question

> Under what technical, contractual and financial conditions can heat recovery from a 1 MW IT data centre deliver bankable low-carbon heat to a Danish district-heating network?

`bankable` is a target of analysis, **not** a claim about the current project. The present repository is an unvalidated technical screening model with synthetic input profiles. Its existing EUR 1.32 million NPV represents *system savings against an assumed gas boiler*, **not** necessarily cash receipts for a heat-recovery project company.

## Proposed research contribution

Separate **physical feasibility**, **system value**, and **investor cash flow**. Estimate the **minimum contracted heat-sale price** needed to meet both project NPV and debt-service constraints under specified heat demand, delivery temperature, data-centre availability, interconnection distance and power prices. Compare three ownership structures, and quantify where each fails.

The proposed result is a **bankability frontier**: axes might be heat purchase price vs. guaranteed annual availability; temperature lift and pipe distance define different curves. Such a figure helps identify technical and commercial trade-offs rather than simply reporting a single positive NPV.

## 1. Evidence to incorporate

| Topic | Source and what it supports | What it does not provide |
|---|---|---|
| Comparable operating installation | Ramboll's Meta/Fjernvarme Fyn project at Odense uses large ammonia heat pumps to deliver heat at about 70–75°C, with approximately 45 MW thermal output [1] | Full equipment quotations, site-hourly loads or a transferable sale tariff |
| Commercial constraints | DTU's 2023 research by Monsalves, Bergaentzlé and Keles finds favorable heat-sale conditions and priority access important in a Danish techno-economic study [2] | Proof that this project's baseline can achieve those terms |
| New investment context | CIP/Thylander/PensionDanmark announced DDC1 at Esbjerg in August 2026, planned as energy-integrated data-centre infrastructure [3] | Operating performance from a completed data centre; it is a development announcement |
| Energy cost data | Energinet's DayAheadPrices/Elspotprices datasets for Danish DK1/DK2 wholesale day-ahead prices [4] | A project's *full delivered electricity tariff*, including grid charges, taxes and contract hedges |
| Weather | Danish Meteorological Institute measured hourly temperature records [5] | Heat demand, unless independently calibrated against demand observations |
| Commercial agreements | Scottish Government guidance on Heat Supply Agreements, outages, heat quality, metering, tariffs and asset ownership [6] | Any specific Danish contract or tariff |
| EU energy-efficiency rules | Directive (EU) 2023/1791 Article 26 and Commission guidance on waste heat and cost-benefit analysis for qualifying data centres [7] | Automatic proof of compliance with Danish implementing rules |
| Reporting boundaries | Delegated Regulation (EU) 2024/1364 on energy reuse and measurement at the data-centre boundary [8] | Permission to call a proxy result a certified Energy Reuse Factor |
| Feasibility structure | EIB/JASPERS guide on district-heating decarbonisation, options analysis and investment preparation [9] | A bank approval or underwriting commitment |
| Programme relevance | ETH MEST case studies, including data-centre electricity flexibility and district-heating heat-pump integration [10] | An ETH endorsement of this individual project |

## 2. Data pipeline and quality controls

**Primary scenario:** A hypothetical facility in Eastern Denmark (price zone **DK2**); do not imply it is an identified operator or that public temperature/price series are measurements from a particular data centre.

1. **Electricity:** fetch DK2 historical observations for a complete calendar year. For 2025, combine **Elspotprices** until 30 September and **DayAheadPrices** from 1 October; the latter moved to 15-minute market-time units. Convert to a single hourly UTC index; check daylight-saving transitions, missing intervals, duplicate delivery hours and DKK/EUR units. Preserve original files, URLs, retrieval dates and checksums. Do not equate spot price to the delivered tariff.
2. **Weather:** obtain DMI's `temp_mean_past1h` at an appropriate station; log station identifier, UTC timestamp, quality issues and missing observations.
3. **District heating demand:** request hourly anonymised district-system load from a utility, or use publicly documented annual totals to calibrate an *explicitly synthetic* degree-day profile. Never label a degree-day estimate as actual district demand.
4. **Source heat:** obtain representative fluid temperature and IT-utilisation intervals; absent permission, retain a sensitivity range and label it assumed. Server cooling architecture (air-cooled vs. direct-liquid-cooled) changes achievable source temperature and hardware.
5. **Heat pump:** calibrate COP and feasible capacity against a public OEM operating map if available, recording operating points, limits, minimum load and defrost/maintenance assumptions. Avoid using a single fixed Carnot-efficiency factor as an empirical performance guarantee.
6. **Costs:** separate vendor quotations, published literature ranges, and assumptions. Record installation, connection pipes, heat exchanger, civil works, pumps, contingencies, insurance, grid charges, O&M, replacements, tax and financing assumptions.

Maintain a `data_dictionary.csv` with fields for unit, source, temporal resolution, original time zone, missing-data treatment, expected range and provenance. Keep observed, assumed and derived inputs visibly distinct.

## 3. Physical model extensions

- **More realistic heat pump:** speed/part-load-dependent COP and maximum output as functions of inlet and outlet temperatures. Retain Carnot as an upper-bound unit test.
- **Cooling integration:** define the baseline data-centre cooling plant (free cooling, chillers), control priority, any genuinely justified cooling-energy savings, and protection of data-centre reliability.
- **Hydraulics and distance:** heat-transfer line temperature losses, pipe diameter, pressure drop, circulation power and installed pipe cost as functions of distance. Distance can make an otherwise favorable source infeasible.
- **District heating temperature:** supply and return temperatures by season, heat-exchanger pinch, and whether low-temperature return-line injection is possible. Compare against at least one realistic alternative heat source, not only a gas boiler.
- **Availability:** planned IT/cooling downtime, heat pump outage, district network curtailment, dispatch response, backup heat and maintenance. Record delivered, curtailed, unrecovered and rejected heat separately.
- **Optional thermal storage:** an energy-balance-constrained hot-water storage model with charging/discharging losses, maximum power and state-of-charge boundaries. Include only if storage resolves a measurable seasonal or hourly mismatch.
- **Carbon accounting:** report *conditional* marginal operational emissions and explicitly distinguish average from marginal grid factors. Avoid claiming lifecycle reductions without LCA data.
- **Exergy:** study the sensitivity of valuable heat output to temperature lift; use clearly defined reference environment and thermodynamic boundaries.

## 4. Distinguish three cash-flow perspectives

| Ownership / offtake case | Who owns recovery equipment? | Project income / benefit | Principal risk |
|---|---|---|---|
| A. Integrated heat utility | District-heating utility | Avoided **actual marginal heat-production cost** | Source reliability, heat-demand mismatch and utility investment |
| B. Independent heat project | Special-purpose project company | Contractual heat sales (EUR/MWh), and only documented availability/capacity payments | Price, volume, buyer credit, power cost, debt service |
| C. Data-centre-led | Data-centre owner | Heat-sale revenue, plus cooling savings only if independently established | IT uptime, heat buyer and cooling-system integration |

For cases B/C, **do not** credit the company with the utility's entire avoided gas expenditure. It can capture only amounts specified by an offtake contract and its own documented savings.

Recommended new outputs:

- Real and nominal unlevered project cash flow by year;
- CAPEX by component and owner, opex variable/fixed, grid charges, replacements, residual value;
- NPV, IRR (where meaningful), levelised cost of delivered heat (LCOH), minimum break-even sale tariff;
- Illustrative financing structure: debt size, interest, amortisation, equity, taxes if modelled, **CFADS**, **DSCR = CFADS / debt service**, minimum/average DSCR, equity IRR;
- Scenarios for guaranteed heat volume, floor vs. indexed heat price, penalties for unavailability, change of counterparty, operating delay and curtailment;
- Clear statement that credit terms are illustrative, not a bank underwriting decision.

### Illustrative diagnostic of the existing baseline

**Held fixed**: current output 5,047.71 MWh/year; operating costs EUR 173,809/year (electricity plus variable/fixed O&M); CAPEX EUR 820,000; 20-year horizon; 6% real discount rate; 12%-of-CAPEX overhaul in year 12; no re-optimisation of dispatch or risk, and no taxes or financing. **Heat-sale prices below are arbitrary stress points, not Danish market quotes**.

| Fixed assumed contractual heat-sale price | Indicative annual cash flow | Indicative NPV |
|---:|---:|---:|
| EUR 40/MWh | EUR 28.1k | **EUR -0.547m** |
| EUR 50/MWh | EUR 78.6k | EUR +0.032m |
| EUR 60/MWh | EUR 129.1k | EUR +0.611m |

The current positive EUR 1.32m NPV implicitly values supplied heat at approximately **EUR 72.22/MWh** (EUR 65/MWh gas fuel divided by assumed 90% boiler efficiency). These are *different economic perspectives*. The new module should therefore re-optimise heat dispatch using actual project revenue per MWh and contract requirements and then recompute the annual energy balance.

## 5. Engineering research hypotheses (falsifiable)

H1. Lower district delivery temperatures improve seasonal COP but do not necessarily increase annual delivered heat under source, capacity and dispatch constraints.

H2. Under the same source conditions, contractual access to a heat-demanding network is at least as influential on viability as small changes in COP.

H3. There is a bounded range of connecting-pipe distances for which heat recovery is economically viable given a specific heat tariff and line-cost curve.

H4. The *investor* optimum compressor size is not necessarily the size that maximises useful annual heat delivery; the optimum changes with tariff and financing assumptions.

H5. A positive system-level NPV is not sufficient for project bankability if revenue is received by a different stakeholder or minimum debt-service coverage fails.

Each should have: method, comparison baseline, predicted direction (not guaranteed result), plot/table, criteria for falsification, and discussion of uncertainty.

## 6. Reproducible acceptance criteria

- Every figure and table regenerated by one documented command from versioned inputs.
- Units, time zones and geographical price zones checked automatically; no silent missing-hour interpolation.
- First-law and demand/capacity constraints asserted at every time step.
- Explicit comparison to at least one hand-calculated operating point and one published/representative heat-pump operating curve.
- No synthetic figure labelled as real-world prediction; finance inputs flagged as interview guidance, quote, public record or illustrative assumption.
- Report includes negative outcomes, failed sensitivities and known model limits.
- No personal interview claim without date, permission and factual note; anonymise nonpublic commercial terms and do not commit confidential documents.

## 7. Deliverable roadmap

**Stage 1 — Audit existing model:** Preserve prior baseline, fix investor vs. system boundary, add documented contract ownership cases and 40/50/60 EUR/MWh stress test; deliver bankability threshold figure.

**Stage 2 — Public observations:** replace synthetic DK2 electricity and weather with verified public time series; retain heat demand as labelled synthetic if no utility data is available.

**Stage 3 — Physics:** implement manufacturer-informed heat pump curve and pipe distance/temperature/availability sensitivity; compare to published Odense performance ranges without pretending the 1 MW system is Meta's site.

**Stage 4 — Financial risk:** build a sourced CAPEX breakdown and CFADS/DSCR model, 3 contract structures and lender downside cases. Interview with an energy-finance professional only with consent and confidential details removed.

**Stage 5 — Thesis-style report:** introduction, focused literature review, system boundary, mathematical methods, numerical verification vs. physical validation, results, uncertainty, financial analysis, implications and limitations. Aim for a rigorous 15–25 pages only if each section adds evidence.

**Most valuable output:** One defensible investment decision table displaying **Proceed to detailed feasibility / Insufficient evidence / Not attractive under stated assumptions**, with a clearly traceable chain from physical inputs to investor cash flow.

## Public references (checked 17 Nov 2026)

[1] Ramboll, *Meta: surplus heat to district heating*, https://www.ramboll.com/en-gb/projects/energy/meta-surplus-heat-to-district-heating

[2] Jerez Monsalves, J., Bergaentzlé, C., and Keles, D. (2023), *Economic feasibility of data center waste-heat integration into district heating: What does it require?*, DTU / EEM, https://orbit.dtu.dk/en/publications/economic-feasibility-of-data-center-waste-heat-integration-into-d/

[3] Copenhagen Infrastructure Partners (13 Aug 2026), *CIP and Thylander start construction of energy-integrated data centre in Denmark backed by PensionDanmark*, https://www.cip.com/copenhagen-infrastructure-partners-p-s/r/cip-and-thylander-start-construction-of-energy-integrated-data-centre-in-denmark-backed-by-pensionda,c4383657

[4] Energinet, *Day-Ahead Prices* https://datavejviser.dk/katalog/energidataservice/e759dc98-249b-4b1f-94ef-261754be05f8 ; *Elspot Prices (discontinued after 2025-09-30)* https://datavejviser.dk/katalog/energinet/f71d142b-e428-4948-be5b-81f7151c5e8a

[5] Danish Meteorological Institute, *Meteorological Observation API* https://www.dmi.dk/friedata/dokumentation/meteorological-observation-api

[6] Scottish Government, *Waste heat recovery: commercial considerations*, https://www.gov.scot/publications/waste-heat-recovery-introductory-guide/pages/5/

[7] Directive (EU) 2023/1791, Article 26, https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023L1791

[8] Delegated Regulation (EU) 2024/1364, https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj

[9] EIB/JASPERS, *Guide to decarbonisation of district heating systems*, https://jaspers.eib.org/knowledge/publications/jaspers-guide-to-decarbonisation-of-district-heating-systems

[10] ETH Zurich, *MEST Case Studies*, https://master-energy.ethz.ch/studies/case-studies.html

[11] IEA (2026), *Key Questions on Energy and AI*, https://www.iea.org/reports/key-questions-on-energy-and-ai/executive-summary
