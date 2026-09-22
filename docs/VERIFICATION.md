# Verification record

Date: September22,2026. Checks use fictitious data. This record separates automated verification from field validation.

## Completed locally

| Check | Result |
|---|---|
| Backend automated suite |56 passing tests|
| Backend lint |Ruff passes|
| TypeScript and production asset build |Pass|
| Frontend dependency audit |0 reported vulnerabilities at build time|
| Chromium partial receipt workflow |Pass:120 reserved/dispatched,112 accepted,8 difference, export, reload persistence, reopened need|
| Real account onboarding |Pass:register, add pantry, stock and protected reserve, request, close incorrect request, sign out and sign in|
| Driver invitation |Pass:separate browser account joins as driver and sees transport view without operator navigation|
| Session expiry recovery |Pass:cleared session returns to authentication instead of trapping the user|
| Mobile390px |No horizontal page overflow; navigation and Escape-to-close dialog pass|
| Automated accessibility |0 WCAG A/AA/2.1 violations across24 screens, forms and transfer states|
| Independent API review |Tenant probes, role denials, late receipt, received-stock protection, request closure and failed delivery independently checked|
| Database backup and recovery |Live WAL backup restores login, workspace and receipt CSV; overwrite guard and corrupt-backup cleanup tested|
| Account recovery |Session revocation and password reset tested without logging credentials|

The six browser scenarios reside in `browser-tests/workflow.spec.ts`. An initial run exposed low-contrast text, which was corrected. Test-only locator mismatches were repaired to reflect explicit form labels. Final application flows pass. Accessibility evidence is in `artifacts/verification/frontend-accessibility.json`, with the core landing/overview/planner recheck files beside it.

Backend coverage includes fractional-weight precision, invalid and nonfinite inputs, stale edits, source reserves, destination capacity, restrictions, expiry, no matching storage, cold-chain checks, partial/full rejection, duplicate transitions, simultaneous reservations, active-request closure rejection, loss after pickup, late confirmation, cross-network access, role enforcement, invite replay, demo expiration, CSRF, origin checks, production configuration, and schema migrations preserving history.

## Reproduce

```sh
uv sync --frozen --extra dev
uv run pytest
uv run ruff check backend tests
cd frontend
npm ci
npm run build
```

With the app running at http://localhost:8010:

```sh
cd browser-tests
npm ci
npx playwright install chromium
npm test
```

The CI runner uses `scripts/test_browser.sh` with an isolated database. GitHub Actions also builds the Docker image. See the actual workflow run for its status; a workflow definition alone is not proof of a passing run.

## Limits

Automated accessibility checks do not establish complete WCAG conformance. No screen-reader user study, real pantry trial, independent penetration test, sustained load test, paid customer validation or food-safety certification has occurred. Browser automation here uses Chromium; Firefox and Safari are not claimed as tested. The local Docker daemon was unavailable during initial verification; Docker execution is checked separately in CI. Real deployment still requires a responsible operator and a documented transport/food policy.

The independent rubric review in `docs/JUDGE-REVIEW.md` is an internal assessment, not an event judge score or a prediction of winning.
