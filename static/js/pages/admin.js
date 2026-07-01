document.addEventListener("DOMContentLoaded", () => {
  const tbody = document.getElementById("usersTableBody");

  const badge = (ok) =>
    `<span class="admin-badge ${ok ? "yes" : "no"}">${ok ? "ใช่" : "ไม่"}</span>`;

  async function loadUsers() {
    const data = await EchoAPI.get("/api/admin/users");
    tbody.innerHTML = (data.users || [])
      .map(
        (u) => `
        <tr data-id="${u.id}">
          <td>${EchoUtils.escapeHtml(u.email)}</td>
          <td>${EchoUtils.escapeHtml(u.name || "-")}</td>
          <td>${badge(u.is_verified)}</td>
          <td>${badge(u.is_active)}</td>
          <td>
            <label><input type="checkbox" class="access-toggle" data-flag="can_access_echo" ${u.can_access_echo ? "checked" : ""}> Echo</label>
          </td>
          <td>
            <label><input type="checkbox" class="access-toggle" data-flag="can_access_emr" ${u.can_access_emr ? "checked" : ""}> EMR</label>
          </td>
          <td class="admin-actions">
            ${
              u.is_active
                ? `<button class="btn-deactivate">ปิดใช้งาน</button>`
                : `<button class="btn-activate" ${u.is_verified ? "" : "disabled"}>อนุมัติ</button>`
            }
            <button class="btn-delete">ลบ</button>
          </td>
        </tr>`,
      )
      .join("");
  }

  tbody.addEventListener("click", async (e) => {
    const row = e.target.closest("tr");
    if (!row) return;
    const id = row.dataset.id;

    if (e.target.classList.contains("btn-activate")) {
      await EchoAPI.post(`/api/admin/users/${id}/activate`);
      loadUsers();
    } else if (e.target.classList.contains("btn-deactivate")) {
      await EchoAPI.post(`/api/admin/users/${id}/deactivate`);
      loadUsers();
    } else if (e.target.classList.contains("btn-delete")) {
      if (confirm("ยืนยันการลบผู้ใช้นี้?")) {
        await EchoAPI.post(`/api/admin/users/${id}/delete`);
        loadUsers();
      }
    }
  });

  tbody.addEventListener("change", async (e) => {
    if (!e.target.classList.contains("access-toggle")) return;
    const row = e.target.closest("tr");
    const id = row.dataset.id;
    const flag = e.target.dataset.flag;
    await EchoAPI.post(`/api/admin/users/${id}/access`, { [flag]: e.target.checked });
  });

  loadUsers();
});
