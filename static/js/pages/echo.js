document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("echoSearchForm");
  const hnInput = document.getElementById("hnInput");
  const resultContainers = document.getElementById("echoResultsContainer");

  // Chart instances
  let egfrChartInstance = null;
  let a1cChartInstance = null;
  const egfrChartContainer = document.getElementById("echoEgfrChartContainer");
  const a1cChartContainer = document.getElementById("echoA1cChartContainer");

  function destroyCharts() {
    if (egfrChartInstance) {
      egfrChartInstance.destroy();
      egfrChartInstance = null;
    }
    if (a1cChartInstance) {
      a1cChartInstance.destroy();
      a1cChartInstance = null;
    }
    if (egfrChartContainer) egfrChartContainer.style.display = "none";
    if (a1cChartContainer) a1cChartContainer.style.display = "none";
  }

  // Hide everything
  function hideResults() {
    resultContainers.style.display = "none";
    destroyCharts();

    // Clear all tables
    [
      "echoConsultTable",
      "echoEgfrTable",
      "echoA1cTable",
      "echoEmrCards",
    ].forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.innerHTML = "";
    });

    // Reset badges
    [
      "echoConsultCount",
      "echoEgfrCount",
      "echoA1cCount",
      "echoEmrCount",
    ].forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.textContent = "0 รายการ";
    });
  }

  // --- EMR Render Function ---
  const renderEMRCards = (records) => {
    if (!records || records.length === 0) return "";
    let html = '<div class="emr-cards-container">';
    records.forEach((row) => {
      const val = (key) =>
        row[key]
          ? EchoUtils.escapeHtml(String(row[key]))
          : '<span style="color: var(--text-muted); opacity: 0.5;">-</span>';

      html += `
        <div class="emr-card">
            <div class="emr-card-header">
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <span class="material-symbols-rounded">event_note</span>
                    <strong>วันที่: ${val("VstDate")} ${val("VstTime")}</strong>
                </div>
            </div>
            <div class="emr-card-body">
                <div class="emr-left-pane">
                    <div class="emr-row">
                        <div class="emr-field"><div class="emr-label">VN</div><div class="emr-value" style="font-weight: bold; color: var(--teal-600);">${val("VN")}</div></div>
                        <div class="emr-field"><div class="emr-label">HN</div><div class="emr-value">${val("HN")}</div></div>
                        <div class="emr-field"><div class="emr-label">AN</div><div class="emr-value">${val("AN")}</div></div>
                    </div>
                    <div class="emr-row">
                        <div class="emr-field"><div class="emr-label">วันที่</div><div class="emr-value" style="white-space: nowrap;">${val("VstDate")}</div></div>
                        <div class="emr-field"><div class="emr-label">เวลา</div><div class="emr-value" style="white-space: nowrap;">${val("VstTime")}</div></div>
                        <div class="emr-field"><div class="emr-label">อายุ</div><div class="emr-value">${val("Age")}</div></div>
                        <div class="emr-field" style="max-width: 100px;"><div class="emr-label">สิทธิ์</div><div class="emr-value">${val("Rights")}</div></div>
                    </div>
                    <div class="emr-row gap-large">
                        <div class="emr-field"><div class="emr-label">แผนก</div><div class="emr-value">${val("Dept")}</div></div>
                        <div class="emr-field"><div class="emr-label" style="width: 75px;">HxTaker</div><div class="emr-value">${val("HxTaker")}</div></div>
                        <div class="emr-field"><div class="emr-label" style="width: 40px;">Dr</div><div class="emr-value">${val("Dr")}</div></div>
                    </div>
                    <div class="emr-field full gap-large">
                        <div class="emr-label large">CC</div>
                        <div class="emr-value textarea" style="color: var(--rose-600); font-weight: 500;">${val("CC")}</div>
                    </div>
                    <div class="emr-field full">
                        <div class="emr-label large">Hpi</div>
                        <div class="emr-value textarea">${val("Hpi")}</div>
                    </div>
                    <div class="emr-field full">
                        <div class="emr-label large">PE</div>
                        <div class="emr-value textarea">${val("PE")}</div>
                    </div>
                </div>
                <!-- Right Pane -->
                <div class="emr-right-pane" style="display: block;">
                    <div class="emr-field full" style="margin-bottom: 0.5rem;">
                        <div class="emr-label large">Dx_Text</div>
                        <div class="emr-value textarea" style="font-weight: 500;">${val("Dx_Text")}</div>
                    </div>
                    <div style="display: flex; gap: 1rem;">
                        <div class="emr-col" style="flex: 1;">
                            <div class="emr-field"><div class="emr-label wide" style="color: var(--teal-600);">PDx</div><div class="emr-value" style="font-weight: 600;">${val("PDx")}</div></div>
                            <div class="emr-field"><div class="emr-label wide">Dx1</div><div class="emr-value">${val("Dx1")}</div></div>
                            <div class="emr-field"><div class="emr-label wide">Dx2</div><div class="emr-value">${val("Dx2")}</div></div>
                            <div class="emr-field"><div class="emr-label wide">Dx3</div><div class="emr-value">${val("Dx3")}</div></div>
                        </div>
                        <div class="emr-col" style="flex: 1;">
                            <div class="emr-field"><div class="emr-label wide">op1</div><div class="emr-value">${val("op1")}</div></div>
                            <div class="emr-field"><div class="emr-label wide">op2</div><div class="emr-value">${val("op2")}</div></div>
                            <div class="emr-field"><div class="emr-label wide">op3</div><div class="emr-value">${val("op3")}</div></div>
                            <div class="emr-field"><div class="emr-label wide">op4</div><div class="emr-value">${val("op4")}</div></div>
                            <div class="emr-field"><div class="emr-label wide">op5</div><div class="emr-value">${val("op5")}</div></div>
                        </div>
                    </div>
                </div>
            </div>`;

      // Render Rx if exists
      const rxList = row.rx_list || [];
      if (rxList.length > 0) {
        html += `
            <div style="padding: 0 1.5rem 1.5rem 1.5rem;">
                <div style="color: var(--teal-700); font-size: 1.05rem; display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; font-weight: 600;">
                    <span class="material-symbols-rounded" style="font-size: 1.2rem;">prescriptions</span>รายการยา (Prescriptions)
                </div>
                <div style="display: flex; flex-direction: column; gap: 0.5rem; width: 100%;">
                    <div style="display: flex; padding: 0 0.75rem; font-weight: 600; font-size: 0.85rem; color: var(--text-muted); gap: 1rem;">
                        <div style="flex: 2; min-width: 150px;">รายการยา</div>
                        <div style="flex: 3; min-width: 200px;">วิธีใช้</div>
                        <div style="flex: 0 0 60px; text-align: right;">จำนวน</div>
                    </div>
                    ${rxList
                      .map(
                        (rx) => `
                        <div class="emr-value" style="display: flex; align-items: center; padding: 0.5rem 0.75rem; min-height: 40px; margin: 0; gap: 1rem; flex-wrap: wrap;">
                            <div style="flex: 2; min-width: 150px; font-weight: 500; color: #111827;">${EchoUtils.escapeHtml(rx.dName || "-")}</div>
                            <div style="flex: 3; min-width: 200px; color: #374151;">${EchoUtils.escapeHtml(rx.use || "-")}</div>
                            <div style="flex: 0 0 60px; text-align: right; font-weight: 600; color: #111827;">${EchoUtils.escapeHtml(String(rx.qty || "0"))}</div>
                        </div>`,
                      )
                      .join("")}
                </div>
            </div>`;
      }
      html += `</div>`;
    });
    html += "</div>";
    return html;
  };

  // Custom Fetch & Render Orchestrator
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    let hn = hnInput.value.trim();
    if (!hn) return;

    // Pad HN to 7 digits with leading zeros
    hn = hn.padStart(7, "0");
    hnInput.value = hn;

    hideResults();

    // Change button state to loading
    const submitBtn = document.getElementById("submitBtn");
    const originalBtnText = submitBtn.innerHTML;
    submitBtn.innerHTML =
      '<span class="loading-spinner"></span> กำลังดึงข้อมูล...';
    submitBtn.disabled = true;

    try {
      const csrfToken = EchoAPI.getCSRFToken();

      // Perform parallel fetch
      const [consultRes, egfrRes, a1cRes, emrRes] =
        await Promise.allSettled([
          fetch("/api/consult", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": csrfToken,
            },
            body: JSON.stringify({ hn }),
          }).then((r) => r.json()),
          fetch("/api/egfr", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": csrfToken,
            },
            body: JSON.stringify({ hn }),
          }).then((r) => r.json()),
          fetch("/api/a1c", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": csrfToken,
            },
            body: JSON.stringify({ hn }),
          }).then((r) => r.json()),
          fetch("/api/emr", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": csrfToken,
            },
            body: JSON.stringify({ hn }),
          }).then((r) => r.json()),
        ]);

      resultContainers.style.display = "block";

      // 1. Consult
      if (
        consultRes.status === "fulfilled" &&
        consultRes.value.status === "success"
      ) {
        const records = consultRes.value.records || [];
        records.forEach((r) =>
          Object.keys(r).forEach((k) => {
            if (typeof r[k] === "string") r[k] = EchoUtils.formatThaiDate(r[k]);
          }),
        );
        document.getElementById("echoConsultCount").textContent =
          `${records.length} รายการ`;
        if (records.length > 0)
          document.getElementById("echoConsultTable").innerHTML =
            EchoUtils.buildTable(consultRes.value.columns, records);
        else
          document.getElementById("echoConsultTable").innerHTML =
            '<div class="no-data">ไม่พบประวัติ Consult</div>';
      }


      // 3. eGFR
      if (
        egfrRes.status === "fulfilled" &&
        egfrRes.value.status === "success"
      ) {
        const records = egfrRes.value.records || [];
        records.forEach((r) =>
          Object.keys(r).forEach((k) => {
            if (typeof r[k] === "string") r[k] = EchoUtils.formatThaiDate(r[k]);
          }),
        );
        document.getElementById("echoEgfrCount").textContent =
          `${records.length} รายการ`;

        if (records.length > 0) {
          const tableHtml = EchoUtils.buildTable(
            egfrRes.value.columns,
            records,
            {
              cellRenderers: {
                CKD_Stage: (val) => {
                  if (!val) return val;
                  const stage = String(val).toLowerCase();
                  let bgColor = "";
                  if (stage === "1") bgColor = "#22c55e";
                  else if (stage === "2") bgColor = "#eab308";
                  else if (stage === "3a") bgColor = "#f59e0b";
                  else if (stage === "3b") bgColor = "#ea580c";
                  else if (stage === "4") bgColor = "#ef4444";
                  else if (stage === "5") bgColor = "#991b1b";
                  else return val;
                  return {
                    content: `<span style="background-color: ${bgColor}; color: white; font-weight: 600; padding: 2px 10px; border-radius: 12px; display: inline-block; min-width: 40px; text-align: center;">${EchoUtils.escapeHtml(val)}</span>`,
                    style: "text-align: center; vertical-align: middle;",
                  };
                },
              },
            },
          );
          document.getElementById("echoEgfrTable").innerHTML = tableHtml;

          const sorted = [...records].reverse();
          const labels = sorted.map((r) => r.LabDate);
          const dataValues = sorted.map((r) => parseFloat(r.result));
          const stages = sorted.map((r) => r.CKD_Stage || "Unknown");

          const pointColors = stages.map((stage) => {
            if (stage === "1") return "#22c55e"; // green-500
            if (stage === "2") return "#eab308"; // yellow-500
            if (stage === "3a") return "#f59e0b"; // amber-500
            if (stage === "3b") return "#ea580c"; // orange-600
            if (stage === "4") return "#ef4444"; // red-500
            if (stage === "5") return "#991b1b"; // red-800
            return "#6b7280"; // gray-500
          });

          egfrChartContainer.style.display = "block";
          const ctx = document.getElementById("echoEgfrChart").getContext("2d");
          egfrChartInstance = new Chart(ctx, {
            type: "line",
            data: {
              labels: labels,
              datasets: [
                {
                  label: "eGFR Level",
                  data: dataValues,
                  borderColor: "#64748b",
                  backgroundColor: "rgba(100, 116, 139, 0.1)",
                  borderWidth: 2,
                  pointBackgroundColor: pointColors,
                  pointBorderColor: pointColors,
                  pointRadius: 5,
                  fill: true,
                  tension: 0.3,
                },
              ],
            },
            options: { responsive: true, maintainAspectRatio: false },
          });
        } else {
          document.getElementById("echoEgfrTable").innerHTML =
            '<div class="no-data">ไม่พบประวัติ eGFR</div>';
        }
      }

      // 4. A1C
      if (a1cRes.status === "fulfilled" && a1cRes.value.status === "success") {
        const records = a1cRes.value.records || [];
        records.forEach((r) =>
          Object.keys(r).forEach((k) => {
            if (typeof r[k] === "string") r[k] = EchoUtils.formatThaiDate(r[k]);
          }),
        );
        document.getElementById("echoA1cCount").textContent =
          `${records.length} รายการ`;

        if (records.length > 0) {
          document.getElementById("echoA1cTable").innerHTML =
            EchoUtils.buildTable(a1cRes.value.columns, records, {
              cellRenderers: {
                Status: (val) => {
                  if (!val) return val;
                  const status = String(val).toLowerCase();
                  let bgColor = "#6b7280";
                  if (status === "control") bgColor = "#22c55e";
                  else if (status === "uncontrol") bgColor = "#ef4444";
                  return {
                    content: `<span style="background-color: ${bgColor}; color: white; font-weight: 600; padding: 2px 10px; border-radius: 12px; display: inline-block; min-width: 60px; text-align: center;">${EchoUtils.escapeHtml(val)}</span>`,
                    style: "text-align: center; vertical-align: middle;",
                  };
                },
              },
            });
          const sorted = [...records].reverse();
          const labels = sorted.map((r) => r.LabDate);
          const dataValues = sorted.map((r) => parseFloat(r.result));

          a1cChartContainer.style.display = "block";
          const ctx = document.getElementById("echoA1cChart").getContext("2d");
          a1cChartInstance = new Chart(ctx, {
            type: "line",
            data: {
              labels: labels,
              datasets: [
                {
                  label: "HbA1c Level",
                  data: dataValues,
                  borderColor: "#94a3b8",
                  backgroundColor: "rgba(148, 163, 184, 0.1)",
                  borderWidth: 2,
                  pointRadius: 5,
                  fill: true,
                  tension: 0.3,
                },
              ],
            },
            options: { responsive: true, maintainAspectRatio: false },
          });
        } else {
          document.getElementById("echoA1cTable").innerHTML =
            '<div class="no-data">ไม่พบประวัติ HbA1c</div>';
        }
      }

      // 5. EMR
      if (emrRes.status === "fulfilled" && emrRes.value.status === "success") {
        const records = emrRes.value.records || [];
        records.forEach((r) =>
          Object.keys(r).forEach((k) => {
            if (typeof r[k] === "string") r[k] = EchoUtils.formatThaiDate(r[k]);
          }),
        );
        document.getElementById("echoEmrCount").textContent =
          `${records.length} รายการ`;
        if (records.length > 0) {
          document.getElementById("echoEmrCards").innerHTML =
            renderEMRCards(records);
        } else {
          document.getElementById("echoEmrCards").innerHTML =
            '<div class="no-data">ไม่พบประวัติ EMR</div>';
        }
      }
    } catch (err) {
      console.error(err);
      alert("เกิดข้อผิดพลาดในการดึงข้อมูล");
    } finally {
      submitBtn.innerHTML = originalBtnText;
      submitBtn.disabled = false;
    }
  });

  document.getElementById("resetBtn")?.addEventListener("click", () => {
    hideResults();
    hnInput.value = "";
    hnInput.focus();
  });
});
