# Pantry Relay: product and market research

Prepared for Shivam Gupta's Hack Away Hunger project. Research date: September 22, 2026. Public primary sources only; no organizations were contacted. Product, pricing, and pilot proposals below are hypotheses, not customer validation.

## Recommendation

Build **Pantry Relay: move food before a shelf goes empty.** It is a coordination tool for an approved network of food pantries. A pantry records what its next service needs and what it can spare. A coordinator sees feasible transfers that protect the sending pantry's own reserve, respect food restrictions and storage limits, and record the receiving pantry's actual receipt. The coordinator arranges the physical transport outside the app; this release has no driver-assignment field.

The strongest wedge is **preventing category shortages at the next pantry service using food already inside a network**. A generic donation marketplace, food directory, client intake platform, or rescue matching app would enter a mature field. This wedge is narrow enough to demonstrate thoroughly and broad enough to support a sustainable network software business if a pilot confirms the need.

The core promise is operational: “Know who needs what before tomorrow's service. Move only what another pantry can spare. Confirm what arrived.” This is an additive coordination layer, with imports and exports, rather than a replacement for a food bank's ordering system or a pantry's client records.

### Illustrative story, explicitly fictional

At 3 p.m., a volunteer records that Cedar Grove Pantry has apples available above its next-service reserve. Eastside Community Pantry needs 120 pounds of produce before opening tomorrow. Pantry Relay checks service deadlines, storage, transfer restrictions and vehicle capacity. The coordinator approves a 120-pound transfer. The recipient records that 112 pounds arrived in acceptable condition, with 8 pounds damaged. The dashboard records 112 pounds received and reopens the 8-pound gap; it does not claim 120 people were fed.

Use fictional pantry names and clearly label demo data. Do not invent a family testimonial or imply any Iowa organization is a customer or partner.

## What the evidence establishes

