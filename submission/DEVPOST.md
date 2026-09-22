# Pantry Relay

**Move food before a shelf goes empty.**

**Creator:** Shivam Gupta
**Built with:** React, TypeScript, Vite, Python, FastAPI, SQLite
**Repository:** [shi1720/Hack-Away-Hunger](https://github.com/shi1720/Hack-Away-Hunger)
**Release:** supervised-pilot release, with an isolated demonstration workspace
**Assistance:** AI-assisted research, implementation, testing and documentation. Shivam set the project direction, priorities and quality requirements.

## Inspiration

A donation is useful only when a pantry can put it into someone's hands. What happens when one pantry has produce it can spare, while another is short before tomorrow's service?

Iowa already has strong food banks, rescue organizations and volunteers. Food Bank of Iowa's FY2025 impact report describes a network of 700 partners and programs across 55 counties. That scale led us to a focused question: could a simple shared workflow help participating pantries rebalance approved food between replenishment deliveries? [Food Bank of Iowa](https://foodbankiowa.org/app/uploads/2025/08/FY_2025_impact_report_v8.pdf)

Pantry Relay is our answer to explore with operators. It starts with a pantry's next service, protects the sending pantry's own stock, and follows a transfer through to what the receiver actually accepted. This problem hypothesis comes from public research. We have not claimed pantry interviews, partnerships or field results.

## What it does

Pantry Relay helps an approved network coordinate food already available at its participating sites.

1. A coordinator records a pantry's next-service category need and another pantry's available lot, including a protected local reserve.
2. The planner proposes transfers based on quantity, urgency, the operator's use-by cutoff, storage compatibility, capacity, restricted-stock status and approximate distance. Each suggestion explains its reasoning.
3. Reserving a transfer commits stock and receiving capacity. The workflow then records acceptance, pickup, arrival and receipt.
4. The receiver records the actual accepted weight. A short or damaged delivery requires an exception reason and reopens the unmet quantity.
5. The impact view and CSV exports preserve the receipt and audit trail.

Our fictional demo makes the difference tangible: Cedar Grove Pantry can send 120 pounds of produce to Eastside Community Pantry. If only 112 pounds are accepted, Pantry Relay counts **112 pounds received**, records the 8-pound exception and leaves that gap visible. A reservation is not a completed delivery. A completed delivery is not a claim that a particular number of people were fed.

Individual accounts, network boundaries and administrator, coordinator and driver roles support the workflow. A new registered network starts empty; demonstration workspaces are explicitly labeled and separate. No household identities are needed.

## How we built it

The application uses a React and TypeScript interface with a FastAPI backend and a persistent SQLite database. The initial deployment is deliberately a single instance for a supervised pilot.

The matching engine is deterministic and explainable. It screens constraints, prioritizes near-term needs and use-by cutoffs, and allocates available quantities without proposing the same stock twice within a plan. Distances are straight-line estimates, clearly labeled; this is not road routing or a claim of globally optimal logistics.

The backend rechecks feasibility when a coordinator commits a proposal. Transactional reservations, version checks for stock edits and explicit transfer transitions protect against stale data and duplicate actions. Stock leaves the source at pickup; accepted stock is added at the destination on receipt. Cancellations before pickup release reservations.

Authentication uses hashed passwords and cookie sessions. Changes require CSRF protection, permissions are enforced by the server, and reports stay within the authenticated network. There is no required AI service or paid mapping API in the operating workflow.

## Challenges we ran into

The hard part was defining what a successful transfer actually means. “Matched” is too early to count impact. “Delivered” can still hide damaged or missing food. We made custody, partial acceptance and outstanding demand explicit.

We also had to avoid solving the wrong problem. MealConnect, Food Rescue Hero and pantry management platforms already handle important parts of food donation and operations. Pantry Relay focuses on next-service pantry shortages, protected surplus and receipt evidence. It is intended to sit beside existing systems; external inventory integrations are not yet implemented.

Food restrictions and physical handling remain operator responsibilities. Restricted lots are excluded from matching. Cold-food movements require temperature and condition records within configured limits, but the app does not certify food safety or replace an organization's procedures.

## Accomplishments that we're proud of

- One connected workflow from a category need to a persisted, auditable receipt.
- A visible local reserve so helping another pantry does not quietly deplete the sender's own service stock.
- A partial-delivery path that preserves the difference between promised and received food.
- Explainable suggestions and exclusions, with useful behavior when no transfer is feasible.
- A complete demo that requires no API keys and collects no household personal data.

## What we learned

Trust depends on modest claims and reliable records. Moving food is not the same as preventing waste; pounds received are not meals consumed; a promising workflow is not validated demand.

Commercial viability also starts with the operator. We propose a six-week supervised pilot, followed by a **$149 per network per month** pricing experiment for up to 10 sites. At a hypothetical coordinator cost of $25 per hour, that price needs about six hours saved per month to break even on labor alone. Neither the savings nor willingness to pay has been established. Free MIT-licensed self-hosting remains an option; there is no per-pound fee or payment flow in the app.

## What's next for Pantry Relay

Start with one willing coordinator, three nearby pantries and existing transport. Establish a baseline, use only approved stock, then measure category gaps, coordination time, accepted weight, exceptions and entry burden. Ask a real budget holder whether the results justify continuing.

Before real operation, the network must confirm transfer permissions, pickup and receiving windows, food-handling procedures and account recovery ownership. Deployment needs HTTPS, persistent storage, tested backups and restore, and disabled public demo access. The release does not provide offline synchronization, road-route optimization, automated email recovery or incumbent-system integration.

The next milestone is a useful, supervised pilot with honest results. If the workflow creates more work than it saves, we will change it with the people who operate it.
