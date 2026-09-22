# Pantry Relay — judge questions and demonstration notes

Prepared for Shivam Gupta. Use these answers as a guide, not as a claim that a pilot has taken place. All demo organizations, needs and weights are fictional. Release status: supervised-pilot release. Reconcile any implementation or test claim with the final build and verification record before presenting.

## The 20-second answer

“Pantry Relay helps a pantry network fill tomorrow's category shortages with food another approved pantry can spare. It protects the sender's own reserve, explains feasible transfers, and follows each one through to the actual receiving weight. Our demo shows 120 pounds dispatched and 112 accepted, with the missing 8 pounds still visible. We want to test whether that saves coordinators time and closes real gaps.”

## Rubric traceability

| Criterion | Weight | What to demonstrate | Evidence and honest boundary |
| --- | ---: | --- | --- |
| Community impact | 30% | A next-service produce need becomes an accepted receipt; a partial receipt leaves the remaining need open. | Received weight is directly recorded. Household outcomes, avoided waste and statewide impact are not established. Pilot measures are defined in `docs/PILOT-PLAN.md`. |
| Innovation | 20% | Source reserve protection, a specific service-category gap, explained constraints and actual receipt in one workflow. | Existing platforms already match donations. Our claim is a focused pantry-to-pantry operating workflow, not invention of food rescue technology. |
| Technical execution | 20% | Reserve stock, accept, pick up, arrive and receive; refresh to show persistence; show an excluded lot and an invalid action being prevented. | Server-side permissions, network isolation, transactions, stock version checks and explicit states matter more than animation. Present the final executed checks accurately. |
| Feasibility and sustainability | 15% | Show a normal empty network, simple lot/need entry and exportable records. Explain one buyer and the $149 hypothesis. | No required paid AI/map dependency. Single-instance deployment and ongoing support costs remain explicit. No paying customer or letter of intent is claimed. |
| User experience and design | 10% | Complete the flow on a narrow viewport; point out units, timestamps, labels and partial-receipt feedback. | Usability must still be observed with pantry operators. Do not call a visual review a field usability study. |
| Presentation | 5% | Follow one fictional transfer from shortage to receipt, then make one specific pilot ask. | Keep live demo claims narrower than the proposed roadmap. Credit Shivam and AI assistance accurately. |

## Questions to expect

### What is the problem, in one sentence?

“A pantry coordinator needs to know whether approved food available elsewhere in the network can fill a specific category shortage before the next service, without leaving the sending pantry short.”

This is a hypothesis worth testing. Large pantry networks are documented; the frequency, cost and severity of this particular mismatch have not been measured by this project.

### Why another food app when rescue platforms already exist?

“We are not proposing that every donor and driver move to a new marketplace. Our starting point is food already inside an approved pantry network. The workflow joins three questions: what is needed before the next service, what can the source genuinely spare, and what actually arrived?”

Public comparisons:

