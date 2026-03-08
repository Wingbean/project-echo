/* ======================================
   MAIN.JS - Core Application Script
   Project Echo
   ====================================== */

document.addEventListener("DOMContentLoaded", () => {
  initThemeToggle();
  initNavToggle();
  initAlertDismiss();

  // Secret Echo Route Logic
  const secretEchoBtn = document.getElementById("secretEchoBtn");
  if (secretEchoBtn) {
    secretEchoBtn.addEventListener("click", () => {
      window.location.href = "/echo";
    });
  }
});

/* --- Theme Toggle (Light/Dark) --- */
function initThemeToggle() {
  const toggle = document.getElementById("themeToggle");
  const icon = document.getElementById("themeIcon");
  if (!toggle || !icon) return;

  // Load saved theme
  const savedTheme = localStorage.getItem("echo-theme") || "light";
  document.documentElement.setAttribute("data-theme", savedTheme);
  icon.textContent = savedTheme === "dark" ? "light_mode" : "dark_mode";

  toggle.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme");
    const next = current === "dark" ? "light" : "dark";

    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("echo-theme", next);
    icon.textContent = next === "dark" ? "light_mode" : "dark_mode";
  });
}

/* --- Mobile Nav Toggle --- */
function initNavToggle() {
  const toggle = document.getElementById("navToggle");
  const menu = document.getElementById("navMenu");
  if (!toggle || !menu) return;

  toggle.addEventListener("click", () => {
    menu.classList.toggle("open");
  });

  // Close menu when clicking outside
  document.addEventListener("click", (e) => {
    if (!toggle.contains(e.target) && !menu.contains(e.target)) {
      menu.classList.remove("open");
    }
  });

  // Close menu when a link is clicked
  menu.querySelectorAll(".nav-link").forEach((link) => {
    link.addEventListener("click", () => {
      menu.classList.remove("open");
    });
  });
}

/* --- Flash Message Dismiss --- */
function initAlertDismiss() {
  document.querySelectorAll(".alert-close").forEach((btn) => {
    btn.addEventListener("click", () => {
      const alert = btn.closest(".alert");
      if (alert) {
        alert.style.opacity = "0";
        alert.style.transform = "translateY(-10px)";
        alert.style.transition = "all 0.3s ease";
        setTimeout(() => alert.remove(), 300);
      }
    });
  });
}
