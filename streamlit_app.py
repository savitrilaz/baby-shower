import { useState, useEffect, useCallback } from "react";

// ─── CONFIG ──────────────────────────────────────────────────────────────────
const SHEET_ID = "1fUsJxGXaovwEEhiP6vjV62xDo1fQ6wlaQ9DGaHMFREE";
const SPLITWISE_URL = "https://splitwise.com";

// To enable live sync: File → Share → Anyone with link → Viewer
// The dashboard fetches the public CSV export automatically.
function csvUrl(sheet) {
  return `https://docs.google.com/spreadsheets/d/${SHEET_ID}/gviz/tq?tqx=out:csv&sheet=${encodeURIComponent(sheet)}`;
}

// ─── CONSTANTS ────────────────────────────────────────────────────────────────
const CAT_ICONS = {
  "Venue & Logistics": "🏛",
  "Invitations & Guest Experience": "✉️",
  "Food": "🍽",
  "Drinks": "🥂",
  "Decor & Styling": "🌿",
  "Activities & Games": "🎯",
  "Keepsakes & Sentimental Touches": "💌",
  "Favors & Gifts": "🎁",
  "Budget & Coordination": "📊",
};

const STATUS_CFG = {
  "Completed":       { bg: "#D1FAE5", color: "#065F46" },
  "In Progress":     { bg: "#DBEAFE", color: "#1E40AF" },
  "Not Yet Started": { bg: "#F3F4F6", color: "#374151" },
  "Considering":     { bg: "#FFF3CD", color: "#856404" },
};

const PRIO_CFG = {
  High:   { bg: "#FEE2E2", color: "#B91C1C" },
  Medium: { bg: "#FEF3C7", color: "#92400E" },
  Low:    { bg: "#EAF2EA", color: "#4A7C59" },
};

const OWNER_CFG = {
  Jessica: { bg: "#F2E4E1", color: "#8C3A3A" },
  Carly:   { bg: "#E4EAF2", color: "#2C4A8C" },
  Kirsten: { bg: "#EAF2E4", color: "#2C6B3A" },
  Savitri: { bg: "#F0E4F2", color: "#6B2C8C" },
};

const STATUS_BAR_COLORS = {
  "Completed":       "#7A9E7E",
  "In Progress":     "#60A5FA",
  "Not Yet Started": "#D1D5DB",
  "Considering":     "#FBBF24",
};

const IDEA_CATS = [
  { key: "decor",      label: "Decor & balloons",   icon: "🌿" },
  { key: "food",       label: "Food ideas",          icon: "🍽" },
  { key: "drinks",     label: "Signature drinks",    icon: "🥂" },
  { key: "gifts",      label: "Favors & gift bags",  icon: "🎁" },
  { key: "activities", label: "Activities & games",  icon: "🎯" },
  { key: "other",      label: "Other / misc",        icon: "✨" },
];

const SEED_IDEAS = {
  decor: [
    { id: 1, text: "Oversized sage balloon arch at entrance", author: "Savitri", score: 3, voted: null },
    { id: 2, text: "Pressed flower place cards at each seat", author: "Kirsten", score: 2, voted: null },
  ],
  food: [
    { id: 3, text: "Cantaloupe + prosciutto skewers as apps", author: "Jessica", score: 4, voted: null },
    { id: 4, text: "Mini uncrustable sliders with fancy labels", author: "Carly", score: 5, voted: null },
  ],
  drinks: [
    { id: 5, text: "Nicole's drink: Hugo Spritz with elderflower", author: "Carly", score: 3, voted: null },
    { id: 6, text: "Zach's drink: smoky mezcal aperol riff", author: "Carly", score: 2, voted: null },
  ],
  gifts: [
    { id: 7, text: "Passport-style booklet favor with trip tips", author: "Kirsten", score: 1, voted: null },
    { id: 8, text: "Custom airline baggage tag with baby's name", author: "Jessica", score: 4, voted: null },
  ],
  activities: [
    { id: 9, text: "Destination bingo — guests pick where baby travels first", author: "Savitri", score: 3, voted: null },
  ],
  other: [],
};

// ─── CSV PARSER ───────────────────────────────────────────────────────────────
function parseCSV(text) {
  const lines = text.split(/\r?\n/);
  return lines.map(line => {
    const cells = [];
    let cur = "", inQ = false;
    for (let i = 0; i < line.length; i++) {
      const c = line[i];
      if (c === '"') { inQ = !inQ; }
      else if (c === "," && !inQ) { cells.push(cur.trim()); cur = ""; }
      else { cur += c; }
    }
    cells.push(cur.trim());
    return cells;
  });
}

