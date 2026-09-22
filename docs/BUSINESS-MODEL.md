# A business that earns its place in a pantry's budget

## Buyer and job

The proposed first buyer is a regional nonprofit or food-bank network operator coordinating 5-25 pantries. The job is to fill near-term category shortages using existing approved surplus, with enough evidence to know whether the move helped. Individual pantries and food recipients should not pay a per-transfer or per-pound fee.

This is a hypothesis based on research into network scale and existing software. No interviews, paying customers, or letters of intent have been completed.

## Beachhead

A small, geographically close network with an existing volunteer transport arrangement and a named coordinator. Begin with unrestricted food whose transfer rules the network already understands. Require a short operating agreement and a food-safety lead. Do not acquire household data.

The product fits beside an incumbent intake or inventory system. CSV/API integration is a future development decision after discovering the actual systems in the pilot. A replacement inventory system is too expensive a starting proposition.

## Proposed offer

A six-week free supervised pilot, then a **$149 per network per month** hypothesis for up to 10 pantry sites. Includes hosting, backups, transfer evidence, and coordinator support. Self-hosting under the MIT license remains free. A sponsor could fund multiple networks; that is an alternate payer to test, not committed revenue.

No payment collection is implemented. There is no artificial checkout in the app.

## Unit economics: explicitly illustrative

| Per network per month | Assumption |
|---|---:|
| Subscription | $149 |
| Allocated hosting and backup | $15 |
| Support: 1 hour at $30 | $30 |
| Contribution before sales, development, tax and overhead | $104 |
| Contribution margin under these assumptions | 69.8% |

At 10 networks, these assumptions yield $1,490 monthly revenue and $1,040 contribution before overhead. These are scenarios, not projections. Hosting allocation assumes infrastructure sharing without crossing tenant boundaries; the hosted release uses a dedicated Cloud SQL database and at most two Cloud Run instances, so actual infrastructure and support costs must be measured. The small Cloud SQL instance has an estimated baseline cost of roughly $8 to $12 monthly including storage, before traffic, backup growth and taxes. This is a cost estimate, not an invoice or a free-tier promise.

Value hurdle: at a hypothetical $25/hour coordinator cost, $149 requires **5.96 hours saved per month** to break even on labor alone. We will ask operators for their actual time and loaded costs rather than treating this as established ROI. Do not assign a retail value to transferred pounds or claim all transferred food would otherwise have been wasted.

## Distribution

Demonstrate a single transfer to a network coordinator at the hackathon. Offer to shadow their existing workflow. Recruit one coordinator and three pantries for a narrow pilot with an existing transport partner. Share the baseline and actual results with the network, which decides whether to expand. No outreach has been sent on the user's behalf.

## Defensibility

The matching formula is explainable and easy to reproduce. An LLM is not a moat. Potential advantages would come from trusted network relationships, integration quality, reliable operational evidence, low training burden, and accumulated aggregate knowledge of which category requests can be fulfilled. Those advantages must be earned. The product must coexist with Food Rescue Hero, MealConnect, and pantry management platforms whose capabilities already overlap.

## Risks and stop rules

- Little genuine transferable surplus: stop or redirect after the baseline, instead of creating busywork.
- Data entry takes more time than calls saved: simplify or stop the pilot.
- Transport cost exceeds the operator's value threshold: do not encourage a transfer solely to increase pounds.
- Restriction or food-safety uncertainty: keep the food out of the planner until the operator resolves it.
- No budget owner or purchasing path: test sponsored networks or free self-hosting before promising startup revenue.
- Unreliable cold capacity data: restrict the pilot to ambient food until the network can operate a documented cold-chain process.
