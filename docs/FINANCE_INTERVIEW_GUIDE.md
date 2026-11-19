# Interview guide — energy infrastructure investment

**Purpose:** optional learning conversation with a professional familiar with financing renewable-energy and energy-infrastructure projects. This is a list of questions, **not** evidence that an interview took place. The interviewee is not expected to provide sensitive or proprietary information.

## Opening (suggested)

"I am developing an academic screening model for recovering heat from a hypothetical data centre and supplying a district-heating network. My thermal model calculates hourly heat production, electricity consumption, and operating costs. I would like to understand how an investor or lender would actually evaluate whether this kind of project could be financed. I only need general industry practices, not confidential figures or details of any transactions."

## The 10 questions

1. **Financial perspective:** Who usually owns the heat pump, network connection and heat export assets? Could the data centre, a district-heating utility and an independent project developer have different financial cases?
2. **Offtake:** Would a financeable project normally require a long-term heat purchase or supply contract? What matters more: heat-sale price, minimum volume or buyer credit quality?
3. **Revenue structure:** Is heat typically sold per delivered MWh, with a capacity payment, through take-or-pay provisions or via an indexed formula? What tariff risks need to be modelled?
4. **Reliability:** Who bears the risk of reduced data-centre IT load, a server cooling outage or summer reductions in district-heat demand?
5. **Capital costs:** What cost categories do early feasibility studies most often forget (pipe connection, heat exchangers, permits, backup, electric interconnection, insurance, maintenance reserves)?
6. **Financing metrics:** Which indicators are most relevant at screening stage: unlevered NPV, IRR, LCOH, discounted payback, cash available for debt service, minimum DSCR, or leverage?
7. **Stress tests:** Which downside scenarios would a lender test before considering financing (higher electricity prices, lower heat volumes, lower tariffs, construction delays, equipment underperformance)?
8. **Contracts and risk allocation:** How is the risk of one counterparty shutting down or terminating the heat supply handled? What about step-in rights and maintenance obligations?
9. **Regulation:** Which permits, tariff rules, subsidies, or grid charges can make or break a district-heating project? What should be checked locally rather than assumed?
10. **Investment committee:** If a student presented a 10–20-page feasibility study, what one missing number or document would immediately prevent an investment decision?

## Interview integrity and use in a CV

- Seek permission for note-taking and for any public mention of an interview.
- Do **not** ask for private bank models, deal files, names of clients, credit committee documents or unpublished pricing.
- When allowed, cite only general insights with an appropriate anonymised attribution, date and limitations.
- If no interview occurs, write "commercial framework informed by public sources" rather than implying professional validation.
- An interview is qualitative research. It cannot replace a project heat-purchase agreement, verified cost quote or lender commitment.

## Turn answers into engineering questions

Each answer should affect an actual model input or output. For example:

- "Price risk dominates" -> vary heat tariff indexation and floor, not just electricity spot prices.
- "Buyer minimum offtake is critical" -> model a guaranteed off-take threshold and curtailment cases.
- "Construction delays matter" -> add a start-year shift to the discounted cash-flow model.
- "Debt service is key" -> compute year-by-year CFADS and DSCR under at least one disclosed illustrative amortisation schedule.
- "The network is already low-carbon" -> replace the gas-boiler counterfactual with the actual marginal heat source.
