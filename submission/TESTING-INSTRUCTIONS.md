# Pantry Relay: testing instructions

Project lead: Shivam Gupta. These instructions cover the quick judge walkthrough, account setup, recovery paths and reproducible automated checks. Use fictional test data throughout. The application does not need an AI API key or a mapping account.

**Live application:** https://pantryrelay.web.app  
**Repository:** https://github.com/shi1720/Hack-Away-Hunger  
**Local application:** http://localhost:8010

The Firebase application is deployed and verified, with account registration enabled. Hosted Chromium passed the full 24-scenario suite. Hosted WebKit passed the 22-scenario baseline and both added short-desktop regression cases. Exact run evidence is tracked in the final verification record. No shared test password is needed: start a fictional demo or create your own empty test network.

## 1. The five-minute judge walkthrough

Open the application and choose **Explore the live demo**. No shared password is needed. The app creates a separate sample network for the session. Sample pantries, service times and food records are fictional. A fresh demo starts with no completed receipts, so results are easy to follow.

| Step | Action | Expected result |
| --- | --- | --- |
| 1 | Look at Overview. | The demo indicator is visible. The overview shows upcoming category needs, available food and a schematic pantry map. |
| 2 | Open **Relay planner**, keep the initial constraints, then select **Find matches**. | Explained proposals appear, alongside reasons stock cannot be offered. Distance is labeled as an estimate. |
| 3 | Find the **120 lb produce transfer** from Cedar Grove Pantry to Eastside Community Pantry. Review its reserve and matching reasons. | The proposal uses food above the source's protected reserve and fits the receiving need. |
| 4 | Select **Reserve this relay**, then open **Deliveries**. | The transfer has a Reserved status. Its stock and receiving capacity are committed. Received impact is still zero. |
| 5 | Select **Accept at destination**. Enter “Jordan, demo receiver”, then **Accept transfer**. | The status becomes Accepted. |
| 6 | Select **Record pickup**. Confirm the condition checkbox for this simulated scenario. If the chilled-food temperature field appears, enter **38°F**. Select **Confirm pickup**. | The status becomes In transit. The source's physical quantity decreases. A frozen-food scenario requires a different, valid frozen reading; do not use 38°F for frozen food. |
| 7 | Select **Mark arrived**, then confirm in the dialog. | The status becomes Arrived. No receipt has been counted yet. |
| 8 | Select **Confirm receipt**. Enter **112 lb**. If a chilled-food temperature field appears, enter **38°F**. Enter the exception: “8 lb damaged in transit, sample scenario.” Confirm receipt. | The transfer becomes Received, preserving the 120-pound dispatch, 112-pound acceptance and 8-pound exception. |
| 9 | Open **Impact & reports**. | The accepted-weight total is **112 lb**, with the exception visible. The record does not claim meals or people fed. |
| 10 | Select **Export receipts** and open the downloaded CSV. | The file contains the actual receipt, exception and service-credit information for this network. Export the audit record as well if desired. |
| 11 | Reload the page. | The same network and its 112-pound receipt remain available in the session. |
| 12 | Open **Pantries & needs**, then **Inventory**. | Eastside's upcoming need has **8 lb remaining**. Its received 112-pound lot has a protected reserve of 112, leaving zero available for immediate redistribution. |

If the 120-pound proposal has already been used, sign out and start a fresh demo. Do not enter 112 against a different transfer quantity. Demo times are generated relative to creation; complete the walkthrough before its service deadline. A late confirmation correctly earns zero service-gap credit even if physical accepted food is recorded.

Demo sessions are disposable. Browser refresh persistence is not a promise that a public demonstration host keeps data permanently. Do not enter real pantry or household information into sample workspaces.

## 2. Test a real empty network

Choose **Start a network** on the live application or the complete local application from section 5. Registration is enabled on the deployed Firebase app. Do not try to invite people into a disposable sample network.

1. Enter your display name, a fictional network name, a unique test email address and a dedicated password of at least 12 characters. Select **Create network**. No email is sent by the application.
2. Verify that the network starts empty rather than inheriting sample records.
3. Add two fictional pantries. For a reproducible local example use **QA West** at latitude `41.60`, longitude `-93.60`, and **QA East** at latitude `41.61`, longitude `-93.59`. Use clearly fictional street addresses, ambient storage and capacity of at least 100 lb at each site.
4. Under **Inventory**, add an ambient produce lot at QA West with **50 lb on hand**, **20 lb protected reserve** and a use-by cutoff at least 48 hours ahead. Its shareable quantity should be **30 lb**.
5. Under **Pantries & needs**, add a **30 lb produce need** at QA East with a service time about 24 hours ahead. The input names the browser's timezone.
6. Find matches and reserve the 30-pound transfer. Follow acceptance, pickup, arrival and receipt. Ambient stock does not require a cold-temperature entry. Accept all 30 pounds for this scenario.
7. Verify 20 pounds remain at QA West, the receiver holds 30 protected pounds, the category need is filled and the received total is 30 pounds.
8. Sign out, then sign in with the same email and password. Verify your network records remain present.