| Platform | Established capability | Pantry Relay's intended relationship |
| --- | --- | --- |
| [MealConnect](https://mealconnect.org/) | Donation coordination across food donors, food banks and agencies. | Complement upstream rescue; do not compete on a generic donor listing. |
| [Food Rescue Hero](https://foodrescuehero.org/harnessing-data-for-fairer-food-distribution/) | Recipient suggestions using timing, compatibility, distance and distribution history. | Acknowledge real matching overlap. Concentrate on pantry reserves, upcoming category deficits and transfer receipts. |
| [PantrySoft](https://www.pantrysoft.com/features/) | Pantry inventory, client services, volunteer tools and reporting. | Avoid replacing client intake or the full inventory system. Test future integration around the limited transfer workflow. |
| [Primarius at Food Bank of Iowa](https://pww.foodbankiowa.org/PrimariusWW/login.aspx) | Existing agency ordering portal. | Help coordinate between replenishment deliveries; do not claim a shipped integration. |

Public feature descriptions are not a complete competitor audit. Say “purpose-built around this workflow,” not “no one else can do this.”

### Have pantries asked for this? Who is using it?

“No organization has agreed to a pilot yet. We researched public operating materials and existing tools, then built a working release to make discovery concrete. Our next step is five short interviews and a small baseline study, not a claim that we already have product-market fit.”

Do not imply that an organization referenced in research is a partner. Do not describe demo usage as real adoption.

### How does the matching work?

“The planner first screens whether a transfer is allowed and feasible: same approved network, compatible category and storage, unrestricted stock, quantity above the sender's reserve, receiving capacity, the operator's use-by cutoff, service deadline, configured distance limit and vehicle capacity. It then prioritizes urgent needs and near-term stock cutoffs, explaining each suggestion.”

“This is a deterministic greedy planner. It is understandable, cheap to run and reproducible. It is not a globally optimal route planner. Distance is a straight-line estimate, and a coordinator must confirm the physical journey and actual pickup windows.”

If asked about AI: “We used AI assistance to build and review the project. The food allocation workflow itself does not require an LLM. We do not need a model to invent quantities or decide whether food is safe.”

### What stops two coordinators allocating the same food?

“A proposal is advisory. On reservation, the backend rechecks the current stock, committed quantities, need and receiving capacity inside the database transaction. Existing reservations reduce future availability. Version checks reject stale stock edits. The transfer state machine rejects actions that are invalid for its current state.”

Demonstrate a stock reservation affecting subsequent availability. If presenting a concurrency test, use its actual executed result; do not infer test coverage from the architecture alone.

### What happens if the driver brings less than expected?

“Pickup records the dispatched stock leaving the source. On receipt, the coordinator records what was accepted. If 112 of 120 pounds are accepted, the destination gains 112, the impact total gains 112, and 8 pounds remain unfilled against the need. The exception requires a reason. We do not silently turn a partial delivery into a success at the promised weight.”

Pre-pickup cancellation releases the reservation. After pickup, a real incident needs operator handling; the app must not pretend the stock teleported back to its source.

### Are you actually preventing waste?

“That is a possible benefit to measure, not a result we can claim now. Our application records pounds accepted by another pantry. To demonstrate avoided waste, the pilot needs comparable disposal logs and a credible baseline. We will not label every transfer as food saved from landfill.”

Likewise, do not convert pounds into a count of families, meals consumed or carbon saved without a stated and suitable methodology. The demo shows prototype sample figures only.

### How will you prove community impact?

“With one coordinator and three nearby pantries, we would first record current category gaps, coordinator time, delivery cost and actual transfers. During a six-week supervised pilot we would track the same measures, plus receipt completeness, exceptions and data-entry burden. The network agrees on success thresholds before the pilot starts.”

The plan proposes a 20% reduction in recorded category gaps and 25% less coordination time as discussion targets, not validated benchmarks or promises. A small uncontrolled pilot cannot prove a causal reduction in household food insecurity.

### Can all donated food be transferred?

“No. The network must confirm transfer permissions and donor or program restrictions. Restricted lots are excluded from the planner. The first pilot should use only food the operator explicitly approves; if cold-chain procedures are not ready, start with ambient stock.”

The product does not decide legal eligibility or certify food safety. An operator-entered use-by cutoff is an operational constraint, not a machine's assessment of edibility. Required temperature/condition logs help record the process; they do not replace training, suitable equipment or incident procedures.

### What sensitive data do you collect?

“We need organization locations, food quantities, service needs and authorized account details. We do not need household identities, income, benefit status, diagnoses or home addresses. Driver permissions are limited to operational delivery actions. We keep stock and transfer changes auditable.”

This is data minimization, not a claim of a privacy certification. Free-text notes should never include beneficiary personal information. Real organizations must agree on access, retention and removal procedures before operation.

### Why would someone pay, and who is the buyer?

“The proposed buyer is the regional organization coordinating the network. Our experiment is $149 per network per month for up to 10 sites after a free supervised pilot. Pantry visitors are not charged, and there is no per-pound or per-transfer fee.”

“At a hypothetical $25 loaded hourly coordinator cost, the price equals about six hours a month. We need to measure whether the tool saves at least that much value once entry, training and transport costs are included. We have not established willingness to pay.”

Free MIT-licensed self-hosting remains available. Hosted service, backups and support are the proposed paid offer. No billing flow or committed sponsor is claimed.

### Does the business work at that price?

“Our illustrative model allocates $15 for infrastructure and backups and one hour of support at $30. That leaves $104 per network per month before development, sales, tax and overhead. These assumptions have to be tested; support could be higher, and the shipped deployment is a single instance.”

Ten such networks would produce $1,490 monthly revenue, which is not a mature business. The purpose of the first paid pilot is to find a repeatable useful service, not inflate a market-size slide. Expand only when the operating results justify it.

### What is defensible about this? Couldn't an incumbent copy it?

“The algorithm is reproducible and the code is open. There is no technical moat on day one. The potential advantage would be a workflow operators trust, integration quality, low training burden and evidence that it improves their coordination. Those advantages must be earned.”

If a current platform solves this well for a network, adopting that platform can be the right answer. The pilot must determine whether Pantry Relay fills a useful gap.

### What is ready now, and what still needs work?

“The release provides accounts and roles, network-scoped pantry records, lots and reserves, category needs, explained proposals, persisted transfer states, partial receipts, audit history and CSV reports. The operating flow runs without external API keys.”

“It is a supervised-pilot release, not a certified production service. Before real use, the operator needs approved transfer procedures, account recovery ownership, suitable transport and incident handling. The deployment needs HTTPS, persistent storage, a successful restore test and public demo access disabled.”

Known product limits include no offline synchronization, road routing, automated email recovery or existing inventory-system integration. Physical pickup/receiving windows must be confirmed outside the planner. Do not claim an SLA, security audit, accessibility certification or validated field usability.

### What did you build, and how did AI contribute?

“I'm Shivam Gupta, the project's creator. I set its direction and priorities, including practical use, commercial viability and honest impact measurement. I used AI assistance extensively for research, implementation, testing and documentation. I take responsibility for what we present and for validating it before people depend on it.”

Use only specific personal contributions that are true. Do not say every line was written unaided or invent user interviews. If additional human teammates join, describe their actual work and list them accurately.

### What would you do with the prize or a willing partner?

“Run the narrow pilot with operators. Spend on onboarding, observation, reliable hosting, transport coordination and the integration the pilot actually needs. Our ask is one willing network coordinator and three nearby pantries with an existing delivery arrangement, not statewide rollout on day one.”

## Presentation discipline

- Keep the distinction between **proposed**, **reserved**, **in transit** and **received** visible.
- Show the partial-receipt exception; it is the clearest proof that the system accounts for reality.
- Use fictional site names consistently. Say “in this demonstration” before its figures.
- If a live action fails, explain what happened and use the recorded backup; do not claim a failed transition succeeded.
- Cite the research sources for local scale. Use the final verification record for engineering claims.
- End with the pilot question: can this close real category gaps at less staff and transport cost than the current process?

## Participant requirements that software cannot complete

The [official rules](https://hack-away-hunger.devpost.com/rules) require a 2–6-member team and an in-person presentation on October 10 in Johnston, Iowa. The [overview](https://hack-away-hunger.devpost.com/) states US eligibility and age 13+. AI assistance does not fill a human teammate slot. Confirm eligibility, team participation, late-proposal acceptance if needed, and who will attend. The [submission deadline](https://hack-away-hunger.devpost.com/details/dates) is October 8 at 11:45 p.m. EDT, equivalent to October 9 at 9:15 a.m. India time. These practical requirements remain separate from the readiness of the code.
