# Verification record

Date: September 22, 2026. Checks use fictitious data. This record separates automated verification from field validation.

## Backend, local browser and CI checks

| Check | Result |
|---|---|
| Backend automated suite |129 passing tests across SQLite and PostgreSQL; 5 intentional storage-specific skips|
| Backend lint |Ruff check and formatting pass|
| TypeScript and production asset build |Pass|
| Frontend dependency audit |0 reported vulnerabilities at build time|
| Local Chromium |24 scenarios passed in the complete expanded suite|
| Local WebKit |22-scenario full baseline passed; both new short-desktop scenarios also passed on a fresh database|
| Firefox Linux CI |24 scenarios passed in 45.6 seconds|
| Chromium partial receipt workflow |Pass:120 reserved/dispatched,112 accepted,8 difference, export, reload persistence, reopened need|
| Real account onboarding |Pass:register, add pantry, stock and protected reserve, request, close incorrect request, sign out and sign in|
| Driver invitation |Pass:separate browser account joins as driver and sees transport view without operator navigation|
| Session expiry recovery |Pass:cleared session returns to authentication instead of trapping the user|
| Mobile320px and390px |No horizontal page overflow; navigation and Escape-to-close dialog pass|
| Automated accessibility |0 WCAG A/AA/2.1 violations across24 screens, forms and transfer states|
| Independent API review |Tenant probes, role denials, late receipt, received-stock protection, request closure and failed delivery independently checked|
| PostgreSQL cross-instance persistence |Independent application instances retain sessions, receipt history and inventory; concurrent reservation race yields one success and one conflict|
| Firebase session security |`__session` cookie, exact trusted browser origins, CSRF, logout and no-store response tests pass|
| Database backup and recovery |Live WAL backup restores login, workspace and receipt CSV; overwrite guard and corrupt-backup cleanup tested|
| Account recovery |Session revocation and password reset tested without logging credentials|

The browser definitions in `browser-tests/workflow.spec.ts` and `browser-tests/recovery.spec.ts` now contain 24 scenarios. Chromium passed the complete expanded suite locally and on the live application. WebKit passed the original 22-scenario suite and then the two added short-desktop cases locally and on the hosted application. Firefox passed the complete 24-scenario suite in Linux CI. An initial run exposed low-contrast text, which was corrected. Test-only locator mismatches were repaired to reflect explicit form labels. Final application flows pass. Accessibility evidence is in `artifacts/verification/frontend-accessibility.json`, with the core landing/overview/planner recheck files beside it.

The dual-database run uses a real PostgreSQL 15 server in isolated temporary schemas. SQLite-specific backup and migration tests and PostgreSQL-specific durability tests skip their inapplicable backend. These are local database tests, not proof of a successful public deployment.

Backend coverage includes fractional-weight precision, invalid and nonfinite inputs, stale edits, source reserves, destination capacity, restrictions, expiry, no matching storage, cold-chain checks, partial/full rejection, duplicate transitions, simultaneous reservations, active-request closure rejection, loss after pickup, late confirmation, cross-network access, role enforcement, invite replay, demo expiration, CSRF, origin checks, production configuration, and schema migrations preserving history.