An account establishes an application workspace, not approval from a food bank or permission to transfer restricted stock. Those relationships are a pilot responsibility.

## 3. Test invitations and driver permissions

Use the registered network from section 2. Invitations are intentionally disabled in disposable demo networks.

1. As the network administrator, open **Your team**, then **Invite teammate**.
2. Select **Driver** and create the invitation. Copy the private link. The application does not send an email.
3. Open the link in a separate private browser window or browser profile. Create the driver account using a different unique test email and a dedicated password.
4. Verify the driver sees **Your delivery board** and does not have Inventory, Relay planner, Impact or team-management navigation.
5. With an accepted transfer available, the driver can record pickup and arrival. The coordinator handles acceptance and final receipt. A driver cannot create proposals, change stock, invite teammates or export network reports.
6. Open the consumed invitation in another private session. Reusing it must fail. Its role cannot be changed by modifying the join page.

The automated backend suite also checks role enforcement directly against the API. Hiding a navigation item alone would not establish authorization.

## 4. Check honest exception handling

Use a fresh demo for each case so the expected totals are unambiguous. Record the relevant transfer quantity before acting.

| Scenario | How to exercise it | Expected behavior |
| --- | --- | --- |
| Cancel before pickup | Reserve a transfer, then cancel it with a reason. | The transfer remains in history as canceled. Stock and receiving-space commitments are released. Nothing counts as received. |
| Delivery fails after pickup | Reserve, accept and pick up. Choose **Report failed delivery**, then supply a reason. | The status becomes Failed. Source stock stays deducted, need and capacity commitments are released, no destination lot is created and received impact stays zero. |
| Full rejection | Advance a transfer to Arrived, then enter **0 lb** accepted and an exception reason. For cold stock, leave an unavailable temperature blank. | The full rejection can be recorded without inventing a temperature. No food is added at the destination and no received pounds are counted. |
| Invalid positive cold receipt | On an arrived chilled transfer, try to accept a positive quantity with a temperature outside its permitted range. | Acceptance is rejected. The record remains available for truthful rejection or incident handling. |
| Incorrect service need | Create an additional need, then select **Close** and enter a reason. | The record is retained as Closed and no longer receives proposals. A need with active transfer commitments cannot be closed. |
| Restricted stock | Add a lot marked restricted. Run the planner. | It remains visible as physical inventory but has zero shareable quantity and is excluded from transfers. |
| No feasible match | Use a very small distance limit or a storage/vehicle combination that cannot handle the candidate food. | The planner explains the lack of workable matches without inventing a transfer. |
| Repeated action | Attempt an already-completed state transition again through a stale page or the relevant automated test. | The backend rejects the invalid transition instead of double-counting it. |
| Session expires | In a local test, revoke the test account's sessions with the operator command below, then perform another authenticated action in its browser. | The interface returns to authentication with session-expiry feedback rather than trapping an apparently signed-in workspace. |
| Receipt after service deadline | Use the isolated automated late-receipt test. | Physical accepted stock is recorded; `need_credited_lb` is zero and the report flags the late confirmation. Do not alter a shared host's database to demonstrate this. |

For a narrow viewport, set the browser to 390 pixels wide. Confirm the navigation opens, content fits without horizontal page scrolling, a form opens, and Escape dismisses its dialog. Automated accessibility checks supplement this exercise; they do not replace keyboard and screen-reader evaluation with people.

## 5. Run the complete application locally

Prerequisites: Git, Python 3.11 or later, Node.js 22 or later, npm, and `uv`. The first dependency installation needs internet access. The running local application needs no cloud account or API key.

```sh
git clone https://github.com/shi1720/Hack-Away-Hunger.git
cd Hack-Away-Hunger
./scripts/start.sh
```

Open http://localhost:8010. Keep the terminal running. The script installs locked frontend dependencies, builds the interface and starts FastAPI. Stop it with Ctrl+C. Local records use the configured SQLite database and are retained across application restarts. See `docs/DEPLOYMENT.md` before exposing the service publicly.

## 6. Reproduce automated checks

Run these from the repository root:

```sh
uv sync --frozen --extra dev
uv run pytest
uv run ruff check backend tests
```

