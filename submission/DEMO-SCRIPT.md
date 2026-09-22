# Pantry Relay: recording script

For the current synthetic-narration video, use `VIDEO-NARRATION.md`. This file is the alternative script for Shivam to speak personally, including the shorter live-presentation fallback. Do not use its first-person introduction with synthetic audio or imply the synthetic voice is Shivam's.

Presenter: **Shivam Gupta**. Target: approximately **3 minutes** at a calm 140-150 words per minute. This is a rehearsal target, not a verified event video requirement. Confirm the Devpost form's actual limit.

The scenario and names are fictional. Keep the demo label visible. Record a fresh demo workspace. Use the first produce proposal; confirm its actual quantity before recording. The canonical illustrative narration below uses 120 lb dispatched and 112 lb received. If the interface shows different quantities, use its actual values rather than reading a conflicting number.

## Verbatim narration

“Hi, I'm Shivam Gupta, and this is Pantry Relay.

Imagine you're opening a food pantry tomorrow. You have shelf-stable food, but you're short of produce. A nearby pantry has more produce than it can use. Someone still has to discover that mismatch, check what can move, arrange the handoff, and find out what actually arrived.

Pantry Relay helps an approved network do that work in one place.

These are fictional pantries and sample records. Here, Cedar Grove has surplus above the stock it needs for its own visitors. Eastside has an upcoming produce gap.

I open the relay planner. It checks the source pantry's protected reserve, the receiving pantry's needs and storage, available space, the food's use-by cutoff, and the vehicle's capacity. Restricted stock stays out. Distances are straight-line estimates, so a coordinator still confirms the actual trip.

Each suggestion tells me why it fits. I can review the pounds and both locations before reserving the transfer. The reservation immediately reduces available stock, which prevents another coordinator from promising the same food twice.

Next, I record the receiving pantry's acceptance. At pickup, we confirm the condition and record a temperature when the food requires it. The driver marks arrival, and the receiver records what they actually accepted.

Here's the detail that matters. Suppose we dispatched one hundred and twenty pounds, but eight pounds arrived damaged. I record one hundred and twelve pounds received and explain the difference.

The impact report counts one hundred and twelve pounds. The unmet need opens back up for the missing eight. The audit trail keeps the original reservation, the handoff, and the receipt. We can export those records for the network's own reporting.

The product has real accounts, isolated networks, role invitations, and persistent storage. The full local application runs without paid AI or map APIs. Our public sample demo is disposable and clearly labeled.

The first buyer we want to test is a pantry-network coordinator. Our proposed price is one hundred and forty-nine dollars per network per month, while self-hosting remains free. We have not validated that price or claimed a customer.

Our next step is a supervised pilot with three pantries. We'll measure category gaps closed, staff time, transport effort, and accepted pounds. We'll also learn when moving the food is not worth the cost.

Pantry Relay makes the food already in a community easier to share, with a record of what reached the receiving pantry. Thank you.”

## Shot list

| Approx. time | Screen/action | Recording note |
|---|---|---|
| 0:00-0:18 | Title slide or landing page | Face camera optional; speak the first two paragraphs |
| 0:18-0:40 | Overview, site map and category needs | Keep fictitious-data indicator visible |
| 0:40-1:10 | Relay planner, inspect proposal reasons | Cursor moves slowly; let the checks be readable |
| 1:10-1:25 | Reserve proposal; open Deliveries | Do not double-click; show the persisted status |
| 1:25-1:45 | Acceptance, pickup, arrival | Use a demo receiver name; fill required safety fields truthfully as simulated observations |
| 1:45-2:05 | Receipt form, 112 lb and “8 lb damaged in transit” | Only use these numbers if the reserved transfer is exactly120 lb |
| 2:05-2:25 | Impact and audit/export | Show accepted pounds and exception, not a fabricated meals number |
| 2:25-2:45 | Business/pilot slides | Clearly say price is proposed and pilot is next |
| 2:45-3:05 | Closing slide | Pause after the final line |

Do one silent rehearsal first. Turn off system notifications, enlarge browser to 1440x900 or 1920x1080, use 100% browser zoom, hide personal tabs, and record at 1080p. Cut pauses and typing time rather than accelerating the entire video. Captions can follow the narration above after the final audio is recorded.

## 60-second fallback, verbatim

“I'm Shivam Gupta. Pantry Relay helps an approved pantry network fill upcoming food gaps using surplus nearby.

In this fictional example, one pantry has produce above its protected reserve and another needs produce for its next service. Our planner checks demand, storage, capacity, restrictions, expiry and distance before suggesting a transfer.

A coordinator reserves the stock and records receiver acceptance. Pickup and arrival lead to an actual receiving record. If one hundred and twenty pounds leave but only one hundred and twelve are accepted, we count one hundred and twelve and reopen the missing eight-pound need.

The app includes accounts, network isolation, driver permissions and an audit export, with no required paid APIs.

We propose a one-hundred-and-forty-nine-dollar monthly network subscription, subject to a supervised three-pantry pilot. We'll measure time, transport effort, category gaps and accepted pounds.

Pantry Relay makes the food already here go further.”

## If the venue internet fails

Use the installed local app at http://localhost:8010. If the app cannot run, use the supplied pitch PDF and actual screenshots. Explicitly call it a walkthrough of the implemented application. Never pretend a pre-recorded sequence is a live demo.
