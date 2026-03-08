document.addEventListener("DOMContentLoaded", () => {
    let egfrChartInstance = null;
    const chartContainer = document.getElementById("egfrChartContainer");
    const ctx = document.getElementById("egfrChart").getContext("2d");

    function destroyChart() {
      if (egfrChartInstance) {
        egfrChartInstance.destroy();
        egfrChartInstance = null;
      }
      chartContainer.style.display = "none";
    }

    EchoUtils.setupHnSearch({
      formId: "egfrForm",
      apiUrl: "/api/egfr",
      loadingMessage: "กำลังค้นหาข้อมูล eGFR ของ HN",
      noDataMessage: "ไม่พบประวัติผล eGFR สำหรับ HN",
      submitButtonHtml:
        '<span class="material-symbols-rounded">search</span> ค้นหาผล eGFR',
      tableOptions: {
        cellRenderers: {
          CKD_Stage: (val) => {
            if (!val) return val;
            const stage = String(val).toLowerCase();
            let bgColor = "";
            if (stage === "1")
              bgColor = "#22c55e"; // green-500
            else if (stage === "2")
              bgColor = "#eab308"; // yellow-500
            else if (stage === "3a")
              bgColor = "#f59e0b"; // amber-500
            else if (stage === "3b")
              bgColor = "#ea580c"; // orange-600
            else if (stage === "4")
              bgColor = "#ef4444"; // red-500
            else if (stage === "5")
              bgColor = "#991b1b"; // red-800
            else return val;

            return {
              content: `<span style="background-color: ${bgColor}; color: white; font-weight: 600; padding: 2px 10px; border-radius: 12px; display: inline-block; min-width: 40px; text-align: center;">${EchoUtils.escapeHtml(val)}</span>`,
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
        const ckdStages = sortedRecords.map((r) => r.CKD_Stage || "Unknown");

        // Map CKD Stage to colors
        const pointColors = ckdStages.map((stage) => {
          if (stage === "1") return "#22c55e"; // green-500
          if (stage === "2") return "#eab308"; // yellow-500
          if (stage === "3a") return "#f59e0b"; // amber-500
          if (stage === "3b") return "#ea580c"; // orange-600
          if (stage === "4") return "#ef4444"; // red-500
          if (stage === "5") return "#991b1b"; // red-800
          return "#6b7280"; // gray-500
        });

        chartContainer.style.display = "block";
        egfrChartInstance = new Chart(ctx, {
          type: "line",
          data: {
            labels: labels,
            datasets: [
              {
                label: "eGFR Level",
                data: dataValues,
                borderColor: "#64748b", // slate-500 (neutral line)
                backgroundColor: "rgba(100, 116, 139, 0.1)",
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
                text: "แนวโน้มค่า eGFR ย้อนหลัง (แบ่งสีตามระยะ CKD)",
              },
              tooltip: {
                callbacks: {
                  label: function (context) {
                    const value = context.parsed.y;
                    const stage = ckdStages[context.dataIndex];
                    return `eGFR: ${value} (CKD Stage ${stage})`;
                  },
                },
              },
            },
            scales: {
              y: {
                beginAtZero: true,
                title: { display: true, text: "eGFR Result" },
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
