const state = {
  incidents: [], selectedId: null, events: [], latestActivity: null, pendingDecision: null,
  tokenRequired: false, operatorToken: null, adminAccess: "local_open", adminToken: null,
  policy: null, wooConfigured: false,
};

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
  activity: document.querySelector("#last-activity"),
  accessStatus: document.querySelector("#access-status"),
  unlock: document.querySelector("#unlock-button"),
  accessDialog: document.querySelector("#access-dialog"),
  accessForm: document.querySelector("#access-form"),
  accessToken: document.querySelector("#access-token"),
  accessError: document.querySelector("#access-error"),
  confirmAccess: document.querySelector("#confirm-access"),
  cancelAccess: document.querySelector("#cancel-access"),
  adminStatus: document.querySelector("#admin-status"),
  adminUnlock: document.querySelector("#admin-unlock-button"),
  woocommerceScan: document.querySelector("#woocommerce-scan-button"),
  adminAccessDialog: document.querySelector("#admin-access-dialog"),
  adminAccessForm: document.querySelector("#admin-access-form"),
  adminAccessToken: document.querySelector("#admin-access-token"),
  adminAccessError: document.querySelector("#admin-access-error"),
  confirmAdminAccess: document.querySelector("#confirm-admin-access"),
  cancelAdminAccess: document.querySelector("#cancel-admin-access"),
  policyVersion: document.querySelector("#policy-version"),
  policySummary: document.querySelector("#policy-summary"),
  policyAccessNote: document.querySelector("#policy-access-note"),
  policyForm: document.querySelector("#policy-form"),
  policyName: document.querySelector("#policy-name"),
  policyAdministrator: document.querySelector("#policy-administrator"),
  policyRules: document.querySelector("#policy-rules"),
  addPolicyRule: document.querySelector("#add-policy-rule"),
  simulatePolicy: document.querySelector("#simulate-policy"),
  publishPolicy: document.querySelector("#publish-policy"),
  policyMessage: document.querySelector("#policy-message"),
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
  const headers = { ...options.headers };
  if (options.body) headers["Content-Type"] = "application/json";
  if (state.operatorToken) headers.Authorization = `Bearer ${state.operatorToken}`;
  const response = await fetch(path, { ...options, headers });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || "The local service could not complete that request.");
  }
  return response.json();
}

async function adminRequest(path, options = {}) {
  const headers = { ...options.headers };
  if (state.adminToken) headers["X-OEC-Admin-Token"] = state.adminToken;
  return request(path, { ...options, headers });
}

function setMetric(id, value) { document.querySelector(id).textContent = value; }

function renderMetrics() {
  setMetric("#awaiting-count", state.incidents.filter((incident) => incident.status === "awaiting_approval").length);
  setMetric("#approved-count", state.incidents.filter((incident) => incident.status === "approved").length);
  setMetric("#rejected-count", state.incidents.filter((incident) => incident.status === "rejected").length);
  setMetric("#total-count", state.incidents.length);
}

function renderActivity() {
  const activity = state.latestActivity;
  if (!activity) {
    elements.activity.textContent = "Latest scan: no activity recorded";
    return;
  }
  const counts = activity.status === "succeeded"
    ? `${activity.scanned_orders} orders · ${activity.new_incident_count} new cases`
    : "review source configuration";
  elements.activity.textContent = `Latest scan: ${readable(activity.status)} · ${counts} · ${formatTimestamp(activity.occurred_at)}`;
}

function renderAccess() {
  const visible = state.tokenRequired;
  elements.accessStatus.hidden = !visible;
  elements.unlock.hidden = !visible;
  if (!visible) return;
  const unlocked = Boolean(state.operatorToken);
  elements.accessStatus.textContent = unlocked ? "Operator access unlocked" : "Operator token required";
  elements.unlock.textContent = unlocked ? "Change access token" : "Unlock operator desk";
}

function canEditPolicy() {
  return state.adminAccess === "local_open" || Boolean(state.adminToken);
}

function renderPolicySummary() {
  if (!state.policy) return;
  elements.policyVersion.textContent = `Active version ${state.policy.version}`;
  elements.policySummary.innerHTML = `<strong>${escapeHtml(state.policy.name)}</strong> · ${state.policy.rules.length} deterministic rule${state.policy.rules.length === 1 ? "" : "s"}<ul class="policy-summary-list">${state.policy.rules.slice().sort((a, b) => a.priority - b.priority).map((rule) => `<li><strong>${escapeHtml(rule.label)}</strong> → ${escapeHtml(readable(rule.resolution))}</li>`).join("")}</ul>`;
}

