# Pantry Relay : independent provisional review

Review date: September 22, 2026. This is an internal, AI-assisted evaluation against the published hackathon rubric, not a score from the event's judges or a prediction of winning. Reviewed the actual backend, frontend source, tests, research, business/pilot plans, Devpost copy, demo script and five rendered desktop/mobile screenshots. The coordinating reviewer also supplied results from the actual browser workflow. The original review preceded the final public deployment. The dated engineering addendum below records later supplied execution evidence. Live pantry use remains untested.

## Assessment

The project has a coherent, useful scope: an approved pantry network can record a near-term category need, reserve food another pantry can spare, and reconcile the actual receipt. The strongest demonstration is a partial receipt that preserves the difference between promised stock and accepted food. The release is more credible because it avoids inventing customers, meals served, carbon savings or an AI requirement.

The principal remaining uncertainty is whether enough real, permitted pantry-to-pantry transfers occur to justify another workflow and recurring subscription. Public research establishes the surrounding network and incumbents; it does not establish that operators need this particular product. More features cannot substitute for observing that work.

## Original provisional rubric score

| Criterion | Available | Provisional | Basis |
| --- | ---: | ---: | --- |
| Community impact | 30 | 22 | Direct link between declared need and recorded food receipt; sensible measurement plan and no household data. No field baseline, participating pantry or observed impact yet. |
| Innovation | 20 | 14 | Source reserve protection, service-specific demand and accountable receipt form a distinctive focus. Existing rescue platforms already have matching and dispatch, so this is a focused workflow improvement rather than a wholly new category. |
| Technical execution | 20 | 18 | Real persistence, role and tenant controls, exact quantity accounting, transactional reservations, state transitions, audit/export and meaningful regression tests. Verified accounting repairs and an independently checked failure closeout strengthen this score. The implementer now reports 129 passing backend tests across SQLite and PostgreSQL, with five storage-specific skips. The addendum records the later public deployment checks. This row retains the original provisional engineering score rather than presenting an event judge result. |
| Feasibility and sustainability | 15 | 11 | One network buyer, low infrastructure dependency, honest price/cost assumptions, free self-hosting and a practical pilot. Entry burden, transfer economics, integration needs and willingness to pay are still unvalidated. |
| User experience and design | 10 | 8 | Cohesive, polished visual system and a clear partial-receipt workflow; supplied mobile screenshots stack cleanly, with reported no 390px overflow and successful Escape handling. Final automated axe results show zero WCAG 2.1 A/AA violations across 24 views/states. Operational recovery and field labels are repaired. Actual volunteer usability, assistive-technology use and full keyboard navigation still need observation. |
| Presentation | 5 | 4 | Strong single-story script, candid competitor positioning, usable judge answers and a concrete pilot ask. Final recording, deck rendering and in-person eligibility are not established by this review. |
| **Total** | **100** | **77** | **Provisional internal assessment, not an event result.** |

The accessibility repairs remove the known contrast and field-label defects. The UX score remains 8 because automated checks and polished screenshots do not establish ease of use for real pantry staff. The largest potential improvement in the overall submission comes from credible operator evidence and a smooth presentation, not inflated claims or more screens.

## Review method and independent checks

Used temporary SQLite databases under a disposable test directory. No real workspace data was changed. The existing backend test suite was read rather than redundantly executed in full; the backend implementer owns the suite run and its results. This reviewer ran narrow API reproductions for identified issues and independent access-control probes. The backend implementer subsequently reported 129 passing tests across SQLite and PostgreSQL, five storage-specific skips and clean Ruff checks. That is a reported suite result, not an independent rerun by this reviewer. Early local browser checks were followed by the larger cross-browser and hosted runs recorded in the dated addendum.

An attempted direct browser review could not start: the in-app browser was unavailable and Chrome session setup failed on runtime authentication. No browser interactions or operational records were changed by this reviewer. Instead, the reviewer visually inspected `artifacts/screenshots/landing.png`, `overview.png`, `planner.png`, `impact.png` and `mobile.png`. The coordinating reviewer reported successful actual-browser partial receipt, CSV download, reload persistence, reopened 8-pound need, 390px mobile overflow check and Escape dismissal. This is supplied execution evidence, not a claim that this reviewer personally ran those browser actions.

The reviewer also read `artifacts/verification/frontend-accessibility.json`: all 24 named views/states have empty violation arrays. The frontend's final rendered audit used WCAG 2.1 A/AA rules and includes forms, failed-delivery recovery, receipt states and the mobile overview. This is supplied automated execution evidence; it does not certify accessibility or cover every possible interaction.

Observed access results:

