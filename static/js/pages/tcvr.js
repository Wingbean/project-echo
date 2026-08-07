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
    resultsTable.innerHTML = EchoUtils.buildTable(currentColumns, records);
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
      currentColumns = data.columns || [];
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
