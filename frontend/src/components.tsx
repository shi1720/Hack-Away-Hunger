import {
  cloneElement,
  isValidElement,
  useId,
  type ReactElement,
  useEffect,
  useRef,
  useState,
  type ReactNode,
  type FormEvent,
} from "react";
import {
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronRight,
  CircleHelp,
  Leaf,
  Loader2,
  MapPin,
  ShieldCheck,
  Sprout,
  Truck,
  X,
} from "lucide-react";
import { ApiError } from "./api";
import type { Category, Site, Storage, Transfer } from "./types";
export const categories: Category[] = [
  "produce",
  "protein",
  "dairy",
  "grains",
  "pantry",
];
export const storages: Storage[] = ["ambient", "chilled", "frozen"];
export const pretty = (text: string) =>
  text.replace(/[_.-]/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
export const qty = (value: number | null | undefined) =>
  new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(
    value || 0,
  );
export const date = (value: string, time = false) =>
  new Date(value).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    ...(time ? { hour: "numeric", minute: "2-digit" } : {}),
  });
export const localDate = (days = 1) => {
  const d = new Date(Date.now() + days * 86400000);
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0, 16);
};
export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <div className="brand">
      <span className="brand-mark">
        <Sprout size={23} />
      </span>
      {!compact && (
        <span>
          pantry<span className="brand-light">relay</span>
          <span className="brand-dot">.</span>
        </span>
      )}
    </div>
  );
}
export function Button({
  children,
  onClick,
  variant = "primary",
  disabled,
  type = "button",
  loading = false,
  className = "",
}: {
  children: ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary" | "ghost" | "danger";
  disabled?: boolean;
  type?: "button" | "submit";
  loading?: boolean;
  className?: string;
}) {
  return (
    <button
      type={type}
      className={`button ${variant} ${className}`}
      disabled={disabled || loading}
      onClick={onClick}
    >
      {loading && <Loader2 size={16} className="spin" />}
      {children}
    </button>
  );
}
export function Badge({
  children,
  color = "",
}: {
  children: ReactNode;
  color?: string;
}) {
  return <span className={`badge ${color}`}>{children}</span>;
}
export function Empty({
  title,
  children,
  action,
}: {
  title: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="empty-state">
      <span className="empty-icon">
        <Sprout size={27} />
      </span>
      <h3>{title}</h3>
      <p>{children}</p>
      {action}
    </div>
  );
}
export function Alert({ children }: { children: ReactNode }) {
  return (
    <div role="alert" className="alert">
      <CircleHelp size={18} />
      <span>{children}</span>
    </div>
  );
}
export function Field({
  label,
  hint,
  children,
  className = "",
}: {
  label: string;
  hint?: string;
  children: ReactNode;
  className?: string;
}) {
  const id = useId();
  const hintId = `${id}-hint`;
  const control = isValidElement(children)
    ? cloneElement(
        children as ReactElement<{ id?: string; "aria-describedby"?: string }>,
        {
          id,
          ...(hint ? { "aria-describedby": hintId } : {}),
        },
      )
    : children;
  return (
    <div className={`field ${className}`}>
      <label htmlFor={id}>{label}</label>
      {control}
      {hint && <small id={hintId}>{hint}</small>}
    </div>
  );
}
export function Modal({
  title,
  subtitle,
  onClose,
  children,
}: {
  title: string;
  subtitle?: string;
  onClose: () => void;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current!;
    dialog.showModal();
    return () => dialog.close();
  }, []);
  return (
    <dialog
      ref={ref}
      onCancel={onClose}
      onClick={(e) => {
        if (e.target === ref.current) {
          const r = ref.current.getBoundingClientRect();
          if (
            e.clientX < r.left ||
            e.clientX > r.right ||
            e.clientY < r.top ||
            e.clientY > r.bottom
          )
            onClose();
        }
      }}
      aria-labelledby="modal-title"
    >
      <div className="modal-head">
        <div>
          <p className="eyebrow">PANTRY RELAY</p>
          <h2 id="modal-title">{title}</h2>
          {subtitle && <p>{subtitle}</p>}
        </div>
        <button
          onClick={onClose}
          className="icon-button"
          aria-label="Close dialog"
        >
          <X size={20} />
        </button>
      </div>
      {children}
    </dialog>
  );
}
export function ActionForm({
  onSubmit,
  children,
  submit = "Save",
  onCancel,
  onConflict,
}: {
  onSubmit: (data: FormData) => Promise<void>;
  children: ReactNode;
  submit?: string;
  onCancel: () => void;
  onConflict?: () => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [conflict, setConflict] = useState(false);
  async function handle(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setConflict(false);
    try {
      await onSubmit(new FormData(e.currentTarget));
    } catch (e) {
      setConflict(e instanceof ApiError && e.status === 409);
      setError(
        e instanceof Error
          ? e.message
          : "Something went wrong. Please try again.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <form onSubmit={handle} className="action-form">
      {children}
      {error && <Alert>{error}</Alert>}
      {conflict && onConflict && (
        <Button
          variant="secondary"
          loading={busy}
          onClick={async () => {
            setBusy(true);
            try {
              await onConflict();
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          Close and reload latest stock
        </Button>
      )}
      <div className="modal-foot">
        <Button variant="secondary" onClick={onCancel} disabled={busy}>
          Cancel
        </Button>
        <Button type="submit" loading={busy}>
          {submit}
          <ArrowRight size={16} />
        </Button>
      </div>
    </form>
  );
}
export function NetworkMap({
  sites,
  transfers = [],
  hero = false,
}: {
  sites: Site[];
  transfers?: Transfer[];
  hero?: boolean;
}) {
  const data = hero
    ? [
        {
          id: "a",
          name: "Food available",
          city: "SOURCE PANTRY",
          lat: 41.7,
          lng: -93.73,
        },
        {
          id: "b",
          name: "Next service",
          city: "RECEIVING PANTRY",
          lat: 41.58,
          lng: -93.54,
        },
        {
          id: "c",
          name: "Community pantry",
          city: "YOUR NETWORK",
          lat: 41.54,
          lng: -93.7,
        },
      ]
    : sites;
  const minLng = Math.min(...data.map((s) => s.lng)),
    maxLng = Math.max(...data.map((s) => s.lng)),
    minLat = Math.min(...data.map((s) => s.lat)),
    maxLat = Math.max(...data.map((s) => s.lat));
  const positions = data.map((s, i) => ({
    ...s,
    x:
      data.length === 1
        ? 300
        : 130 + ((s.lng - minLng) / Math.max(maxLng - minLng, 0.01)) * 350,
    y:
      data.length === 1
        ? 160
        : 90 + ((maxLat - s.lat) / Math.max(maxLat - minLat, 0.01)) * 170,
    index: i,
  }));
  const lines = hero
    ? [{ source_id: "a", destination_id: "b", status: "reserved" }]
    : transfers.filter(
        (t) => !["cancelled", "received", "failed"].includes(t.status),
      );
  return (
    <div className={`network-map ${hero ? "hero-map" : ""}`}>
      <svg
        viewBox="0 0 650 350"
        role="img"
        aria-label={
          hero
            ? "Illustration of food moving between community pantries"
            : `Schematic of ${sites.length} pantry locations and active transfers`
        }
      >
        <defs>
          <pattern
            id={hero ? "hero-grid" : "map-grid"}
            width="36"
            height="36"
            patternUnits="userSpaceOnUse"
          >
            <path
              d="M 36 0 L 0 0 0 36"
              fill="none"
              stroke="#dce3d5"
              strokeWidth=".65"
            />
          </pattern>
          <linearGradient id="river" x1="0" y1="0" x2="1" y2="1">
            <stop stopColor="#c3dcd9" />
            <stop offset="1" stopColor="#d6e5da" />
          </linearGradient>
        </defs>
        <rect width="650" height="350" fill="#eef1e6" />
        <rect
          width="650"
          height="350"
          fill={`url(#${hero ? "hero-grid" : "map-grid"})`}
        />
        <path
          d="M360-20C310 45 423 63 372 122S261 184 320 226 342 297 297 380"
          fill="none"
          stroke="url(#river)"
          strokeWidth="22"
        />
        <path
          d="M-10 210C124 210 188 136 320 151S557 146 670 63M80-20C147 101 228 158 235 360M-10 286L660 280"
          fill="none"
          stroke="#fffdf5"
          strokeWidth="10"
        />
        <path
          d="M-10 210C124 210 188 136 320 151S557 146 670 63M80-20C147 101 228 158 235 360M-10 286L660 280"
          fill="none"
          stroke="#d8dece"
          strokeWidth="1"
        />
        <text x="30" y="38" className="map-region">
          {hero ? "A CONNECTED COMMUNITY" : "YOUR PANTRY NETWORK"}
        </text>
        <text x="595" y="40" className="map-north">
          N ↑
        </text>
        {lines.map((t, i) => {
          const a = positions.find((s) => s.id === t.source_id),
            b = positions.find((s) => s.id === t.destination_id);
          if (!a || !b) return null;
          return (
            <g key={i}>
              <path
                d={`M${a.x},${a.y} Q${(a.x + b.x) / 2},${Math.min(a.y, b.y) - 45} ${b.x},${b.y}`}
                stroke="#386f50"
                strokeWidth="2.5"
                strokeDasharray="7 5"
                fill="none"
              />
              <circle
                cx={(a.x + b.x) / 2}
                cy={(a.y + b.y) / 2 - 22.5}
                r="15"
                fill="#173e31"
              />
              <path
                d={`M${(a.x + b.x) / 2 - 5},${(a.y + b.y) / 2 - 22.5}h10m-4-4l4 4-4 4`}
                stroke="#e0eeaa"
                strokeWidth="1.7"
                fill="none"
              />
            </g>
          );
        })}
        {positions.map((s) => (
          <g key={s.id}>
            <circle cx={s.x} cy={s.y} r="22" fill="#deeabf" opacity=".9" />
            <circle
              cx={s.x}
              cy={s.y}
              r="12"
              fill={s.index === 0 ? "#173e31" : "#fdfdf6"}
              stroke="#173e31"
              strokeWidth="2"
            />
            <path
              d={`M${s.x - 4} ${s.y + 3}v-5l4-3 4 3v5h-8`}
              fill="none"
              stroke={s.index === 0 ? "#e8f4b8" : "#173e31"}
              strokeWidth="1.5"
            />
            <rect
              x={s.x - 92}
              y={s.y + 27}
              width="184"
              height="43"
              rx="8"
              fill="#fffffa"
              stroke="#dce2d5"
            />
            <text x={s.x} y={s.y + 44} textAnchor="middle" className="map-site">
              {s.name.length > 25 ? s.name.slice(0, 23) + "…" : s.name}
            </text>
            <text x={s.x} y={s.y + 59} textAnchor="middle" className="map-city">
              {s.city.toUpperCase()}
            </text>
          </g>
        ))}
        {!data.length && (
          <text
            x="325"
            y="185"
            textAnchor="middle"
            fill="#607266"
            fontSize="15"
          >
            Add your first pantry to build your network.
          </text>
        )}
      </svg>
      <div className="map-caption">
        <span>
          <span className="legend-dot" />{" "}
          {hero
            ? "Illustrative pantry network"
            : `${sites.length} pantry locations`}
        </span>
        <span>Schematic · straight-line distances</span>
      </div>
    </div>
  );
}
export function Progress({ status }: { status: string }) {
  const labels = ["Reserved", "Accepted", "In transit", "Arrived", "Received"];
  const active = [
    "reserved",
    "accepted",
    "in_transit",
    "arrived",
    "received",
  ].indexOf(status);
  return (
    <ol
      className="transfer-progress"
      aria-label={`Transfer status: ${pretty(status)}`}
    >
      {labels.map((s, i) => (
        <li className={i <= active ? "done" : ""} key={s}>
          <span>{i < active ? <Check size={12} /> : i + 1}</span>
          <small>{s}</small>
        </li>
      ))}
    </ol>
  );
}
export function InfoNote({ children }: { children: ReactNode }) {
  return (
    <div className="info-note">
      <ShieldCheck size={18} />
      <span>{children}</span>
    </div>
  );
}
export function SectionTitle({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow: string;
  title: string;
  description: string;
  actions?: ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {actions && <div className="heading-actions">{actions}</div>}
    </div>
  );
}
export function IconFor({
  kind,
}: {
  kind: "food" | "truck" | "check" | "pin";
}) {
  return kind === "food" ? (
    <Leaf size={22} />
  ) : kind === "truck" ? (
    <Truck size={22} />
  ) : kind === "check" ? (
    <CheckCircle2 size={22} />
  ) : (
    <MapPin size={22} />
  );
}
export function TextLink({
  children,
  onClick,
}: {
  children: ReactNode;
  onClick: () => void;
}) {
  return (
    <button className="text-link" onClick={onClick}>
      {children}
      <ChevronRight size={16} />
    </button>
  );
}
