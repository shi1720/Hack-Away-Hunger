import { useEffect, useState, type FormEvent } from "react";
import {
  ArrowDownToLine,
  ArrowRight,
  ArrowUpRight,
  Check,
  CheckCircle2,
  ChevronRight,
  ClipboardList,
  Clock3,
  Download,
  Filter,
  Leaf,
  MapPin,
  PackageCheck,
  Plus,
  Printer,
  RefreshCw,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Snowflake,
  Sparkles,
  Truck,
  Users,
  Wheat,
} from "lucide-react";
import { api, downloadReport } from "./api";
import {
  Alert,
  Badge,
  Button,
  Empty,
  Field,
  IconFor,
  InfoNote,
  NetworkMap,
  Progress,
  SectionTitle,
  TextLink,
  categories,
  date,
  pretty,
  qty,
} from "./components";
import type {
  Constraints,
  Page,
  Plan,
  Proposal,
  Team,
  Transfer,
  Workspace,
} from "./types";
import type { DialogState } from "./Forms";
export type ViewProps = {
  w: Workspace;
  setPage: (page: Page) => void;
  open: (s: DialogState) => void;
  refresh: () => Promise<void>;
  notify: (text: string) => void;
};
const siteName = (w: Workspace, id: string) =>
  w.sites.find((s) => s.id === id)?.name || "Pantry";
const active = (t: Transfer) =>
  !["received", "cancelled", "failed"].includes(t.status);
