import { useState } from "react";
import { Copy, ExternalLink, ShieldCheck } from "lucide-react";
import { api } from "./api";
import {
  ActionForm,
  Alert,
  Badge,
  Button,
  Field,
  InfoNote,
  Modal,
  categories,
  date,
  localDate,
  pretty,
  qty,
  storages,
} from "./components";
import type { Lot, Need, Site, Transfer, Workspace } from "./types";
export type DialogState =
  | { kind: "site"; site?: Site }
  | { kind: "lot"; lot?: Lot }
  | { kind: "need"; siteId?: string }
  | {
      kind: "transfer";
      transfer: Transfer;
      action: "accept" | "pickup" | "arrive" | "receive" | "cancel" | "fail";
    }
  | { kind: "close_need"; need: Need }
  | { kind: "invite" };
const str = (f: FormData, n: string) => String(f.get(n) || "");
const num = (f: FormData, n: string) => Number(f.get(n));
function inputDate(iso: string) {
  const d = new Date(iso);
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0, 16);
}
export default function Forms({
  state,
  workspace,
  onClose,
  onSaved,
}: {
  state: DialogState;
  workspace: Workspace;
  onClose: () => void;
  onSaved: (message: string) => Promise<void>;
}) {
  const [receivedWeight, setReceivedWeight] = useState<number | null>(null);
  const [invite, setInvite] = useState<{
      token: string;
      expires_at: string;
    } | null>(null),
    [copied, setCopied] = useState(false),
    [copyError, setCopyError] = useState("");
  const sites = workspace.sites;
  async function save(
    path: string,
    body: unknown,
    message: string,
    method?: string,
  ) {
    await api(path, body, method);
    await onSaved(message);
    onClose();
  }
  const siteSelect = (current?: string) => (
    <select name="site_id" required defaultValue={current || ""}>
      <option value="" disabled>
        Select a pantry
      </option>
      {sites.map((s) => (
        <option value={s.id} key={s.id}>
          {s.name}
        </option>
      ))}
    </select>
  );
  if (state.kind === "site") {
    const s = state.site;
    return (
      <Modal
        title={s ? "Edit pantry" : "Add a pantry"}
        subtitle="Create a location in your private network."
        onClose={onClose}
      >
        <ActionForm
          onCancel={onClose}
          submit={s ? "Save pantry" : "Add pantry"}
          onSubmit={(f) =>
            save(
              s ? `/sites/${s.id}` : "/sites",
              {
                name: str(f, "name"),
                city: str(f, "city"),
                address: str(f, "address"),
                lat: num(f, "lat"),
                lng: num(f, "lng"),
                capacity_lb: num(f, "capacity_lb"),
                storage_types: f.getAll("storage_types"),
                notes: str(f, "notes"),
              },
              s ? "Pantry updated." : "Pantry added to your network.",
              s ? "PATCH" : undefined,
            )
          }
        >
          <Field label="Pantry name">
            <input
              name="name"
              required
              maxLength={120}
              defaultValue={s?.name}
            />
          </Field>
          <div className="form-grid">
            <Field label="City">
              <input
                name="city"
                required
                maxLength={100}
                defaultValue={s?.city}
              />
            </Field>
            <Field
              label="Total stock capacity (lb)"
              hint="Maximum stock held, including inbound reservations."
            >
              <input
                name="capacity_lb"
                type="number"
                min="1"
                max="1000000"
                step="0.01"
                required
                defaultValue={s?.capacity_lb || 1000}
              />
            </Field>
          </div>
          <Field label="Street address">
            <input
              name="address"
              required
              maxLength={300}
              defaultValue={s?.address}
            />
          </Field>
          <div className="form-grid">
            <Field label="Latitude" hint="Iowa locations are around 41–43° N.">
              <input
                name="lat"
                type="number"
                min="-90"
                max="90"
                step="any"
                required
                defaultValue={s?.lat}
                placeholder="41.6005"
              />
            </Field>
            <Field
              label="Longitude"
              hint="Iowa locations are around −90 to −96°."
            >
              <input
                name="lng"
                type="number"
                min="-180"
                max="180"
                step="any"
                required
                defaultValue={s?.lng}
                placeholder="-93.6091"
              />
            </Field>
          </div>
          <fieldset>
            <legend>Available storage</legend>
            <div className="check-options">
              {storages.map((t) => (
                <label key={t}>
                  <input
                    type="checkbox"
                    name="storage_types"
                    value={t}
                    defaultChecked={
                      s ? s.storage_types.includes(t) : t === "ambient"
                    }
                  />
                  {pretty(t)}
                </label>
              ))}
            </div>
          </fieldset>
          <Field label="Operating notes (optional)">
            <textarea
              name="notes"
              rows={2}
              maxLength={2000}
              defaultValue={s?.notes}
              placeholder="Loading entrance, contact process, receiving hours…"
            />
          </Field>
          <InfoNote>
            Coordinates support approximate matching. Confirm driving directions
            and receiving hours directly before dispatch.
          </InfoNote>
        </ActionForm>
      </Modal>
    );
  }
  if (state.kind === "lot") {
    const l = state.lot;
    return (
      <Modal
        title={l ? "Adjust inventory" : "Add available food"}
        subtitle="Protect what your own pantry needs before offering food to the network."
        onClose={onClose}
      >
        <ActionForm
          onCancel={onClose}
          submit={l ? "Save adjustment" : "Add food lot"}
          onConflict={
            l
              ? async () => {
                  await onSaved(
                    "Inventory refreshed. Open Adjust to review the latest stock.",
                  );
                  onClose();
                }
              : undefined
          }
          onSubmit={(f) =>
            save(
              l ? `/lots/${l.id}` : "/lots",
              {
                site_id: str(f, "site_id"),
                food_name: str(f, "food_name"),
                category: str(f, "category"),
                storage: str(f, "storage"),
                quantity_lb: num(f, "quantity_lb"),
                reserve_lb: num(f, "reserve_lb"),
                expires_at: new Date(str(f, "expires_at")).toISOString(),
                restricted: f.has("restricted"),
                notes: str(f, "notes"),
                ...(l ? { version: l.version } : {}),
              },
              l ? "Inventory adjusted." : "Food lot added.",
              l ? "PATCH" : undefined,
            )
          }
        >
          <Field label="Pantry">{siteSelect(l?.site_id)}</Field>
          <Field label="Food name">
            <input
              name="food_name"
              required
              maxLength={120}
              defaultValue={l?.food_name}
              placeholder="Mixed seasonal vegetables"
            />
          </Field>
          <div className="form-grid">
            <Field label="Food category">
              <select name="category" defaultValue={l?.category || "produce"}>
                {categories.map((c) => (
                  <option key={c}>{c}</option>
                ))}
              </select>
            </Field>
            <Field label="Storage requirement">
              <select name="storage" defaultValue={l?.storage || "ambient"}>
                {storages.map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
            </Field>
            <Field label="Stock on hand (lb)">
              <input
                name="quantity_lb"
                type="number"
                min={l ? 0 : 0.01}
                max="1000000"
                step="0.01"
                required
                defaultValue={l?.quantity_lb}
              />
            </Field>
            <Field
              label="Protected reserve (lb)"
              hint="Stock kept for this pantry’s own visitors."
            >
              <input
                name="reserve_lb"
                type="number"
                min="0"
                max="1000000"
                step="0.01"
                required
                defaultValue={l?.reserve_lb || 0}
              />
            </Field>
          </div>
          <Field
            label="Operational use-by cutoff"
            hint="Set by your pantry in your browser’s local timezone. This field does not certify food safety."
          >
            <input
              name="expires_at"
              type="datetime-local"
              required
              defaultValue={l ? inputDate(l.expires_at) : localDate(3)}
            />
          </Field>
          <label className="check-card">
            <input
              type="checkbox"
              name="restricted"
              defaultChecked={l?.restricted}
            />
            <span>
              <strong>Restricted food: do not transfer</strong>
              <small>Use for donor restrictions or other sharing limits.</small>
            </span>
          </label>
          <Field label="Notes (optional)">
            <textarea
              rows={2}
              name="notes"
              maxLength={2000}
              defaultValue={l?.notes}
            />
          </Field>
        </ActionForm>
      </Modal>
    );
  }
  if (state.kind === "need")
    return (
      <Modal
        title="Request food for a service"
        subtitle="Let your network know what your next service needs."
        onClose={onClose}
      >
        <ActionForm
          onCancel={onClose}
          submit="Add service need"
          onSubmit={(f) =>
            save(
              "/needs",
              {
                site_id: str(f, "site_id"),
                category: str(f, "category"),
                quantity_lb: num(f, "quantity_lb"),
                service_at: new Date(str(f, "service_at")).toISOString(),
                notes: str(f, "notes"),
              },
              "Service need added.",
            )
          }
        >
          <Field label="Receiving pantry">{siteSelect(state.siteId)}</Field>
          <div className="form-grid">
            <Field label="Category needed">
              <select name="category">
                {categories.map((c) => (
                  <option key={c}>{c}</option>
                ))}
              </select>
            </Field>
            <Field label="Total need (lb)">
              <input
                name="quantity_lb"
                type="number"
                min="0.01"
                max="1000000"
                step="0.01"
                required
              />
            </Field>
          </div>
          <Field
            label="Service date and time"
            hint={`Enter local time in ${Intl.DateTimeFormat().resolvedOptions().timeZone}.`}
          >
            <input
              name="service_at"
              type="datetime-local"
              required
              defaultValue={localDate()}
            />
          </Field>
          <Field label="Notes (optional)">
            <textarea
              name="notes"
              rows={3}
              maxLength={2000}
              placeholder="Specific food preferences or receiving instructions…"
            />
          </Field>
          <InfoNote>
            The planner subtracts food already reserved and received so your
            need cannot be filled twice.
          </InfoNote>
        </ActionForm>
      </Modal>
    );
  if (state.kind === "close_need")
    return (
      <Modal
        title="Close this service need"
        subtitle="Use this when the request is cancelled or needs correcting. Create a new request with the corrected details."
        onClose={onClose}
      >
        <ActionForm
          onCancel={onClose}
          submit="Close service need"
          onSubmit={(f) =>
            save(
              `/needs/${state.need.id}/close`,
              { reason: str(f, "reason") },
              "Service need closed.",
            )
          }
        >
          <Field label="Reason for closing">
            <textarea name="reason" rows={3} required maxLength={2000} />
          </Field>
          <InfoNote>
            Active incoming commitments must be resolved first. The original
            request and closing reason remain in the audit trail.
          </InfoNote>
        </ActionForm>
      </Modal>
    );
  if (state.kind === "invite") {
    const link = invite
      ? `${window.location.origin}/?invite=${encodeURIComponent(invite.token)}`
      : "";
    return (
      <Modal
        title="Grow your relay team"
        subtitle="Invite a trusted coordinator or volunteer driver to this network."
        onClose={onClose}
      >
        {invite ? (
          <div className="action-form">
            <div className="success-panel">
              <ShieldCheck />
              <h3>Invitation ready</h3>
              <p>
                Share this private link directly with your teammate. It expires{" "}
                {date(invite.expires_at, true)} and can be used once.
              </p>
            </div>
            <Field label="Private invitation link">
              <input readOnly value={link} onFocus={(e) => e.target.select()} />
            </Field>
            <Button
              onClick={async () => {
                try {
                  await navigator.clipboard.writeText(link);
                  setCopied(true);
                } catch {
                  setCopyError(
                    "Copy is unavailable in this browser. Select and copy the invitation link above.",
                  );
                }
              }}
            >
              <Copy size={16} />
              {copied ? "Copied to clipboard" : "Copy invitation link"}
            </Button>
            {copyError && <Alert>{copyError}</Alert>}
            <InfoNote>
              Anyone with this invitation can join the network in the selected
              role. Only share it with the intended teammate.
            </InfoNote>
            <div className="modal-foot">
              <Button variant="secondary" onClick={onClose}>
                Done
              </Button>
              <a
                className="button secondary"
                href={link}
                target="_blank"
                rel="noreferrer"
              >
                Open join page
                <ExternalLink size={15} />
              </a>
            </div>
          </div>
        ) : (
          <ActionForm
            onCancel={onClose}
            submit="Create invitation"
            onSubmit={async (f) => {
              setInvite(await api("/invites", { role: str(f, "role") }));
              await onSaved("Invitation created.");
            }}
          >
            <Field label="Team member role">
              <select name="role">
                <option value="coordinator">
                  Coordinator: inventory, planning and handoffs
                </option>
                <option value="driver">Driver: pickup and arrival only</option>
              </select>
            </Field>
            <InfoNote>
              Invitations are single use. Your teammate creates their own
              account; you never share your password.
            </InfoNote>
          </ActionForm>
        )}
      </Modal>
    );
  }
  const t = state.transfer,
    a = state.action,
    cold = t.storage !== "ambient",
    zeroReceipt = a === "receive" && receivedWeight === 0;
  const labels = {
    accept: "Accept receiving responsibility",
    pickup: "Confirm food pickup",
    arrive: "Mark delivery arrived",
    receive: "Confirm actual receipt",
    cancel: "Cancel this transfer",
    fail: "Report a failed delivery",
  };
  const subtitles = {
    accept: "Confirm that the receiving pantry is ready for this food.",
    pickup: "Record the handoff before the driver leaves the source pantry.",
    arrive:
      "Arrival does not count as received food. The receiver still confirms the handoff.",
    receive:
      "Only the weight actually received counts toward impact and the service need.",
    cancel:
      "This releases the stock, destination capacity and service need reservation.",
    fail: "Use this when dispatched food will not reach the destination. This is a permanent delivery outcome.",
  };
  return (
    <Modal title={labels[a]} subtitle={subtitles[a]} onClose={onClose}>
      <div className="transfer-modal-summary">
        <Badge color={t.category}>{pretty(t.category)}</Badge>
        <strong>
          {t.food_name} · {qty(t.quantity_lb)} lb
        </strong>
        <p>
          {sites.find((s) => s.id === t.source_id)?.name} →{" "}
          {sites.find((s) => s.id === t.destination_id)?.name}
        </p>
      </div>
      <ActionForm
        onCancel={onClose}
        submit={
          a === "receive"
            ? "Confirm receipt"
            : a === "cancel"
              ? "Cancel transfer"
              : a === "fail"
                ? "Report delivery failure"
                : a === "pickup"
                  ? "Confirm pickup"
                  : a === "arrive"
                    ? "Mark arrived"
                    : "Accept transfer"
        }
        onSubmit={async (f) => {
          let body: Record<string, unknown> = {};
          if (a === "accept") body = { receiver_name: str(f, "receiver_name") };
          if (a === "pickup")
            body = {
              temperature_f: cold ? num(f, "temperature_f") : null,
              condition_confirmed: f.has("condition_confirmed"),
            };
          if (a === "receive") {
            const received = num(f, "received_lb");
            if (received < t.quantity_lb && !str(f, "exception_reason").trim())
              throw new Error(
                "Explain the difference when less food is received than was dispatched.",
              );
            body = {
              received_lb: received,
              temperature_f:
                cold && str(f, "temperature_f") !== ""
                  ? num(f, "temperature_f")
                  : null,
              receiver_name: str(f, "receiver_name"),
              exception_reason: str(f, "exception_reason"),
            };
          }
          if (a === "cancel" || a === "fail")
            body = { reason: str(f, "reason") };
          await save(
            `/transfers/${t.id}/${a}`,
            body,
            a === "receive"
              ? "Receipt confirmed. Actual food received has been recorded."
              : `Transfer ${a === "arrive" ? "marked arrived" : a === "pickup" ? "picked up" : a === "accept" ? "accepted" : a === "fail" ? "reported failed" : "cancelled"}.`,
          );
        }}
      >
        {(a === "accept" || a === "receive") && (
          <Field label="Receiver’s name">
            <input
              name="receiver_name"
              required
              maxLength={120}
              defaultValue={t.receiver_name || workspace.user.name}
            />
          </Field>
        )}
        {a === "receive" && (
          <Field
            label="Actual food received (lb)"
            hint={`Dispatched: ${qty(t.quantity_lb)} lb. Enter 0 to reject the full shipment and record why. Only accepted pounds count.`}
          >
            <input
              name="received_lb"
              type="number"
              min="0"
              max={t.quantity_lb}
              step="0.01"
              required
              defaultValue={t.quantity_lb}
              onChange={(e) => setReceivedWeight(Number(e.target.value))}
            />
          </Field>
        )}
        {(a === "pickup" || a === "receive") && cold && (
          <Field
            label="Measured food temperature (°F)"
            hint={
              zeroReceipt
                ? "Optional for a full rejection. No food is accepted into destination stock."
                : t.storage === "chilled"
                  ? "Chilled food must be 32–41°F for this workflow."
                  : "Frozen food must be at or below 0°F for this workflow."
            }
          >
            <input
              name="temperature_f"
              type="number"
              step="0.1"
              required={!zeroReceipt}
              min={
                a === "pickup" ? (t.storage === "chilled" ? 32 : -100) : -100
              }
              max={a === "pickup" ? (t.storage === "chilled" ? 41 : 0) : 180}
              placeholder={t.storage === "chilled" ? "e.g. 38" : "e.g. -2"}
            />
          </Field>
        )}
        {a === "pickup" && (
          <label className="check-card">
            <input type="checkbox" name="condition_confirmed" required />
            <span>
              <strong>Condition checked at handoff</strong>
              <small>
                I have checked packaging, condition and the applicable local
                food-handling policy.
              </small>
            </span>
          </label>
        )}
        {a === "receive" && (
          <Field
            label="Exception note"
            hint="Required if actual received weight is less than dispatched weight."
          >
            <textarea
              name="exception_reason"
              rows={3}
              maxLength={2000}
              placeholder="For example: 8 lb rejected due to damaged packaging."
            />
          </Field>
        )}
        {(a === "cancel" || a === "fail") && (
          <Field
            label={
              a === "fail"
                ? "Reason for delivery failure"
                : "Reason for cancellation"
            }
          >
            <textarea name="reason" rows={3} required maxLength={2000} />
          </Field>
        )}
        {a === "fail" && (
          <Alert>
            Source stock has already been dispatched and will not be returned to
            inventory. This records 0 lb received and releases the destination’s
            reserved capacity and service demand. Record the cause, disposition
            of food and follow-up in your reason.
          </Alert>
        )}
        {a === "arrive" && (
          <div className="info-note">
            Confirm the food has reached the receiving pantry. A coordinator
            will record its measured weight and condition next.
          </div>
        )}
        {(a === "pickup" || a === "receive") && (
          <InfoNote>
            Temperature and condition checks support your organization’s
            procedures. If a check fails, stop the handoff and follow local
            policy.
          </InfoNote>
        )}
      </ActionForm>
    </Modal>
  );
}
