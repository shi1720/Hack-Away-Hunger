# Pantry Relay submission kit

Project lead: **Shivam Gupta**
Event: **Hack Away Hunger 2026**
Repository: https://github.com/shi1720/Hack-Away-Hunger
Live app: https://pantryrelay.web.app

The live application is deployed and verified. It supports registration for an empty network and separate fictional demo workspaces. Hosted Chromium passed the complete 24-scenario suite. Hosted WebKit passed its 22-scenario baseline plus both added short-desktop regressions. A signed-in session with a reserved 120-pound transfer survived a forced Cloud Run revision replacement. See `docs/VERIFICATION.md` for the evidence and its limits.

The 1080p demonstration video is rendered at `output/Pantry-Relay-Demo.mp4`. The public walkthrough target is https://pantryrelay.web.app/demo; deployment verification for that page is pending. The video is not yet published on YouTube and Devpost submission is not yet complete. Prepared assets and successful application tests are not publication confirmations.

## Run and rehearse

Run `./scripts/start.sh` and open http://localhost:8010. Enter a fresh demo. Use `VIDEO-NARRATION.md` for the current segmented synthetic narration and shot plan. `DEMO-SCRIPT.md` remains available for Shivam's own spoken presentation and its short fallback. Demo pantries and all operational results are fictitious. The app can also create a real, empty network account and persist records.

## Materials

- `DEVPOST.md`: title, tagline, story and built-with fields
- `DEMO-SCRIPT.md`: narration and exact shot plan
- `VIDEO-NARRATION.md`: final segmented synthetic narration with matching scenes and disclosure
- `YOUTUBE.md`: video title, description and upload checks
- `TESTING-INSTRUCTIONS.md`: judge walkthrough, account/driver tests, exceptions and automated reproduction
- `JUDGE-QA.md`: likely objections and candid answers
- `ORGANIZER-DRAFT.md`: eligibility and late-proposal clarification, unsent
- `output/`: final pitch and PDF deliverables, when generated
- `docs/VERIFICATION.md`: actual test results and remaining limits
- `docs/PILOT-PLAN.md`: validation and adoption plan

## Personal actions that software cannot substitute for

1. **Confirm eligibility and proposal acceptance.** The overview says US-only and ages 13+. The page listed September 17 for proposals, which is before this build began. Obtain organizer confirmation if needed. No eligibility assertion has been submitted on your behalf.
2. **Have an eligible human team of 2-6 people.** The rules allow joining individually and help with team formation. Codex is not a human teammate.
3. **Arrange the in-person presentation on October 10 in Johnston, Iowa.** The official rules require in-person presentation for prize eligibility.

## Publishing checks

Review the rendered demonstration video, its synthetic narration disclosure and the actual submission fields. The rendered video is 170.633333 seconds, approximately 2 minutes 51 seconds; inspect its final captions before uploading. The authenticated Devpost form determines required fields, video duration and visibility. Do not describe the submission or upload as complete until the corresponding platform confirms it.

The verified Firebase URL is ready for the submission's live-app field. The cloud stack uses Cloud Run and PostgreSQL on Cloud SQL; local self-hosting can use SQLite. Daily backups retain seven backups, and an on-demand Cloud SQL backup completed successfully. A restore drill remains a separate real-operation check. Managed cloud hosting has operating costs even when temporary credits are available. Keep fictional demo records separate from registered networks and real operations.

Official deadline: **October 8, 2026 at 11:45 pm EDT**, equivalent to **October 9 at 9:15 am IST**. Sources: https://hack-away-hunger.devpost.com/rules and https://hack-away-hunger.devpost.com/details/dates. Recheck for organizer updates before submission.

## Credit

Use “Project lead: Shivam Gupta.” The credits file accurately describes AI assistance. Add your actual testing, edits, interviews and presenting work after completing it. Do not claim customers, field trials or manual code contributions that did not happen.
