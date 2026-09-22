# Browser verification

The suite uses real API calls and independent network fixtures. It covers registration, invitations, driver handoffs, partial receipts, rejected cold food, failed dispatch, cancellation, request closure, concurrent stock changes, network failures, CSV contents, printable manifests, mobile focus management and all-view accessibility checks.

Start the integrated backend with a **fresh disposable database**, then run:

```sh
npm ci
npx playwright install chromium webkit firefox
BASE_URL=http://127.0.0.1:8013 npm test
PANTRY_BROWSER=webkit BASE_URL=http://127.0.0.1:8013 npm test
PANTRY_BROWSER=firefox BASE_URL=http://127.0.0.1:8013 npm test
```

Restart with another fresh database between full browser runs. Normal authentication rate limits remain enabled and intentional repeated signup/demo tests can reach them if all browser runs share one database. The default is Chromium so existing CI only needs its browser installed. `PANTRY_BROWSER` selects a single engine per run.

For a hosted deployment, set `BASE_URL=https://pantryrelay.web.app`. The suite creates fictitious demo networks and real test accounts using `example.org` addresses. Do not run it against a workspace containing real pantry operations. Registration and demo creation must both be enabled to run the full suite.

Reports are saved in `playwright-report/`; failed screenshots and traces go to `test-results/`. Axe violation reports are attached to the accessibility test. Tests do not overwrite the curated submission screenshots. `npm run screenshots` is the separate, intentional capture command.

The default suite never hides retries or raises application rate limits. User actions wait on visible state, requests or accessible elements, with no fixed sleeps used to mask races.
