# Pantry Relay frontend

Responsive React 19 + TypeScript application built with Vite. All operational views use the FastAPI API; there is no simulated backend, third-party map service, font CDN, AI API key or client-side credential persistence.

## Local development

```sh
npm ci
npm run dev
```

Run the backend at `http://127.0.0.1:8010`. Vite proxies `/api` to that address. The backend serves `frontend/dist` after `npm run build` for the integrated application.

```sh
npm run typecheck
npm run build
npm run format:check
npm audit
```

## Structure

- `src/App.tsx` owns session recovery, navigation, workspace refresh and dialogs.
- `src/Auth.tsx` implements landing, sign-in, registration and invitation acceptance.
- `src/api.ts` includes cookie-based API requests and an in-memory CSRF token. A 401 during an authenticated operation clears local session state.
- `src/views.tsx` implements overview, matching, stock, locations/needs, delivery handoffs, receipt reporting and team management.
- `src/Forms.tsx` handles validated operational forms, cancellation, failed delivery and need closure.
- `src/components.tsx` contains accessible native dialogs, fields and a dependency-free network schematic.
- `src/styles.css` supplies the original responsive visual system, print manifest and reduced-motion support.

The UI hides operations unavailable to drivers; authorization is enforced by the server. Public disposable-demo deployments use `/api/config` to disable account creation and real team invitations. All demo networks prohibit invitations.

Operational datetimes are entered and displayed in the browser’s local timezone and submitted as UTC timestamps. The service form and workspace footer identify the local timezone. Map connections show approximate straight-line distances; the map is a schematic, not driving navigation.

Only recorded actual receipt weights contribute to food-received reporting. Full rejection is supported with 0 lb and a reason, without requiring a temperature reading. A failed dispatched delivery is recorded separately from arrival and receipt. Late receipts add destination inventory but do not fill the original service’s need.

## Accessibility and testing

Every form has associated labels, dialogs use native focus management, icon-only controls have accessible names, operational state changes are announced, and keyboard focus is visible. The layout supports a compact navigation drawer, horizontal table scrolling, reduced motion and a standalone printable manifest. Browser tests and accessibility reports live in the repository’s `browser-tests/` and `artifacts/verification/` directories.