function renderAdminAccess() {
  const canEdit = canEditPolicy();
  const adminRequired = state.adminAccess === "token_required";
  const notConfigured = state.adminAccess === "not_configured";
  elements.adminStatus.hidden = state.adminAccess === "local_open";
  elements.adminUnlock.hidden = !adminRequired;
  elements.woocommerceScan.hidden = !(state.wooConfigured && canEdit);
  if (adminRequired) {
    elements.adminStatus.textContent = state.adminToken ? "Policy builder unlocked" : "Administrator token required";
    elements.adminUnlock.textContent = state.adminToken ? "Change administrator token" : "Unlock policy builder";
  } else if (notConfigured) {
    elements.adminStatus.textContent = "Policy builder disabled";
  }
  elements.policyForm.hidden = !canEdit;
  elements.policyAccessNote.textContent = canEdit
    ? "Publishing creates a new immutable version. It changes future triage only; every proposed resolution still needs a named operator approval."
    : notConfigured
      ? "Policy viewing is available to the desk. A separate OEC_ADMIN_TOKEN is required before a protected service can change rules."
      : "Use the separate administrator token to edit or test a policy. Operator access alone cannot change rules.";
}

function policyRuleMarkup(rule) {
  const options = (items, selected) => items.map(([value, label]) => `<option value="${value}"${value === selected ? " selected" : ""}>${label}</option>`).join("");
  return `<article class="policy-rule" data-rule>
    <div class="policy-rule-heading"><strong>Rule</strong><button class="button danger remove-policy-rule" type="button">Remove</button></div>
    <div class="policy-form-grid rule-grid">
      <label>Rule ID<input data-field="id" maxlength="80" pattern="[a-z0-9][a-z0-9-]*" value="${escapeHtml(rule.id)}" required></label>
      <label>Label<input data-field="label" maxlength="120" value="${escapeHtml(rule.label)}" required></label>
      <label>Priority<input data-field="priority" type="number" min="1" max="1000" value="${escapeHtml(rule.priority)}" required></label>
      <label>Carrier status<select data-field="carrier_status">${options([["stalled", "Stalled"], ["lost", "Lost"], ["delivery_attempt_failed", "Delivery attempt failed"], ["in_transit", "In transit"], ["delivered", "Delivered"]], rule.carrier_status)}</select></label>
      <label>Proposed resolution<select data-field="resolution">${options([["carrier_escalation", "Carrier escalation"], ["replacement", "Replacement"], ["refund", "Refund"], ["address_confirmation", "Address confirmation"]], rule.resolution)}</select></label>
      <label>Minimum hours without tracking<input data-field="minimum_hours_without_tracking_update" type="number" min="0" max="8760" value="${rule.minimum_hours_without_tracking_update ?? ""}" placeholder="No threshold"></label>
    </div>
    <label class="checkbox-label"><input data-field="requires_promised_delivery_date_past" type="checkbox"${rule.requires_promised_delivery_date_past ? " checked" : ""}> Require the promised delivery date to be past</label>
    <label>Reason shown to the operator<textarea data-field="reason" minlength="8" maxlength="300" required>${escapeHtml(rule.reason)}</textarea></label>
  </article>`;
}

function renderPolicyForm() {
  if (!state.policy) return;
  elements.policyName.value = state.policy.name;
  elements.policyAdministrator.value = "";
  elements.policyRules.innerHTML = state.policy.rules.slice().sort((a, b) => a.priority - b.priority).map(policyRuleMarkup).join("");
  wirePolicyRuleButtons();
}

function wirePolicyRuleButtons() {
  elements.policyRules.querySelectorAll(".remove-policy-rule").forEach((button) => {
    button.addEventListener("click", () => {
      const cards = elements.policyRules.querySelectorAll("[data-rule]");
      if (cards.length <= 1) {
        elements.policyMessage.textContent = "A policy needs at least one rule.";
        return;
      }
      button.closest("[data-rule]").remove();
    });
  });
}

function addPolicyRule() {
  const number = elements.policyRules.querySelectorAll("[data-rule]").length + 1;
  const priority = number * 10;
  elements.policyRules.insertAdjacentHTML("beforeend", policyRuleMarkup({
    id: `new-rule-${number}`, label: "New delivery rule", priority, carrier_status: "stalled",
    resolution: "carrier_escalation", reason: "tracking matches the configured delivery exception condition",
    minimum_hours_without_tracking_update: null, requires_promised_delivery_date_past: false,
  }));
  wirePolicyRuleButtons();
}

function policyDraft() {
  const rules = [...elements.policyRules.querySelectorAll("[data-rule]")].map((card) => {
    const value = (field) => card.querySelector(`[data-field="${field}"]`).value.trim();
    const minimumHours = value("minimum_hours_without_tracking_update");
    return {
      id: value("id"), label: value("label"), priority: Number(value("priority")),
      carrier_status: value("carrier_status"), resolution: value("resolution"), reason: value("reason"),
      minimum_hours_without_tracking_update: minimumHours ? Number(minimumHours) : null,
      requires_promised_delivery_date_past: card.querySelector('[data-field="requires_promised_delivery_date_past"]').checked,
    };
  });
  return { name: elements.policyName.value.trim(), rules };
}