- A second network's lot edit, transfer acceptance and transfer creation each returned **404**.
- A driver attempting to invite, accept, plan or export receipts received **403**.
- The driver workspace omitted inventory lots and needs.
- A consumed invitation returned **400** on reuse; its original join assigned the server-stored driver role.
- The planner and receiving records use integer hundredths of a pound internally. Reservation writes use `BEGIN IMMEDIATE`; pending incoming quantities are included in receiving capacity.

Read regression coverage includes concurrent duplicate reservation, source reserve preservation, stale inventory edits, inbound capacity through arrival, partial and full rejection, cold thresholds, invalid transitions, tenant boundaries, role escalation, expired sessions/invites, production configuration and CSV formula injection. A test's presence is not a substitute for its executed result; see the final verification document for that result.

## Important findings and verified repairs

Line references identify the reviewed source snapshot; function names remain the stable reference if formatting changes.

### R1 : Late receipt incorrectly fulfilled a missed service : repaired and independently rechecked

Initial location: `backend/main.py`, `receive`, originally lines 418–444. A transfer was picked up while its service was upcoming; its need was then advanced past deadline in the isolated test database. Receiving 112 pounds returned 200 and increased that already-missed service's `fulfilled_lb` by 112.

Repaired behavior in `receive` (formatted source: `backend/main.py:866`, credited quantity at line 920): late confirmation still records physical accepted stock, but credits **zero** toward the missed service. The response and report distinguish `on_time`, `late` and `need_credited_lb`. Independent recheck returned `fulfilled_lb=0`, `late=true`, `need_credited_lb=0`, with 112 pounds actually received preserved.

The timestamp measures receipt confirmation, not guaranteed physical arrival. Current user-facing language and the audit say receipt was confirmed after the service deadline. This distinction matters if someone records a timely physical delivery late.

### R2 : Received stock could immediately be sent away again : repaired and independently rechecked

Initial location: `backend/main.py`, `receive`, originally line 440. The destination lot was created with no protected reserve. A second need made the planner offer all 112 just-received pounds to a third pantry while the first pantry's service remained credited as fulfilled.

Repaired behavior in `backend/main.py:866`, `receive`, creates the received lot with **reserve equal to accepted quantity**. Independent recheck showed quantity 112, reserve 112, available 0, and no downstream proposal from that lot. A coordinator can intentionally release reserve through an audited stock adjustment. Regression coverage exercises both protection and deliberate release.

### R3 : Restricted stock was labeled shareable : repaired and independently rechecked

Initial locations: `backend/domain.py`, `available_units`, and `frontend/src/views.tsx`, `Inventory`. A restricted 30-pound lot returned `available_lb=30`; the inventory row labeled that quantity shareable even though matching and the global total excluded it.

`available_units` (`backend/domain.py:78`) now returns zero for restricted or expired lots. Independent recheck returned **0** for the restricted lot. The underlying quantity is retained so the physical inventory is still accurate.

### R4 : Real invitees could join a disposable demo network : repaired and independently rechecked

Initial locations: `backend/main.py`, `invite` and `join`, originally lines 203–230. A sample-workspace administrator could generate an invitation, and an ordinary email/password user could join. Demo cleanup would later delete that supposedly normal account and its work.

Both endpoints (`backend/main.py:263` and `backend/main.py:292`) now reject demo-network membership, including previously generated demo invites. Independent invite recheck returned **403**. The final frontend hides the invitation action in a demo and explains that real team onboarding starts with an empty registered network.

### R5 : A mistaken or canceled need had no recovery action : backend repair independently rechecked; UI source checked

Initial locations: `backend/main.py`, `create_need`, and `frontend/src/views.tsx`, `Sites`. A mistaken quantity or canceled service remained eligible for planning until its time passed.

The new `POST /api/needs/{id}/close` endpoint (`backend/main.py:667`) preserves the original record and audits a reason. It refuses closure with active transfers. Independent close returned **200** with `closed=true` and remaining quantity zero. Regression tests cover active commitments, repeated closure, stale proposals, tenant scope and schema migration. The final `Sites` and `Forms` source includes the close action, reason form and closed-state label.

## UI findings and source recheck

These were sent to the frontend implementer. The final source was reread after the changes; all five repairs below are present. The supplied browser workflow and accessibility evidence provide additional verification; see the final project verification record for the complete end-to-end scenario results.

