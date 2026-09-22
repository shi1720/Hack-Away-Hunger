# Pantry Relay — independent provisional review

Review date: September 22, 2026. This is an internal, AI-assisted evaluation against the published hackathon rubric, not a score from the event's judges or a prediction of winning. Reviewed the actual backend, frontend source, tests, research, business/pilot plans, Devpost copy, demo script and five rendered desktop/mobile screenshots. The coordinating reviewer also supplied results from the actual browser workflow. The final presentation recording and live pantry use remain untested.

## Assessment

The project has a coherent, useful scope: an approved pantry network can record a near-term category need, reserve food another pantry can spare, and reconcile the actual receipt. The strongest demonstration is a partial receipt that preserves the difference between promised stock and accepted food. The release is more credible because it avoids inventing customers, meals served, carbon savings or an AI requirement.

The principal remaining uncertainty is whether enough real, permitted pantry-to-pantry transfers occur to justify another workflow and recurring subscription. Public research establishes the surrounding network and incumbents; it does not establish that operators need this particular product. More features cannot substitute for observing that work.

## Provisional rubric score

| Criterion | Available | Provisional | Basis |
| --- | ---: | ---: | --- |
| Community impact | 30 | 22 | Direct link between declared need and recorded food receipt; sensible measurement plan and no household data. No field baseline, participating pantry or observed impact yet. |
| Innovation | 20 | 14 | Source reserve protection, service-specific demand and accountable receipt form a distinctive focus. Existing rescue platforms already have matching and dispatch, so this is a focused workflow improvement rather than a wholly new category. |
| Technical execution | 20 | 18 | Real persistence, role and tenant controls, exact quantity accounting, transactional reservations, state transitions, audit/export and meaningful regression tests. The independent review found important accounting edge cases; verified fixes and an independently checked failure closeout materially strengthen this score. Final frontend verification remains to check. |
| Feasibility and sustainability | 15 | 11 | One network buyer, low infrastructure dependency, honest price/cost assumptions, free self-hosting and a practical pilot. Entry burden, transfer economics, integration needs and willingness to pay are still unvalidated. |
| User experience and design | 10 | 8 | Cohesive, polished visual system and a clear partial-receipt workflow; supplied mobile screenshots stack cleanly, and the coordinating reviewer reported no 390px overflow plus successful Escape handling. The reviewed operational UI repairs are integrated. Real volunteer usability and the final contrast scan remain distinct checks. |
| Presentation | 5 | 4 | Strong single-story script, candid competitor positioning, usable judge answers and a concrete pilot ask. Final recording, deck rendering and in-person eligibility are not established by this review. |
| **Total** | **100** | **77** | **Provisional internal assessment, not an event result.** |

The engineering score can improve with verified final behavior. The largest potential improvement in the overall submission comes from credible operator evidence and a smooth presentation, not inflated claims or more screens.

## Review method and independent checks

Used temporary SQLite databases under a disposable test directory. No real workspace data was changed. The existing backend test suite was read rather than redundantly executed in full; the backend implementer owns the suite run and its results. This reviewer ran narrow API reproductions for identified issues and independent access-control probes. The backend implementer subsequently reported 51 passing tests and clean Ruff checks; that is a reported suite result, not an independent rerun by this reviewer.

An attempted direct browser review could not start: the in-app browser was unavailable and Chrome session setup failed on runtime authentication. No browser interactions or operational records were changed by this reviewer. Instead, the reviewer visually inspected `artifacts/screenshots/landing.png`, `overview.png`, `planner.png`, `impact.png` and `mobile.png`. The coordinating reviewer reported successful actual-browser partial receipt, CSV download, reload persistence, reopened 8-pound need, 390px mobile overflow check and Escape dismissal. This is supplied execution evidence, not a claim that this reviewer personally ran those browser actions.

Observed access results:

- A second network's lot edit, transfer acceptance and transfer creation each returned **404**.
- A driver attempting to invite, accept, plan or export receipts received **403**.
- The driver workspace omitted inventory lots and needs.
- A consumed invitation returned **400** on reuse; its original join assigned the server-stored driver role.
- The planner and receiving records use integer hundredths of a pound internally. Reservation writes use `BEGIN IMMEDIATE`; pending incoming quantities are included in receiving capacity.

