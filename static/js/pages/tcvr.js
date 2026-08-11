const RISK_BADGE_COLORS = {
  Low: "#22c55e",
  Medium: "#eab308",
  High: "#f97316",
  VeryHigh: "#ef4444",
  Extreme: "#991b1b",
};

function tcvrBadge(text, color) {
  return `<span style="background-color: ${color}; color: white; padding: 2px 8px; border-radius: 12px; font-weight: bold; display: inline-block;">${text}</span>`;
}

// Mask a name part: keep first/last char, blank out the middle with ***.
function maskNamePart(part) {
  if (part.length <= 2) return part[0] + "*".repeat(part.length - 1);
  return part[0] + "***" + part[part.length - 1];
}

function maskName(fullName) {
  return fullName
    .split(" ")
    .filter(Boolean)
    .map(maskNamePart)
    .join(" ");
}

// Show the CVD risk result columns right after Age instead of at the end.
function reorderColumns(columns) {
  const cols = columns.slice();
  const ageIdx = cols.indexOf("Age");
  if (ageIdx === -1) return cols;
  const moveCols = ["ThaiCVD_Risk_pct", "RiskCat"].filter((c) => cols.includes(c));
  const rest = cols.filter((c) => !moveCols.includes(c));
  const insertAt = rest.indexOf("Age") + 1;
  rest.splice(insertAt, 0, ...moveCols);
  return rest;
}

const TCVR_TABLE_OPTIONS = {
  columnLabels: {
    HN: "HN",
    Name: "Name",
    Sex: "Sex",
    Age: "Age",
    DM: "DM",
    HT: "HT",
    Smoke: "Smoke",
    bps_ops: "bps",
    TC_ops: "TC",
    waist_ops: "waist",
    height_ops: "height",
    lastDate: "Last Visit",
    RegDate: "Reg. Date",
    ThaiCVD_Risk_pct: "CVD Risk %",
    RiskCat: "Risk",
  },
  cellRenderers: {
    Name: (val) =>
      val ? EchoUtils.escapeHtml(maskName(String(val))) : "-",
    Sex: (val) => (val === 1 || val === "1" ? "M" : val === 2 || val === "2" ? "F" : "-"),
    DM: (val) => (val === "Y" ? tcvrBadge("✓", "#22c55e") : "-"),
    HT: (val) => (val === "Y" ? tcvrBadge("✓", "#22c55e") : "-"),
    Smoke: (val) => (val === 2 || val === "2" ? tcvrBadge("S", "#eab308") : "-"),
    ThaiCVD_Risk_pct: (val, row) => {
      if (val === null || val === undefined || val === "") return "-";
      const color = RISK_BADGE_COLORS[row.RiskCat];
      return color ? tcvrBadge(`${val}%`, color) : `${val}%`;
    },
    RiskCat: (val) =>
      val && RISK_BADGE_COLORS[val] ? tcvrBadge(val, RISK_BADGE_COLORS[val]) : val || "-",
  },
};

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("tcvrForm");
  const dateInput = document.getElementById("tcvrDate");
  const submitBtn = document.getElementById("tcvrSubmitBtn");
  const resultsTable = document.getElementById("resultsTable");
  const resultCount = document.getElementById("resultCount");
  const hnFilterInput = document.getElementById("hnFilterInput");

  let currentRecords = [];
  let currentColumns = [];

  function renderTable(records) {
    resultsTable.innerHTML = EchoUtils.buildTable(currentColumns, records, TCVR_TABLE_OPTIONS);
    resultCount.textContent = records.length + " รายการ";
  }

  async function loadTcvr(dateStr) {
    submitBtn.disabled = true;
    resultsTable.innerHTML = `<div class="loading-placeholder"><span class="material-symbols-rounded spin">progress_activity</span><span>กำลังคำนวณ Thai CVD Risk ของวันที่ ${EchoUtils.escapeHtml(dateStr)}...</span></div>`;

    try {
      const data = await EchoAPI.get("/api/tcvr", { date: dateStr });

      if (data.status === "error") {
        resultsTable.innerHTML = `<div class="empty-state error"><span class="material-symbols-rounded">error</span><p>${EchoUtils.escapeHtml(data.message)}</p></div>`;
        resultCount.textContent = "0 รายการ";
        currentRecords = [];
        currentColumns = [];
        return;
      }

      currentRecords = data.records || [];
      currentColumns = reorderColumns(data.columns || []);
      hnFilterInput.value = "";
      renderTable(currentRecords);
    } catch (err) {
      resultsTable.innerHTML = `<div class="empty-state error"><span class="material-symbols-rounded">error</span><p>เกิดข้อผิดพลาด: ${EchoUtils.escapeHtml(err.message)}</p></div>`;
      resultCount.textContent = "0 รายการ";
    } finally {
      submitBtn.disabled = false;
    }
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    if (!dateInput.value) return;
    loadTcvr(dateInput.value);
  });

  hnFilterInput.addEventListener(
    "input",
    EchoUtils.debounce(() => {
      const q = hnFilterInput.value.trim();
      const filtered = q
        ? currentRecords.filter((r) => String(r.HN || "").includes(q))
        : currentRecords;
      renderTable(filtered);
    }, 150),
  );

  const today = new Date();
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
  dateInput.value = todayStr;
  loadTcvr(todayStr);
});
