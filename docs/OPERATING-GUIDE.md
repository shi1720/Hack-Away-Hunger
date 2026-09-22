# Pantry Relay operating guide

## A first network

Create an account with your name, email, a passphrase of at least12 characters, and network name. This creates an empty private workspace. Add approved pantry locations in **Pantries & needs**, including an address, coordinates, storage capabilities, and the maximum total weight each site can hold. Coordinates support approximate screening only. Confirm actual travel and receiving windows outside the app.

In **Inventory**, add only lots you want to manage in this workflow. Enter physical stock and a protected reserve for your own visitors. Food with donor or other transfer restrictions must be marked restricted. Enter the pantry's operational use-by cutoff based on its actual policy. That field does not certify safety or replace label interpretation.

In **Pantries & needs**, add the food category, total weight and service date for an upcoming gap. If a request was entered incorrectly or the service is canceled, close the request with a reason. Cancel any open commitments first. Create a corrected request when appropriate. Do not leave inaccurate needs in the planner.

## Plan a transfer

Set a maximum approximate distance, carrying capacity for each trip, and whether the transport can maintain cold/frozen conditions. Generate matches. Read the reasons and stock exclusions. The planner accounts for reservations and checks the whole proposal batch, but any proposal can become stale if stock changes. Reservation rechecks the current state atomically and may reject a stale proposal.

Protected stock, restricted lots, expired food, insufficient storage and incompatible transport prevent suggestions. The network operator must still authorize movement and verify actual travel time, access, donor terms, transport and food safety procedures.

## Complete the handoff

1. **Reserve.** Stock, recipient space and demand are committed. Physical food remains at the source.
2. **Accept at destination.** A coordinator records the receiving contact who agreed to take the food. This is an operator attestation, not independent identity verification.
3. **Record pickup.** Confirm condition and enter an observed temperature when required. Physical stock leaves the source at this step.
4. **Mark arrived.** The driver confirms physical arrival. Arrival alone does not count as accepted food.
5. **Confirm receipt.** Record actual accepted pounds, receiver name, and required temperature. Explain any shortfall. The destination receives a traceable stock lot protected by default for its own visitors.

## Exceptions

- **Before pickup:** cancel a reserved or accepted relay with a reason. The source stock remains in place and reservations release.
- **Damaged or missing food at receipt:** enter only accepted weight and explain the difference. The missing amount reopens the need, subject to its service deadline.
- **Reject everything:** enter0 accepted with an explanation. A missing or out-of-policy temperature can be recorded as a rejection instead of forcing a false successful receipt.
- **Lost or impossible delivery after pickup:** choose **Report failed delivery**. Explain the incident. The software releases the receiving capacity and need commitment, records a loss, and does not pretend the stock returned to the source. Follow the network's incident procedure.
- **Late receipt confirmation:** record the physical outcome. Accepted pounds remain throughput, but a confirmation after the service deadline does not credit that earlier service need. The system conservatively uses receipt-confirmation time because it cannot prove when food became available to the service.
- **Stale edit:** refresh and inspect the new inventory version before trying again.
- **Expired session:** sign in again; never share an account to bypass this.

## Reporting

**Impact & reports** sums actual accepted weight once per receiving record. A partially accepted shipment contributes only its accepted portion. A failed shipment contributes zero. Receipt differences and the audit trail remain visible/exportable. These measures describe transfers, not incremental waste avoided, household consumption, meals, carbon or people reached.

Receipt CSV includes actual quantities and timeliness fields. Audit CSV includes actor and action history. Treat exports as operational records and use your organization's retention policy. CSV protection prevents leading formula markers in user-controlled cells from being treated as formulas in common spreadsheet applications.

## People and permissions

Admins manage invitations and operations. Coordinators manage stock, requests and handoffs. Drivers can record pickup and arrival; they cannot adjust inventory, accept receiving responsibility or confirm the final received weight. Coordinators are trusted across the entire network. There is no per-pantry coordinator isolation in this release.

Share invitation links only with the intended verified person. They expire and work once. Demo workspaces cannot invite teammates. For account recovery, use the verified local-operator procedure in SECURITY.md. There is no automated email service.

## Offline contingency

The installed application operates without external APIs while the local server is available. It is not an offline-synchronizing PWA. A disconnected phone cannot queue writes. Print a transfer manifest before departure, capture observations on paper, then have the responsible coordinator enter the record. Do not fabricate a timestamp to make a late entry appear on time.
