import { useEffect, useState } from "react";
import {
  BarChart3,
  Boxes,
  ChevronDown,
  LayoutDashboard,
  Leaf,
  LogOut,
  Menu,
  Network,
  RefreshCw,
  Route,
  ShieldCheck,
  Sprout,
  Truck,
  Users,
  X,
} from "lucide-react";
import AuthScreen from "./Auth";
import Forms from "./Forms";
import type { DialogState } from "./Forms";
import { api, clearAuth, setAuth } from "./api";
import { Alert, Button, Logo } from "./components";
import type { Auth, Page, User, Workspace } from "./types";
import {
  Deliveries,
  Impact,
  Inventory,
  Overview,
  Planner,
  Sites,
  TeamView,
} from "./views";
export type PublicConfig = {
  demo_enabled: boolean;
  demo_only: boolean;
  registration_enabled: boolean;
};
const navigation = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "planner", label: "Relay planner", icon: Route },
  { id: "inventory", label: "Inventory", icon: Boxes },
  { id: "sites", label: "Pantries & needs", icon: Network },
  { id: "deliveries", label: "Deliveries", icon: Truck },
  { id: "impact", label: "Impact & reports", icon: BarChart3 },
  { id: "team", label: "Your team", icon: Users },
] as const;
export default function App() {
  const [user, setUser] = useState<User | null>(null),
    [w, setWorkspace] = useState<Workspace | null>(null),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [page, setPageState] = useState<Page>(() => {
      const h = window.location.hash.slice(1);
      return navigation.some((n) => n.id === h) ? (h as Page) : "overview";
    }),
    [dialog, setDialog] = useState<DialogState | null>(null),
    [toast, setToast] = useState(""),
    [mobile, setMobile] = useState(false),
    [refreshing, setRefreshing] = useState(false),
    [config, setConfig] = useState<PublicConfig>({
      demo_enabled: true,
      demo_only: false,
      registration_enabled: true,
    });
  useEffect(() => {
    void api<PublicConfig>("/config")
      .then(setConfig)
      .catch(() => {});
    void api<Auth>("/auth/me")
      .then((a) => {
        setAuth(a);
        setUser(a.user);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);
  async function refresh() {
    const data = await api<Workspace>("/workspace");
    setWorkspace(data);
    setUser(data.user);
  }
  useEffect(() => {
    const expired = () => {
      clearAuth();
      setUser(null);
      setWorkspace(null);
      setDialog(null);
      setError(
        "Your session has expired. Sign in again or open a fresh demo workspace.",
      );
    };
    window.addEventListener("pantry-session-expired", expired);
    return () => window.removeEventListener("pantry-session-expired", expired);
  }, []);
  useEffect(() => {
    if (user && !w) {
      void refresh().catch((e) => setError(e.message));
    }
  }, [user, w]);
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(""), 6500);
      return () => clearTimeout(timer);
    }
  }, [toast]);
  useEffect(() => {
    document.title = `${user ? navigation.find((n) => n.id === page)?.label + " · " : ""}Pantry Relay`;
  }, [user, page]);
  useEffect(() => {
    if (user?.role === "driver") setPageState("deliveries");
  }, [user?.role]);
  function setPage(p: Page) {
    setPageState(p);
    setMobile(false);
    window.history.replaceState(
      {},
      "",
      `${window.location.pathname}${window.location.search}#${p}`,
    );
    window.scrollTo(0, 0);
  }
  async function logout() {
    try {
      await api("/auth/logout", {});
      clearAuth();
      setUser(null);
      setWorkspace(null);
      setDialog(null);
      setPageState("overview");
      window.history.replaceState({}, "", window.location.pathname);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function manualRefresh() {
    setRefreshing(true);
    setError("");
    try {
      await refresh();
      setToast("Network is up to date.");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setRefreshing(false);
    }
  }
  const publicBanner = config.demo_only ? (
    <div className="public-demo-banner">
      <ShieldCheck size={15} />
      <span>
        <strong>Public demo</strong> · Fictitious data · Resets on restart. Do
        not enter real pantry or personal information.
      </span>
    </div>
  ) : null;
  if (loading)
    return (
      <div className="boot-screen">
        <Logo />
        <RefreshCw size={22} className="spin" />
        <p>Getting your network ready…</p>
      </div>
    );
  if (!user)
    return (
      <>
        {publicBanner}
        {error && (
          <div className="auth-session-alert">
            <Alert>{error}</Alert>
          </div>
        )}
        <AuthScreen
          config={config}
          onAuth={(a) => {
            setUser(a.user);
            setWorkspace(null);
            setError("");
          }}
        />
      </>
    );
  const currentPage =
    user.role === "driver"
      ? "deliveries"
      : config.demo_only && page === "team"
        ? "overview"
        : page;
  const props = w
    ? { w, setPage, open: setDialog, refresh, notify: setToast }
    : null;
  return (
    <div className="app-layout">
      <a href="#main-content" className="skip-link">
        Skip to content
      </a>
      {mobile && (
        <button
          className="sidebar-scrim"
          aria-label="Close navigation"
          onClick={() => setMobile(false)}
        />
      )}
      <aside className={`sidebar ${mobile ? "is-open" : ""}`}>
        <div className="sidebar-logo">
          <Logo />
          <button
            className="icon-button mobile-close"
            aria-label="Close navigation"
            onClick={() => setMobile(false)}
          >
            <X size={20} />
          </button>
        </div>
        <div className="network-selector">
          <span className="network-symbol">
            <Network size={20} />
          </span>
          <div>
            <strong>{w?.network.name || "Your network"}</strong>
            <small>
              {w?.network.is_demo ? "DEMO WORKSPACE" : "PRIVATE WORKSPACE"}
            </small>
          </div>
          <ChevronDown size={14} />
        </div>
        <div className="nav-label">YOUR WORKSPACE</div>
        <nav aria-label="Main navigation">
          {navigation
            .filter((n) => user.role !== "driver" || n.id === "deliveries")
            .filter((n) => !config.demo_only || n.id !== "team")
            .map((n) => (
              <button
                key={n.id}
                className={`nav-item ${currentPage === n.id ? "active" : ""}`}
                onClick={() => setPage(n.id)}
                aria-current={currentPage === n.id ? "page" : undefined}
              >
                <n.icon size={19} />
                <span>{n.label}</span>
                {n.id === "deliveries" && !!w?.metrics.active_transfers && (
                  <span className="nav-count">
                    {w.metrics.active_transfers}
                  </span>
                )}
                {currentPage === n.id && <span className="nav-active-dot" />}
              </button>
            ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-purpose">
            <span className="purpose-icon">
              <Sprout size={23} />
            </span>
            <p>
              Small relays.
              <br />
              <strong>Stronger communities.</strong>
            </p>
            <span>Good food. Better connected.</span>
          </div>
          <div className="sidebar-account">
            <span className="avatar">
              {user.name
                .split(" ")
                .map((x) => x[0])
                .slice(0, 2)
                .join("")
                .toUpperCase()}
            </span>
            <div>
              <strong>{user.name}</strong>
              <small>
                {user.role === "admin"
                  ? "Network admin"
                  : user.role === "driver"
                    ? "Volunteer driver"
                    : "Coordinator"}
              </small>
            </div>
            <button
              className="icon-button"
              aria-label="Sign out"
              onClick={() => void logout()}
            >
              <LogOut size={17} />
            </button>
          </div>
        </div>
      </aside>
      <div className="app-main">
        <header className="workspace-header">
          <button
            className="icon-button mobile-menu"
            aria-label="Open navigation"
            onClick={() => setMobile(true)}
          >
            <Menu size={23} />
          </button>
          <div className="breadcrumb">
            <span>Workspace</span>
            <span>/</span>
            <strong>
              {navigation.find((n) => n.id === currentPage)?.label}
            </strong>
          </div>
          <div className="header-right">
            <span className="network-status">
              <span className="status-dot" />
              People powered. Purpose driven.
            </span>
            <button
              className="icon-button"
              aria-label="Refresh workspace"
              title="Refresh workspace"
              disabled={refreshing}
              onClick={() => void manualRefresh()}
            >
              <RefreshCw size={17} className={refreshing ? "spin" : ""} />
            </button>
            <span className="header-avatar">
              {user.name.charAt(0).toUpperCase()}
            </span>
          </div>
        </header>
        {publicBanner}
        {w?.network.is_demo && !config.demo_only && (
          <div className="demo-banner">
            <span className="demo-label">DEMO</span>
            <span>
              Your own sample workspace. All organizations and activity are
              fictitious.
            </span>
            <span className="demo-safe">
              <ShieldCheck size={14} />
              Safe to explore
            </span>
          </div>
        )}
        <main className="workspace-content" id="main-content" tabIndex={-1}>
          {error && (
            <div className="workspace-error">
              <Alert>{error}</Alert>
              <Button variant="secondary" onClick={() => void manualRefresh()}>
                Retry
                <RefreshCw size={15} />
              </Button>
            </div>
          )}
          {!w ? (
            <div className="loading-workspace">
              <Leaf size={36} />
              <h2>Connecting your network…</h2>
              <p>Loading pantry stock, service needs and relays.</p>
            </div>
          ) : (
            props && (
              <>
                {currentPage === "overview" && <Overview {...props} />}{" "}
                {currentPage === "planner" && <Planner {...props} />}{" "}
                {currentPage === "inventory" && <Inventory {...props} />}{" "}
                {currentPage === "sites" && <Sites {...props} />}{" "}
                {currentPage === "deliveries" && <Deliveries {...props} />}{" "}
                {currentPage === "impact" && <Impact {...props} />}{" "}
                {currentPage === "team" && !config.demo_only && (
                  <TeamView {...props} />
                )}
              </>
            )
          )}
        </main>
        <footer className="workspace-footer">
          <span>
            <Sprout size={14} />
            Pantry Relay
          </span>
          <span>
            Times shown in {Intl.DateTimeFormat().resolvedOptions().timeZone}.
          </span>
          <span>By Shivam Gupta · Hack Away Hunger</span>
        </footer>
      </div>
      {dialog && w && (
        <Forms
          state={dialog}
          workspace={w}
          onClose={() => setDialog(null)}
          onSaved={async (message) => {
            await refresh();
            setToast(message);
          }}
        />
      )}
      {toast && (
        <div className="toast" role="status">
          <ShieldCheck size={18} />
          <span>{toast}</span>
          <button
            aria-label="Dismiss notification"
            onClick={() => setToast("")}
          >
            <X size={15} />
          </button>
        </div>
      )}
    </div>
  );
}