| Initial priority | Final reviewed location | Finding and repair |
| --- | --- | --- |
| P1 | `frontend/src/Forms.tsx:513` and `:637` | Full cold rejection originally required a temperature. The form now makes it optional only at zero accepted weight, sends null when blank and preserves the required exception reason and positive-acceptance checks. |
| P2 | `frontend/src/views.tsx:68`, `Overview` | Past unmet needs originally became “NEXT SERVICE.” The current filter requires an open need, positive remaining quantity and future service time. |
| P2 | `frontend/src/api.ts:25` and `frontend/src/App.tsx:83` | Expired sessions originally stranded local signed-in state. Authenticated-request 401 now dispatches a session-expired event that clears the session, workspace and modal and returns to authentication. |
| P2 | `frontend/src/views.tsx:1154` and `:1488` | Late receipts originally had no visible distinction. Delivery cards now say receipt was confirmed after the service, and impact rows show the service-credited quantity separately. |
| P3 | `frontend/src/App.tsx:374` and `frontend/src/Forms.tsx:374` | Times originally lacked a visible zone. The footer and service-time input now name the browser's timezone. |

Static CSS review also identified **P2 contrast/readability issues** in the initial styles: hero description `#7f8777` on `#f8f9f2` was 3.52:1; helper text `#7d8976` on `#f7f8f2` was 3.44:1; field hints `#83907d` on `#fffef9` were 3.33:1; small labels `#929a8b` on `#fffef9` were 2.88:1. These are below 4.5:1 for normal text. Several mobile rules reduced operational metadata to 7–9 px. The final stylesheet darkens informational text and enlarges critical metadata. Field labels and their hints now have explicit associations. The final rendered axe audit reports zero violations in 24 views/states. Neither the initial source calculations nor the final automated scan is a complete accessibility certification.

### Visual critique

The rendered identity is consistent across landing, planning and reporting: a forest-green sidebar, warm background, restrained accent and readable large serif headings. The planner gives the food, source/destination and quantity distinct positions. The 112-pound receipt view is a strong presentation moment without pretending to count people. Mobile retains the important content without overlapping panels in the supplied screenshot.

The first screenshot set exposed overly faint small metadata, which the subsequent stylesheet revisions address. The initial mobile screenshot made the primary action less obvious when reduced to an icon. Retaining its visible “Find a relay” text is a low-priority usability check on the final recording. The schematic map is useful orientation, but tiny map labels should stay supplemental to the accessible pantry list. No additional illustration or animation is needed to make this product more convincing.

## Additional operational repair

**R6 : A transfer lost before arrival lacked a truthful terminal incident action : repaired and independently rechecked.** In the initial implementation, `arrive` accepted only `in_transit`, `receive` accepted only `arrived`, and `cancel` accepted only pre-pickup states. A never-arrived shipment could retain demand/capacity commitments indefinitely or require an untrue arrival record before full rejection.

`backend/main.py:962`, `fail_transfer`, now lets a coordinator record a reason and close an in-transit or arrived delivery as `failed`. Independent API reproduction returned 200 for a 120-pound transit failure: source stock remained 180 with its 180-pound reserve, the original need reopened to 120, its committed quantity became zero, received total remained zero, and the destination gained no lot. Repeating failure or attempting a later positive receipt returned 409. The API exposes `failed_lb`, writes a failure audit event and excludes the loss from received totals. Schema version 3 migration and failure regressions were added by the implementer. The final frontend source includes a coordinator action and reason form, while excluding failed transfers from active lists and capacity calculations.

Account recovery is also supplied as an operator task: `scripts/account_admin.py` can reset a password interactively or revoke an account's sessions against the configured database. It records a local-operator audit event and revokes existing sessions on a password reset. This is deliberately not self-service email recovery; a deployed network still needs an authorized operator and a documented identity-verification process.

## Business and story review

The $149/month offer is presented as a hypothesis for up to 10 sites. The value hurdle of 5.96 hours/month at a hypothetical $25/hour is arithmetically consistent. The cost model correctly separates its $30/hour support assumption and does not mistake contribution for profit. The illustrative $15 infrastructure allocation is not a measured Cloud SQL bill; actual managed-hosting costs and any temporary credits must be reconciled before quoting hosted margins. Ten paying networks would not yet constitute a mature business; the materials acknowledge the lean economics.

The six-week pilot plan defines a buyer role, a baseline, a proposed small network, a requirement for existing transport and explicit stop rules. No network has agreed to participate. It needs to answer whether genuine transferable surplus exists, whether entry creates more work than it removes, and whether transport is economical. Existing MealConnect, Food Rescue Hero and pantry software remain credible alternatives or integration partners. The pitch must preserve that honesty.

The narrative should emphasize **a service gap, a protected reserve and an operator-confirmed receipt**. Show one partial receipt, then its remaining gap and audit export. Avoid spending the demo on a long list of unrelated features. Explain that receipt totals measure pantry-to-pantry movement, not new food rescued or people fed.

## Release findings and current status

