import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useBackends, useTracker } from "../lib/backend";
import { useChanges } from "../lib/changes";
import { Status, WorkItem } from "../lib/types";

const STATUSES: Status[] = ["OPEN", "IN_PROGRESS", "BLOCKED", "DONE", "CANCELLED"];
type SortKey = "priority" | "title" | "updatedAt";

/** Field-prefixed, so each message can render against the input that caused it. */
function validate(title: string, priority: string, assignee: string): string[] {
  const found: string[] = [];
  if (title.trim().length < 3) found.push("title needs at least three characters");
  const value = Number(priority);
  if (!priority.trim() || Number.isNaN(value) || value < 1 || value > 10) {
    found.push("priority must be a number from one to ten");
  }
  if (!assignee.trim()) found.push("assignee is required");
  return found;
}

/**
 * The same application as the Angular module, from the same stylesheet, in hooks.
 *
 * Angular holds arrivals and departures in signals and binds classes off them; this derives
 * the same two sets with useState and a ref for what has been seen. The rendered output is
 * identical because the stylesheet is one file copied into both — the route to it is the
 * pair's whole point, and it is the part that cannot be faked.
 */
export function Tracker() {
  const { options, selected, select } = useBackends();
  const api = useTracker(selected);

  const [items, setItems] = useState<WorkItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);
  const [status, setStatus] = useState("");
  const [tag, setTag] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("priority");
  const [rejection, setRejection] = useState<Record<string, string> | null>(null);
  const [workload, setWorkload] = useState<Record<string, number> | null>(null);
  const [workloadLoading, setWorkloadLoading] = useState(false);
  const [workloadProgress, setWorkloadProgress] = useState(0);
  const [liveEvents, setLiveEvents] = useState(0);

  const [arrivals, setArrivals] = useState<Set<string>>(new Set());
  const [leaving, setLeaving] = useState<Set<string>>(new Set());
  const known = useRef<Set<string>>(new Set());

  const [title, setTitle] = useState("");
  const [priority, setPriority] = useState("");
  const [assignee, setAssignee] = useState("");
  const [errors, setErrors] = useState<string[]>([]);
  const [runtimeShown, setRuntimeShown] = useState(false);
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [toasts, setToasts] = useState<{ id: number; text: string }[]>([]);

  /** One attribute on the document; both palettes are declared, so nothing here knows a colour. */
  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.setAttribute("data-theme", next);
  };
  const [runtime, setRuntime] = useState<any>(null);

  const refresh = useCallback(async () => {
    if (!selected) return;
    setLoading(true);
    try {
      const next = await api.list({ status, tag });
      // Anything not seen before arrived while this browser sat still, which is what the
      // animation says: the change came from somewhere else.
      const fresh = next.filter((item) => !known.current.has(item.id)).map((item) => item.id);
      const first = known.current.size === 0;
      known.current = new Set(next.map((item) => item.id));
      setItems(next);
      setFailed(false);
      if (fresh.length && !first) {
        setArrivals((current) => new Set([...current, ...fresh]));
        setTimeout(() => setArrivals((current) => {
          const rest = new Set(current);
          fresh.forEach((id) => rest.delete(id));
          return rest;
        }), 1200);
      }
    } catch {
      // An empty list and a backend that did not answer are different states and must not
      // render the same.
      setItems([]);
      setFailed(true);
    } finally {
      setLoading(false);
    }
  }, [api, selected, status, tag]);

  useEffect(() => { void refresh(); }, [refresh]);

  const onChange = useCallback(() => {
    setLiveEvents((n) => {
      const next = n + 1;
      // Unmissable: the row animates and this says what happened, because a change made in
      // another browser is the one thing a viewer will otherwise miss.
      setToasts((current) => [...current, { id: next, text: "change from another client" }].slice(-3));
      setTimeout(() => setToasts((current) => current.filter((t) => t.id !== next)), 4000);
      return next;
    });
    void refresh();
  }, [refresh]);
  useChanges(selected ? `/api/${selected}` : "", onChange);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const wanted = params.get("backend");
    if (wanted && options.some((option) => option.id === wanted) && selected !== wanted) {
      select(wanted);
    }
  }, [options, selected, select]);

  useEffect(() => {
    if (!runtimeShown || !selected) return;
    let cancelled = false;
    fetch(`/__runtime?backend=${encodeURIComponent(selected)}`)
      .then((response) => (response.ok ? response.json() : null))
      .then((body) => !cancelled && setRuntime(body))
      .catch(() => undefined);
    return () => { cancelled = true; };
  }, [runtimeShown, selected]);

  const sorted = useMemo(
    () => [...items].sort((a, b) => {
      if (sortKey === "priority") return b.priority - a.priority || a.title.localeCompare(b.title);
      if (sortKey === "title") return a.title.localeCompare(b.title);
      return (b.updatedAt ?? "").localeCompare(a.updatedAt ?? "");
    }),
    [items, sortKey],
  );

  const workloadRows = useMemo(() => Object.entries(workload ?? {}), [workload]);
  const highest = useMemo(
    () => Math.max(1, ...workloadRows.map(([, total]) => total)),
    [workloadRows],
  );

  const capabilities: [string, any][] = Object.entries(
    runtime?.autoconfig?.capabilities ?? runtime?.beans?.capabilities ?? {},
  );

  /** What supplied the capability, not the category it is filed under. */
  const suppliedBy = (row: any): string => {
    const declared = String(row?.declared_at ?? "");
    if (!declared) return String(row?.source ?? "");
    const cleaned = declared.replace(/^class path resource \[/, "").replace(/\.class\]$/, "");
    return cleaned.split(/[/.]/).filter(Boolean).pop() ?? cleaned;
  };

  const errorFor = (field: string) => errors.find((message) => message.startsWith(field)) ?? null;

  async function move(item: WorkItem, next: Status) {
    if (next === item.status) return;
    setRejection(null);
    const result = await api.transition(item.id, next);
    if (result.rejected) setRejection(result.rejected);
    await refresh();
  }

  async function archive(item: WorkItem) {
    // Out, then gone. Removing the row instantly reads as the list flickering; the exit is
    // what tells the viewer which row went.
    setLeaving((current) => new Set([...current, item.id]));
    setTimeout(async () => {
      await api.archive(item.id);
      setLeaving((current) => {
        const rest = new Set(current);
        rest.delete(item.id);
        return rest;
      });
      await refresh();
    }, 240);
  }

  async function runWorkload() {
    setWorkloadLoading(true);
    setWorkloadProgress(0);
    // Real progress rather than the word "loading": the aggregate is a deliberately slow
    // fan-out of one computation per assignee, so the bar advances against how long that
    // should take and completes when the answer lands.
    const expected = Math.max(400, items.length * 120);
    const started = Date.now();
    const ticker = setInterval(
      () => setWorkloadProgress(Math.min(95, ((Date.now() - started) / expected) * 100)),
      60,
    );
    try {
      setWorkload(await api.workload());
      setWorkloadProgress(100);
    } finally {
      clearInterval(ticker);
      setWorkloadLoading(false);
    }
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    const found = validate(title, priority, assignee);
    setErrors(found);
    if (found.length) return;
    await api.create({
      id: `WI-${Date.now().toString().slice(-6)}`,
      title: title.trim(),
      status: "OPEN",
      priority: Number(priority),
      assignee: assignee.trim(),
      tags: [],
    });
    setTitle("");
    setPriority("");
    setAssignee("");
    await refresh();
  }

  return (
    <div className="app" data-testid="tracker">
      <header className="bar">
        <h1 className="brand">
          <svg className="icon" viewBox="0 0 16 16" aria-hidden="true">
            <path fill="currentColor" d="M2 3.2A1.2 1.2 0 0 1 3.2 2h9.6A1.2 1.2 0 0 1 14 3.2v9.6a1.2 1.2 0 0 1-1.2 1.2H3.2A1.2 1.2 0 0 1 2 12.8Zm2.4 2.3h7.2v1.4H4.4Zm0 3h4.8v1.4H4.4Z" />
          </svg>
          Work items
        </h1>
        <span className="sub">React</span>
        <span className="spacer" />
        <span className="sub live-count" data-testid="live-count">{liveEvents} live</span>
        <button type="button" className="ghost" data-testid="theme-toggle" onClick={toggleTheme}
                aria-label={theme === "dark" ? "switch to light" : "switch to dark"}>
          {theme === "dark" ? (
            <svg className="icon" viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M8 1.5a1 1 0 0 1 1 1V4a1 1 0 1 1-2 0V2.5a1 1 0 0 1 1-1Zm0 9a2.5 2.5 0 1 1 0-5 2.5 2.5 0 0 1 0 5Zm0 1.5a1 1 0 0 1 1 1v1.5a1 1 0 1 1-2 0V13a1 1 0 0 1 1-1Zm6-4a1 1 0 0 1-1 1h-1.5a1 1 0 1 1 0-2H13a1 1 0 0 1 1 1ZM4.5 8a1 1 0 0 1-1 1H2a1 1 0 1 1 0-2h1.5a1 1 0 0 1 1 1Z" /></svg>
          ) : (
            <svg className="icon" viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M13.2 9.6A5.6 5.6 0 0 1 6.4 2.8 5.6 5.6 0 1 0 13.2 9.6Z" /></svg>
          )}
        </button>
        <button type="button" className="ghost" data-testid="runtime-toggle" onClick={() => setRuntimeShown(!runtimeShown)}>
          <svg className="icon" viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M8 1.6 14 5v6l-6 3.4L2 11V5Zm0 1.8L3.6 5.9v4.2L8 12.6l4.4-2.5V5.9Z" /></svg>
          runtime
        </button>
        <label className="field">
          <span className="label">backend</span>
          <select data-testid="backend-select" value={selected}
                  onChange={(e) => { select(e.target.value); setWorkload(null); setRejection(null); }}>
            {options.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
          </select>
        </label>
      </header>

      <aside className="rail">
        <div>
          <span className="label">filter</span>
          <label className="field">
            <select data-testid="filter-status" value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="">any status</option>
              {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </label>
          <label className="field">
            <input data-testid="filter-tag" value={tag} onChange={(e) => setTag(e.target.value)}
                   placeholder="part of a tag" />
          </label>
        </div>

        <div>
          <span className="label">sort</span>
          <label className="field">
            <select data-testid="sort" value={sortKey} onChange={(e) => setSortKey(e.target.value as SortKey)}>
              <option value="priority">priority</option>
              <option value="title">title</option>
              <option value="updatedAt">recently updated</option>
            </select>
          </label>
        </div>

        <div>
          <span className="label">aggregate</span>
          <button type="button" data-testid="run-workload" onClick={runWorkload} disabled={workloadLoading}>
            <svg className="icon" viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M2 13h12v1.4H2Zm1.6-4h2v3h-2Zm3.4-4h2v7H7Zm3.4-3h2v10h-2Z" /></svg>
            workload
          </button>
        </div>
      </aside>

      <main className="main">
        <h2 className="page-title">{selected}</h2>
        <p className="sub">One contract, {options.length} runtimes. This screen is the same in both frameworks.</p>

        {runtimeShown && runtime && (
          <section className="card runtime" data-testid="runtime-panel">
            <h2>{runtime.backend}</h2>
            <p className="sub">
              {/* The exact build, because "25" is a claim and "25.0.3+9-LTS" is an answer.
                  The short form remains what the version floor is compared against; this
                  panel is where someone asks which JDK actually produced the page. */}
              <strong data-testid="runtime-version">
                {runtime.identity?.runtime_version_exact ?? runtime.identity?.runtime_version}
              </strong>
              {runtime.identity?.runtime_vendor && (
                <>{" · "}<span data-testid="runtime-vendor">{runtime.identity.runtime_vendor}</span></>
              )}
              {" · "}<span data-testid="runtime-server">{runtime.identity?.http_server_class}</span>
              {" · "}<span data-testid="runtime-artifacts">{(runtime.identity?.artifacts ?? []).length} artifacts</span>
            </p>
            {(runtime.identity?.artifacts ?? []).length > 0 && (
              // The count above answers "how many"; this answers "which, and at what
              // version" — the question the count can't. Collapsed by default so the
              // panel stays scannable, but the exact resolved versions are one click
              // away rather than only visible in the raw JSON.
              <details data-testid="runtime-artifacts-detail">
                <summary>show artifacts</summary>
                <ul className="artifact-list" data-testid="runtime-artifacts-list">
                  {(runtime.identity?.artifacts ?? []).map((artifact: string) => (
                    <li key={artifact}>{artifact}</li>
                  ))}
                </ul>
              </details>
            )}
            {runtime.pair?.identity && (
              <>
              {/* The framework version, not the JVM underneath it: spring-boot and
                  spring-traditional share a base image, so runtime_version_exact is
                  identical on both sides and says nothing about which framework is
                  which. frameworkVersion is resolved server-side from the artifact the
                  declared framework actually ships as; falls back to the runtime
                  version only for the two stacks that have no framework by design,
                  where the runtime genuinely is the whole answer. */}
              <p className="sub pair-versions" data-testid="runtime-pair-versions">
                <strong>{runtime.backend}</strong> version:{" "}
                <strong>
                  {runtime.frameworkVersion ?? runtime.identity?.runtime_version_exact ?? runtime.identity?.runtime_version}
                </strong>
                {" · "}<strong>{runtime.pair.backend}</strong> version:{" "}
                <strong>
                  {runtime.pair.frameworkVersion
                    ?? runtime.pair.identity?.runtime_version_exact
                    ?? runtime.pair.identity?.runtime_version}
                </strong>
              </p>
              <p className="sub pair-counts" data-testid="runtime-pair">
                against its pair — <strong>{runtime.backend}: {(runtime.identity?.artifacts ?? []).length}</strong> artifacts,{" "}
                <strong>{runtime.pair.backend}: {(runtime.pair.identity.artifacts ?? []).length}</strong>. Same contract,
                same behaviour,{" "}
                {Math.abs((runtime.pair.identity.artifacts ?? []).length - (runtime.identity?.artifacts ?? []).length)}{" "}
                {/* The word follows the sign. An absolute count said "more" on both sides,
                    which read as the opposite of the truth on the smaller runtime. */}
                {(runtime.identity?.artifacts ?? []).length > (runtime.pair.identity.artifacts ?? []).length
                  ? "more"
                  : "fewer"}{" "}
                jars to get there.
              </p>
              </>
            )}
            {capabilities.length > 0 && (
              <table data-testid="runtime-capabilities">
                <thead><tr><th>capability</th><th>bean</th><th>supplied by</th><th>declared at</th></tr></thead>
                <tbody>
                  {capabilities.map(([name, row]) => (
                    <tr key={name}>
                      <td>{name}</td><td>{row.bean}</td>
                      <td data-testid="capability-source">{suppliedBy(row)}</td>
                      <td className="where">{row.declared_at}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        )}

        {workloadLoading ? (
          <section className="card" data-testid="workload-loading">
            <h2>workload</h2>
            <p className="sub">Fanning out one slow computation per assignee.</p>
            <div className="progress"><span style={{ width: `${workloadProgress}%` }} /></div>
          </section>
        ) : workload ? (
          <section className="card" data-testid="workload">
            <h2>workload</h2>
            <div className="bars">
              {workloadRows.map(([who, total]) => (
                <div className="bar-row" key={who}>
                  <span>{who}</span>
                  <span className="meter"><span style={{ width: `${Math.round((total / highest) * 100)}%` }} /></span>
                  <span className="num">{total}</span>
                </div>
              ))}
            </div>
          </section>
        ) : null}

        {rejection && (
          <p className="refused" data-testid="rejection" role="status">
            <svg className="icon" viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M8 1.6 14.6 13H1.4Zm-.8 4v4h1.6v-4Zm0 5v1.6h1.6v-1.6Z" /></svg>
            {rejection.reason || `${rejection.from} cannot move to ${rejection.to}`}
          </p>
        )}

        <p className="sub" data-testid="transition-note">
          the status control runs a state machine: an illegal move is refused by the
          backend, not hidden by the form.
        </p>

        {loading ? (
          <section className="card table-card" data-testid="loading">
            {[1, 2, 3, 4, 5].map((row) => (
              <div className="skeleton-row" key={row}>
                <span className="skeleton" /><span className="skeleton" />
                <span className="skeleton" /><span className="skeleton" />
              </div>
            ))}
          </section>
        ) : failed ? (
          <section className="card state" data-kind="error" data-testid="error">
            <svg className="icon-lg" viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M8 1.6 14.6 13H1.4Zm-.8 4v4h1.6v-4Zm0 5v1.6h1.6v-1.6Z" /></svg>
            <strong>{selected} did not answer</strong>
            <span className="sub">The request failed. The other runtimes are still selectable.</span>
            <button type="button" onClick={() => void refresh()}>try again</button>
          </section>
        ) : sorted.length === 0 ? (
          <section className="card state" data-testid="empty">
            <svg className="icon-lg" viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M2.5 3h11v1.6h-11Zm0 4h11v1.6h-11Zm0 4h7v1.6h-7Z" /></svg>
            <strong>Nothing matches those filters</strong>
            <span className="sub">{items.length} items exist on this backend.</span>
            <button type="button" onClick={() => { setStatus(""); setTag(""); }}>clear filters</button>
          </section>
        ) : (
          <section className="card table-card">
            <table data-testid="list">
              <thead>
                <tr>
                  <th>id</th><th>title</th><th>status</th><th className="num">pri</th>
                  <th>assignee</th><th>tags</th><th />
                </tr>
              </thead>
              <tbody>
                {sorted.map((item) => (
                  <tr key={item.id} data-testid="row"
                      className={`${arrivals.has(item.id) ? "arrived" : ""} ${leaving.has(item.id) ? "leaving" : ""}`.trim()}>
                    <td className="id mono">{item.id}</td>
                    <td className="title">{item.title}</td>
                    <td>
                      <span className="pill" data-status={item.status}>
                        <select data-testid="row-status" value={item.status} aria-label="change status"
                                onChange={(e) => void move(item, e.target.value as Status)}>
                          {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                        </select>
                      </span>
                    </td>
                    <td className="num">{item.priority}</td>
                    <td>{item.assignee}</td>
                    <td><span className="tags">{item.tags.map((t) => <span className="tag" key={t}>{t}</span>)}</span></td>
                    <td>
                      <button type="button" className="ghost row-actions" data-testid="archive"
                              onClick={() => void archive(item)} aria-label="archive">
                        <svg className="icon" viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M2 3h12v2.4H2Zm1 3.4h10V13H3Zm2.4 2v1.4h5.2V8.4Z" /></svg>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        )}

        <section className="card">
          <h2>new item</h2>
          <form onSubmit={submit} style={{ display: "flex", gap: "var(--space-2)", alignItems: "end", flexWrap: "wrap" }}>
            <label className={`field ${errorFor("title") ? "invalid" : ""}`} style={{ flex: "2 1 14rem" }}>
              <span className="label">title</span>
              <input data-testid="new-title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="what needs doing" />
              {errorFor("title") && <span className="error" data-testid="error-title">{errorFor("title")}</span>}
            </label>
            <label className={`field ${errorFor("priority") ? "invalid" : ""}`} style={{ flex: "0 1 7rem" }}>
              <span className="label">priority</span>
              <input data-testid="new-priority" value={priority} onChange={(e) => setPriority(e.target.value)} placeholder="1–10" />
              {errorFor("priority") && <span className="error" data-testid="error-priority">{errorFor("priority")}</span>}
            </label>
            <label className={`field ${errorFor("assignee") ? "invalid" : ""}`} style={{ flex: "1 1 10rem" }}>
              <span className="label">assignee</span>
              <input data-testid="new-assignee" value={assignee} onChange={(e) => setAssignee(e.target.value)} placeholder="who" />
              {errorFor("assignee") && <span className="error" data-testid="error-assignee">{errorFor("assignee")}</span>}
            </label>
            <button className="primary" type="submit" data-testid="create">create</button>
          </form>
          {errors.length > 0 && (
            <ul className="error" data-testid="create-errors">
              {errors.map((error) => <li key={error}>{error}</li>)}
            </ul>
          )}
        </section>
      </main>

      <div className="toasts" data-testid="toasts">
        {toasts.map((toast) => (
          <div className="toast" key={toast.id}><span className="dot" />{toast.text}</div>
        ))}
      </div>
    </div>
  );
}
