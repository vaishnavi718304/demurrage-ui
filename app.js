// ============================================================
// Demurrage Settlement Intelligence — app.js
// Frontend on Vercel. Backend on Railway.
// After Railway deployment, update RAILWAY_URL below.
// ============================================================

const RAILWAY_URL = "https://vxyvaish-autobackend.hf.space"; // ← UPDATE THIS after Railway deployment

// ── Utility ──────────────────────────────────────────────────
function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;").replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;").replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
function fmt(val, d = 2)  { const n = parseFloat(val); return isNaN(n) ? "—" : n.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d }); }
function fmtUSD(val)       { const n = parseFloat(val); return isNaN(n) ? "—" : "$" + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
function fmtPct(val)       { const n = parseFloat(val); return isNaN(n) ? "—" : (n * 100).toFixed(1) + "%"; }

function setStatus(msg, type = "") {
  const box = document.getElementById("statusBox");
  if (!box) return;
  box.textContent = msg;
  box.classList.remove("error-state", "success-state");
  if (type) box.classList.add(type);
}

function saveClaim(data) { localStorage.setItem("demurrage_claim", JSON.stringify(data)); }
function loadClaim() {
  try { const r = localStorage.getItem("demurrage_claim"); return r ? JSON.parse(r) : null; }
  catch (e) { return null; }
}

// ══════════════════════════════════════════════════════════════
// PAGE 1 — Upload & Extraction
// ══════════════════════════════════════════════════════════════
function initPage1() {
  const runBtn = document.getElementById("runBtn");
  if (!runBtn) return;

  runBtn.addEventListener("click", async () => {
    const cpFile  = document.getElementById("cpFile")?.files[0];
    const sofFile = document.getElementById("sofFile")?.files[0];

    if (!cpFile || !sofFile) {
      setStatus("Please upload both a Charter Party and a Statement of Facts file.", "error-state");
      return;
    }

    setStatus("Connecting to backend...");
    runBtn.disabled = true;

    // ── Health check ──────────────────────────────────────────
    try {
      const h  = await fetch(`${RAILWAY_URL}/health`);
      const hj = await h.json();
      if (!hj.ok) throw new Error("backend not ready");
      setStatus(`Backend online${hj.model_loaded ? " · Model loaded ✓" : " · Running in fallback mode"}. Running contract extraction...`);
    } catch (e) {
      setStatus("Cannot reach backend. Check RAILWAY_URL in app.js.", "error-state");
      runBtn.disabled = false;
      return;
    }

    // ── Extract contract ──────────────────────────────────────
    let contractData = null;
    try {
      const fd  = new FormData();
      fd.append("cp_file", cpFile);
      const res  = await fetch(`${RAILWAY_URL}/extract_contract`, { method: "POST", body: fd });
      const json = await res.json();
      contractData = json.contract;
      renderContractTerms(contractData);
      setStatus("Contract extracted. Processing claim pipeline...");
    } catch (e) {
      setStatus("Contract extraction failed: " + e.message, "error-state");
      runBtn.disabled = false;
      return;
    }

    // ── Process claim ─────────────────────────────────────────
    let claimData = null;
    try {
      const fd2  = new FormData();
      fd2.append("sof_file", sofFile);
      fd2.append("cp_file",  cpFile);
      const res2 = await fetch(`${RAILWAY_URL}/process_claim`, { method: "POST", body: fd2 });
      if (!res2.ok) {
        const err = await res2.json();
        throw new Error(err.error || "process_claim failed");
      }
      claimData = await res2.json();
      renderTimeline(claimData.timeline);
    } catch (e) {
      setStatus("Claim processing failed: " + e.message, "error-state");
      runBtn.disabled = false;
      return;
    }

    // ── Save and done ─────────────────────────────────────────
    saveClaim({ contract: contractData, ...claimData });
    setStatus(
      `✓ Extraction complete. Action: ${claimData?.decision?.recommended_action || "—"} · Navigate to Trigger Engine →`,
      "success-state"
    );
    runBtn.disabled = false;
  });
}

function renderContractTerms(contract) {
  const el = document.getElementById("contractTerms");
  if (!el || !contract) return;
  const fields = [
    ["Source File",          contract.source_file],
    ["Allowed Laytime",      contract.allowed_laytime],
    ["NOR Rule",             contract.nor_rule],
    ["Laytime Start Rule",   contract.laytime_start_rule],
    ["Laytime Offset (hrs)", contract.laytime_offset_hours],
    ["Counting Rule",        contract.counting_rule],
    ["Demurrage Rate",       contract.demurrage_rate],
    ["Weather / Congestion", contract.weather_congestion_clauses],
  ];
  el.innerHTML = `<div class="term-grid">
    ${fields.map(([l, v]) => `
      <div class="term-item">
        <div class="term-label">${escapeHtml(l)}</div>
        <div class="term-value">${escapeHtml(v || "—")}</div>
      </div>`).join("")}
  </div>`;
}

function renderTimeline(timeline) {
  const el = document.getElementById("timelineOutput");
  if (!el || !timeline?.events) return;
  el.innerHTML = `<div class="timeline-list">
    ${timeline.events.map(ev => `
      <div class="timeline-item">
        <div class="timeline-step">${escapeHtml(ev.label)}</div>
        <div class="timeline-time">${escapeHtml(ev.value || "—")}</div>
      </div>`).join("")}
  </div>`;
}

// ══════════════════════════════════════════════════════════════
// PAGE 2 — Trigger Engine
// ══════════════════════════════════════════════════════════════
function initPage2() {
  const claim = loadClaim();
  if (!claim) return;

  // Claim Context
  const ctx = document.getElementById("claimContext");
  if (ctx && claim.timeline) {
    const t      = claim.timeline;
    const fields = [
      ["Port", t.port_name],
      ["Operation", t.operation],
      ...t.events.map(e => [e.label, e.value])
    ];
    ctx.innerHTML = `<div class="context-grid">
      ${fields.map(([l, v]) => `
        <div class="context-item">
          <div class="context-label">${escapeHtml(l)}</div>
          <div class="context-value">${escapeHtml(v || "—")}</div>
        </div>`).join("")}
    </div>`;
  }

  // Demurrage Flag
  const flag = document.getElementById("demurrageFlagBadge");
  if (flag && claim.triggers) {
    const fired = claim.triggers.demurrage_flag;
    flag.innerHTML = `<div class="demurrage-flag-wrap">
      <div class="flag-badge ${fired ? "flag-true" : "flag-false"}">
        ${fired ? "✓ DEMURRAGE CONFIRMED" : "✗ NO DEMURRAGE"}
      </div>
      <div class="flag-sub">
        ${fired
          ? "One or more triggers fired. This port call qualifies as a demurrage event."
          : "No triggers fired. Port call does not meet demurrage criteria."}
      </div>
    </div>`;
  }

  // Trigger Grid
  const grid = document.getElementById("triggerGrid");
  if (grid && claim.triggers?.items) {
    grid.innerHTML = claim.triggers.items.map(t => `
      <div class="trigger-card">
        <div class="trigger-label">${escapeHtml(t.name)}</div>
        <div class="trigger-desc">${escapeHtml(t.description)}</div>
        <div class="trigger-value ${t.flag ? "trigger-on" : "trigger-off"}">
          ${t.flag ? "● FIRED" : "○ Not fired"}
        </div>
      </div>`).join("");
  }
}

// ══════════════════════════════════════════════════════════════
// PAGE 3 — Intelligence Layer
// ══════════════════════════════════════════════════════════════
function initPage3() {
  const claim = loadClaim();
  if (!claim) return;

  // Feature Grid
  const fg = document.getElementById("featureGrid");
  if (fg && claim.features) {
    const f     = claim.features;
    const feats = [
      ["calculated_amount",   fmtUSD(f.calculated_amount),  "Primary claim value"],
      ["total_events",        f.total_events || "—",         "SoF event count"],
      ["long_gap_ratio",      fmtPct(f.long_gap_ratio),      "Proportion of gaps > 4 hours"],
      ["unique_clause_count", f.unique_clause_count || "—",  "Distinct laytime clause types"],
      ["events_per_day",      fmt(f.events_per_day, 1),      "Operational density"],
      ["ambiguity_score",     fmt(f.ambiguity_score, 3),     "0 = clear · 1 = high risk"],
    ];
    fg.innerHTML = `<div class="feature-grid">
      ${feats.map(([l, v, d]) => `
        <div class="feature-item">
          <div class="feature-label">${escapeHtml(l)}</div>
          <div class="feature-value">${escapeHtml(String(v))}</div>
          <div class="feature-desc">${escapeHtml(d)}</div>
        </div>`).join("")}
    </div>`;
  }

  // Ambiguity Panel
  const ap = document.getElementById("ambiguityPanel");
  if (ap && claim.ambiguity_recovery) {
    const a = claim.ambiguity_recovery;
    ap.innerHTML = `<div class="ambiguity-result">
      <div class="ambiguity-row"><span class="ambiguity-key">Status</span><span class="ambiguity-val">${escapeHtml(a.status || "—")}</span></div>
      <div class="ambiguity-row"><span class="ambiguity-key">Confidence</span><span class="ambiguity-val">${escapeHtml(a.confidence || "—")}</span></div>
      <div class="ambiguity-row"><span class="ambiguity-key">Fallback Interpretation</span><span class="ambiguity-val">${escapeHtml(a.fallback_interpretation || "—")}</span></div>
    </div>`;
  }

  // Port Panel
  const pp = document.getElementById("portPanel");
  if (pp && claim.port_intelligence) {
    const p = claim.port_intelligence;
    pp.innerHTML = `<div class="port-result">
      <div class="port-row"><span class="port-key">Port Pattern</span><span class="port-val">${escapeHtml(p.port_pattern || "—")}</span></div>
      <div class="port-row"><span class="port-key">Historical Discount</span><span class="port-val">${escapeHtml(p.historical_discount_tendency || "—")}</span></div>
      <div class="port-row"><span class="port-key">Trigger Density</span><span class="port-val">${escapeHtml(p.trigger_density || "—")}</span></div>
    </div>`;
  }

  // Timeline
  const tl = document.getElementById("timelineList");
  if (tl && claim.timeline?.events) {
    tl.innerHTML = `<div class="timeline-list">
      ${claim.timeline.events.map(ev => `
        <div class="timeline-item">
          <div class="timeline-step">${escapeHtml(ev.label)}</div>
          <div class="timeline-time">${escapeHtml(ev.value || "—")}</div>
        </div>`).join("")}
    </div>`;
  }
}

// ══════════════════════════════════════════════════════════════
// PAGE 4 — Decision Engine
// ══════════════════════════════════════════════════════════════
function initPage4() {
  const claim = loadClaim();
  if (!claim?.decision) return;
  const d = claim.decision;

  // KPIs
  const kpi = document.getElementById("decisionKpis");
  if (kpi) {
    const aScore = parseFloat(d.ambiguity_score);
    const aClass = aScore >= 0.55 ? "kpi-danger" : aScore >= 0.25 ? "kpi-warn" : "kpi-accent";
    kpi.innerHTML = `
      <div class="kpi-card">
        <div class="kpi-label">Calculated Amount</div>
        <div class="kpi-value kpi-neutral">${fmtUSD(d.calculated_amount)}</div>
        <div class="kpi-sub">From Charter Party & SoF</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Predicted Settlement</div>
        <div class="kpi-value kpi-accent">${fmtUSD(d.pred_settlement_amount)}</div>
        <div class="kpi-sub">RandomForest model output</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Settlement Ratio</div>
        <div class="kpi-value kpi-accent">${fmt(d.pred_settlement_ratio, 3)}</div>
        <div class="kpi-sub">Target range: 0.98–1.02</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Ambiguity Score</div>
        <div class="kpi-value ${aClass}">${fmt(d.ambiguity_score, 3)}</div>
        <div class="kpi-sub">Threshold: 0.25 AUTO · 0.55 ESCALATE</div>
      </div>`;
  }

  // Action
  const ap = document.getElementById("actionPanel");
  if (ap && d.recommended_action) {
    const action = d.recommended_action.toUpperCase();
    const cls    = action === "AUTO" ? "action-auto" : action === "REVIEW" ? "action-review" : "action-escalate";
    const icon   = { AUTO: "✓", REVIEW: "⟳", ESCALATE: "↑" }[action] || "";
    ap.innerHTML = `<div class="action-result">
      <div class="action-result-badge ${cls}">${icon} ${escapeHtml(action)}</div>
      <div style="font-size:13px;color:var(--muted);text-align:center;line-height:1.6;max-width:320px;">
        ${escapeHtml(d.explanation || "")}
      </div>
    </div>`;
  }

  // Reason codes
  const rp = document.getElementById("reasonPanel");
  if (rp && d.reason_codes) {
    const codes   = Array.isArray(d.reason_codes) ? d.reason_codes : d.reason_codes.split(",").map(s => s.trim());
    const chipCls = c => c === "clean_case_high_recovery" ? "chip-success" : c === "needs_human_check" ? "chip-warn" : "chip-danger";
    rp.innerHTML  = `<div class="reason-chips">
      ${codes.map(c => `<span class="reason-chip ${chipCls(c)}">${escapeHtml(c)}</span>`).join("")}
    </div>`;
  }
}

// ── Operator buttons ──────────────────────────────────────────
function handleOperatorAction(action) {
  const el = document.getElementById("operatorStatus");
  if (!el) return;
  el.style.display = "block";
  const msgs = {
    AUTO:     "AUTO accepted. Claim sent for direct settlement.",
    REVIEW:   "Claim routed to analyst review queue.",
    ESCALATE: "Claim escalated to senior analyst / legal."
  };
  const cls = { AUTO: "success-state", REVIEW: "", ESCALATE: "error-state" };
  el.className    = "status-box " + (cls[action] || "");
  el.textContent  = msgs[action];
}

// ── Router ────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("runBtn"))       initPage1();
  if (document.getElementById("triggerGrid"))  initPage2();
  if (document.getElementById("featureGrid"))  initPage3();
  if (document.getElementById("decisionKpis")) initPage4();
});