Without additional configuration, the backend suite uses isolated temporary SQLite databases. To reproduce coverage across both storage engines, set `PANTRY_TEST_POSTGRES` in your environment to an authorized **test PostgreSQL database**, then rerun `uv run pytest`. Its test role needs permission to create and drop temporary schemas. The fixture creates a unique schema per test and removes it afterward. Do not point this test setting at the live pantry database or print its credential-bearing connection string in a shared terminal recording. The two-engine run has a different test count from the default SQLite-only run; five storage-specific cases are intentionally skipped for PostgreSQL.

Then build the frontend:

```sh
cd frontend
npm ci
npm run build
cd ..
```

The browser-test helper starts its own instance on an available local port against a temporary test database, installs Chromium and runs the browser scenarios:

```sh
./scripts/test_browser.sh
```

To select WebKit, run `PANTRY_BROWSER=webkit ./scripts/test_browser.sh`. Firefox is selected with `PANTRY_BROWSER=firefox` and has been verified in the Linux CI environment.

Alternatively, with a local application already running, run the browser tests against it. This creates fictional QA accounts and records in that instance, so use only an instance intended for testing:

```sh
cd browser-tests
npm ci
npx playwright install chromium
npm test
```

The test definitions are `browser-tests/workflow.spec.ts` and `browser-tests/recovery.spec.ts`; the browser configuration is `browser-tests/playwright.config.ts`. A failed run retains traces and screenshots. Open the generated HTML report with `npx playwright show-report` from the browser-tests directory. The hosted target can be selected with `BASE_URL=https://pantryrelay.web.app`; use an authorized test target because these tests create fictional QA accounts and records. Use `PANTRY_BROWSER` to select Chromium, WebKit or Firefox and install the corresponding engine first.

## 7. Operator recovery and backup checks

These commands require authorized access to a **local test database**. Substitute its actual path and the test account's email. Do not use an account you do not administer.

```sh
uv run python scripts/account_admin.py revoke-sessions \
  --database data/pantry-relay.sqlite3 \
  --email your-test-account@example.org
```

```sh
uv run python scripts/account_admin.py reset-password \
  --database data/pantry-relay.sqlite3 \
  --email your-test-account@example.org
```

The reset command requests the new password interactively, revokes existing sessions and records a local-operator audit event. It does not print the password. Verify the old password fails and the new password signs in. There is no self-service email reset in this release. The same operator command supports PostgreSQL through `PANTRY_DATABASE`; use authorized secret handling rather than putting a credential-bearing URL into a recorded command line.

To create an online backup of a running local test instance:

```sh
uv run python scripts/backup.py \
  data/pantry-relay.sqlite3 \
  backups/pantry-test-backup.sqlite3
```

This backup command is for SQLite. Use a new backup filename because overwrite is intentionally refused. Restore into a separate stopped test instance following `docs/DEPLOYMENT.md`, then verify sign-in, workspace records and receipt export. PostgreSQL and Cloud SQL require their corresponding database backup/restore procedure. Do not overwrite a working instance merely to try the product. The automated suite includes recovery checks, but each real deployment still needs its own tested backup procedure.

## Recorded results and limits

The latest reported backend verification is **129 passing tests across SQLite and PostgreSQL**, with **five storage-specific skips**. Ruff and the TypeScript production build passed. Chromium passed the **complete 24-scenario suite locally and on the hosted app**. WebKit passed the **22-scenario baseline plus both new short-desktop cases**, locally and on the hosted app. These are separate WebKit runs, not a claimed single 24-case run. Firefox passed the **complete 24-scenario suite in Linux CI**. A rendered axe audit found zero WCAG 2.1 A/AA violations across **24 views and states**. The checked 320-pixel and 390-pixel layouts had no horizontal page overflow.

`docs/VERIFICATION.md` is the canonical results record. `artifacts/verification/frontend-accessibility.json` contains the 24-state accessibility findings. Hosted evidence is in `artifacts/verification/frontend-cross-browser.json` for the complete expanded Chromium suite, `hosted-webkit.json` for its 22-case baseline and `hosted-webkit-short-desktop.json` for the two added cases. The earlier Chromium baseline is retained in `hosted-chromium.json`. `hosted-restart.json` records that an authenticated session and reserved 120-pound transfer survived forced Cloud Run revision replacement. GitHub Actions run `35692685218` succeeded. Cloud SQL has daily backups with seven retained copies, and on-demand backup `1790055203051` succeeded; a cloud restore drill remains a separate check.

No real pantry trial, paid-customer validation, independent penetration test, sustained load test or food-safety certification has occurred. Browser coverage includes Chromium and WebKit locally and on the hosted application, and Firefox in Linux CI. WebKit is not a claim of physical Safari-device testing; a hosted Firefox run is not claimed. Real transport, approval and food-handling decisions remain with the participating network.