function sheetToTasks(text) {
  const rows = parseCSV(text);
  let hi = rows.findIndex(r => r[0]?.replace(/"/g, "").trim() === "Category");
  if (hi < 0) hi = 0;
  const hdrs = rows[hi].map(h => h.replace(/"/g, "").trim().toLowerCase());
  const col = (...aliases) => hdrs.findIndex(h => aliases.some(a => h.includes(a)));
  const C = {
    cat: col("category"), item: col("item name"), desc: col("description", "notes"),
    status: col("status"), owner: col("owner"), priority: col("priority"),
    link: col("link"), sw: col("splitwise"),
  };
  return rows.slice(hi + 1).map((r, i) => {
    const cat  = r[C.cat]?.replace(/"/g, "").trim();
    const item = r[C.item]?.replace(/"/g, "").trim();
    if (!cat || !item || cat === "Category") return null;
    return {
      id: i, cat, item,
      desc:     r[C.desc]?.replace(/"/g, "").trim() || "",
      status:   r[C.status]?.replace(/"/g, "").trim() || "Not Yet Started",
      owner:    r[C.owner]?.replace(/"/g, "").trim() || "",
      priority: r[C.priority]?.replace(/"/g, "").trim() || "",
      link:     r[C.link]?.replace(/"/g, "").trim() || "",
      sw:       r[C.sw]?.replace(/"/g, "").trim() || "",
    };
  }).filter(Boolean);
}

// ─── TINY UI ATOMS ────────────────────────────────────────────────────────────
const mono = { fontFamily: "'DM Mono', monospace" };

function Pill({ label, bg, color, size = 11 }) {
  return (
    <span style={{
      display: "inline-flex", alignItems: "center",
      padding: "2px 9px", borderRadius: 12,
      fontSize: size, fontWeight: 600, whiteSpace: "nowrap",
      background: bg, color,
    }}>{label}</span>
  );
}

function StatusBadge({ s }) {
  const c = STATUS_CFG[s] || { bg: "#F3F4F6", color: "#374151" };
  return <Pill label={s} bg={c.bg} color={c.color} />;
}

function OwnerChip({ o }) {
  if (!o) return <span style={{ fontSize: 12, color: "#9CA3AF" }}>—</span>;
  const c = OWNER_CFG[o] || { bg: "#F3F4F6", color: "#555" };
  return <Pill label={o} bg={c.bg} color={c.color} />;
}

function PriorityPill({ p }) {
  if (!p) return null;
  const c = PRIO_CFG[p] || PRIO_CFG.Medium;
  return <Pill label={p} bg={c.bg} color={c.color} />;
}

function CheckBox({ status }) {
  const done = status === "Completed";
  const prog = status === "In Progress";
  return (
    <div style={{
      width: 17, height: 17, borderRadius: 4, flexShrink: 0,
      border: `1.5px solid ${done ? "#7A9E7E" : prog ? "#60A5FA" : "#D1D5DB"}`,
      background: done ? "#7A9E7E" : prog ? "#DBEAFE" : "transparent",
      display: "flex", alignItems: "center", justifyContent: "center",
    }}>
      {done && (
        <svg width="10" height="10" viewBox="0 0 10 10">
          <polyline points="1.5,5 4,7.5 8.5,2.5" stroke="#fff" strokeWidth="1.5" fill="none" strokeLinecap="round" />
        </svg>
      )}
      {prog && <div style={{ width: 6, height: 6, borderRadius: "50%", background: "#3B82F6" }} />}
    </div>
  );
}

function PlaneIcon({ size = 18, color = "#C8DCC8" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
      <path d="M21 16v-2l-8-5V3.5a1.5 1.5 0 0 0-3 0V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z" fill={color} />
    </svg>
  );
}

// ─── TASK TABLE ───────────────────────────────────────────────────────────────
function TaskTable({ tasks, onBack, title, icon }) {
  const [ownerF, setOwnerF]   = useState("All");
  const [statusF, setStatusF] = useState("All");

  const owners   = ["All", ...new Set(tasks.map(t => t.owner).filter(Boolean))];
  const statuses = ["All", "Completed", "In Progress", "Not Yet Started", "Considering"];

  const filtered = tasks.filter(t =>
    (ownerF  === "All" || t.owner  === ownerF) &&
    (statusF === "All" || t.status === statusF)
  );

  const fBtn = (val, active, set) => (
    <button key={val} onClick={() => set(val)} style={{
      padding: "4px 11px", borderRadius: 14,
      border: "0.5px solid",
      borderColor: active ? "#2C3E35" : "rgba(0,0,0,0.12)",
      cursor: "pointer", fontSize: 11, ...mono,
      background: active ? "#2C3E35" : "rgba(0,0,0,0.03)",
      color: active ? "#FDFAF4" : "#6B7280",
      transition: "all 0.12s",
    }}>{val}</button>
  );

  const thStyle = { padding: "9px 12px", textAlign: "left", fontSize: 11, ...mono, color: "#9CA3AF", letterSpacing: "0.05em", textTransform: "uppercase", fontWeight: 400, background: "rgba(0,0,0,0.02)", borderBottom: "0.5px solid rgba(0,0,0,0.08)" };
  const tdStyle = { padding: "11px 12px", verticalAlign: "middle", borderTop: "0.5px solid rgba(0,0,0,0.07)" };

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
        {onBack && (
          <button onClick={onBack} style={{ padding: "6px 14px", borderRadius: 8, border: "0.5px solid rgba(0,0,0,0.12)", cursor: "pointer", fontSize: 12, ...mono, background: "rgba(0,0,0,0.03)", color: "#6B7280" }}>
            ← All categories
          </button>
        )}
        {icon && <span style={{ fontSize: 22 }}>{icon}</span>}
        <span style={{ fontSize: 16, fontWeight: 500, color: "#2C3E35" }}>{title}</span>
        <span style={{ marginLeft: "auto", ...mono, fontSize: 11, color: "#9CA3AF" }}>{filtered.length} items</span>
      </div>

      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 8, alignItems: "center" }}>
        <span style={{ ...mono, fontSize: 11, color: "#9CA3AF" }}>OWNER</span>
        {owners.map(o => fBtn(o, ownerF === o, setOwnerF))}
      </div>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 14, alignItems: "center" }}>
        <span style={{ ...mono, fontSize: 11, color: "#9CA3AF" }}>STATUS</span>
        {statuses.map(s => fBtn(s, statusF === s, setStatusF))}
      </div>

      <div style={{ background: "#fff", borderRadius: 14, border: "0.5px solid rgba(0,0,0,0.1)", overflow: "hidden", boxShadow: "0 1px 8px rgba(74,124,89,0.05)" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr>
              <th style={{ ...thStyle, width: 30 }}></th>
              <th style={thStyle}>Item</th>
              <th style={thStyle}>Notes</th>
              <th style={thStyle}>Status</th>
              <th style={thStyle}>Owner</th>
              <th style={thStyle}>Priority</th>
              <th style={thStyle}>Splitwise owed to</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 && (
              <tr><td colSpan={7} style={{ padding: 28, textAlign: "center", color: "#9CA3AF", ...mono, fontSize: 12 }}>No items match</td></tr>
            )}
            {filtered.map((t, i) => {
              const rowBg =
                t.status === "Completed" ? "rgba(209,250,229,0.15)" :
                (t.priority === "High" && t.status !== "Completed") ? "rgba(255,248,225,0.4)" :
                i % 2 === 0 ? "#fff" : "rgba(234,242,234,0.2)";
              return (
                <tr key={t.id} style={{ background: rowBg }}>
                  <td style={{ ...tdStyle, paddingRight: 4 }}><CheckBox status={t.status} /></td>
                  <td style={{ ...tdStyle, fontWeight: 500, color: t.status === "Completed" ? "#9CA3AF" : "#1F2937", maxWidth: 200, textDecoration: t.status === "Completed" ? "line-through" : "none", opacity: t.status === "Completed" ? 0.7 : 1 }}>
                    {t.link && t.link.startsWith("http")
                      ? <a href={t.link} target="_blank" rel="noopener noreferrer" style={{ color: "#4A7C59", textDecoration: "none" }}>{t.item} ↗</a>
                      : t.item}
                    {t.link && !t.link.startsWith("http") && t.link && (
                      <div style={{ fontSize: 10, color: "#9CA3AF", ...mono, marginTop: 2 }}>{t.link}</div>
                    )}
                  </td>
                  <td style={{ ...tdStyle, color: "#6B7280", fontSize: 12, maxWidth: 220 }}>{t.desc || "—"}</td>
                  <td style={tdStyle}><StatusBadge s={t.status} /></td>
                  <td style={tdStyle}><OwnerChip o={t.owner} /></td>
                  <td style={tdStyle}><PriorityPill p={t.priority} /></td>
                  <td style={{ ...tdStyle, ...mono, fontSize: 11, color: t.sw ? "#4A7C59" : "#D1D5DB" }}>{t.sw || "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── IDEAS BOARD ──────────────────────────────────────────────────────────────
function IdeasBoard({ ideas, setIdeas, nextId, setNextId }) {
  const [inputs, setInputs] = useState({});
  const [authors, setAuthors] = useState({});

  const vote = (catKey, id, dir) => {
    setIdeas(prev => {
      const next = { ...prev, [catKey]: prev[catKey].map(idea => {
        if (idea.id !== id) return idea;
        const wasVoted = idea.voted === dir;
        const scoreChange = wasVoted
          ? (dir === "up" ? -1 : 1)
          : (idea.voted ? (idea.voted === "up" ? -1 : 1) : 0) + (dir === "up" ? 1 : -1);
        return { ...idea, score: idea.score + scoreChange, voted: wasVoted ? null : dir };
      })};
      return next;
    });
  };

  const addIdea = (catKey) => {
    const text = (inputs[catKey] || "").trim();
    const author = (authors[catKey] || "").trim() || "Anonymous";
    if (!text) return;
    const newIdea = { id: nextId, text, author, score: 0, voted: null };
    setIdeas(prev => ({ ...prev, [catKey]: [...(prev[catKey] || []), newIdea] }));
    setNextId(n => n + 1);
    setInputs(prev => ({ ...prev, [catKey]: "" }));
  };

  return (
    <div>
      <div style={{ marginBottom: 18 }}>
        <div style={{ fontSize: 16, fontWeight: 500, color: "#2C3E35", marginBottom: 4 }}>Ideas board</div>
        <div style={{ fontSize: 13, color: "#6B7280" }}>Drop suggestions below — anyone can upvote or downvote to help the hosts decide what makes the cut.</div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0,1fr))", gap: 12 }}>
        {IDEA_CATS.map(({ key, label, icon }) => {
          const catIdeas = (ideas[key] || []).slice().sort((a, b) => b.score - a.score);
          return (
            <div key={key} style={{ background: "#fff", borderRadius: 14, border: "0.5px solid rgba(0,0,0,0.1)", padding: "16px 18px", boxShadow: "0 1px 8px rgba(74,124,89,0.05)" }}>
              <div style={{ fontSize: 14, fontWeight: 500, color: "#2C3E35", marginBottom: 12, display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{ fontSize: 17 }}>{icon}</span> {label}
              </div>

              {catIdeas.length === 0 && (
                <div style={{ fontSize: 12, color: "#9CA3AF", padding: "6px 0 10px", ...mono }}>No suggestions yet — be the first!</div>
              )}

              {catIdeas.map(idea => (
                <div key={idea.id} style={{ display: "flex", alignItems: "flex-start", gap: 10, padding: "9px 0", borderTop: "0.5px solid rgba(0,0,0,0.07)" }}>
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 2, flexShrink: 0, paddingTop: 2 }}>
                    <button
                      onClick={() => vote(key, idea.id, "up")}
                      style={{
                        width: 24, height: 20, border: "0.5px solid", cursor: "pointer",
                        borderRadius: 4, fontSize: 10, display: "flex", alignItems: "center", justifyContent: "center",
                        borderColor: idea.voted === "up" ? "#7A9E7E" : "rgba(0,0,0,0.12)",
                        background: idea.voted === "up" ? "#D1FAE5" : "rgba(0,0,0,0.02)",
                        color: idea.voted === "up" ? "#4A7C59" : "#9CA3AF",
                        transition: "all 0.1s",
                      }}
                    >▲</button>
                    <div style={{
                      fontSize: 12, fontWeight: 500, ...mono, minWidth: 20, textAlign: "center",
                      color: idea.score > 0 ? "#4A7C59" : idea.score < 0 ? "#B91C1C" : "#6B7280",
                    }}>{idea.score}</div>
                    <button
                      onClick={() => vote(key, idea.id, "down")}
                      style={{
                        width: 24, height: 20, border: "0.5px solid", cursor: "pointer",
                        borderRadius: 4, fontSize: 10, display: "flex", alignItems: "center", justifyContent: "center",
                        borderColor: idea.voted === "down" ? "#F87171" : "rgba(0,0,0,0.12)",
                        background: idea.voted === "down" ? "#FEE2E2" : "rgba(0,0,0,0.02)",
                        color: idea.voted === "down" ? "#B91C1C" : "#9CA3AF",
                        transition: "all 0.1s",
                      }}
                    >▼</button>
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, color: "#1F2937", lineHeight: 1.4 }}>{idea.text}</div>
                    <div style={{ fontSize: 11, color: "#9CA3AF", marginTop: 3 }}>— {idea.author}</div>
                  </div>
                </div>
              ))}

              <div style={{ display: "flex", gap: 6, marginTop: 12 }}>
                <input
                  value={inputs[key] || ""}
                  onChange={e => setInputs(p => ({ ...p, [key]: e.target.value }))}
                  onKeyDown={e => e.key === "Enter" && addIdea(key)}
                  placeholder="Add a suggestion..."
                  style={{ flex: 1, fontSize: 12, padding: "6px 10px", borderRadius: 8, border: "0.5px solid rgba(0,0,0,0.15)", background: "rgba(0,0,0,0.02)", color: "#1F2937", outline: "none" }}
                />
                <input
                  value={authors[key] || ""}
                  onChange={e => setAuthors(p => ({ ...p, [key]: e.target.value }))}
                  placeholder="Your name"
                  style={{ width: 88, fontSize: 12, padding: "6px 10px", borderRadius: 8, border: "0.5px solid rgba(0,0,0,0.15)", background: "rgba(0,0,0,0.02)", color: "#1F2937", outline: "none" }}
                />
                <button
                  onClick={() => addIdea(key)}
                  style={{ padding: "6px 12px", borderRadius: 8, border: "0.5px solid rgba(0,0,0,0.15)", background: "#2C3E35", color: "#FDFAF4", fontSize: 12, cursor: "pointer", whiteSpace: "nowrap" }}
                >+ Add</button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── MAIN APP ─────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const [tasks, setTasks]         = useState([]);
  const [syncStatus, setSyncStatus] = useState("loading"); // loading | live | error
  const [view, setView]           = useState("overview");
  const [catFilter, setCatFilter] = useState(null);
  const [ideas, setIdeas]         = useState(SEED_IDEAS);
  const [nextId, setNextId]       = useState(10);

  useEffect(() => {
    fetch(csvUrl("Master Tracker"))
      .then(r => { if (!r.ok) throw new Error(); return r.text(); })
      .then(text => {
        const parsed = sheetToTasks(text);
        if (parsed.length > 0) { setTasks(parsed); setSyncStatus("live"); }
        else throw new Error("empty");
      })
      .catch(() => { setFallback(); setSyncStatus("error"); });
  }, []);

  function setFallback() {
    setTasks([
      { id:0,  cat:"Venue & Logistics", item:"Confirm venue", desc:"Apartment vs Box Cafe, Dream Vista", status:"Completed", owner:"Jessica", priority:"High", link:"Box Cafe JC", sw:"" },
      { id:1,  cat:"Venue & Logistics", item:"Secure booking / reservation", desc:"Lock in date and deposits", status:"Completed", owner:"Jessica", priority:"High", link:"", sw:"Jessica" },
      { id:2,  cat:"Venue & Logistics", item:"Confirm guest capacity", desc:"Headcount check against venue max", status:"In Progress", owner:"Savitri", priority:"High", link:"", sw:"" },
      { id:3,  cat:"Venue & Logistics", item:"Splitwise tracking setup", desc:"Create group, add all hosts", status:"Completed", owner:"Carly", priority:"Medium", link:"", sw:"" },
      { id:4,  cat:"Invitations & Guest Experience", item:"Boarding pass invite design", desc:"Digital boarding pass invite", status:"Completed", owner:"Savitri", priority:"High", link:"", sw:"" },
      { id:5,  cat:"Invitations & Guest Experience", item:"QR code RSVP setup", desc:"QR code linking to RSVP form", status:"Completed", owner:"Savitri", priority:"High", link:"", sw:"" },
      { id:6,  cat:"Invitations & Guest Experience", item:"Evite creation", desc:"Backup digital send", status:"Completed", owner:"Savitri", priority:"Medium", link:"", sw:"" },
      { id:7,  cat:"Invitations & Guest Experience", item:"Print keepsake invites", desc:"Physical boarding pass invites", status:"Not Yet Started", owner:"Savitri", priority:"Medium", link:"", sw:"Savitri" },
      { id:8,  cat:"Invitations & Guest Experience", item:"Send invites", desc:"Target: early April", status:"Not Yet Started", owner:"Savitri", priority:"High", link:"", sw:"Savitri" },
      { id:9,  cat:"Keepsakes & Sentimental Touches", item:"Bookstand for Book Tree", desc:"Wooden or acrylic stand", status:"In Progress", owner:"Savitri", priority:"", link:"Book Tree", sw:"" },
      { id:10, cat:"Food", item:"Define food concept", desc:"Mini bites vs full catering", status:"In Progress", owner:"Jessica", priority:"High", link:"", sw:"" },
      { id:11, cat:"Food", item:"Incorporate pregnancy cravings", desc:"Cantaloupe, uncrustables, queso", status:"In Progress", owner:"Jessica", priority:"High", link:"", sw:"" },
      { id:12, cat:"Food", item:"Catering vs self-serve plan", desc:"Assign roles or get quotes", status:"In Progress", owner:"Jessica", priority:"High", link:"", sw:"" },
      { id:13, cat:"Food", item:"Finalize menu", desc:"Full menu locked", status:"Not Yet Started", owner:"Jessica", priority:"High", link:"", sw:"" },
      { id:14, cat:"Food", item:"Serving setup", desc:"Platters, labels, serving utensils", status:"Not Yet Started", owner:"Savitri", priority:"Low", link:"", sw:"" },
      { id:15, cat:"Drinks", item:"Define two signature drinks", desc:"Nicole + Zach inspired", status:"Not Yet Started", owner:"", priority:"Medium", link:"", sw:"" },
      { id:16, cat:"Drinks", item:"Cocktail bar format", desc:"Hugo / Aperol / mimosa bar", status:"Not Yet Started", owner:"", priority:"Medium", link:"", sw:"" },
      { id:17, cat:"Drinks", item:"Ice cube detail", desc:"Airplane or balloon silicone molds", status:"Not Yet Started", owner:"", priority:"Medium", link:"", sw:"" },
      { id:18, cat:"Decor & Styling", item:"Balloon box decision", desc:"Giant balloon box", status:"Not Yet Started", owner:"", priority:"High", link:"", sw:"Savitri" },
      { id:19, cat:"Decor & Styling", item:"Balloon bouquets (2 large)", desc:"Three large helium bouquets — sage, cream, silver", status:"Not Yet Started", owner:"", priority:"Medium", link:"", sw:"Savitri" },
      { id:20, cat:"Decor & Styling", item:"Table styling direction", desc:"Elevated — no kitschy baby stuff", status:"Not Yet Started", owner:"", priority:"High", link:"", sw:"" },
      { id:21, cat:"Decor & Styling", item:"Paper plane drink markers", desc:"Paper plane drink stirrers", status:"Not Yet Started", owner:"", priority:"Low", link:"", sw:"" },
      { id:22, cat:"Decor & Styling", item:"Table cloths & confetti", desc:"Table confetti & cloths", status:"Not Yet Started", owner:"", priority:"Medium", link:"", sw:"" },
      { id:23, cat:"Decor & Styling", item:"Baby photo display", desc:"Baby photos of Gena & Brian", status:"Not Yet Started", owner:"", priority:"High", link:"", sw:"" },
      { id:24, cat:"Decor & Styling", item:"Overall palette consistency check", desc:"Final review", status:"Not Yet Started", owner:"", priority:"Medium", link:"", sw:"" },
      { id:25, cat:"Activities & Games", item:"Travel trivia — couple's story", desc:"10 Qs about Nicole + Zach", status:"Not Yet Started", owner:"", priority:"High", link:"", sw:"" },
      { id:26, cat:"Activities & Games", item:"Guess baby traits", desc:"Eye color, hair, first word", status:"Not Yet Started", owner:"", priority:"Medium", link:"", sw:"" },
      { id:27, cat:"Activities & Games", item:"Guess baby's first trip", desc:"Guests write destination", status:"Not Yet Started", owner:"", priority:"Low", link:"", sw:"" },
      { id:28, cat:"Keepsakes & Sentimental Touches", item:"Letters to Nicole (before baby)", desc:"Advice / memories to Nicole", status:"Not Yet Started", owner:"", priority:"High", link:"", sw:"" },
      { id:29, cat:"Keepsakes & Sentimental Touches", item:"Postpartum letters from women", desc:"Sealed for postpartum", status:"Not Yet Started", owner:"", priority:"High", link:"", sw:"" },
      { id:30, cat:"Favors & Gifts", item:"Travel-themed gift bags", desc:"Travel kit, personalized tag", status:"Not Yet Started", owner:"", priority:"Medium", link:"", sw:"" },
    ]);
  }

  const nav = (v) => {
    setView(v);
    if (v !== "tasks") setCatFilter(null);
  };

  // ── Derived ────────────────────────────────────────────────────────────────
  const done   = tasks.filter(t => t.status === "Completed").length;
  const inProg = tasks.filter(t => t.status === "In Progress").length;
  const highOpen = tasks.filter(t => t.status !== "Completed" && t.priority === "High");
  const statusCounts = tasks.reduce((a, t) => { a[t.status] = (a[t.status] || 0) + 1; return a; }, {});
  const STATUS_ORDER = ["Completed", "In Progress", "Not Yet Started", "Considering"];

  const CATS = Object.keys(CAT_ICONS);
  const byCat = CATS.map(cat => ({
    cat, icon: CAT_ICONS[cat] || "📌",
    done:  tasks.filter(t => t.cat === cat && t.status === "Completed").length,
    total: tasks.filter(t => t.cat === cat).length,
    highOpen: tasks.filter(t => t.cat === cat && t.status !== "Completed" && t.priority === "High").length,
  })).filter(c => c.total > 0);

  // ── Styles ─────────────────────────────────────────────────────────────────
  const card = { background: "#fff", borderRadius: 14, padding: "18px 20px", border: "0.5px solid rgba(0,0,0,0.1)", boxShadow: "0 1px 8px rgba(74,124,89,0.05)" };

  return (
    <div style={{ minHeight: "100vh", background: "linear-gradient(145deg,#FDFAF4 0%,#F7F2EA 40%,#EAF2EA 100%)", fontFamily: "'Cormorant Garamond', Georgia, serif", color: "#1F2937" }}>
      {/* HEADER */}
      <div style={{ background: "#2C3E35", padding: "20px 32px", display: "flex", alignItems: "center", justifyContent: "space-between", position: "relative", overflow: "hidden" }}>
        <div style={{ position: "absolute", inset: 0, opacity: 0.04, backgroundImage: "radial-gradient(circle,#fff 1px,transparent 1px)", backgroundSize: "24px 24px" }} />
        <div style={{ display: "flex", alignItems: "center", gap: 12, position: "relative" }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.12)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <PlaneIcon />
          </div>
          <div>
            <div style={{ fontSize: 20, fontWeight: 500, color: "#FDFAF4", letterSpacing: "0.01em" }}>Baby's First Flight</div>
            <div style={{ ...mono, fontSize: 10, color: "#B8C4CC", marginTop: 2, letterSpacing: "0.07em" }}>JESSICA · CARLY · KIRSTEN · SAVITRI</div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center", position: "relative" }}>
          <div style={{
            ...mono, fontSize: 11, padding: "5px 12px", borderRadius: 14,
            background: syncStatus === "live" ? "rgba(122,158,126,0.2)" : "rgba(255,255,255,0.06)",
            border: `1px solid ${syncStatus === "live" ? "rgba(122,158,126,0.35)" : "rgba(255,255,255,0.12)"}`,
            color: syncStatus === "live" ? "#C8DCC8" : "#9CA3AF",
          }}>
            {syncStatus === "loading" ? "Syncing sheet..." : syncStatus === "live" ? "✓ Live from Sheet" : "⚠ Make sheet public to sync"}
          </div>
          <a href={SPLITWISE_URL} target="_blank" rel="noopener noreferrer" style={{ display: "flex", alignItems: "center", gap: 5, background: "rgba(122,158,126,0.2)", border: "1px solid rgba(122,158,126,0.35)", borderRadius: 20, padding: "6px 14px", color: "#C8DCC8", textDecoration: "none", fontSize: 12, ...mono }}>
            💸 Splitwise
          </a>
        </div>
      </div>

      {/* NAV */}
      <div style={{ padding: "18px 32px 0" }}>
        <div style={{ display: "flex", gap: 3, background: "rgba(255,255,255,0.5)", borderRadius: 10, padding: 3, width: "fit-content", border: "0.5px solid rgba(0,0,0,0.08)" }}>
          {["overview", "tasks", "ideas board"].map(v => (
            <button key={v} onClick={() => nav(v === "ideas board" ? "ideas" : v)} style={{
              padding: "7px 18px", borderRadius: 8, border: "none", cursor: "pointer",
              fontSize: 13, fontWeight: view === (v === "ideas board" ? "ideas" : v) ? 500 : 400,
              background: view === (v === "ideas board" ? "ideas" : v) ? "#2C3E35" : "transparent",
              color: view === (v === "ideas board" ? "ideas" : v) ? "#FDFAF4" : "#6B7280",
              fontFamily: "'Cormorant Garamond', Georgia, serif",
              transition: "all 0.15s",
            }}>{v.charAt(0).toUpperCase() + v.slice(1)}</button>
          ))}
        </div>
      </div>

      <div style={{ padding: "20px 32px 40px" }}>
        {/* ══ OVERVIEW ══ */}
        {view === "overview" && (
          <>
            {/* KPIs */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3,minmax(0,1fr))", gap: 12, marginBottom: 14 }}>
              <div style={card}>
                <div style={{ ...mono, fontSize: 11, color: "#9CA3AF", letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 8 }}>Tasks done</div>
                <div style={{ fontSize: 48, fontWeight: 300, lineHeight: 1, color: "#4A7C59" }}>{done}</div>
                <div style={{ fontSize: 13, color: "#6B7280", marginTop: 5 }}>of {tasks.length} total items</div>
                <div style={{ height: 4, background: "rgba(0,0,0,0.07)", borderRadius: 2, marginTop: 10, overflow: "hidden" }}>
                  <div style={{ height: "100%", width: `${tasks.length ? Math.round(done / tasks.length * 100) : 0}%`, background: "#7A9E7E", borderRadius: 2, transition: "width 0.5s" }} />
                </div>
              </div>

              <div style={{ ...card, cursor: "pointer", transition: "transform 0.1s" }}
                onClick={() => nav("tasks")}
                onMouseEnter={e => e.currentTarget.style.transform = "translateY(-2px)"}
                onMouseLeave={e => e.currentTarget.style.transform = ""}>
                <div style={{ ...mono, fontSize: 11, color: "#9CA3AF", letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 8 }}>In progress</div>
                <div style={{ fontSize: 48, fontWeight: 300, lineHeight: 1, color: "#1E40AF" }}>{inProg}</div>
                <div style={{ fontSize: 13, color: "#6B7280", marginTop: 5 }}>items actively in motion</div>
                <div style={{ ...mono, fontSize: 11, color: "#7A9E7E", marginTop: 10 }}>view all tasks →</div>
              </div>

              <div style={{ ...card, background: highOpen.length > 0 ? "#FFFBEB" : "#fff", border: `0.5px solid ${highOpen.length > 0 ? "#F0D890" : "rgba(0,0,0,0.1)"}` }}>
                <div style={{ ...mono, fontSize: 11, color: highOpen.length > 0 ? "#B5860A" : "#9CA3AF", letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 8 }}>High priority open</div>
                <div style={{ fontSize: 48, fontWeight: 300, lineHeight: 1, color: highOpen.length > 0 ? "#B5860A" : "#1F2937" }}>{highOpen.length}</div>
                <div style={{ fontSize: 13, color: "#9A7200", marginTop: 5 }}>need attention before event</div>
                {highOpen.length > 0 && (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 10 }}>
                    {highOpen.slice(0, 3).map(t => (
                      <span key={t.id} style={{ fontSize: 10, background: "rgba(255,255,255,0.7)", padding: "2px 8px", borderRadius: 8, color: "#8a6500", border: "0.5px solid #F0D890" }}>
                        {t.item.length > 22 ? t.item.slice(0, 22) + "…" : t.item}
                      </span>
                    ))}
                    {highOpen.length > 3 && <span style={{ fontSize: 10, color: "#9CA3AF" }}>+{highOpen.length - 3} more</span>}
                  </div>
                )}
              </div>
            </div>

            {/* Status bar */}
            <div style={{ ...card, marginBottom: 14 }}>
              <div style={{ ...mono, fontSize: 11, color: "#9CA3AF", letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 12 }}>Status overview</div>
              <div style={{ display: "flex", borderRadius: 4, overflow: "hidden", height: 8 }}>
                {STATUS_ORDER.map(s => {
                  const c = statusCounts[s] || 0;
                  const pct = tasks.length ? (c / tasks.length) * 100 : 0;
                  return pct > 0 ? <div key={s} title={`${s}: ${c}`} style={{ flex: pct, background: STATUS_BAR_COLORS[s], borderLeft: "1px solid rgba(255,255,255,0.4)" }} /> : null;
                })}
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 16, marginTop: 12 }}>
                {STATUS_ORDER.map(s => (
                  <div key={s} style={{ display: "flex", alignItems: "center", gap: 5 }}>
                    <div style={{ width: 10, height: 10, borderRadius: 2, background: STATUS_BAR_COLORS[s] }} />
                    <span style={{ ...mono, fontSize: 12, color: "#6B7280" }}>{s} <strong style={{ color: "#1F2937" }}>{statusCounts[s] || 0}</strong></span>
                  </div>
                ))}
              </div>
            </div>

            {/* Categories */}
            <div style={{ fontSize: 15, fontWeight: 500, color: "#2C3E35", marginBottom: 12 }}>Categories</div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3,minmax(0,1fr))", gap: 8 }}>
              {byCat.map(({ cat, icon, done, total, highOpen }) => (
                <button key={cat}
                  onClick={() => { setCatFilter(cat); setView("tasks"); }}
                  style={{
                    ...card, display: "flex", alignItems: "center", gap: 12, cursor: "pointer",
                    textAlign: "left", width: "100%",
                    background: highOpen > 0 ? "rgba(255,248,225,0.7)" : "#fff",
                    border: `0.5px solid ${highOpen > 0 ? "#F0D890" : "rgba(0,0,0,0.1)"}`,
                    transition: "transform 0.1s",
                  }}
                  onMouseEnter={e => e.currentTarget.style.transform = "translateY(-2px)"}
                  onMouseLeave={e => e.currentTarget.style.transform = ""}
                >
                  <span style={{ fontSize: 20, flexShrink: 0 }}>{icon}</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 500, color: "#2C3E35", lineHeight: 1.3 }}>{cat}</div>
                    {highOpen > 0 && <div style={{ ...mono, fontSize: 10, color: "#B5860A", marginTop: 2 }}>{highOpen} high priority open</div>}
                    <div style={{ height: 3, background: "rgba(0,0,0,0.07)", borderRadius: 2, marginTop: 6 }}>
                      <div style={{ height: 3, borderRadius: 2, width: total > 0 ? `${Math.round(done / total * 100)}%` : "0", background: "#7A9E7E", transition: "width 0.5s" }} />
                    </div>
                  </div>
                  <div style={{ textAlign: "right", flexShrink: 0 }}>
                    <div style={{ fontSize: 18, fontWeight: 500, color: "#4A7C59" }}>{done}</div>
                    <div style={{ ...mono, fontSize: 11, color: "#9CA3AF" }}>/{total}</div>
                  </div>
                </button>
              ))}
            </div>
          </>
        )}

        {/* ══ TASKS ══ */}
        {view === "tasks" && (
          <>
            {!catFilter && (
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 14 }}>
                {byCat.map(({ cat, icon, total, highOpen }) => (
                  <button key={cat} onClick={() => setCatFilter(cat)} style={{
                    padding: "5px 12px", borderRadius: 16,
                    border: `0.5px solid ${highOpen > 0 ? "#F0D890" : "rgba(0,0,0,0.1)"}`,
                    cursor: "pointer", fontSize: 11, ...mono,
                    background: highOpen > 0 ? "rgba(255,248,225,0.9)" : "rgba(255,255,255,0.7)",
                    color: highOpen > 0 ? "#8a6500" : "#6B7280",
                    transition: "all 0.12s",
                  }}>
                    {icon} {cat} ({total})
                  </button>
                ))}
              </div>
            )}
            <TaskTable
              tasks={catFilter ? tasks.filter(t => t.cat === catFilter) : tasks}
              onBack={catFilter ? () => setCatFilter(null) : null}
              title={catFilter || "All tasks"}
              icon={catFilter ? CAT_ICONS[catFilter] : "✈️"}
            />
          </>
        )}

        {/* ══ IDEAS ══ */}
        {view === "ideas" && (
          <IdeasBoard ideas={ideas} setIdeas={setIdeas} nextId={nextId} setNextId={setNextId} />
        )}

        {/* Footer */}
        <div style={{ marginTop: 36, paddingTop: 16, borderTop: "0.5px solid #C8DCC8", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, color: "#9CA3AF", fontSize: 12 }}>
            <PlaneIcon size={13} color="#C8DCC8" />
            <span style={{ ...mono, letterSpacing: "0.05em" }}>BABY'S FIRST FLIGHT · SOFT GREEN · CREAM · SILVER</span>
          </div>
          <a href={SPLITWISE_URL} target="_blank" rel="noopener noreferrer" style={{ ...mono, fontSize: 12, color: "#7A9E7E", textDecoration: "none" }}>
            💸 Open Splitwise →
          </a>
        </div>
      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');
        * { box-sizing: border-box; }
        body { margin: 0; }
        button { font-family: inherit; }
        input { font-family: inherit; }
        a { cursor: pointer; }
      `}</style>
    </div>
  );
}