export function Overview({ w, setPage, open }: ViewProps) {
  const upcoming = w.needs
    .filter(
      (n) =>
        !n.closed &&
        n.remaining_lb > 0 &&
        new Date(n.service_at).getTime() > Date.now(),
    )
    .sort((a, b) => a.service_at.localeCompare(b.service_at));
  const next = upcoming[0];
  return (
    <>
      <SectionTitle
        eyebrow="A LITTLE COORDINATION. A LOT OF GOOD."
        title="Every connection counts."
        description={`Here’s what’s moving across ${w.network.name}.`}
        actions={
          <Button onClick={() => setPage("planner")}>
            <Sparkles size={16} />
            Find a relay
            <ArrowRight size={16} />
          </Button>
        }
      />
      <div className="metrics-grid">
        {[
          {
            label: "Food received",
            value: w.metrics.received_lb,
            unit: "lb",
            kind: "check" as const,
            detail: "Confirmed at the receiving pantry",
            className: "featured",
          },
          {
            label: "Ready to share",
            value: w.metrics.available_lb,
            unit: "lb",
            kind: "food" as const,
            detail: "After protected stock and reservations",
          },
          {
            label: "Active relays",
            value: w.metrics.active_transfers,
            unit: "",
            kind: "truck" as const,
            detail: "From reservation to arrival",
          },
          {
            label: "Open service needs",
            value: w.metrics.unmet_need_lb,
            unit: "lb",
            kind: "pin" as const,
            detail: "Not yet received or reserved",
          },
        ].map((m) => (
          <article className={`metric-card ${m.className || ""}`} key={m.label}>
            <div className="metric-top">
              <span>{m.label}</span>
              <IconFor kind={m.kind} />
            </div>
            <strong>
              {qty(m.value)}
              <small>{m.unit}</small>
            </strong>
            <p>{m.detail}</p>
          </article>
        ))}
      </div>
      {!w.sites.length ? (
        <div className="onboarding">
          <div>
            <p className="eyebrow">YOUR NETWORK STARTS WITH ONE PANTRY</p>
            <h2>Let’s make your first connection.</h2>
            <p>
              Add your locations, record available food, then tell the network
              what’s needed.
            </p>
          </div>
          <div className="onboarding-steps">
            <button onClick={() => open({ kind: "site" })}>
              <span>1</span>
              <strong>Add your first pantry</strong>
              <ArrowRight size={18} />
            </button>
            <div>
              <span>2</span>
              <strong>Record food and protected stock</strong>
            </div>
            <div>
              <span>3</span>
              <strong>Add a service need and plan a relay</strong>
            </div>
          </div>
        </div>
      ) : (
        <div className="overview-grid">
          <section className="panel map-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">NEIGHBORS, CONNECTED</p>
                <h2>Your pantry network</h2>
              </div>
              <TextLink onClick={() => setPage("sites")}>
                View pantries
              </TextLink>
            </div>
            <NetworkMap sites={w.sites} transfers={w.transfers} />
            <div className="map-foot">
              <span>
                <span className="legend-dot" />
                {w.sites.length} connected{" "}
                {w.sites.length === 1 ? "pantry" : "pantries"}
              </span>
              <span>
                <span className="legend-line" />
                Active relays
              </span>
              <span>
                <ShieldCheck size={14} />
                Private network
              </span>
            </div>
          </section>
          <section className="next-service">
            <div className="next-top">
              <span className="circle-icon">
                <Clock3 size={22} />
              </span>
              <Badge color="light">NEXT SERVICE</Badge>
            </div>
            {next ? (
              <>
                <h2>
                  The next table
                  <br />
                  to help fill.
                </h2>
                <div className="service-details">
                  <p>{siteName(w, next.site_id)}</p>
                  <strong>
                    {qty(next.remaining_lb)} <span>lb of {next.category}</span>
                  </strong>
                  <span>
                    <Clock3 size={14} />
                    {date(next.service_at, true)}
                  </span>
                </div>
                <p className="service-description">
                  Match food in your network to this upcoming service. Every
                  pantry keeps its protected reserve.
                </p>
                <Button onClick={() => setPage("planner")}>
                  Explore available matches
                  <ArrowRight size={17} />
                </Button>
              </>
            ) : (
              <>
                <h2>
                  A place for
                  <br />
                  every next need.
                </h2>
                <p className="service-description">
                  Record an upcoming service so your network can help fill its
                  food gaps.
                </p>
                <Button onClick={() => open({ kind: "need" })}>
                  Add a service need
                  <Plus size={16} />
                </Button>
              </>
            )}
          </section>
        </div>
      )}
      <div className="overview-bottom">
        <section className="panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">PLAN AHEAD</p>
              <h2>Upcoming service needs</h2>
            </div>
            <TextLink onClick={() => setPage("sites")}>View all</TextLink>
          </div>
          {upcoming.length ? (
            <div className="need-list">
              {upcoming.slice(0, 3).map((n) => (
                <div className="need-row" key={n.id}>
                  <span className={`food-icon ${n.category}`}>
                    {n.category === "produce" ? (
                      <Leaf size={20} />
                    ) : (
                      <Wheat size={20} />
                    )}
                  </span>
                  <div>
                    <strong>{siteName(w, n.site_id)}</strong>
                    <small>
                      {pretty(n.category)} · {date(n.service_at, true)}
                    </small>
                  </div>
                  <strong className="need-weight">
                    {qty(n.remaining_lb)} <small>lb needed</small>
                  </strong>
                </div>
              ))}
            </div>
          ) : (
            <Empty title="No unfilled service needs">
              Record your next service to start matching food.
            </Empty>
          )}
        </section>
        <section className="panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">THE HANDOFF RECORD</p>
              <h2>Recent activity</h2>
            </div>
            <span className="small-label">AUDITED</span>
          </div>
          {w.events.length ? (
            <div className="activity-list">
              {w.events.slice(0, 4).map((e, i) => (
                <div className="activity-item" key={e.id}>
                  <span className={`activity-dot ${i === 0 ? "recent" : ""}`} />
                  <div>
                    <strong>
                      {e.summary ||
                        pretty(e.action || e.event_type || "Network activity")}
                    </strong>
                    <small>
                      {e.actor_name ? `${e.actor_name} · ` : ""}
                      {date(e.created_at, true)}
                    </small>
                  </div>
                  <Check size={14} />
                </div>
              ))}
            </div>
          ) : (
            <Empty title="Your story starts here">
              Inventory updates and handoffs will appear in your audit trail.
            </Empty>
          )}
        </section>
      </div>
      <div className="bottom-note">
        <ShieldCheck size={15} />
        <span>
          Impact means actual food received. No estimated meals, no assumed
          outcomes.
        </span>
        {w.metrics.at_risk_lb > 0 && (
          <span className="at-risk">
            <Clock3 size={14} />
            {qty(w.metrics.at_risk_lb)} lb approaching use-by
          </span>
        )}
      </div>
    </>
  );
}
export function Planner({ w, refresh, notify, open }: ViewProps) {
  const [constraints, setConstraints] = useState<Constraints>({
    max_distance_miles: 50,
    vehicle_capacity_lb: 500,
    refrigerated: true,
  });
  const [plan, setPlan] = useState<Plan | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [reserving, setReserving] = useState("");
  async function generate(e?: FormEvent) {
    e?.preventDefault();
    setBusy(true);
    setError("");
    try {
      setPlan(await api("/planner", constraints));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function reserve(p: Proposal) {
    setReserving(p.lot_id + p.need_id);
    setError("");
    let saved = false;
    try {
      await api("/transfers", {
        lot_id: p.lot_id,
        need_id: p.need_id,
        quantity_lb: p.quantity_lb,
        ...constraints,
      });
      saved = true;
      setPlan(null);
      notify(
        `${qty(p.quantity_lb)} lb reserved. Ask the receiving pantry to accept the relay.`,
      );
      await refresh();
      setPlan(await api("/planner", constraints));
    } catch (e) {
      setError(
        saved
          ? "Your relay was reserved, but the latest matches could not load. Refresh the workspace to see the saved delivery before planning more."
          : (e as Error).message,
      );
    } finally {
      setReserving("");
    }
  }
  return (
    <>
      <SectionTitle
        eyebrow="TURN AVAILABLE INTO ARRIVING"
        title="Find the next good match."
        description="Practical connections, explained. You make the final call."
      />
      <div className="planner-layout">
        <aside className="panel planner-controls">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">PLAN FOR THE REAL WORLD</p>
              <h2>Relay constraints</h2>
            </div>
            <SlidersHorizontal size={20} />
          </div>
          <form onSubmit={generate}>
            <Field
              label="Maximum distance (miles)"
              hint="Approximate straight-line distance, not driving miles."
            >
              <input
                type="number"
                value={constraints.max_distance_miles}
                min="1"
                max="500"
                step="1"
                required
                onChange={(e) => {
                  setConstraints({
                    ...constraints,
                    max_distance_miles: Number(e.target.value),
                  });
                  setPlan(null);
                }}
              />
            </Field>
            <Field
              label="Vehicle capacity (lb)"
              hint="Maximum load for each individual relay."
            >
              <input
                type="number"
                value={constraints.vehicle_capacity_lb}
                min="1"
                max="100000"
                required
                onChange={(e) => {
                  setConstraints({
                    ...constraints,
                    vehicle_capacity_lb: Number(e.target.value),
                  });
                  setPlan(null);
                }}
              />
            </Field>
            <label className="check-card">
              <input
                type="checkbox"
                checked={constraints.refrigerated}
                onChange={(e) => {
                  setConstraints({
                    ...constraints,
                    refrigerated: e.target.checked,
                  });
                  setPlan(null);
                }}
              />
              <span>
                <strong>Temperature-controlled transport</strong>
                <small>
                  Vehicle can maintain the required cold or frozen conditions.
                </small>
              </span>
            </label>
            <Button type="submit" loading={busy} disabled={!w.sites.length}>
              <Sparkles size={16} />
              {plan ? "Refresh matches" : "Find matches"}
              <ArrowRight size={16} />
            </Button>
          </form>
          <div className="planner-principles">
            <h3>Every match checks</h3>
            {[
              "Protected source reserves",
              "Receiving storage & total capacity",
              "Service and food use-by deadlines",
              "Donor restrictions",
              "Stock already committed",
            ].map((s) => (
              <span key={s}>
                <ShieldCheck size={15} />
                {s}
              </span>
            ))}
          </div>
        </aside>
        <div className="planner-results">
          {error && <Alert>{error}</Alert>}
          {!plan ? (
            <div className="planner-welcome">
              <span className="large-icon">
                <ArrowRight size={34} />
              </span>
              <p className="eyebrow">LOCAL FOOD. A BETTER CONNECTION.</p>
              <h2>
                Your next relay
                <br />
                starts with a good match.
              </h2>
              <p>
                Set your transport constraints and find food that can meet the
                network’s next service needs.
              </p>
              <div className="match-equation">
                <span>
                  <Leaf size={20} />
                  Shareable stock
                </span>
                <Plus size={16} />
                <span>
                  <ClipboardList size={20} />A service need
                </span>
              </div>
              {!w.sites.length && (
                <Button onClick={() => open({ kind: "site" })}>
                  Add your first pantry
                  <Plus size={16} />
                </Button>
              )}
            </div>
          ) : (
            <>
              <div className="results-heading">
                <div>
                  <h2>
                    {plan.proposals.length} workable{" "}
                    {plan.proposals.length === 1 ? "connection" : "connections"}
                  </h2>
                  <p>Prioritized by service urgency and food use-by cutoff.</p>
                </div>
                <Badge color="green">
                  <span className="status-dot" />
                  Checked {date(plan.generated_at, true)}
                </Badge>
              </div>
              {plan.proposals.length ? (
                plan.proposals.map((p, i) => (
                  <article className="proposal-card" key={p.lot_id + p.need_id}>
                    <div className="proposal-top">
                      <span className="proposal-rank">
                        {String(i + 1).padStart(2, "0")}
                      </span>
                      <div>
                        <h3>{p.food_name}</h3>
                        <div className="badge-row">
                          <Badge color={p.category}>{pretty(p.category)}</Badge>
                          <Badge>
                            {p.storage === "ambient" ? (
                              "Ambient"
                            ) : (
                              <>
                                <Snowflake size={12} />
                                {pretty(p.storage)}
                              </>
                            )}
                          </Badge>
                        </div>
                      </div>
                      <strong className="proposal-quantity">
                        {qty(p.quantity_lb)}
                        <small>lb to relay</small>
                      </strong>
                    </div>
                    <div className="route-row">
                      <div>
                        <span className="eyebrow">FROM</span>
                        <strong>{siteName(w, p.source_id)}</strong>
                      </div>
                      <div className="route-distance">
                        <ArrowRight size={21} />
                        <small>≈ {qty(p.distance_miles)} mi</small>
                      </div>
                      <div>
                        <span className="eyebrow">TO</span>
                        <strong>{siteName(w, p.destination_id)}</strong>
                      </div>
                    </div>
                    <div className="proposal-reasons">
                      <span>
                        <CheckCircle2 size={16} />
                        Why this connection works
                      </span>
                      <ul>
                        {p.reasons.map((r, j) => (
                          <li key={j}>{r}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="proposal-footer">
                      <span>
                        <Clock3 size={14} />
                        Service {date(p.service_at, true)}
                      </span>
                      <Button
                        onClick={() => void reserve(p)}
                        loading={reserving === p.lot_id + p.need_id}
                        disabled={!!reserving}
                      >
                        Reserve this relay
                        <ArrowRight size={16} />
                      </Button>
                    </div>
                  </article>
                ))
              ) : (
                <div className="panel">
                  <Empty
                    title="No workable matches right now"
                    action={
                      <Button
                        variant="secondary"
                        onClick={() => open({ kind: "need" })}
                      >
                        Add a service need
                        <Plus size={16} />
                      </Button>
                    }
                  >
                    Try wider transport constraints, add shareable food, or
                    check the exclusions below. The planner keeps your
                    operational limits in place.
                  </Empty>
                </div>
              )}
              {plan.excluded.length > 0 && (
                <details className="panel exclusion-panel">
                  <summary>
                    <ShieldCheck size={18} />
                    {plan.excluded.length} stock{" "}
                    {plan.excluded.length === 1 ? "exclusion" : "exclusions"}
                    <ChevronRight size={16} />
                  </summary>
                  <div>
                    {plan.excluded.map((e, i) => (
                      <div className="exclusion-row" key={i}>
                        <strong>
                          {w.lots.find((l) => l.id === e.lot_id)?.food_name ||
                            "Food lot"}
                        </strong>
                        <p>{e.reason}</p>
                      </div>
                    ))}
                  </div>
                </details>
              )}
              <InfoNote>
                Matches are proposals, not dispatch instructions. Confirm
                addresses, driving time, receiving hours and your organization’s
                food-handling policies before pickup.
              </InfoNote>
              {plan.assumptions.length > 0 && (
                <details className="assumptions">
                  <summary>Matching assumptions & methodology</summary>
                  <ul>
                    {plan.assumptions.map((a, i) => (
                      <li key={i}>{a}</li>
                    ))}
                  </ul>
                </details>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
}
export function Inventory({ w, open }: ViewProps) {
  const [search, setSearch] = useState(""),
    [category, setCategory] = useState("all");
  const lots = w.lots.filter(
    (l) =>
      (category === "all" || l.category === category) &&
      `${l.food_name} ${siteName(w, l.site_id)}`
        .toLowerCase()
        .includes(search.toLowerCase()),
  );
  return (
    <>
      <SectionTitle
        eyebrow="SHARE WHAT YOU CAN. KEEP WHAT YOU NEED."
        title="Food, with a purpose."
        description="A clear view of stock, protected reserves and food ready for its next pantry."
        actions={
          <Button
            onClick={() => open({ kind: "lot" })}
            disabled={!w.sites.length}
          >
            <Plus size={17} />
            Add food lot
          </Button>
        }
      />
      <div className="inventory-strip">
        <div>
          <Leaf size={21} />
          <span>
            <strong>
              {qty(w.lots.reduce((s, l) => s + l.quantity_lb, 0))} lb
            </strong>
            Total stock on hand
          </span>
        </div>
        <div>
          <ShieldCheck size={21} />
          <span>
            <strong>
              {qty(w.lots.reduce((s, l) => s + l.reserve_lb, 0))} lb
            </strong>
            Protected for local visitors
          </span>
        </div>
        <div>
          <ArrowUpRight size={21} />
          <span>
            <strong>{qty(w.metrics.available_lb)} lb</strong>Available to share
          </span>
        </div>
      </div>
      <section className="panel">
        <div className="table-toolbar">
          <label className="search-field">
            <Search size={17} />
            <input
              aria-label="Search food or pantry"
              placeholder="Search food or pantry…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </label>
          <label className="filter-select">
            <Filter size={16} />
            <select
              aria-label="Filter by category"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              <option value="all">All categories</option>
              {categories.map((c) => (
                <option key={c} value={c}>
                  {pretty(c)}
                </option>
              ))}
            </select>
          </label>
          <span className="small-label">{lots.length} FOOD LOTS</span>
        </div>
        {lots.length ? (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Food & pantry</th>
                  <th>Category / storage</th>
                  <th>On hand</th>
                  <th>Protected</th>
                  <th>Shareable</th>
                  <th>Use-by cutoff</th>
                  <th>
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {lots.map((l) => (
                  <tr key={l.id}>
                    <td>
                      <strong>{l.food_name}</strong>
                      <small>{siteName(w, l.site_id)}</small>
                    </td>
                    <td>
                      <Badge color={l.category}>{pretty(l.category)}</Badge>
                      <small>
                        {pretty(l.storage)}
                        {l.restricted ? " · Restricted" : ""}
                      </small>
                    </td>
                    <td>{qty(l.quantity_lb)} lb</td>
                    <td>
                      <span className="protected">
                        <ShieldCheck size={13} />
                        {qty(l.reserve_lb)} lb
                      </span>
                    </td>
                    <td>
                      <strong
                        className={l.available_lb > 0 ? "green-text" : ""}
                      >
                        {qty(l.available_lb)} lb
                      </strong>
                    </td>
                    <td>
                      <span
                        className={
                          new Date(l.expires_at).getTime() < Date.now()
                            ? "expired"
                            : new Date(l.expires_at).getTime() <
                                Date.now() + 172800000
                              ? "soon"
                              : ""
                        }
                      >
                        {date(l.expires_at)}
                      </span>
                      <small>
                        {new Date(l.expires_at).toLocaleTimeString("en-US", {
                          hour: "numeric",
                          minute: "2-digit",
                        })}
                      </small>
                    </td>
                    <td>
                      <Button
                        variant="ghost"
                        onClick={() => open({ kind: "lot", lot: l })}
                      >
                        Adjust
                        <ChevronRight size={14} />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty
            title={
              w.lots.length
                ? "No food matches this search"
                : "Good connections start with good inventory"
            }
            action={
              !w.sites.length ? (
                <Button onClick={() => open({ kind: "site" })}>
                  Add your first pantry
                </Button>
              ) : (
                <Button onClick={() => open({ kind: "lot" })}>
                  Add food lot
                  <Plus size={15} />
                </Button>
              )
            }
          >
            {w.lots.length
              ? "Try a different name or category."
              : "Record stock at your pantry and protect the amount your own visitors need."}
          </Empty>
        )}
      </section>
      <InfoNote>
        Shareable stock excludes protected reserves, restricted food, expired
        food and existing commitments. Inventory changes are recorded in the
        audit trail.
      </InfoNote>
    </>
  );
}
export function Sites({ w, open }: ViewProps) {
  return (
    <>
      <SectionTitle
        eyebrow="ONE NETWORK. MANY NEIGHBORS."
        title="Know your pantries."
        description="Locations, storage and upcoming services: the context behind every connection."
        actions={
          <>
            <Button
              variant="secondary"
              disabled={!w.sites.length}
              onClick={() => open({ kind: "need" })}
            >
              <ClipboardList size={16} />
              Add service need
            </Button>
            <Button onClick={() => open({ kind: "site" })}>
              <Plus size={17} />
              Add pantry
            </Button>
          </>
        }
      />
      {w.sites.length ? (
        <div className="site-grid">
          {w.sites.map((s, i) => {
            const stock = w.lots
                .filter((l) => l.site_id === s.id)
                .reduce((n, l) => n + l.quantity_lb, 0),
              inbound = w.transfers
                .filter((t) => t.destination_id === s.id && active(t))
                .reduce((n, t) => n + t.quantity_lb, 0);
            return (
              <article className="panel site-card" key={s.id}>
                <div className="site-card-top">
                  <span className="site-number">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <Badge>{s.city}</Badge>
                  <button
                    className="text-link"
                    onClick={() => open({ kind: "site", site: s })}
                  >
                    Edit
                    <ChevronRight size={14} />
                  </button>
                </div>
                <h2>{s.name}</h2>
                <p className="site-address">
                  <MapPin size={15} />
                  {s.address}
                </p>
                <div className="badge-row">
                  {s.storage_types.map((t) => (
                    <Badge color={t === "ambient" ? "" : "blue"} key={t}>
                      {t !== "ambient" && <Snowflake size={12} />} {pretty(t)}
                    </Badge>
                  ))}
                </div>
                <div className="capacity-label">
                  <span>Stock + inbound reservations</span>
                  <strong>
                    {qty(stock + inbound)} / {qty(s.capacity_lb)} lb
                  </strong>
                </div>
                <progress
                  max={s.capacity_lb}
                  value={stock + inbound}
                  aria-label={`${s.name} stock and inbound capacity`}
                />
                <div className="capacity-breakdown">
                  <span>{qty(stock)} lb on hand</span>
                  <span>{qty(inbound)} lb inbound</span>
                </div>
                {s.notes && <p className="site-note">{s.notes}</p>}
                <button
                  className="site-action"
                  onClick={() => open({ kind: "need", siteId: s.id })}
                >
                  Add an upcoming service need
                  <Plus size={16} />
                </button>
              </article>
            );
          })}
        </div>
      ) : (
        <div className="panel">
          <Empty
            title="Build your local network"
            action={
              <Button onClick={() => open({ kind: "site" })}>
                Add first pantry
                <Plus size={16} />
              </Button>
            }
          >
            Add pantry locations with their storage types and total capacity to
            make matching possible.
          </Empty>
        </div>
      )}
      <section className="panel service-table">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">WHAT THE NEXT SERVICE NEEDS</p>
            <h2>Service needs</h2>
          </div>
          <Badge>{w.needs.length} recorded</Badge>
        </div>
        {w.needs.length ? (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Pantry / service</th>
                  <th>Category</th>
                  <th>Total needed</th>
                  <th>Received</th>
                  <th>Committed</th>
                  <th>Still needed</th>
                  <th>
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {[...w.needs]
                  .sort((a, b) => a.service_at.localeCompare(b.service_at))
                  .map((n) => (
                    <tr key={n.id}>
                      <td>
                        <strong>{siteName(w, n.site_id)}</strong>
                        <small>{date(n.service_at, true)}</small>
                        {n.notes && (
                          <small className="table-note">{n.notes}</small>
                        )}
                      </td>
                      <td>
                        <Badge color={n.category}>{pretty(n.category)}</Badge>
                      </td>
                      <td>{qty(n.quantity_lb)} lb</td>
                      <td className="green-text">{qty(n.fulfilled_lb)} lb</td>
                      <td>{qty(n.reserved_lb)} lb</td>
                      <td>
                        <strong>{qty(n.remaining_lb)} lb</strong>
                        {n.closed && <small>Closed</small>}
                        {!n.closed && n.remaining_lb === 0 && (
                          <small>
                            {n.fulfilled_lb >= n.quantity_lb
                              ? "Fulfilled"
                              : "Reserved in full"}
                          </small>
                        )}
                      </td>
                      <td>
                        {!n.closed && (
                          <Button
                            variant="ghost"
                            onClick={() =>
                              open({ kind: "close_need", need: n })
                            }
                          >
                            Close
                            <ChevronRight size={14} />
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty title="Plan for your next service">
            Record the category and quantity each pantry needs, along with the
            service date.
          </Empty>
        )}
      </section>
    </>
  );
}
export function Deliveries({ w, open, notify }: ViewProps) {
  const [filter, setFilter] = useState("active"),
    [print, setPrint] = useState<Transfer | null>(null);
  const list = w.transfers.filter(
    (t) =>
      filter === "all" ||
      (filter === "active" ? active(t) : t.status === "received"),
  );
  const driver = w.user.role === "driver";
  useEffect(() => {
    if (print) {
      const timer = setTimeout(() => window.print(), 150);
      return () => clearTimeout(timer);
    }
  }, [print]);
  return (
    <>
      <SectionTitle
        eyebrow="A GOOD MATCH IS JUST THE BEGINNING"
        title={
          driver ? "Your delivery board." : "Every handoff, accounted for."
        }
        description={
          driver
            ? "Confirm pickup and arrival. Your coordinator handles acceptance and final receipt."
            : "From reservation to real receipt. Keep the whole network on the same page."
        }
      />
      <div className="delivery-toolbar">
        <div className="segmented" role="group" aria-label="Delivery filter">
          {[
            {
              id: "active",
              label: "Active relays",
              count: w.transfers.filter(active).length,
            },
            {
              id: "received",
              label: "Received",
              count: w.transfers.filter((t) => t.status === "received").length,
            },
            { id: "all", label: "All activity", count: w.transfers.length },
          ].map((f) => (
            <button
              className={filter === f.id ? "selected" : ""}
              key={f.id}
              onClick={() => setFilter(f.id)}
            >
              {f.label}
              <span>{f.count}</span>
            </button>
          ))}
        </div>
        <span className="small-label">
          <ShieldCheck size={14} /> EVERY TRANSITION AUDITED
        </span>
      </div>
      {list.length ? (
        <div className="deliveries-list">
          {list.map((t) => (
            <article className="panel delivery-card" key={t.id}>
              <div className="delivery-heading">
                <div className="delivery-food-icon">
                  <Truck size={21} />
                </div>
                <div>
                  <h2>{t.food_name}</h2>
                  <p>
                    Relay {t.id.slice(0, 8).toUpperCase()} · Created{" "}
                    {date(t.created_at)}
                  </p>
                </div>
                <Badge color={t.status}>{pretty(t.status)}</Badge>
                <strong className="delivery-weight">
                  {qty(t.status === "received" ? t.received_lb : t.quantity_lb)}
                  <small>
                    lb{" "}
                    {t.status === "received"
                      ? "received"
                      : t.status === "failed"
                        ? "not received"
                        : ["in_transit", "arrived"].includes(t.status)
                          ? "dispatched"
                          : "reserved"}
                  </small>
                </strong>
              </div>
              <div className="route-row">
                <div>
                  <span className="eyebrow">PICKUP</span>
                  <strong>{siteName(w, t.source_id)}</strong>
                  <small>
                    {w.sites.find((s) => s.id === t.source_id)?.address}
                  </small>
                </div>
                <div className="route-distance">
                  <ArrowRight size={21} />
                  <small>≈ {qty(t.distance_miles)} mi</small>
                </div>
                <div>
                  <span className="eyebrow">DELIVERY</span>
                  <strong>{siteName(w, t.destination_id)}</strong>
                  <small>
                    {w.sites.find((s) => s.id === t.destination_id)?.address}
                  </small>
                </div>
              </div>
              {!["cancelled", "failed"].includes(t.status) && (
                <Progress status={t.status} />
              )}
              <div className="delivery-meta">
                <Badge color={t.storage === "ambient" ? "" : "blue"}>
                  {t.storage !== "ambient" && <Snowflake size={12} />}{" "}
                  {pretty(t.storage)}
                </Badge>
                {t.receiver_name && <span>Receiver: {t.receiver_name}</span>}
                {t.pickup_temperature_f !== null &&
                  t.pickup_temperature_f !== undefined && (
                    <span>Pickup: {t.pickup_temperature_f}°F</span>
                  )}
                {t.receipt_temperature_f !== null &&
                  t.receipt_temperature_f !== undefined && (
                    <span>Receipt: {t.receipt_temperature_f}°F</span>
                  )}
              </div>
              {t.late && (
                <div className="exception-note">
                  <strong>Receipt confirmed after the planned service</strong>
                  <span>
                    {qty(t.received_lb)} lb was added to destination stock. This
                    late receipt does not fill the original service need.
                  </span>
                </div>
              )}
              {t.exception_reason && (
                <div className="exception-note">
                  <strong>
                    {t.status === "received"
                      ? `${qty(t.quantity_lb - (t.received_lb || 0))} lb difference recorded`
                      : "Transfer note"}
                  </strong>
                  <span>{t.exception_reason}</span>
                </div>
              )}
              <div className="delivery-footer">
                <button
                  className="text-link subtle"
                  onClick={() => {
                    if (print?.id === t.id) window.print();
                    else setPrint(t);
                    notify(
                      "Print manifest ready. Use your browser’s print dialog.",
                    );
                  }}
                >
                  <Printer size={15} />
                  Print manifest
                </button>
                <div className="action-buttons">
                  {!driver && ["in_transit", "arrived"].includes(t.status) && (
                    <Button
                      variant="ghost"
                      onClick={() =>
                        open({ kind: "transfer", transfer: t, action: "fail" })
                      }
                    >
                      Report failed delivery
                    </Button>
                  )}
                  {!driver && ["reserved", "accepted"].includes(t.status) && (
                    <Button
                      variant="ghost"
                      onClick={() =>
                        open({
                          kind: "transfer",
                          transfer: t,
                          action: "cancel",
                        })
                      }
                    >
                      Cancel relay
                    </Button>
                  )}
                  {!driver && t.status === "reserved" && (
                    <Button
                      onClick={() =>
                        open({
                          kind: "transfer",
                          transfer: t,
                          action: "accept",
                        })
                      }
                    >
                      Accept at destination
                      <Check size={16} />
                    </Button>
                  )}
                  {t.status === "accepted" && (
                    <Button
                      onClick={() =>
                        open({
                          kind: "transfer",
                          transfer: t,
                          action: "pickup",
                        })
                      }
                    >
                      Record pickup
                      <Truck size={16} />
                    </Button>
                  )}
                  {t.status === "in_transit" && (
                    <Button
                      onClick={() =>
                        open({
                          kind: "transfer",
                          transfer: t,
                          action: "arrive",
                        })
                      }
                    >
                      Mark arrived
                      <MapPin size={16} />
                    </Button>
                  )}
                  {!driver && t.status === "arrived" && (
                    <Button
                      onClick={() =>
                        open({
                          kind: "transfer",
                          transfer: t,
                          action: "receive",
                        })
                      }
                    >
                      Confirm receipt
                      <PackageCheck size={16} />
                    </Button>
                  )}
                  {t.status === "received" && (
                    <span className="receipt-confirmed">
                      <CheckCircle2 size={17} />
                      Receipt confirmed {date(t.updated_at)}
                    </span>
                  )}
                  {driver && ["reserved", "arrived"].includes(t.status) && (
                    <span className="driver-wait">
                      Awaiting coordinator{" "}
                      {t.status === "reserved" ? "acceptance" : "receipt"}
                    </span>
                  )}
                </div>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="panel">
          <Empty
            title={
              filter === "received"
                ? "Your first confirmed receipt is ahead"
                : "No relays here yet"
            }
          >
            {driver
              ? "Accepted transfers will appear here for pickup and arrival."
              : "Reserve a match in the relay planner to begin. Completed receipts will be counted in your impact report."}
          </Empty>
        </div>
      )}
      <InfoNote>
        Distance is approximate. Confirm driving directions before travel. Food
        is counted as received only after the destination confirms actual
        weight.
      </InfoNote>
      {print && (
        <div className="print-manifest">
          <h1>Pantry Relay: delivery manifest</h1>
          <p>Relay ID: {print.id}</p>
          <h2>
            {print.food_name} · {qty(print.quantity_lb)} lb
          </h2>
          <p>
            Category: {pretty(print.category)} · Storage:{" "}
            {pretty(print.storage)}
          </p>
          <p>
            Times shown in {Intl.DateTimeFormat().resolvedOptions().timeZone}.
          </p>
          {print.service_at && (
            <p>Receiving service: {date(print.service_at, true)}</p>
          )}
          {w.lots.find((l) => l.id === print.lot_id)?.expires_at && (
            <p>
              Operational use-by cutoff:{" "}
              {date(
                w.lots.find((l) => l.id === print.lot_id)!.expires_at,
                true,
              )}
            </p>
          )}
          <h3>Pickup</h3>
          <p>
            {siteName(w, print.source_id)}
            <br />
            {w.sites.find((s) => s.id === print.source_id)?.address}
          </p>
          <h3>Delivery</h3>
          <p>
            {siteName(w, print.destination_id)}
            <br />
            {w.sites.find((s) => s.id === print.destination_id)?.address}
          </p>
          <p>
            Receiver: {print.receiver_name || "Not yet assigned"}
            <br />
            Current status: {pretty(print.status)}
          </p>
          <hr />
          <p>Pickup temperature: __________ °F · Time: __________</p>
          <p>Condition checked by: ____________________________________</p>
          <p>
            Actual received: __________ lb · Receipt temperature: __________ °F
          </p>
          <p>Receiver signature: _______________________________________</p>
          <p>Exception / rejected food: __________________________________</p>
          <hr />
          <p>
            Record the handoff in Pantry Relay to update inventory and impact.
            This manifest is a working aid and does not certify food safety.
          </p>
          {w.network.is_demo && (
            <p>DEMO: Fictitious organizations and sample data.</p>
          )}
        </div>
      )}
    </>
  );
}
export function Impact({ w, notify }: ViewProps) {
  const receipts = w.transfers.filter((t) => t.status === "received"),
    exception = receipts.reduce(
      (s, t) => s + t.quantity_lb - (t.received_lb || 0),
      0,
    ),
    completedSites = new Set(
      receipts
        .filter((t) => (t.received_lb || 0) > 0)
        .map((t) => t.destination_id),
    );
  const [error, setError] = useState("");
  async function download(report: string) {
    setError("");
    try {
      await downloadReport(
        report,
        `pantry-relay-${report}-${new Date().toISOString().slice(0, 10)}.csv`,
      );
      notify("Report downloaded.");
    } catch (e) {
      setError((e as Error).message);
    }
  }
  return (
    <>
      <SectionTitle
        eyebrow="REAL RECEIPTS. REAL ACCOUNTABILITY."
        title="Good that you can count."
        description="A transparent record of the food that reached another pantry."
        actions={
          <Button variant="secondary" onClick={() => void download("receipts")}>
            <Download size={16} />
            Export receipts
          </Button>
        }
      />
      {error && <Alert>{error}</Alert>}
      <div className="impact-hero">
        <div>
          <p className="eyebrow">CONFIRMED AT DESTINATION</p>
          <strong>
            {qty(w.metrics.received_lb)}
            <span>lb</span>
          </strong>
          <h2>
            Food received.
            <br />
            Handoffs completed.
          </h2>
          <p>
            Measured at the receiving pantry. Recorded by a person. Backed by an
            audit trail.
          </p>
        </div>
        <div className="impact-graphic" aria-hidden="true">
          <div className="impact-ring ring-1" />
          <div className="impact-ring ring-2" />
          <div className="impact-ring ring-3" />
          <span>
            <SproutIcon />
          </span>
          <div className="graphic-note">
            <CheckCircle2 size={15} />
            Actual, not estimated
          </div>
        </div>
      </div>
      <div className="impact-stats">
        <article className="panel">
          <PackageCheck size={22} />
          <strong>{receipts.length}</strong>
          <span>Recorded receipts</span>
        </article>
        <article className="panel">
          <Users size={22} />
          <strong>{completedSites.size}</strong>
          <span>Receiving pantries</span>
        </article>
        <article className="panel">
          <ClipboardList size={22} />
          <strong>
            {qty(exception)} <small>lb</small>
          </strong>
          <span>Recorded receipt differences</span>
        </article>
      </div>
      <section className="panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">EVERY POUND HAS A RECORD</p>
            <h2>Confirmed receipts</h2>
          </div>
          <Badge color="green">
            {w.network.is_demo ? "SAMPLE DATA" : "YOUR NETWORK"}
          </Badge>
        </div>
        {receipts.length ? (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Food / date</th>
                  <th>Receiving pantry</th>
                  <th>Dispatched</th>
                  <th>Received</th>
                  <th>Difference</th>
                  <th>Service credited</th>
                  <th>Receiver</th>
                </tr>
              </thead>
              <tbody>
                {receipts.map((t) => (
                  <tr key={t.id}>
                    <td>
                      <strong>{t.food_name}</strong>
                      <small>{date(t.updated_at, true)}</small>
                    </td>
                    <td>{siteName(w, t.destination_id)}</td>
                    <td>{qty(t.quantity_lb)} lb</td>
                    <td>
                      <strong className="green-text">
                        {qty(t.received_lb)} lb
                      </strong>
                    </td>
                    <td>
                      {qty(t.quantity_lb - (t.received_lb || 0))} lb
                      {t.exception_reason && (
                        <small className="table-note">
                          {t.exception_reason}
                        </small>
                      )}
                    </td>
                    <td>
                      {qty(t.need_credited_lb ?? t.received_lb)} lb
                      {t.late && <small>Confirmed after service</small>}
                    </td>
                    <td>{t.receiver_name}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty title="Impact starts with the first receipt">
            Complete a relay and confirm actual food received. Your results will
            appear here automatically.
          </Empty>
        )}
      </section>
      <div className="export-panel">
        <span className="circle-icon">
          <ArrowDownToLine size={23} />
        </span>
        <div>
          <h3>Take the record with you.</h3>
          <p>
            Export the complete audit trail for network reviews and operational
            reporting.
          </p>
        </div>
        <Button variant="secondary" onClick={() => void download("audit")}>
          Download audit CSV
          <Download size={16} />
        </Button>
      </div>
      <InfoNote>
        These figures measure food transferred between your pantries. They do
        not imply additional food rescued, meals served, people reached or
        emissions avoided.
      </InfoNote>
    </>
  );
}
function SproutIcon() {
  return <Leaf size={68} strokeWidth={1.3} />;
}
export function TeamView({ w, open }: ViewProps) {
  const [team, setTeam] = useState<Team | null>(null),
    [error, setError] = useState("");
  async function load() {
    try {
      setError("");
      setTeam(await api("/team"));
    } catch (e) {
      setError((e as Error).message);
    }
  }
  useEffect(() => {
    void load();
  }, [w]);
  return (
    <>
      <SectionTitle
        eyebrow="GOOD WORK TAKES GOOD PEOPLE"
        title="Your relay team."
        description="The coordinators and drivers making the next handoff possible."
        actions={
          w.user.role === "admin" && !w.network.is_demo ? (
            <Button onClick={() => open({ kind: "invite" })}>
              <Plus size={17} />
              Invite teammate
            </Button>
          ) : undefined
        }
      />
      {w.network.is_demo && (
        <InfoNote>
          Create your own network to invite teammates. Demo workspaces expire.
        </InfoNote>
      )}
      {error && (
        <Alert>
          {error}
          <button onClick={() => void load()} className="inline-retry">
            Try again
          </button>
        </Alert>
      )}
      <section className="panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">A PRIVATE, TRUSTED NETWORK</p>
            <h2>{w.network.name}</h2>
          </div>
          <Badge>{team?.users.length || 0} members</Badge>
        </div>
        {team ? (
          <div className="team-list">
            {team.users.map((u) => (
              <div className="team-member" key={u.id}>
                <span className="avatar">
                  {u.name
                    .split(" ")
                    .map((x) => x[0])
                    .slice(0, 2)
                    .join("")
                    .toUpperCase()}
                </span>
                <div>
                  <strong>
                    {u.name}
                    {u.id === w.user.id && <span className="you-tag">YOU</span>}
                  </strong>
                  <small>{u.email}</small>
                </div>
                <Badge color={u.role === "admin" ? "green" : ""}>
                  {pretty(u.role)}
                </Badge>
              </div>
            ))}
          </div>
        ) : (
          <div className="loading-inline">
            <RefreshCw size={20} className="spin" />
            Loading team…
          </div>
        )}
      </section>
      <div className="role-grid">
        {[
          {
            role: "Admin",
            icon: <ShieldCheck />,
            text: "Manage pantry operations and invite trusted teammates.",
          },
          {
            role: "Coordinator",
            icon: <ClipboardList />,
            text: "Manage stock and needs, plan relays and confirm receipts.",
          },
          {
            role: "Driver",
            icon: <Truck />,
            text: "Record pickup checks and mark deliveries arrived.",
          },
        ].map((r) => (
          <article className="panel role-card" key={r.role}>
            {r.icon}
            <h3>{r.role}</h3>
            <p>{r.text}</p>
          </article>
        ))}
      </div>
      {team && team.invites.length > 0 && (
        <section className="panel">
          <div className="panel-heading">
            <h2>Invitation history</h2>
            <Badge>Single-use links</Badge>
          </div>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Role</th>
                  <th>Expires</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {team.invites.map((i, n) => (
                  <tr key={i.id || n}>
                    <td>{pretty(i.role)}</td>
                    <td>{date(i.expires_at, true)}</td>
                    <td>
                      <Badge color={i.used_at ? "green" : ""}>
                        {i.used_at
                          ? "Accepted"
                          : new Date(i.expires_at) < new Date()
                            ? "Expired"
                            : "Awaiting teammate"}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
      <InfoNote>
        Each teammate signs in with their own account. All users belong to this
        network only; no household or client personal data is collected.
      </InfoNote>
    </>
  );
}
