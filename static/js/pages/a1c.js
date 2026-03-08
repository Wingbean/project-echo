document.addEventListener("DOMContentLoaded", () => {
    let a1cChartInstance = null;
    const chartContainer = document.getElementById("a1cChartContainer");
    const ctx = document.getElementById("a1cChart").getContext("2d");

    function destroyChart() {
      if (a1cChartInstance) {
        a1cChartInstance.destroy();
        a1cChartInstance = null;
      }
      chartContainer.style.display = "none";
    }

    EchoUtils.setupHnSearch({
      formId: "a1cForm",
      apiUrl: "/api/a1c",
      loadingMessage: "กำลังค้นหาข้อมูล HbA1c ของ HN",
      noDataMessage: "ไม่พบประวัติผล HbA1c สำหรับ HN",
      submitButtonHtml:
        '<span class="material-symbols-rounded">search</span> ค้นหาผล HbA1c',
      tableOptions: {
        cellRenderers: {
          Status: (val) => {
            if (!val) return val;
            const status = String(val).toLowerCase();
            let bgColor = "#6b7280"; // gray by default
            if (status === "control")
              bgColor = "#22c55e"; // green-500
            else if (status === "uncontrol") bgColor = "#ef4444"; // red-500

            return {
              content: `<span style="background-color: ${bgColor}; color: white; font-weight: 600; padding: 2px 10px; border-radius: 12px; display: inline-block; min-width: 60px; text-align: center;">${EchoUtils.escapeHtml(val)}</span>`,
              style: "text-align: center; vertical-align: middle;",
            };
          },
        },
      },
      onReset: () => {
        destroyChart();
      },
      onSuccess: (records) => {
        destroyChart();
        if (!records || records.length === 0) return;

        // Ensure records are ordered chronologically for plotting (oldest to newest)
        const sortedRecords = [...records].reverse();

        const labels = sortedRecords.map((r) => r.LabDate);
        const dataValues = sortedRecords.map((r) => parseFloat(r.result));
        const statuses = sortedRecords.map((r) => r.Status || "Unknown");

        // Map status to colors for chart
        const pointColors = statuses.map((status) => {
          const s = status.toLowerCase();
          if (s === "control") return "#22c55e"; // green-500
          if (s === "uncontrol") return "#ef4444"; // red-500
          return "#6b7280";
        });

        chartContainer.style.display = "block";
        a1cChartInstance = new Chart(ctx, {
          type: "line",
          data: {
            labels: labels,
            datasets: [
              {
                label: "HbA1c Level",
                data: dataValues,
                borderColor: "#94a3b8", // slate-400 (neutral line)
                backgroundColor: "rgba(148, 163, 184, 0.1)",
                borderWidth: 2,
                pointBackgroundColor: pointColors,
                pointBorderColor: pointColors,
                pointRadius: 5,
                pointHoverRadius: 7,
                fill: true,
                tension: 0.3,
              },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { position: "top" },
              title: {
                display: true,
                text: "แนวโน้มค่า HbA1c ย้อนหลัง (สีเขียว=Control, สีแดง=unControl)",
              },
              annotation: {
                annotations: {
                  cutoffLine: {
                    type: "line",
                    yMin: 7,
                    yMax: 7,
                    borderColor: "rgba(239, 68, 68, 0.4)", // Faint red line (unobtrusive)
                    borderWidth: 2,
                    borderDash: [5, 5],
                    label: {
                      display: true,
                      content: "Cutoff (7%)",
                      position: "end",
                      backgroundColor: "rgba(239, 68, 68, 0.7)",
                      color: "white",
                      font: {
                        size: 10,
                      },
                    },
                  },
                },
              },
              tooltip: {
                callbacks: {
                  label: function (context) {
                    const value = context.parsed.y;
                    const status = statuses[context.dataIndex];
                    return `HbA1c: ${value} % (${status})`;
                  },
                },
              },
            },
            scales: {
              y: {
                beginAtZero: true,
                title: { display: true, text: "HbA1c (%)" },
                suggestedMax: 12, // typical max for A1c graph scale
              },
              x: {
                title: { display: true, text: "วันที่ตรวจ" },
              },
            },
          },
        });
      },
    });
  });