The completed [GitHub Actions run 35692685218](https://github.com/shi1720/Hack-Away-Hunger/actions/runs/35692685218) succeeded. Its logs record 129 backend passes with five skips, 24 Chromium scenarios in 35.3 seconds, 24 Firefox scenarios in 45.6 seconds and a successful Docker image build. This is an executed run, not merely the presence of a workflow definition.

## Verified public deployment

Live application: **https://pantryrelay.web.app**. Firebase Hosting serves the public address, Cloud Run serves the application, and PostgreSQL on Cloud SQL retains operational records. Account registration is enabled, alongside isolated fictional demo workspaces.

| Check | Result and evidence |
| --- | --- |
| Hosted Chromium |24 scenarios passed in the expanded full suite, with 0 failures, flaky results or automatic retries. Evidence: `artifacts/verification/frontend-cross-browser.json`, under `sidebar_regression`. The earlier 22-case report is retained in `hosted-chromium.json`. |
| Hosted WebKit |The full 22-scenario baseline passed, then both added short-desktop regressions passed in a targeted run. No failures or flaky results. Evidence: `artifacts/verification/hosted-webkit.json` and `hosted-webkit-short-desktop.json`. This is not described as a single 24-case WebKit run. |
| Cloud Run revision replacement |An authenticated session and a reserved 120-pound transfer survived forced revision replacement. Evidence: `artifacts/verification/hosted-restart.json`. |
| Cloud SQL backup configuration |Daily automatic backups configured with seven retained backups. |
| Cloud SQL on-demand backup |Backup `1790055203051` completed successfully. This establishes backup creation, not a performed cloud restore drill. |

The retained hosted baseline reports started September 22, 2026 at 05:32 UTC for Chromium and 05:34 UTC for WebKit. Supplemental reports cover the later sidebar correction at 1600 by 800 and 1280 by 600 pixels. They exercise the application on the live Firebase origin, including account and invitation flows, receipts and recovery behavior. Firefox was checked in Linux CI; a hosted Firefox run is not claimed. WebKit automation is not real-device Safari testing.

The demonstration video has rendered to `output/Pantry-Relay-Demo.mp4`: 1920 by 1080 pixels, H.264 video and AAC audio, duration 170.633333 seconds. Evidence is `artifacts/verification/video-metadata.json`. The public walkthrough at https://pantryrelay.web.app/demo is deployed and verified in Chromium and WebKit. Both played the unmuted 1920 by 1080 video, advanced playback, sought successfully and loaded the pitch PDF with HTTP 200. The page had no horizontal overflow at 390 pixels. Evidence: `artifacts/verification/demo-media-verification.json`. One WebKit range request was canceled during seeking; seeking and playback succeeded with an audio track and no media, page, console or CSP errors. YouTube publication and final Devpost submission remain incomplete.

## Submission status

The Devpost overview has been saved with the project name and elevator pitch. The story, nine technology tags, three URLs and three captioned gallery images were saved, advancing to Additional info. The required supported-platform video URL is still missing. There is no separate testing-instructions field; the form offers an optional upload up to 35 MB, for which the public submission ZIP is prepared. No final submission has been made. The participant confirmed publication, but YouTube required fresh Google authentication after MP4 selection. The passkey Touch ID prompt is awaiting the participant; successful YouTube upload is not yet claimed.

## Reproduce

```sh
uv sync --frozen --extra dev
uv run pytest
uv run ruff check backend tests scripts/account_admin.py scripts/backup.py
cd frontend
npm ci
npm run build
```

For the full SQLite and PostgreSQL run, provide a dedicated test database URL through `PANTRY_TEST_POSTGRES` and run `uv run pytest`. The test account must be able to create and drop schemas. Never use a production database. See [PostgreSQL test coverage](POSTGRESQL.md#database-test-coverage).

With the app running at http://localhost:8010:

```sh
cd browser-tests
npm ci
npx playwright install chromium
npm test
```

Chromium is the default. Install the corresponding browser and set `PANTRY_BROWSER=webkit` or `PANTRY_BROWSER=firefox` to select another engine. To test the public origin, set `BASE_URL=https://pantryrelay.web.app`; browser tests create fictional QA accounts and records, so only target an authorized test deployment.

For an isolated local server and database, run `./scripts/test_browser.sh` from the repository root. It chooses an available local port. `PANTRY_BROWSER=webkit ./scripts/test_browser.sh` selects WebKit; Firefox is supported in the Linux CI environment. The CI runner provides PostgreSQL 15 for the dual-database backend suite and also builds the Docker image.

## Limits

Automated accessibility checks do not establish complete WCAG conformance. No screen-reader user study, real pantry trial, independent penetration test, sustained load test, paid customer validation or food-safety certification has occurred. Browser checks cover Chromium, WebKit and Firefox in the environments specified above. The local Docker daemon was unavailable; the image builds successfully in GitHub Actions and Google Cloud Build. A Cloud SQL restore drill and real-network operating acceptance remain separate from the successful backup and technical deployment checks. Real pantry use requires a responsible operator and a documented transport/food policy.

The independent rubric review in `docs/JUDGE-REVIEW.md` is an internal assessment, not an event judge score or a prediction of winning.