| Priority | Remaining issue | Concrete completion check |
| --- | --- | --- |
| P1, resolved | Local tests alone did not prove the deployed PostgreSQL-backed service worked. | The live Firebase application passed the full 24-scenario Chromium run; WebKit passed its 22-case baseline and both added short-desktop regressions. The authenticated session and reserved transfer survived forced Cloud Run revision replacement. See the addendum and evidence files. |
| P1, reconciled in submission kit | The storage and hosting design changed after the original copy was written. Conflicting SQLite-only descriptions or old test counts would weaken credibility. | The submission kit and verification record now describe SQLite self-hosting plus PostgreSQL cloud operation, live hosting and explicit evidence. Spoken narration contains no changing test counts. Recheck the final rendered slides and actual submitted fields against this copy. |
| P2 | The $149 price and $15 infrastructure allocation remain hypotheses, and managed database cost can change the margin. | Record actual cloud resources, a non-promotional monthly estimate and a cost owner. Preserve the distinction between proposed price, assumed support cost and observed cost. |
| P2 | A feature-heavy video could hide the most persuasive behavior. | Center the actual 120 dispatched, 112 accepted and 8 remaining sequence. Show the operator-confirmed receipt and remaining need. Keep the fictional-data and synthetic-voice disclosures visible. |

The final narration has 415 spoken words across ten short segments, with matching application scenes. The generated narration timeline in `tmp/video/scenes.json` is 170.6115 seconds. The rendered 1080p MP4 is 170.633333 seconds, approximately 2 minutes 51 seconds, with H.264 video and AAC audio. YouTube publication and Devpost completion are not yet claimed. No new major accounting defect was found in the final source pass. The new PostgreSQL adapter uses transaction-wide advisory write locking and repeatable read snapshots, preserving the deliberately bounded concurrency model. The supplied regression and hosted evidence now complement this source review. They do not turn it into an independent penetration test or real-world impact evaluation.

The largest unresolved product risk remains adoption. Required stock/need entry, manually supplied coordinates and transport coordination impose real operator work. These should be observed in the proposed pilot before adding integrations or expansion. A willingness-to-pay claim cannot be repaired by improving the wording.

## Final engineering addendum, September 22, 2026

The original **77/100** remains a historical internal rubric assessment. The evidence below materially reduces engineering and deployment uncertainty. It does not establish adoption, willingness to pay, field outcomes or an event judge score.

- **Backend:** 129 reported passing tests across SQLite and PostgreSQL, with five intentional storage-specific skips. The coordinating team also reports clean lint/build checks.
- **Local and CI browsers:** the expanded 24-scenario Chromium suite passed. WebKit passed the original 22-case suite and the two added short-desktop cases on a fresh database. Firefox passed the 22-case baseline in Linux CI; the expanded Firefox run is not yet claimed. [GitHub Actions run 35690841301](https://github.com/shi1720/Hack-Away-Hunger/actions/runs/35690841301) succeeded.
- **Hosted browsers:** this reviewer read the retained baseline reports `artifacts/verification/hosted-chromium.json` and `hosted-webkit.json`, each with 22 passes and no skipped, failed or flaky results. The later `frontend-cross-browser.json` records a full 24-case hosted Chromium pass after the sidebar repair. `hosted-webkit-short-desktop.json` records both added cases passing in a targeted run. WebKit coverage is reported as 22 plus two, not a single expanded full-suite run. These are supplied execution artifacts, not browser actions personally performed by this reviewer.
- **Live persistence:** `artifacts/verification/hosted-restart.json` records that an authenticated session and a reserved 120-pound transfer survived forced Cloud Run revision replacement at `https://pantryrelay.web.app`. Registration is enabled on the actual public application.
- **Backup:** the coordinating team reports daily Cloud SQL backups with seven retained backups and successful on-demand backup `1790055203051`. Backup creation is not proof that a restore drill has been performed.
- **Late responsive finding, repaired:** a short-desktop sidebar could place sign-out below the visible area. The frontend implementer added independent sidebar scrolling and two regression scenarios at 1600 by 800 and 1280 by 600. Both now pass locally and on the hosted app in Chromium and WebKit, including the receipt, inventory, report and sign-out sequence.

The remaining release checks are to record the expanded Firefox result if completed, inspect final captions, verify the public walkthrough page and verify publication/submission confirmations. Before a real pantry pilot, perform a cloud restore drill, assign the operator and confirm transport/food procedures. Eligibility, the 2-6-person human team, late-proposal acceptance and in-person presentation remain participant requirements that software cannot establish.

This review supports the application's readiness for a supervised technical evaluation and a carefully agreed pilot. It does not establish production certification, field effectiveness, video publication or hackathon eligibility.