Read regression coverage includes concurrent duplicate reservation, source reserve preservation, stale inventory edits, inbound capacity through arrival, partial and full rejection, cold thresholds, invalid transitions, tenant boundaries, role escalation, expired sessions/invites, production configuration and CSV formula injection. A test's presence is not a substitute for its executed result; see the final verification document for that result.

## Important findings and verified repairs

Line references identify the reviewed source snapshot; function names remain the stable reference if formatting changes.

### R1 — Late receipt incorrectly fulfilled a missed service — repaired and independently rechecked

Initial location: `backend/main.py`, `receive`, originally lines 418–444. A transfer was picked up while its service was upcoming; its need was then advanced past deadline in the isolated test database. Receiving 112 pounds returned 200 and increased that already-missed service's `fulfilled_lb` by 112.

Repaired behavior in `receive` (formatted source: `backend/main.py:866`, credited quantity at line 920): late confirmation still records physical accepted stock, but credits **zero** toward the missed service. The response and report distinguish `on_time`, `late` and `need_credited_lb`. Independent recheck returned `fulfilled_lb=0`, `late=true`, `need_credited_lb=0`, with 112 pounds actually received preserved.

The timestamp measures receipt confirmation, not guaranteed physical arrival. User-facing language and the audit must say “receipt confirmed after the service deadline.” This distinction matters if someone records a timely physical delivery late.

### R2 — Received stock could immediately be sent away again — repaired and independently rechecked

Initial location: `backend/main.py`, `receive`, originally line 440. The destination lot was created with no protected reserve. A second need made the planner offer all 112 just-received pounds to a third pantry while the first pantry's service remained credited as fulfilled.

Repaired behavior in `backend/main.py:866`, `receive`, creates the received lot with **reserve equal to accepted quantity**. Independent recheck showed quantity 112, reserve 112, available 0, and no downstream proposal from that lot. A coordinator can intentionally release reserve through an audited stock adjustment. Regression coverage exercises both protection and deliberate release.

### R3 — Restricted stock was labeled shareable — repaired and independently rechecked

Initial locations: `backend/domain.py`, `available_units`, and `frontend/src/views.tsx`, `Inventory`. A restricted 30-pound lot returned `available_lb=30`; the inventory row labeled that quantity shareable even though matching and the global total excluded it.

`available_units` (`backend/domain.py:78`) now returns zero for restricted or expired lots. Independent recheck returned **0** for the restricted lot. The underlying quantity is retained so the physical inventory is still accurate.

### R4 — Real invitees could join a disposable demo network — repaired and independently rechecked

Initial locations: `backend/main.py`, `invite` and `join`, originally lines 203–230. A sample-workspace administrator could generate an invitation, and an ordinary email/password user could join. Demo cleanup would later delete that supposedly normal account and its work.

Both endpoints (`backend/main.py:263` and `backend/main.py:292`) now reject demo-network membership, including previously generated demo invites. Independent invite recheck returned **403**. The frontend should also hide the invitation action in a demo and explain that real team onboarding starts with an empty registered network.

### R5 — A mistaken or canceled need had no recovery action — backend repair independently rechecked; UI source checked

Initial locations: `backend/main.py`, `create_need`, and `frontend/src/views.tsx`, `Sites`. A mistaken quantity or canceled service remained eligible for planning until its time passed.

The new `POST /api/needs/{id}/close` endpoint (`backend/main.py:667`) preserves the original record and audits a reason. It refuses closure with active transfers. Independent close returned **200** with `closed=true` and remaining quantity zero. Regression tests cover active commitments, repeated closure, stale proposals, tenant scope and schema migration. The final `Sites` and `Forms` source includes the close action, reason form and closed-state label.

## UI findings and source recheck

These were sent to the frontend implementer. The final source was reread after the changes; all five repairs below are present. A final browser exercise remains the stronger verification for the interaction paths.

| Initial priority | Final reviewed location | Finding and repair |
| --- | --- | --- |
| P1 | `frontend/src/Forms.tsx:513` and `:637` | Full cold rejection originally required a temperature. The form now makes it optional only at zero accepted weight, sends null when blank and preserves the required exception reason and positive-acceptance checks. |
| P2 | `frontend/src/views.tsx:68`, `Overview` | Past unmet needs originally became “NEXT SERVICE.” The current filter requires an open need, positive remaining quantity and future service time. |
| P2 | `frontend/src/api.ts:25` and `frontend/src/App.tsx:83` | Expired sessions originally stranded local signed-in state. Authenticated-request 401 now dispatches a session-expired event that clears the session, workspace and modal and returns to authentication. |
| P2 | `frontend/src/views.tsx:1154` and `:1488` | Late receipts originally had no visible distinction. Delivery cards now say receipt was confirmed after the service, and impact rows show the service-credited quantity separately. |
| P3 | `frontend/src/App.tsx:374` and `frontend/src/Forms.tsx:374` | Times originally lacked a visible zone. The footer and service-time input now name the browser's timezone. |

