/* ── app.js ── */

let sortState = { col: null, asc: true };
let currentData = [];

// ─────────────────────────────────────────────
// START SCRAPE
// ─────────────────────────────────────────────
async function startScrape() {
  const keyword = document.getElementById("keyword").value.trim();
  const city    = document.getElementById("city").value.trim();
  const max     = document.getElementById("max_results").value;

  if (!keyword || !city) {
    shakeInput(!keyword ? "keyword" : "city");
    return;
  }

  showProgress();
  animateProgressBar();

  try {
    const res = await fetch("/scrape", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ keyword, city, max_results: parseInt(max) }),
    });

    const data = await res.json();

    if (!res.ok || data.error) {
      showError(data.error || "An unexpected error occurred.");
      return;
    }

    currentData = data.results || [];
    renderResults(currentData);

  } catch (err) {
    showError("Network error — make sure the Flask server is running.");
  }
}

// ─────────────────────────────────────────────
// RENDER TABLE
// ─────────────────────────────────────────────
function renderResults(data) {
  document.getElementById("lead-count").textContent = data.length;

  const tbody = document.getElementById("leads-tbody");
  tbody.innerHTML = "";

  if (data.length === 0) {
    showError("No leads found. Try a different keyword or city.");
    return;
  }

  data.forEach((row, i) => {
    const tr = document.createElement("tr");
    tr.className = "fade-in";
    tr.style.animationDelay = `${i * 0.03}s`;

    const website = row.Website
      ? `<a href="${sanitize(row.Website.startsWith("http") ? row.Website : "https://" + row.Website)}" target="_blank" rel="noopener">${sanitize(row.Website)}</a>`
      : `<span class="td-empty">—</span>`;

    const rating = row.Rating
      ? `<span class="td-rating">⭐ ${sanitize(row.Rating)}</span>`
      : `<span class="td-empty">—</span>`;

    tr.innerHTML = `
      <td>${i + 1}</td>
      <td class="td-name">${sanitize(row.Name) || "—"}</td>
      <td>${sanitize(row.Category) || "<span class='td-empty'>—</span>"}</td>
      <td class="td-phone">${sanitize(row.Phone) || "<span class='td-empty'>—</span>"}</td>
      <td>${sanitize(row.Address) || "<span class='td-empty'>—</span>"}</td>
      <td>${rating}</td>
      <td>${sanitize(row.Reviews) || "<span class='td-empty'>—</span>"}</td>
      <td class="td-website">${website}</td>
    `;
    tbody.appendChild(tr);
  });

  hide("progress-section");
  hide("error-section");
  show("results-section", true);
  resetBtn();

  // Attach sort listeners
  document.querySelectorAll("th[data-col]").forEach(th => {
    th.onclick = () => sortTable(th.dataset.col);
  });
}

// ─────────────────────────────────────────────
// SORT
// ─────────────────────────────────────────────
function sortTable(col) {
  if (sortState.col === col) {
    sortState.asc = !sortState.asc;
  } else {
    sortState.col = col;
    sortState.asc = true;
  }

  const sorted = [...currentData].sort((a, b) => {
    let va = a[col] || "";
    let vb = b[col] || "";
    // Try numeric sort
    const na = parseFloat(va), nb = parseFloat(vb);
    if (!isNaN(na) && !isNaN(nb)) {
      return sortState.asc ? na - nb : nb - na;
    }
    return sortState.asc
      ? va.localeCompare(vb)
      : vb.localeCompare(va);
  });

  renderResults(sorted);
}

// ─────────────────────────────────────────────
// UI STATE HELPERS
// ─────────────────────────────────────────────
function showProgress() {
  const btn = document.getElementById("scrape-btn");
  btn.disabled = true;
  document.getElementById("btn-text").textContent = "Scraping…";
  hide("results-section");
  hide("error-section");
  show("progress-section", true);
}

let _progressTimer = null;
function animateProgressBar() {
  const bar = document.getElementById("progress-bar");
  let pct = 0;
  bar.style.width = "0%";
  clearInterval(_progressTimer);
  _progressTimer = setInterval(() => {
    pct += Math.random() * 3 + 0.5;
    if (pct >= 92) pct = 92;
    bar.style.width = pct + "%";
  }, 600);
}

function showError(msg) {
  clearInterval(_progressTimer);
  document.getElementById("error-msg").textContent = msg;
  hide("progress-section");
  hide("results-section");
  show("error-section", true);
  resetBtn();
}

function resetUI() {
  hide("progress-section");
  hide("results-section");
  hide("error-section");
  resetBtn();
  currentData = [];
}

function resetBtn() {
  const btn = document.getElementById("scrape-btn");
  btn.disabled = false;
  document.getElementById("btn-text").textContent = "Scrape Leads";
  clearInterval(_progressTimer);
  document.getElementById("progress-bar").style.width = "100%";
}

function show(id, animate = false) {
  const el = document.getElementById(id);
  el.classList.remove("hidden");
  if (animate) el.classList.add("fade-in");
}

function hide(id) {
  document.getElementById(id).classList.add("hidden");
}

function sanitize(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function shakeInput(id) {
  const el = document.getElementById(id);
  el.style.borderColor = "#ff6b6b";
  el.style.boxShadow = "0 0 0 3px rgba(255,107,107,0.25)";
  el.focus();
  setTimeout(() => {
    el.style.borderColor = "";
    el.style.boxShadow = "";
  }, 1800);
}

// ── Allow Enter key to trigger search ──
document.addEventListener("DOMContentLoaded", () => {
  ["keyword", "city"].forEach(id => {
    document.getElementById(id).addEventListener("keydown", e => {
      if (e.key === "Enter") startScrape();
    });
  });
});
