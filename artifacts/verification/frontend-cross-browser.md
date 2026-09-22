# Frontend verification

The original baseline verified 22 independent browser scenarios in each of Chromium, WebKit and Firefox: 66 passing test executions. Each full run used a fresh isolated database. No automatic retries hid failures.

| Engine                | Result                       | Time   |
| --------------------- | ---------------------------- | ------ |
| Chromium, local macOS | 22 passed, 0 failed, 0 flaky | 17.4 s |
| WebKit, local macOS   | 22 passed, 0 failed, 0 flaky | 23.9 s |
| Firefox, Linux CI     | 22 passed, 0 failed, 0 flaky | 49.4 s |

## Tested behavior

- Full 120 lb reservation to 112 lb actual receipt, 8 lb exception, downloadable CSV values and reload persistence.
- Registration, sign-in, pantry onboarding, stock, service needs and closure of mistaken requests.
- Separate driver invitation and account, pickup and arrival, with receipt and coordinator controls withheld.
- Complete cold-food rejection without an invented temperature, and recovery from an unsafe positive receipt.
- Cancellation and failed dispatch accounting, with protected stock and request commitments preserved.
- Concurrent stock conflict and reload recovery.
- Successful mutation followed by a failed refresh, without inviting a duplicate submission.
- API interruption, session expiry during ordinary operations and CSV download, and meaningful retry messages.
- Search and category filtering, restricted stock visibility, and printable manifests with locations, service date and use-by cutoff.
- Every operational view at 320 px and 390 px without page overflow. Mobile drawer focus containment, Escape restoration and sign-out scroll cleanup.
- Automated WCAG A/AA checks across the landing page and all workspace screens.

## Fixes made from failures

The previous CI failure was a dynamic accessible name: the delivery count changed the navigation button label. Navigation names are now stable. Broader tests exposed and fixed a mobile table overflow caused by absolutely positioned hidden header text, Safari focus restoration after drawer dismissal, mobile sign-out scroll locking, and ambiguous save-versus-refresh errors.

## Firefox evidence

The complete Firefox suite passed in [GitHub Actions run 35690841301, Firefox job](https://github.com/shi1720/Hack-Away-Hunger/actions/runs/35690841301/job/106627310568) against commit `f067566883a232860cda2e192d1e690a03aa166d`. Logs record all 22 passing scenarios. The separate backend, PostgreSQL, Chromium and Docker build job also passed in that run.

Firefox could not start on the local macOS 27 host due to its profile-access restriction, including after a fresh browser installation. Mozilla [documents this launch issue](https://bugzilla.mozilla.org/show_bug.cgi?id=2062988). Running the same full suite on Linux CI provided the Firefox validation without modifying host privacy protections.

## Reproduce

Build the frontend, then run `PANTRY_BROWSER=chromium ./scripts/test_browser.sh` or `PANTRY_BROWSER=webkit ./scripts/test_browser.sh`. The script creates a fresh database and selects an unused port. For Firefox on Linux, use `PANTRY_BROWSER=firefox ./scripts/test_browser.sh`. Hosted verification uses `BASE_URL=https://pantryrelay.web.app npm test --prefix browser-tests`. The supplemental hosted results below cover the later sidebar fix.

## Short desktop sidebar regression

The complete suite now has 24 scenarios. Recording the hosted demo exposed a real responsive bug: the fixed sidebar could exceed the viewport height without a scroll container, placing sign-out beyond reach. The sidebar now scrolls independently, and short desktop layouts omit its decorative purpose card and use tighter footer spacing.

Two added tests reproduce the recording sequence at 1600 × 800 and 1280 × 600: confirm a partial receipt, scroll the service table, scroll the received inventory row, open impact, and sign out. The 1600 × 800 test failed before the change and passed after it.

| Supplemental run                 | Result                       | Time    |
| -------------------------------- | ---------------------------- | ------- |
| Chromium, local full suite       | 24 passed, 0 failed, 0 flaky | 20.1 s  |
| Chromium, hosted full suite      | 24 passed, 0 failed, 0 flaky | 164.1 s |
| WebKit, local new sidebar cases  | 2 passed, 0 failed, 0 flaky  | 3.0 s   |
| WebKit, hosted new sidebar cases | 2 passed, 0 failed, 0 flaky  | 20.2 s  |

Hosted Chromium exercised [the deployed app](https://pantryrelay.web.app) with stylesheet `index-lNWa-LnA.css`, including all original workflows, accessibility checks, adverse cases and both new desktop regressions. The historical Firefox evidence above remains the 22-case baseline; this report does not claim the two new tests have run in Firefox.

A preliminary extra local WebKit run reused the full Chromium run's database and reached the normal 30-attempt demo sign-in quota before its second case. Both new cases passed on a fresh database. TypeScript, Prettier and diff whitespace checks also passed. No further application changes followed these results.
