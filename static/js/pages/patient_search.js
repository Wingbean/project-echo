document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("patientSearchForm");
  const resultsSection = document.getElementById("resultsSection");
  const resultsTable = document.getElementById("resultsTable");
  const resultCount = document.getElementById("resultCount");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fname = document.getElementById("fnameInput").value.trim();
    const lname = document.getElementById("lnameInput").value.trim();

    resultsSection.style.display = "block";
    resultsTable.innerHTML = `<div class="loading-placeholder"><span class="material-symbols-rounded spin">progress_activity</span><span>กำลังค้นหา...</span></div>`;

    try {
      const data = await EchoAPI.post("/api/patient_search", { fname, lname });
      if (data.status === "error") {
        resultsTable.innerHTML = `<div class="empty-state error"><span class="material-symbols-rounded">error</span><p>${EchoUtils.escapeHtml(data.message)}</p></div>`;
        return;
      }

      const records = data.records || [];
      resultCount.textContent =
        records.length + " รายการ" + (data.limit_reached ? " (แสดง 100 รายการแรก)" : "");

      if (records.length === 0) {
        resultsTable.innerHTML = `<div class="empty-state"><span class="material-symbols-rounded">search_off</span><p>ไม่พบผู้ป่วยที่ตรงกับเงื่อนไข</p></div>`;
        return;
      }

      const display = records.map((r) => ({
        HN: r.hn,
        "ชื่อ-นามสกุล": `${r.pname || ""}${r.fname || ""} ${r.lname || ""}`.trim(),
      }));
      resultsTable.innerHTML = EchoUtils.buildTable(["HN", "ชื่อ-นามสกุล"], display, {});
    } catch (err) {
      resultsTable.innerHTML = `<div class="empty-state error"><span class="material-symbols-rounded">error</span><p>เกิดข้อผิดพลาด: ${EchoUtils.escapeHtml(err.message)}</p></div>`;
    }
  });

  form.addEventListener("reset", () => {
    resultsSection.style.display = "none";
    resultsTable.innerHTML = "";
  });
});