async function refreshPolicy({ resetForm = false } = {}) {
  state.policy = await request("/policy");
  renderPolicySummary();
  renderAdminAccess();
  if (resetForm) renderPolicyForm();
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
  const [incidents, activity] = await Promise.all([request("/incidents"), request("/activity?limit=1")]);
  state.incidents = incidents;
  state.latestActivity = activity[0] || null;
  if (state.selectedId && !state.incidents.some((incident) => incident.id === state.selectedId)) state.selectedId = null;
  renderMetrics();
  renderActivity();
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
elements.unlock.addEventListener("click", () => {
  elements.accessToken.value = "";
  elements.accessError.textContent = "";
  elements.accessDialog.showModal();
  elements.accessToken.focus();
});
elements.cancelAccess.addEventListener("click", () => elements.accessDialog.close());
elements.accessForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const previousToken = state.operatorToken;
  state.operatorToken = elements.accessToken.value.trim();
  elements.confirmAccess.disabled = true;
  elements.accessError.textContent = "";
  try {
    await refreshQueue();
    elements.accessDialog.close();
    renderAccess();
  } catch (error) {
    state.operatorToken = previousToken;
    elements.accessError.textContent = error.message;
  } finally { elements.confirmAccess.disabled = false; }
});
elements.adminUnlock.addEventListener("click", () => {
  elements.adminAccessToken.value = "";
  elements.adminAccessError.textContent = "";
  elements.adminAccessDialog.showModal();
  elements.adminAccessToken.focus();
});
elements.cancelAdminAccess.addEventListener("click", () => elements.adminAccessDialog.close());
elements.adminAccessForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const previousToken = state.adminToken;
  state.adminToken = elements.adminAccessToken.value.trim();
  elements.confirmAdminAccess.disabled = true;
  elements.adminAccessError.textContent = "";
  try {
    await adminRequest("/admin/policy");
    elements.adminAccessDialog.close();
    renderAdminAccess();
    renderPolicyForm();
  } catch (error) {
    state.adminToken = previousToken;
    elements.adminAccessError.textContent = error.message;
  } finally { elements.confirmAdminAccess.disabled = false; }
});
elements.addPolicyRule.addEventListener("click", addPolicyRule);
elements.simulatePolicy.addEventListener("click", async () => {
  elements.simulatePolicy.disabled = true;
  elements.policyMessage.textContent = "";
  try {
    const simulation = await adminRequest("/admin/policy/simulate", {
      method: "POST",
      body: JSON.stringify({
        ...policyDraft(),
        order: {
          id: "synthetic-policy-test", customer_name: "Synthetic customer", customer_email: "synthetic@example.com",
          carrier: "Demo Carrier", carrier_status: "stalled", hours_without_tracking_update: 72,
          promised_delivery_date: "2020-01-01T00:00:00Z", total_amount: 12900, currency: "PLN", lines: [],
        },
      }),
    });
    elements.policyMessage.textContent = simulation.matched
      ? `Test matched ${simulation.rule_id}: ${readable(simulation.resolution)}. No external action was attempted.`
      : "Test did not match any draft rule. No external action was attempted.";
  } catch (error) { elements.policyMessage.textContent = error.message; }
  finally { elements.simulatePolicy.disabled = false; }
});
elements.policyForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  elements.publishPolicy.disabled = true;
  elements.policyMessage.textContent = "";
  try {
    const published = await adminRequest("/admin/policy", {
      method: "PUT",
      body: JSON.stringify({ ...policyDraft(), administrator: elements.policyAdministrator.value.trim() }),
    });
    state.policy = published;
    renderPolicySummary();
    renderPolicyForm();
    elements.policyMessage.textContent = `Published version ${published.version}. It will apply to future scans only.`;
  } catch (error) { elements.policyMessage.textContent = error.message; }
  finally { elements.publishPolicy.disabled = false; }
});
elements.woocommerceScan.addEventListener("click", async () => {
  elements.woocommerceScan.disabled = true;
  elements.policyMessage.textContent = "";
  try {
    const result = await adminRequest("/admin/woocommerce/scan", { method: "POST" });
    elements.policyMessage.textContent = `Read ${result.scanned_orders} eligible WooCommerce orders; ${result.new_incident_ids.length} new approval-gated case${result.new_incident_ids.length === 1 ? "" : "s"}.`;
    await refreshQueue();
  } catch (error) { elements.policyMessage.textContent = error.message; }
  finally { elements.woocommerceScan.disabled = false; }
});
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

async function initialise() {
  const health = await request("/health");
  state.tokenRequired = health.operator_access === "token_required";
  state.adminAccess = health.admin_access;
  state.wooConfigured = health.woocommerce_connector === "configured";
  renderAccess();
  renderAdminAccess();
  await refreshPolicy({ resetForm: canEditPolicy() });
  if (!state.tokenRequired) await refreshQueue();
}

initialise().catch((error) => { elements.detail.innerHTML = `<p class="error-banner">${escapeHtml(error.message)}</p>`; });
