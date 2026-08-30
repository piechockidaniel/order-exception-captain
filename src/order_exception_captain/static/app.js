const state = { incidents: [], selectedId: null, events: [], pendingDecision: null };

const elements = {
  queue: document.querySelector("#queue"),
  caption: document.querySelector("#queue-caption"),
  detail: document.querySelector("#detail-panel"),
  demo: document.querySelector("#demo-button"),
  refresh: document.querySelector("#refresh-button"),
  dialog: document.querySelector("#decision-dialog"),
  form: document.querySelector("#decision-form"),
  title: document.querySelector("#decision-title"),
  kind: document.querySelector("#decision-kind"),
  summary: document.querySelector("#decision-summary"),
  operator: document.querySelector("#operator-name"),
  reasonField: document.querySelector("#reason-field"),
  reason: document.querySelector("#rejection-reason"),
  confirm: document.querySelector("#confirm-decision"),
  cancel: document.querySelector("#cancel-decision"),
  error: document.querySelector("#decision-error"),
};

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#039;", '"': "&quot;",
  })[character]);
}

function readable(value) {
  return String(value ?? "").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatTimestamp(value) {
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

async function request(path, options = {}) {
  const response = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || "The local service could not complete that request.");
  }
  return response.json();
}

function setMetric(id, value) { document.querySelector(id).textContent = value; }

function renderMetrics() {
  setMetric("#awaiting-count", state.incidents.filter((incident) => incident.status === "awaiting_approval").length);
  setMetric("#approved-count", state.incidents.filter((incident) => incident.status === "approved").length);
  setMetric("#rejected-count", state.incidents.filter((incident) => incident.status === "rejected").length);
  setMetric("#total-count", state.incidents.length);
}

function renderQueue() {
  elements.caption.textContent = state.incidents.length ? `${state.incidents.length} case${state.incidents.length === 1 ? "" : "s"}` : "No cases loaded";
  if (!state.incidents.length) {
    elements.queue.replaceChildren(document.querySelector("#empty-queue-template").content.cloneNode(true));
    return;
  }
  elements.queue.innerHTML = state.incidents.map((incident) => `
    <button class="incident-card ${incident.id === state.selectedId ? "selected" : ""}" type="button" data-incident-id="${escapeHtml(incident.id)}">
      <span class="incident-title"><strong>${escapeHtml(incident.order_id)}</strong><span class="status ${escapeHtml(incident.status)}">${escapeHtml(readable(incident.status))}</span></span>
      <p>${escapeHtml(incident.reason)}</p>
    </button>
  `).join("");
  elements.queue.querySelectorAll("[data-incident-id]").forEach((button) => {
    button.addEventListener("click", () => selectIncident(button.dataset.incidentId));
  });
}

function renderDetail() {
  const incident = state.incidents.find((item) => item.id === state.selectedId);
  if (!incident) {
    elements.detail.innerHTML = `<div class="empty-state"><p class="eyebrow">Ready when you are</p><h2>Choose an incident to review.</h2><p>Load the synthetic queue, then inspect its policy evidence and full audit history.</p></div>`;
    return;
  }
  const draft = incident.drafts[0];
  const isPending = incident.status === "awaiting_approval";
  const isApproved = incident.status === "approved";
  const hasPreparedDryRun = state.events.some((event) => event.event_type === "dry_run_prepared");
  const decision = draft.approved_by ? `Approved by ${escapeHtml(draft.approved_by)} on ${escapeHtml(formatTimestamp(draft.approved_at))}.` : draft.rejected_by ? `Rejected by ${escapeHtml(draft.rejected_by)} on ${escapeHtml(formatTimestamp(draft.rejected_at))}. Reason: ${escapeHtml(draft.rejection_reason)}` : "A named operator decision is required before any future action.";
  const events = state.events.length ? `<ul class="audit-list">${state.events.map((event) => `<li><span>${escapeHtml(formatTimestamp(event.occurred_at))} · ${escapeHtml(readable(event.event_type))}${event.actor ? ` · ${escapeHtml(event.actor)}` : ""}</span>${escapeHtml(event.detail)}</li>`).join("")}</ul>` : "<p>Loading audit history…</p>";
  elements.detail.innerHTML = `
    <div class="detail-heading"><div><p class="eyebrow">${escapeHtml(readable(incident.status))}</p><h2>${escapeHtml(incident.order_id)}</h2></div><span class="status ${escapeHtml(incident.status)}">${escapeHtml(readable(draft.kind))}</span></div>
    ${isPending ? `<div class="decision-actions"><button class="button primary" data-decision="approve" type="button">Approve draft</button><button class="button danger" data-decision="reject" type="button">Reject draft</button></div>` : ""}
    ${isApproved ? `<div class="decision-actions">${hasPreparedDryRun ? `<p class="action-note">Dry-run handoff prepared. No request was sent.</p>` : `<button class="button secondary" data-decision="dry-run" type="button">Prepare dry-run handoff</button>`}</div>` : ""}
    <div class="detail-grid">
      <section class="detail-section"><h3>Policy trigger</h3><p>${escapeHtml(incident.reason)}</p></section>
      <section class="detail-section"><h3>Proposed next step</h3><p>${escapeHtml(draft.summary)}</p></section>
      <section class="detail-section wide"><h3>Evidence</h3><p>${escapeHtml(incident.evidence_summary)}</p></section>
      <section class="detail-section wide"><h3>Resolution explanation</h3><p>${escapeHtml(incident.policy_summary)}</p></section>
      <section class="detail-section wide"><h3>Customer-message draft</h3><p>${escapeHtml(incident.customer_message_draft)}</p></section>
      <section class="detail-section wide"><h3>Decision record</h3><p>${decision}</p></section>
      <section class="detail-section wide"><h3>Audit trail</h3>${events}</section>
    </div>`;
  elements.detail.querySelectorAll("[data-decision]").forEach((button) => button.addEventListener("click", () => openDecision(button.dataset.decision, incident)));
}