| Evidence | What it supports | What it does not establish |
| --- | --- | --- |
| Food Bank of Iowa's FY2025 impact report describes 700 partners and programs across 55 counties and reports 27.3 million pounds distributed. [FY2025 report](https://foodbankiowa.org/app/uploads/2025/08/FY_2025_impact_report_v8.pdf) | Coordination spans many independent sites and substantial food volume. | It does not measure how often a pantry has transferable surplus when another has a shortage. |
| The Iowa Food Bank Association identifies six food banks working with more than 1,500 partners statewide. Its state-data page uses 2023 Map the Meal Gap estimates. [State data](https://www.iowafba.org/state-data) | Iowa has an existing network through which a pilot can expand. | These are not 1,500 independent paying customers, and estimates should not be presented as a live count. |
| Food Bank of Iowa's published partner handbook describes online case-lot ordering and minimum food distributions. [2023 handbook](https://foodbankiowa.org/app/uploads/2023/03/CURRENT-Partner-Agency-Handbook-2023.pdf) | Food allocation and pantry service requirements are real operating processes. | A public handbook is not permission to transfer inventory; current partner agreements must govern a pilot. |
| Food Bank of Iowa's ordering manual says partners report monthly service statistics and that accurate reporting informs funding and allocations. [Ordering manual](https://foodbankiowa.org/app/uploads/2022/03/Online-Ordering-System-Training-Manual.pdf) | Data has practical value; compatibility with existing reporting matters. | An export file is not an official Primarius integration. |
| DMARC's FY25 advocacy agenda describes 14 partner pantries, mobile sites and home delivery, serving more than 70,000 unique people in FY24. [Agenda](https://dmarcunited.org/app/uploads/2024/12/DMARC_Advocacy-Agenda_FY25_State.pdf) | A regional coordinator is a plausible buyer and operational partner. | It does not establish DMARC's interest in this product. |
| DMARC's 2024 newsletter describes its home delivery program and transportation barriers. [Newsletter](https://dmarcunited.org/app/uploads/2024/12/TheVoice_JanFebMar_2024-digital.pdf) | Moving inventory closer to households is relevant to access. | Pantry-to-pantry transfers alone do not solve household transportation barriers. |
| Table to Table's FY24 report describes route-based rescue alongside warehouse, farm and transportation partnerships, and reports 2.7 million pounds delivered. [Report](https://table2table.org/wp-content/uploads/2024/11/FY24-FINAL-Annual-Report-Online.pdf) | Iowa already has capable rescue operators; their work should be complemented. | It does not establish wasted food inside their network or a need to replace their logistics system. |

Some Iowa public pages show different food-insecurity percentages because dates and source studies differ. Do not mix a 2021 estimate, a 2023 study and a 2025 toolkit into a single “current” statistic. For a pitch, one clearly dated local scale statistic is more defensible than a slide full of incompatible numbers.

## Competition and the honest differentiation

| Existing solution | Verified public capability | Consequence for Pantry Relay |
| --- | --- | --- |
| [MealConnect](https://mealconnect.org/) and [its donor FAQ](https://www.mealconnect.org/how-it-works) | Connects donors, food banks and partner agencies; donor access is free. | “Food donation matching” is neither novel nor a strong paid wedge. Respect existing donor networks. |
| [Food Rescue Hero](https://foodrescuehero.org/harnessing-data-for-fairer-food-distribution/) | Its Suggested Nonprofits feature screens or ranks recipients using opening times, food fit, storage, distance and distribution history. | Do not claim to invent constraint-based matching or equitable rescue dispatch. Distinguish source-pantry reserve protection and next-service category deficits after inventory has reached a pantry. |
| [Food Rescue US](https://foodrescue.us/about/how-we-help/) | Donors publish food, agencies communicate needs and volunteers collect and deliver it. | A three-sided donor/volunteer/recipient marketplace is established. |
| [PantrySoft](https://www.pantrysoft.com/features/) | Pantry inventory, client portal, service tracking, reporting and volunteer tools. | Do not build a full pantry ERP or claim inventory itself is novel. Make onboarding lighter and support existing records. |
| [Food Bank of Iowa's Primarius portal](https://pww.foodbankiowa.org/PrimariusWW/login.aspx) | Existing agency ordering portal. | Pantry Relay should bridge the interval between replenishment orders, not replace the core order system. |
| [Food Bank Manager](https://www.foodbankmanager.com/) | Pantry/network recordkeeping, reporting, inventory and volunteer features. | Network reporting is not unique by itself. |

These public feature pages are not exhaustive product audits. We cannot claim competitors lack every proposed feature. The credible claim is: “Our product is purpose-built around one workflow: a pantry's next-service shortage, a neighboring pantry's protected surplus, and verified receipt.”

### Why this is more promising than alternatives

| Alternative | Reason not to lead with it |
| --- | --- |
| AI pantry finder | Crowded, depends on current hours and eligibility, and discovery is not fulfillment. |
| Restaurant surplus marketplace | Strong established free platforms and a difficult three-sided cold start. |
| Household food delivery marketplace | High address/privacy burden, driver coordination, recurring delivery expense and strong operational dependence. |
| AI food insecurity predictor | Weak ground truth for a hackathon, little immediate operational action and risk of false precision. |
| Benefits eligibility chatbot | Accuracy and policy maintenance are demanding; a wrong answer can prevent access. |
| Pantry Relay | Narrow operator workflow, limited sensitive data, visible closed-loop demo, inexpensive deterministic matching, one network buyer. Still requires real workflow validation. |

## Product design implications

These are research recommendations. The implemented scope is defined in `docs/BUILD-SPEC.md`; the following list must not be presented as a list of shipped features. In particular, CSV import/previews, pickup-window checks, driver assignment, demand forecasting and recurring trip integration are future/discovery ideas. This release relies on coordinator confirmation of physical windows and transport, and shows estimated straight-line distance only.

1. **Start with a 60-second pantry pulse.** Capture the next service, category deficits, surplus lots, storage and pickup availability. Do not require volunteer teams to count every SKU before they receive value. Let the operator provide demand directly; forecasting can be an optional estimate with its assumptions visible.
2. **Protect the sending pantry.** Transferable quantity must not exceed available inventory minus local reserve minus active reservations. Keep all quantities in compatible units. Never automatically translate cases to pounds without a supplied conversion.
3. **Use hard constraints before ranking.** Approved organizations, transfer permission, compatible food/category, available quantity, receiving storage, time windows and vehicle capability are eligibility checks. Urgency, gap coverage and travel distance rank the remaining options. Explain both matches and blocked options.
4. **Model reservations and actuals.** Accepting a proposal reserves stock; cancellation releases it; pickup moves custody; receipt records actual accepted quantity. Prevent double allocation and over-receipt. Only completed, accepted quantities feed impact totals.
5. **Make “why this match” visible.** Example: “120 lb produce gap; 180 lb available above sender reserve; receiver open before 4 p.m.; 7.2-mile straight-line estimate.” If there is no route API, label distance as straight-line, not driving distance or route time.
6. **Treat freshness as operator input.** A staff-defined distribute-by window is not a machine judgment of food safety. Preserve label date type separately if tracked. The [USDA FSIS dating guidance](https://www.fsis.usda.gov/guidelines/2019-0022) distinguishes types of date labels; the software should not reduce all labels to “safe until.”
7. **Keep exception handling central.** Stale availability, quantity shortfall, damaged food, temperature concern, driver cancellation and no eligible match must have understandable states and recovery actions. The receiver must be able to reject all or part of a shipment.
8. **Make data entry cheap.** Mobile layout, keyboard use, large touch targets, empty states, timestamps, CSV template and an editable import preview are more useful than a chatbot overlay.
9. **Use existing operations as the anchor.** Coordinators arrange known drivers and trips outside the first release. An assignment field or recurring-trip integration is a future idea to validate. Do not promise optimal multi-stop routes without implementing and testing routing.
10. **Make operational evidence exportable.** A transfer ledger and receipt export should let a coordinator audit decisions without being locked into the product.

### Food restrictions and operational boundaries

For an initial pilot, accept only stock the network has explicitly approved for transfer. Default USDA/TEFAP, donor-restricted, unknown-source and recalled/quarantined stock to unavailable. A later policy workflow can capture the responsible coordinator's authorization; the app must not invent authority.

The [Food Bank of Iowa's older public terms](https://foodbankiowa.org/app/uploads/2022/03/Partner-Agency-Handbook-Current.pdf) include restrictions and donor stipulations. [River Bend's current forms page](https://riverbendfoodbank.org/forms/) separates Iowa and Illinois TEFAP materials; its USDA transfer sheet appears under the Illinois section. That form must not be treated as universal Iowa permission. Obtain the pilot network's current procedures before moving real restricted food.

Do not market the app as certifying food safety, legal compliance or driver suitability. It records required operational confirmations and leaves the responsible organization's rules in force. Software does not create a refrigerated vehicle, a trained volunteer or permission to redistribute.

## Sustainable commercial model

**User:** pantry volunteer or coordinator. **Buyer:** food bank, pantry coalition or rescue-network operator. **Beneficiary:** households receiving food. Keep household access free and never take a percentage of donated food.

**Proposed offer, not validated pricing:** a six-week free supervised pilot, then a **$149/network/month** plan for up to **10 sites**, including hosting, backups, transfer evidence and coordinator support. Sponsors may underwrite a network's subscription. MIT-licensed self-hosting remains free. The canonical commercial proposal is in `docs/BUSINESS-MODEL.md`; no payment flow or paid customer is claimed.

The price must be justified by measured coordinator time and operational benefit. At a hypothetical loaded coordinator cost of **$25/hour**, the **$149** subscription requires **5.96 hours saved per month** to break even on labor alone. That is a pricing experiment, not an observed saving. The separate illustrative cost model uses $15/month infrastructure plus one support hour at $30, leaving $104 before development, sales, tax and overhead. Food value, rescued pounds and avoided purchasing should not be double-counted as cash savings.

Start as a small software business testing a path to sustainability. Fifty networks paying $149/month would generate $89,400 in annual recurring revenue before support, hosting, sales, insurance and other costs. This is a scenario, not a market forecast, and it would support only a very lean operation. A larger business would require higher-value network contracts, paid services or broader adoption demonstrated by evidence. Iowa's six food banks do not alone imply a large market.

**Operating cost design:** no required paid AI calls; no SMS requirement; simple deterministic matching; one conventional application and database; basic maps or local schematic visualization; email and route services optional. Infrastructure can be inexpensive, but human onboarding and support are likely the important costs. Record actual hosting quotes at deployment rather than presenting a generic free tier as a permanent operating model.

**Potential defensibility:** trusted network relationships, reliable integrations, verified transfer history and a workflow volunteers continue to use. None is an existing moat on launch day. Data must remain exportable; lock-in and private beneficiary information should not be the strategy.

**Disqualifying commercial risks:** too little real surplus to justify the effort; transfers cost more than replenishment; coordinator already solves this well; participants cannot update data; donor restrictions block most lots; regional buyers will not budget for it. Test these early. If the pilot finds little transferable stock but frequent shortages, adapt the same need pulse toward shared replenishment planning rather than force an unneeded marketplace.

## Impact measurement

| Metric | Definition | Important limitation |
| --- | --- | --- |
| Pounds received | Sum of accepted receipt quantities in pounds, with explicit conversions where applicable. | Movement between pantries is not proof of household consumption. |
| Requested category gap filled | Accepted quantity allocated to a recorded category need, capped at that need. | It depends on the accuracy of the recorded need. |
| On-time fulfillment | Transfers received before the required service time / completed transfers with a deadline. | Show the denominator; do not omit failed transfers. |
| Coordination minutes | Time observed or logged from opportunity identification to committed transfer. | Compare with the same task before rollout; do not infer from click count. |
| Source reserve violations | Completed transfers that leave recorded available stock below the agreed reserve. | Target zero, while acknowledging stale stock data. |
| Spoilage at participating sites | Comparable weighed disposal logs before and during pilot. | Do not call every transferred pound “saved from landfill.” |
| Cost per accepted pound | Incremental driving, staff and platform costs / accepted pounds. | Report inputs and distinguish donated time from paid costs. |
| Participation and staleness | Active sites, pulses updated before service, age of stock/need data. | A low-friction system is only valuable when data stays current. |

Do not display “families fed,” “meals provided,” CO₂ avoided or money saved without an explicit, appropriate methodology and evidence. The demo should use visibly labeled synthetic metrics. The strongest first impact claim is much narrower: verified food arrived where a specific pantry said it was needed.

## Privacy and fairness

The operating workflow needs organizations, food, service deadlines and authorized drivers; it does not need household names, benefit status, birth dates, immigration information, diagnoses or home addresses. Keep category demand aggregate. Avoid free-text notes that encourage household stories. The first release has a network-level driver role for delivery actions, not per-driver assignment or assignment-scoped visibility. More granular delivery access is a future design decision.

Use individual accounts, role-based access and organization boundaries; maintain an audit log for stock and custody changes. Document retention, account removal and data export. Do not expose private operational phone numbers in public demos or logs. Never publish real recipient records in fixtures, screenshots or presentations.

A distance-only score could systematically favor urban sites. A reasonable pilot should report rural and urban fulfillment separately and let a coordinator prioritize urgent unmet needs. Do not infer an individual's need from demographic characteristics. Fairness claims require outcome data and participation from affected organizations, not merely a scoring coefficient.

## Six-week validation plan

No outreach has happened. These are proposed steps and success criteria. `docs/PILOT-PLAN.md` contains the canonical operating plan.

**Before the pilot: Understand the existing workflow.** Recruit one willing network coordinator and three nearby pantries. Conduct five short interviews about recent shortages or excess lots, their current workarounds, restriction rules and cost of moving food. Observe an actual service and inventory update with permission. Include limited-staff or rural context where practical. Confirm transfer permissions, operating procedures, account recovery and deployment readiness.

**Week 1: Establish baseline.** Record category gaps, surplus, discarded food, existing transfers, coordinating time and actual delivery cost using current tools. Do not change delivery decisions yet. Agree on the stock eligible for transfer and collect no household-level information.

**Weeks 2–5: Supervised pilot.** Run Pantry Relay in one network. Every proposed transfer requires human confirmation. Use existing drivers. Review failed matches and stale data daily. Keep phone/spreadsheet fallback and a named coordinator. Track why suggestions were rejected.

**Throughout the pilot: Usability and reliability.** Observe whether a volunteer can enter a need/lot and complete a receipt without coaching. Test cancellations, partial receipts and connection failures; offline synchronization is not implemented. Reconcile a sample of physical receipts against the ledger. Revise the workflow rather than add features to hide friction.

**Week 6: Decision.** Compare fulfillment, time and transport cost with baseline. Ask the actual budget holder for a paid continuation decision at an explicit price. Publish findings with permission, including null or negative results.

Suggested pilot gates to agree with operators (targets, not promises): at least 20% reduction in recorded category gaps, at least 25% reduction in coordination time, at least 95% receipt completeness, three consistently participating sites, review of every exception and a credible paid-continuation decision or documented rejection. Report actual received pounds without imposing an arbitrary pounds quota. A small pilot cannot establish a statewide causal reduction in food insecurity.

### Interview questions

- Tell me about the most recent time you lacked a category of food during service. What happened next?
- Tell me about the last lot you could not distribute in time. Was another organization able to use it?
- Who is authorized to move your stock, and which sources or programs prohibit a transfer?
- What do you count today, how often, and in what units?
- What makes you decline a delivery even when the food is free?
- How do you know the quantity actually arrived? Who reconciles a discrepancy?
- What coordination task would you stop doing if this worked?
- Who could approve paying for it? What evidence would they require?

Ask about past behavior before showing the product. “Would you use this?” is weak validation compared with observing a real recurring problem and securing a paid continuation.

## Judge-facing positioning

**Community impact (30%):** show a recorded shortage becoming a verified receipt, with a concrete and modest outcome measure. Explain the pilot and avoid claiming impact that has not occurred.

**Innovation (20%):** emphasize next-service category gaps, source reserve protection and accountability across independent pantries. Acknowledge existing rescue platforms. The innovation is the focused workflow and constraints, not simply AI.

**Technical execution (20%):** demonstrate persistence, authentication, role boundaries, transactional stock reservations, explainable matching, partial receipt/cancellation handling, audit history and meaningful tests.

**Feasibility and sustainability (15%):** present a single-network adoption path, explicit cost assumptions, one buyer, low data-entry burden and compatibility with current systems.

**User experience (10%):** let a judge complete the main task quickly on mobile; use clear statuses, units and freshness timestamps. The difference between suggested, reserved, in transit and received must be obvious.

**Presentation (5%):** use one fictional but plausible story, one live end-to-end flow and one candid ask: an approved pilot network. Credit Shivam Gupta as project creator/builder; describe AI assistance accurately if disclosure is required, without inventing specific human work or field research.

## Claims to avoid

- “We are the first food rescue matching platform.”
- “Iowa pantries waste X% of their food” without directly applicable research.
- “Partnered with Food Bank of Iowa/DMARC/Table to Table” unless an actual agreement exists.
- “AI predicts hunger” when the implementation uses seeded quantities or simple estimates.
- “Production-ready” as a substitute for documented deployment, security and operational readiness.
- “These 112 pounds fed 93 people.” A pound-to-meal convention is not a count of people served.
- “All transfers are legally compliant” or “the app certifies food safety.”
- “A $0 free tier means there are no operating costs.”

The strongest submission demonstrates a complete, honest operating loop, knows where incumbent tools already work, and states precisely what a pilot still has to prove.

## Event requirements and participant-only work

Verified against the official pages on September 22, 2026:

| Requirement | Source | Consequence |
| --- | --- | --- |
| Ages 13+; US only. | [Official overview](https://hack-away-hunger.devpost.com/) | Shivam must establish his eligibility; device timezone is not proof of citizenship, residence or location. |
| Teams have 2–6 members; individuals may register and be connected to a team. | [Official rules](https://hack-away-hunger.devpost.com/rules) | At least one real teammate is needed; AI assistance should not be counted as a human teammate. |
| Completed project must be presented in person on October 10, 2026, at Corteva Agriscience in Johnston, Iowa, to qualify for judging and prizes. | [Official rules](https://hack-away-hunger.devpost.com/rules) | A recorded demo does not itself satisfy this requirement. Confirm who will attend and present. |
| Final submission closes October 8, 2026, 11:45 p.m. EDT. | [Official schedule](https://hack-away-hunger.devpost.com/details/dates) | This equals October 9, 2026, 9:15 a.m. India time. Submit well before then. |
| Overview lists proposals due September 17 at midnight and the accelerator September 24–26. | [Official overview](https://hack-away-hunger.devpost.com/) | Proposal date has passed; late-entry/late-proposal acceptance is not established by the public page. |
| Project must develop during the event, show meaningful progress and include the required Devpost materials. | [Official rules](https://hack-away-hunger.devpost.com/rules) | Keep project history and complete the actual submission form. The public rules do not enumerate every required field. |

The participant needs to confirm eligibility and entry status, recruit/confirm a human teammate, arrange the in-person presentation, supply any required Devpost account information, and record the final voiceover if desired. No organization or organizer has been contacted and no submission has been made through this research task. The public rules inspected do not state a specific AI prohibition or a video-length requirement; this is not permission to invent either. Disclose assistance accurately when the submission form or organizer requests it.
