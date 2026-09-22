# Pantry Relay

**Make the food already here go further.**

Pantry Relay helps a trusted network of food pantries fill upcoming food-category gaps using nearby surplus. A coordinator can protect a pantry's own reserve, find a feasible transfer, record the handoff, and report the pounds the receiving pantry actually accepted.

Built for **Hack Away Hunger 2026**. Project lead: **Shivam Gupta**. AI-assisted development and research are documented in [CREDITS.md](CREDITS.md).

## Why this project

A food directory helps someone find a pantry. Pantry Relay helps the pantry have the food it needs for its next service. The first customer hypothesis is a regional pantry-network coordinator who already spends time arranging transfers through calls and spreadsheets. The software collects operational food quantities, not household identities.

Food Bank of Iowa reports serving a network of 700 partners and programs across 55 counties. That establishes the coordination context, not proof of demand for this product. Actual willingness to use and pay for Pantry Relay remains a pilot question. See [research](research/research.md) and the [pilot plan](docs/PILOT-PLAN.md).

## Run locally

Prerequisites: Python 3.11+, Node.js 22+, npm, and [uv](https://docs.astral.sh/uv/).

```sh
./scripts/start.sh
```

Open **http://localhost:8010**. Choose **Explore the demo** for an isolated workspace containing fictitious pantries and relative dates, or create an account for an empty network. No API keys, cloud account, payment method, or internet connection are required for the running app after dependencies are installed.

For development, run the backend and frontend separately:

```sh
uv sync --extra dev
uv run uvicorn backend.main:app --reload --host 127.0.0.1 --port 8010
```

```sh
cd frontend
npm ci
npm run dev
```

## What works end to end

- Email/password accounts, cookie sessions, logout, isolated networks, and expiring role invitations.
- Pantry sites with storage capability and capacity. Food lots with quantity, protected reserve, use-by cutoff, and transfer restrictions. Category needs for the next service.
- Explainable matching that checks stock, demand, distance, per-trip carrying capacity, refrigeration, destination storage and space. The planner allocates its proposal batch against shared availability.
- Atomic reservation, receiver acceptance, pickup, arrival, and actual receipt. Cancellation before pickup releases reservations. Partial receipts record the shortfall and reopen unmet demand.
- Temperature and condition checks, an audit trail, and CSV exports with spreadsheet-formula protection.
- Role-based driver workspace, responsive layouts, and printable transfer manifests.

The app deliberately reports **received pounds**, not unverified meals, people fed, or carbon savings. Map lines and distances are schematic straight-line estimates. Humans arrange travel, verify access windows, and follow their organization's food safety procedures.

## A two-minute demo

1. Enter a fresh demo and open **Relay planner**.
2. Generate proposals. Inspect the reason and the source pantry's protected reserve.
3. Reserve the produce transfer and open **Deliveries**.
4. Record receiver acceptance, pickup, and arrival.
5. Receive fewer pounds than dispatched and explain the difference.
6. Open **Impact**. Only accepted pounds count; the remaining need and audit evidence stay visible.

Full narration and shot list: [submission/DEMO-SCRIPT.md](submission/DEMO-SCRIPT.md).

## Quality and operations

```sh
uv run pytest
cd frontend
npm run build
```

See [VERIFICATION.md](docs/VERIFICATION.md) for the actual checks performed and their limits. The backend uses tenant-scoped queries, transactional SQLite writes, HttpOnly session cookies, CSRF checks, password hashing and server-side role checks. See [SECURITY.md](SECURITY.md).

Deployment uses one application instance and a persistent SQLite volume. [Docker Compose](compose.yaml), a [Dockerfile](Dockerfile), and [deployment instructions](docs/DEPLOYMENT.md) are included. Free ephemeral cloud filesystems are suitable only for disposable demos, not pantry records. This is a working release for a supervised pilot; it has not received an independent security audit or real pantry validation.

## Submission and adoption kit

- [Start here](submission/START-HERE.md): deliverables and participant-only actions
- [Devpost text](submission/DEVPOST.md)
- [Verbatim demo script](submission/DEMO-SCRIPT.md)
- [Business model](docs/BUSINESS-MODEL.md) and [pilot plan](docs/PILOT-PLAN.md)
- [Architecture](docs/ARCHITECTURE.md), [operating guide](docs/OPERATING-GUIDE.md), and [deployment](docs/DEPLOYMENT.md)
- [Evidence and competitors](research/research.md)

## Scope boundaries

This release does not integrate with an existing pantry inventory system, send email or SMS, optimize road routes, certify food safety, determine food-assistance eligibility, or claim nonprofit partnerships. Invitations are links shared by the administrator. Sites belong to a coordinator-approved network; account creation alone does not establish a real-world partnership. A live pilot requires an identified network operator and an agreed operating policy.

MIT licensed. No real household records or private credentials belong in this repository.
