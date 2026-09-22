import { useEffect, useState, type FormEvent } from "react";
import {
  ArrowDown,
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronRight,
  HeartHandshake,
  Leaf,
  LockKeyhole,
  MoveRight,
  ShieldCheck,
  Sprout,
  Truck,
} from "lucide-react";
import { api, setAuth } from "./api";
import type { Auth } from "./types";
import type { PublicConfig } from "./App";
import { Alert, Button, Field, Logo, NetworkMap } from "./components";
export default function AuthScreen({
  onAuth,
  config,
}: {
  onAuth: (auth: Auth) => void;
  config: PublicConfig;
}) {
  const invite =
    new URLSearchParams(window.location.search).get("invite") || "";
  const [mode, setMode] = useState<"landing" | "login" | "register" | "join">(
    invite ? "join" : "landing",
  );
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  useEffect(() => {
    if (config.demo_only) setMode("landing");
  }, [config.demo_only]);
  const choose = (m: typeof mode) => {
    setMode(m);
    setError("");
  };
  async function run(path: string, body: unknown) {
    setBusy(true);
    setError("");
    try {
      const auth = await api<Auth>(path, body);
      setAuth(auth);
      onAuth(auth);
      if (invite) window.history.replaceState({}, "", window.location.pathname);
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Unable to sign in. Please try again.",
      );
    } finally {
      setBusy(false);
    }
  }
  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    void run(`/auth/${mode}`, Object.fromEntries(f));
  }
  return (
    <div className="public-page">
      <header className="public-header">
        <button
          className="brand-button"
          aria-label="Pantry Relay home"
          onClick={() => choose("landing")}
        >
          <Logo />
        </button>
        <nav aria-label="Account navigation">
          {mode === "landing" && (
            <a className="public-about" href="#how-it-works">
              How it works
            </a>
          )}
          {!config.demo_only && (
            <Button variant="ghost" onClick={() => choose("login")}>
              Sign in
            </Button>
          )}
          {config.registration_enabled && (
            <Button onClick={() => choose("register")}>
              Start a network
              <ArrowRight size={16} />
            </Button>
          )}
        </nav>
      </header>
      {mode === "landing" ? (
        <>
          <main className="landing">
            <section className="hero">
              <div className="hero-copy">
                <p className="eyebrow">
                  <span className="status-dot" /> BUILT FOR THE PEOPLE WHO FEED
                  IOWA
                </p>
                <h1>
                  Good food.
                  <br />
                  Better <em>connected.</em>
                </h1>
                <p className="hero-description">
                  One pantry has extra. Another has a line out the door. Make
                  the connection before the next service.
                </p>
                <div className="hero-actions">
                  <Button
                    onClick={() => void run("/auth/demo", {})}
                    loading={busy}
                    disabled={!config.demo_enabled}
                  >
                    Explore the live demo
                    <ArrowRight size={18} />
                  </Button>
                  {config.registration_enabled && (
                    <Button
                      variant="secondary"
                      onClick={() => choose("register")}
                    >
                      Create your network
                    </Button>
                  )}
                </div>
                {error && <Alert>{error}</Alert>}
                <p className="hero-fine">
                  <CheckCircle2 size={15} /> No API keys. No household data.
                  Every handoff accounted for.
                </p>
              </div>
              <div className="hero-visual">
                <div className="visual-heading">
                  <span>
                    <span className="status-dot" /> THE NEXT GOOD CONNECTION
                  </span>
                  <span className="mini-tag">PANTRY → PANTRY</span>
                </div>
                <NetworkMap sites={[]} hero />
                <div className="hero-relay">
                  <div className="hero-food">
                    <Leaf size={23} />
                  </div>
                  <div>
                    <strong>Extra here. Needed there.</strong>
                    <p>Protect local stock. Move only what can be shared.</p>
                  </div>
                  <span className="relay-arrow">
                    <ArrowRight size={22} />
                  </span>
                </div>
                <div className="hero-sticker">
                  <ShieldCheck size={16} /> People approve. The system checks.
                </div>
              </div>
            </section>
            <div className="value-strip">
              <span>
                <ShieldCheck size={19} /> Protected pantry reserves
              </span>
              <span>
                <Truck size={19} /> Explained, practical matches
              </span>
              <span>
                <CheckCircle2 size={19} /> Confirmed receipt accounting
              </span>
            </div>
            <section id="how-it-works" className="how-section">
              <div className="section-intro">
                <p className="eyebrow">A SMALL RELAY. A REAL DIFFERENCE.</p>
                <h2>
                  From “we have extra”
                  <br />
                  to “it’s here.”
                </h2>
                <p>
                  Food access takes more than a directory. Give your network a
                  shared way to turn available food into a completed handoff.
                </p>
              </div>
              <div className="steps-grid">
                {[
                  {
                    n: "01",
                    icon: <Sprout />,
                    title: "See what can be shared",
                    text: "Log pantry stock and upcoming needs. Keep a protected reserve for your own visitors.",
                  },
                  {
                    n: "02",
                    icon: <MoveRight />,
                    title: "Make a workable match",
                    text: "Check deadlines, distance, storage and vehicle capacity. Understand why every match works.",
                  },
                  {
                    n: "03",
                    icon: <HeartHandshake />,
                    title: "Close the loop",
                    text: "Accept, pick up and confirm delivery. Count the pounds that actually arrive, with a complete record.",
                  },
                ].map((s) => (
                  <article className="how-card" key={s.n}>
                    <span className="step-number">{s.n}</span>
                    <div>{s.icon}</div>
                    <h3>{s.title}</h3>
                    <p>{s.text}</p>
                  </article>
                ))}
              </div>
            </section>
            <section className="landing-bottom">
              <div>
                <p className="eyebrow">LOCAL KNOWLEDGE. SHARED POSSIBILITY.</p>
                <h2>
                  Keep the food moving.
                  <br />
                  Keep the community in control.
                </h2>
              </div>
              <Button
                onClick={() => void run("/auth/demo", {})}
                loading={busy}
                disabled={!config.demo_enabled}
              >
                Try the complete workflow
                <ArrowRight size={18} />
              </Button>
            </section>
          </main>
        </>
      ) : (
        <main className="auth-layout">
          <section className="auth-story">
            <p className="eyebrow">GOOD FOOD DESERVES A GOOD HANDOFF.</p>
            <h1>
              A stronger network.
              <br />A fuller table.
            </h1>
            <p>
              Connect the pantries doing the work. Make every pound, every
              volunteer trip and every next service count.
            </p>
            <div className="auth-story-list">
              <span>
                <Check /> Keep pantry reserves protected
              </span>
              <span>
                <Check /> Plan around real capacity and deadlines
              </span>
              <span>
                <Check /> Track actual receipts, not promises
              </span>
            </div>
            <div className="auth-sprout">
              <Sprout size={110} />
            </div>
            <small>Created by Shivam Gupta for Hack Away Hunger</small>
          </section>
          <section className="auth-panel">
            <button className="text-link" onClick={() => choose("landing")}>
              <ArrowDown size={14} className="rotate-right" /> Back to home
            </button>
            <div className="auth-title">
              <span className="auth-lock">
                <LockKeyhole size={22} />
              </span>
              <h2>
                {mode === "login"
                  ? "Welcome back."
                  : mode === "join"
                    ? "Join your pantry network."
                    : "Start something good."}
              </h2>
              <p>
                {mode === "login"
                  ? "Your next good connection is waiting."
                  : mode === "join"
                    ? "Your coordinator has invited you to Pantry Relay."
                    : "Create a private workspace for your pantry network."}
              </p>
            </div>
            <form onSubmit={submit} className="auth-form">
              {mode === "join" && (
                <input type="hidden" name="token" value={invite} />
              )}
              {mode !== "login" && (
                <Field label="Your full name">
                  <input
                    name="name"
                    required
                    maxLength={120}
                    autoComplete="name"
                    placeholder="Shivam Gupta"
                  />
                </Field>
              )}
              {mode === "register" && (
                <Field label="Network name">
                  <input
                    name="network_name"
                    required
                    maxLength={120}
                    placeholder="Your community pantry network"
                  />
                </Field>
              )}
              <Field label="Email address">
                <input
                  name="email"
                  type="email"
                  required
                  autoComplete="email"
                  placeholder="you@yourorganization.org"
                />
              </Field>
              <Field
                label="Password"
                hint={
                  mode !== "login"
                    ? "Use at least 12 characters. A memorable passphrase works well."
                    : undefined
                }
              >
                <input
                  name="password"
                  type="password"
                  required
                  minLength={mode === "login" ? 1 : 12}
                  maxLength={256}
                  autoComplete={
                    mode === "login" ? "current-password" : "new-password"
                  }
                />
              </Field>
              {error && <Alert>{error}</Alert>}
              <Button type="submit" loading={busy}>
                {mode === "login"
                  ? "Sign in"
                  : mode === "join"
                    ? "Join network"
                    : "Create network"}
                <ArrowRight size={16} />
              </Button>
            </form>
            <p className="auth-switch">
              {mode === "login"
                ? "New to Pantry Relay?"
                : "Already have an account?"}{" "}
              <button
                onClick={() => choose(mode === "login" ? "register" : "login")}
              >
                {mode === "login" ? "Create a network" : "Sign in"}
                <ChevronRight size={14} />
              </button>
            </p>
            <div className="auth-demo">
              <span>Just looking around?</span>
              <button
                onClick={() => void run("/auth/demo", {})}
                disabled={busy}
              >
                Open an isolated sample workspace <ArrowRight size={15} />
              </button>
              <small>Demo organizations and activity are fictitious.</small>
            </div>
          </section>
        </main>
      )}
      <footer className="public-footer">
        <Logo />
        <span>Good food. Better connected.</span>
        <span>Built by Shivam Gupta · Hack Away Hunger 2026</span>
      </footer>
    </div>
  );
}
