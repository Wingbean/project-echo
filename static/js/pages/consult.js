document.addEventListener("DOMContentLoaded", () => {
  EchoUtils.setupHnSearch({
    formId: "consultForm",
    apiUrl: "/api/consult",
    loadingMessage: "กำลังค้นหาข้อมูล Consult ของ HN",
    noDataMessage: "ไม่พบข้อมูลการ Consult สำหรับ HN",
    submitButtonHtml:
      '<span class="material-symbols-rounded">search</span> ค้นหา',
  });
});