Static CSS review also identified **P2 contrast/readability issues** in the initial styles: hero description `#7f8777` on `#f8f9f2` was 3.52:1; helper text `#7d8976` on `#f7f8f2` was 3.44:1; field hints `#83907d` on `#fffef9` were 3.33:1; small labels `#929a8b` on `#fffef9` were 2.88:1. These are below 4.5:1 for normal text. Several mobile rules reduced operational metadata to 7–9 px. The final stylesheet darkens informational text and enlarges critical metadata; the coordinating reviewer is rerunning axe against the rendered release. These initial calculations are source-based checks, not a complete accessibility certification.

### Visual critique

The rendered identity is consistent across landing, planning and reporting: a forest-green sidebar, warm background, restrained accent and readable large serif headings. The planner gives the food, source/destination and quantity distinct positions. The 112-pound receipt view is a strong presentation moment without pretending to count people. Mobile retains the important content without overlapping panels in the supplied screenshot.

The first screenshot set exposed overly faint small metadata, which the subsequent stylesheet revisions address. A remaining low-priority improvement is retaining visible text on the mobile overview's primary “Find a relay” action instead of an icon alone. The schematic map is useful orientation, but tiny map labels should stay supplemental to the accessible pantry list. No additional illustration or animation is needed to make this product more convincing.

## Additional operational repair

**R6 — A transfer lost before arrival lacked a truthful terminal incident action — repaired and independently rechecked.** In the initial implementation, `arrive` accepted only `in_transit`, `receive` accepted only `arrived`, and `cancel` accepted only pre-pickup states. A never-arrived shipment could retain demand/capacity commitments indefinitely or require an untrue arrival record before full rejection.

`backend/main.py:962`, `fail_transfer`, now lets a coordinator record a reason and close an in-transit or arrived delivery as `failed`. Independent API reproduction returned 200 for a 120-pound transit failure: source stock remained 180 with its 180-pound reserve, the original need reopened to 120, its committed quantity became zero, received total remained zero, and the destination gained no lot. Repeating failure or attempting a later positive receipt returned 409. The API exposes `failed_lb`, writes a failure audit event and excludes the loss from received totals. Schema version 3 migration and failure regressions were added by the implementer. The final frontend source includes a coordinator action and reason form, while excluding failed transfers from active lists and capacity calculations.

## Business and story review

The $149/month offer is presented as a hypothesis for up to 10 sites. The value hurdle of 5.96 hours/month at a hypothetical $25/hour is arithmetically consistent. The cost model correctly separates its $30/hour support assumption and does not mistake contribution for profit. Ten paying networks would not yet constitute a mature business; the materials acknowledge the lean economics.

The six-week pilot has a named buyer, a baseline, a small participating network, existing transport and explicit stop rules. It needs to answer whether genuine transferable surplus exists, whether entry creates more work than it removes, and whether transport is economical. Existing MealConnect, Food Rescue Hero and pantry software remain credible alternatives or integration partners. The pitch must preserve that honesty.

The narrative should emphasize **a service gap, a protected reserve and a verified receipt**. Show one partial receipt, then its remaining gap and audit export. Avoid spending the demo on a long list of unrelated features. Explain that receipt totals measure pantry-to-pantry movement, not new food rescued or people fed.

## Final release checks for the coordinating reviewer

1. Confirm the full suite and frontend production build after the last edits; report actual results.
2. Exercise the positive and negative receipt cases through the browser, including zero cold acceptance and late confirmation.
3. Check empty-network setup, invite/join/driver permissions, expired-session recovery, need closure and mobile layout.
4. Verify the real deployment's persistence and backup/restore separately from the disposable public demo.
5. Reconcile final copy, screenshots and narration with the interface. Keep fictional demo labels visible.
6. Treat eligibility, a 2–6-person human team, late-proposal acceptance and the in-person presentation as participant requirements. Software cannot establish them.

This review supports continuing toward a supervised pilot after final verification. It does not establish production certification, field effectiveness or hackathon eligibility.
