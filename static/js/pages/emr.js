document.addEventListener("DOMContentLoaded", () => {
    // Custom render function for EMR cards
    const renderEMRCards = (records) => {
      if (!records || records.length === 0) return "";

      let html = '<div class="emr-cards-container">';

      records.forEach((row) => {
        const val = (key) => {
          const v = row[key];
          return v
            ? EchoUtils.escapeHtml(String(v))
            : '<span style="color: var(--text-muted); opacity: 0.5;">-</span>';
        };

        html += `
            <div class="emr-card">
                <div class="emr-card-header">
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <span class="material-symbols-rounded">event_note</span>
                        <strong>วันที่: ${val("VstDate")} ${val("VstTime")}</strong>
                    </div>
                </div>
                <div class="emr-card-body">
                    <!-- Left Pane -->
                    <div class="emr-left-pane">
                        <div class="emr-row">
                            <div class="emr-field"><div class="emr-label">VN</div><div class="emr-value" style="font-weight: bold; color: var(--teal-600);">${val("VN")}</div></div>
                            <div class="emr-field"><div class="emr-label">HN</div><div class="emr-value">${val("HN")}</div></div>
                            <div class="emr-field"><div class="emr-label">AN</div><div class="emr-value">${val("AN")}</div></div>
                        </div>
                        <div class="emr-row">
                            <div class="emr-field"><div class="emr-label">VstDate</div><div class="emr-value">${val("VstDate")}</div></div>
                            <div class="emr-field"><div class="emr-label">VstTime</div><div class="emr-value">${val("VstTime")}</div></div>
                            <div class="emr-field"><div class="emr-label">Rights</div><div class="emr-value">${val("Rights")}</div></div>
                        </div>
                        <div class="emr-row gap-large">
                            <div class="emr-field"><div class="emr-label">Dept</div><div class="emr-value">${val("Dept")}</div></div>
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
                    <div class="emr-right-pane">
                        <div class="emr-col">
                            <div class="emr-field"><div class="emr-label wide">Dx_Text</div><div class="emr-value" style="font-weight: 500;">${val("Dx_Text")}</div></div>
                            <div class="emr-field"><div class="emr-label wide" style="color: var(--teal-600);">PDx</div><div class="emr-value" style="font-weight: 600;">${val("PDx")}</div></div>
                            <div class="emr-field"><div class="emr-label wide">Dx1</div><div class="emr-value">${val("Dx1")}</div></div>
                            <div class="emr-field"><div class="emr-label wide">Dx2</div><div class="emr-value">${val("Dx2")}</div></div>
                            <div class="emr-field"><div class="emr-label wide">Dx3</div><div class="emr-value">${val("Dx3")}</div></div>
                        </div>
                        <div class="emr-col">
                            <div class="emr-field"><div class="emr-label wide">op1</div><div class="emr-value">${val("op1")}</div></div>
                            <div class="emr-field"><div class="emr-label wide">op2</div><div class="emr-value">${val("op2")}</div></div>
                            <div class="emr-field"><div class="emr-label wide">op3</div><div class="emr-value">${val("op3")}</div></div>
                            <div class="emr-field"><div class="emr-label wide">op4</div><div class="emr-value">${val("op4")}</div></div>
                            <div class="emr-field"><div class="emr-label wide">op5</div><div class="emr-value">${val("op5")}</div></div>
                        </div>
                    </div>
                </div>`;

        // Render Rx if exists
        const rxList = row.rx_list || [];
        if (rxList.length > 0) {
          html += `
                <div style="padding: 0 1.5rem 1.5rem 1.5rem;">
                    <div style="color: var(--teal-700); font-size: 1.05rem; display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; font-weight: 600;">
                        <span class="material-symbols-rounded" style="font-size: 1.2rem;">prescriptions</span>
                        รายการยา (Prescriptions)
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
                            </div>
                        `,
                          )
                          .join("")}
                    </div>
                </div>`;
        }

        html += `
            </div>`;
      });

      html += "</div>";
      return html;
    };

    EchoUtils.setupHnSearch({
      apiUrl: "/api/emr",
      formId: "emrSearchForm",
      hnInputId: "hnInput",
      submitBtnId: "searchBtn",
      resetBtnId: "resetBtn",
      resultsSectionId: "resultsSection",
      resultsTableId: "resultsTable",
      resultCountId: "resultCount",
      hnBadgeId: "hnBadge",
      loadingMessage: "กำลังดึงประวัติการรักษา EMR สำหรับ HN:",
      noDataMessage: "ไม่พบประวัติการรักษา EMR สำหรับ HN:",
      submitButtonHtml:
        '<span class="material-symbols-rounded">search</span> ค้นหาข้อมูล',
      customRender: renderEMRCards,
    });
  });
