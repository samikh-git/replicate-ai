/** Run dashboard: SSE stream + detail rendering. */

let lastAuditMd = null;

if (typeof marked !== "undefined") {
  marked.use({ gfm: true, breaks: true });
}

function runIdFromQuery() {
  const params = new URLSearchParams(window.location.search);
  return params.get("id");
}

function formatElapsed(startedAt) {
  if (!startedAt) return "00:00:00";
  const dt = Math.max(0, Math.floor(Date.now() / 1000 - startedAt));
  const h = Math.floor(dt / 3600);
  const m = Math.floor((dt % 3600) / 60);
  const s = dt % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function highlightBeta(spec) {
  return spec.replace(/β/g, '<span class="beta">β</span>');
}

function fmtSe(se) {
  return se == null ? "—" : se.toFixed(2);
}

function formatHeadlineCard(c) {
  const g = c.verdict === "ok" ? "✓" : c.verdict === "borderline" ? "△" : "✗";
  const est = c.estimate.toFixed(2);
  const pub = c.published.toFixed(2);
  const d = (c.delta >= 0 ? "+" : "") + c.delta.toFixed(2);
  const lines = [
    "COEFFICIENT  ─────────────────────────────────────────",
    "",
    `  ${c.estimate_label.padEnd(18)}${est.padStart(8)}   (${fmtSe(c.estimate_se)})  ${c.estimate_stars || ""}`,
    `  published`.padEnd(18) + `${pub.padStart(8)}   (${fmtSe(c.published_se)})  ${c.published_stars || ""}`,
    `  Δ`.padEnd(18) + `${d.padStart(8)}   ${g} ${c.verdict}`,
  ];
  return lines.join("\n");
}

function parseAuditMarkdown(audit) {
  if (typeof marked === "undefined") {
    return `<pre class="audit-fallback">${escapeHtml(audit)}</pre>`;
  }
  const html = marked.parse(audit);
  const wrap = document.createElement("div");
  wrap.innerHTML = html;
  wrap.querySelectorAll("table").forEach((table) => {
    const shell = document.createElement("div");
    shell.className = "audit-table-wrap";
    table.parentNode.insertBefore(shell, table);
    shell.appendChild(table);
  });
  return wrap.innerHTML;
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

async function copyAuditToClipboard() {
  if (!lastAuditMd) return;
  const btn = document.getElementById("btn-copy-audit");
  try {
    await navigator.clipboard.writeText(lastAuditMd);
    if (btn) {
      const prev = btn.textContent;
      btn.textContent = "Copied!";
      btn.classList.add("copied");
      setTimeout(() => {
        btn.textContent = prev;
        btn.classList.remove("copied");
      }, 2000);
    }
  } catch (_) {
    alert("Could not copy to clipboard.");
  }
}

function renderPhases(state) {
  const el = document.getElementById("phases");
  const current = state.phase_display;
  el.innerHTML = (state.phases || []).map((p) => {
    const active = p === current;
    return `<span class="phase${active ? " active" : ""}"><span class="dot">${active ? "●" : "○"}</span>${p}</span>`;
  }).join("");
}

function renderDetail(state) {
  const body = document.getElementById("detail-body");
  const c = state.coeffs;
  const audit = state.audit_md;

  if (!c && !audit) {
    body.innerHTML = '<p style="color: var(--dim)">Waiting for target specification and estimates…</p>';
    return;
  }

  let html = "";
  if (c) {
    html += `<div class="model-spec">${highlightBeta(c.model_spec)}</div>`;
    html += `<pre class="coeff-table">${formatHeadlineCard(c)}</pre>`;
    html += `<p style="color: var(--dim); font-size: 0.85rem">${c.citation_line}</p>`;
  }
  lastAuditMd = audit || null;
  if (audit) {
    const md = parseAuditMarkdown(audit);
    html += `
      <section class="audit-section" aria-label="Replication audit">
        <div class="audit-section-header">
          <h2>Replication audit</h2>
          <button type="button" class="secondary btn-copy" id="btn-copy-audit">Copy audit</button>
        </div>
        <div class="audit-md">${md}</div>
      </section>`;
  } else {
    lastAuditMd = null;
  }
  body.innerHTML = html;
}

function applyState(state) {
  const meta = document.getElementById("run-meta");
  const parts = [];
  if (state.example_dir) parts.push(state.example_dir.split("/").pop());
  if (state.provider) parts.push(state.provider);
  parts.push(formatElapsed(state.started_at));
  meta.textContent = parts.join(" · ");

  renderPhases(state);
  document.getElementById("log-body").textContent = (state.log_lines || []).join("\n");
  const logEl = document.getElementById("log-body");
  logEl.scrollTop = logEl.scrollHeight;
  renderDetail(state);
  document.getElementById("running-head").textContent = state.running_head || "";
}

const runId = runIdFromQuery();
if (!runId) {
  window.location.href = "/";
} else {
  const es = new EventSource(`/api/runs/${runId}/events`);
  es.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data);
      if (msg.state) applyState(msg.state);
    } catch (_) {}
  };
  es.onerror = () => {
    fetch(`/api/runs/${runId}`)
      .then((r) => r.json())
      .then(applyState)
      .catch(() => {});
  };

  fetch(`/api/runs/${runId}`)
    .then((r) => r.json())
    .then(applyState);

  setInterval(() => {
    fetch(`/api/runs/${runId}`)
      .then((r) => r.json())
      .then((s) => {
        document.getElementById("run-meta").textContent = [
          s.example_dir?.split("/").pop(),
          s.provider,
          formatElapsed(s.started_at),
        ]
          .filter(Boolean)
          .join(" · ");
      });
  }, 1000);
}

document.getElementById("detail-body").addEventListener("click", (e) => {
  if (e.target.closest("#btn-copy-audit")) {
    copyAuditToClipboard();
  }
});

document.getElementById("btn-home").addEventListener("click", () => {
  window.location.href = "/";
});

const logBtn = document.getElementById("btn-log");
if (logBtn) {
  logBtn.addEventListener("click", () => {
    window.open(`/api/runs/${runId}/log`, "_blank");
  });
}

document.getElementById("btn-save").addEventListener("click", async () => {
  const r = await fetch(`/api/runs/${runId}/save-audit`, { method: "POST" });
  const data = await r.json();
  if (r.ok) alert(`Saved audit → ${data.path}`);
  else alert(data.error || "Could not save audit");
});