async function selectIncident(incidentId) {
  state.selectedId = incidentId;
  state.events = [];
  renderQueue();
  renderDetail();
  try {
    state.events = await request(`/incidents/${encodeURIComponent(incidentId)}/events`);
  } catch (error) {
    state.events = [{ occurred_at: new Date().toISOString(), event_type: "audit_unavailable", detail: error.message, actor: null }];
  }
  renderDetail();
}

function openDecision(kind, incident) {
  state.pendingDecision = { kind, incidentId: incident.id };
  elements.kind.textContent = kind === "approve" ? "Human approval required" : kind === "reject" ? "Human rejection required" : "Dry-run handoff";
  elements.title.textContent = kind === "approve" ? "Approve proposed next step" : kind === "reject" ? "Reject proposed next step" : "Prepare a safe handoff preview";
  elements.summary.textContent = incident.drafts[0].summary;
  elements.reasonField.hidden = kind !== "reject";
  elements.reason.required = kind === "reject";
  elements.reason.disabled = kind !== "reject";
  elements.reason.value = "";
  elements.operator.value = "";
  elements.error.textContent = "";
  elements.confirm.textContent = kind === "approve" ? "Confirm approval" : kind === "reject" ? "Confirm rejection" : "Prepare dry run";
  elements.dialog.showModal();
  elements.operator.focus();
}

async function refreshQueue() {
  state.incidents = await request("/incidents");
  if (state.selectedId && !state.incidents.some((incident) => incident.id === state.selectedId)) state.selectedId = null;
  renderMetrics();
  renderQueue();
  if (state.selectedId) await selectIncident(state.selectedId); else renderDetail();
}

elements.demo.addEventListener("click", async () => {
  elements.demo.disabled = true;
  try { await request("/demo/scan", { method: "POST" }); await refreshQueue(); if (state.incidents[0]) await selectIncident(state.incidents[0].id); }
  catch (error) { elements.detail.innerHTML = `<p class="error-banner">${escapeHtml(error.message)}</p>`; }
  finally { elements.demo.disabled = false; }
});
elements.refresh.addEventListener("click", () => refreshQueue().catch((error) => { elements.detail.innerHTML = `<p class="error-banner">${escapeHtml(error.message)}</p>`; }));
elements.cancel.addEventListener("click", () => elements.dialog.close());
elements.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const decision = state.pendingDecision;
  if (!decision) return;
  const body = { operator: elements.operator.value.trim() };
  if (decision.kind === "reject") body.reason = elements.reason.value.trim();
  elements.confirm.disabled = true;
  elements.error.textContent = "";
  try {
    await request(`/incidents/${encodeURIComponent(decision.incidentId)}/${decision.kind}`, { method: "POST", body: JSON.stringify(body) });
    elements.dialog.close();
    await refreshQueue();
  } catch (error) { elements.error.textContent = error.message; }
  finally { elements.confirm.disabled = false; }
});

refreshQueue().catch((error) => { elements.detail.innerHTML = `<p class="error-banner">${escapeHtml(error.message)}</p>`; });
