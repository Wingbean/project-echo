document.addEventListener("DOMContentLoaded", () => {
  EchoUtils.setupHnSearch({
    formId: "flowOpdForm",
    apiUrl: "/api/flow_opd",
    loadingMessage: "กำลังค้นหาข้อมูล OPD Flow ของ HN",
    noDataMessage: "ไม่พบข้อมูล OPD Flow วันนี้สำหรับ HN",
    submitButtonHtml:
      '<span class="material-symbols-rounded">search</span> ค้นหาข้อมูล Flow รพ.',
  });
});
