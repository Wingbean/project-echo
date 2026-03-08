document.addEventListener("DOMContentLoaded", () => {
  let inrChartInstance = null;
  const chartContainer = document.getElementById("inrChartContainer");
  const ctx = document.getElementById("inrChart").getContext("2d");

  function destroyChart() {
    if (inrChartInstance) {
      inrChartInstance.destroy();
      inrChartInstance = null;
    }
    chartContainer.style.display = "none";
  }

  EchoUtils.setupHnSearch({
    formId: "inrForm",
    apiUrl: "/api/inr",
    loadingMessage: "กำลังค้นหาข้อมูล INR ของ HN",
    noDataMessage: "ไม่พบประวัติผล INR สำหรับ HN",
    submitButtonHtml:
      '<span class="material-symbols-rounded">search</span> ค้นหาผล INR',
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
      inrChartInstance = new Chart(ctx, {
        type: "line",
        data: {
          labels: labels,
          datasets: [
            {
              label: "INR Level",
              data: dataValues,
              borderColor: "#f59e0b", // amber-500
              backgroundColor: "rgba(245, 158, 11, 0.1)",
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
              text: "แนวโน้มค่า INR ย้อนหลัง (สีเขียว=Control 2.0-3.0, สีแดง=unControl)",
            },
            annotation: {
              annotations: {
                targetRange: {
                  type: "box",
                  yMin: 2,
                  yMax: 3,
                  backgroundColor: "rgba(34, 197, 94, 0.1)", // Light green target range
                  borderWidth: 0,
                  label: {
                    display: true,
                    content: "Target (2.0 - 3.0)",
                    position: "center",
                    color: "rgba(34, 197, 94, 0.5)",
                    font: {
                      size: 14,
                      weight: "bold",
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
                  return `INR: ${value} (${status})`;
                },
              },
            },
          },
          scales: {
            y: {
              beginAtZero: true,
              title: { display: true, text: "INR" },
              suggestedMax: 6, // typical max for INR graph scale
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
