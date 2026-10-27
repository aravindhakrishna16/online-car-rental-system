/* ==========================================================
   DRIVEEASE - MAIN JAVASCRIPT
   Dropdowns, Notifications, Flash Alerts, and Demo Login helper
   ========================================================== */

document.addEventListener("DOMContentLoaded", () => {
  // 1. Dropdown Toggle (User profile & Notifications)
  const dropdownToggles = document.querySelectorAll("[data-toggle='dropdown']");
  dropdownToggles.forEach(toggle => {
    toggle.addEventListener("click", (e) => {
      e.stopPropagation();
      const targetId = toggle.getAttribute("data-target");
      const targetMenu = document.getElementById(targetId);
      
      // Close other menus
      document.querySelectorAll(".dropdown-menu").forEach(menu => {
        if (menu !== targetMenu) menu.classList.remove("show");
      });

      if (targetMenu) {
        targetMenu.classList.toggle("show");
      }
    });
  });

  // Close dropdowns on outside click
  document.addEventListener("click", () => {
    document.querySelectorAll(".dropdown-menu").forEach(menu => {
      menu.classList.remove("show");
    });
  });

  // 2. Flash Message Dismissal
  const alertCloseBtns = document.querySelectorAll(".alert-close");
  alertCloseBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const alert = btn.closest(".alert");
      if (alert) {
        alert.style.opacity = "0";
        setTimeout(() => alert.remove(), 250);
      }
    });
  });

  // Auto-dismiss flash messages after 6 seconds
  setTimeout(() => {
    document.querySelectorAll(".alert").forEach(alert => {
      alert.style.opacity = "0";
      setTimeout(() => alert.remove(), 250);
    });
  }, 6000);

  // 3. Mark All Notifications As Read
  const markAllReadBtn = document.getElementById("markAllReadBtn");
  if (markAllReadBtn) {
    markAllReadBtn.addEventListener("click", async () => {
      try {
        const resp = await fetch("/api/notifications/mark-all-read", { method: "POST" });
        const data = await resp.json();
        if (data.success) {
          const badge = document.querySelector(".notif-badge");
          if (badge) badge.style.display = "none";
          document.querySelectorAll(".notif-item.unread").forEach(item => {
            item.classList.remove("unread");
          });
        }
      } catch (err) {
        console.error("Error marking notifications read:", err);
      }
    });
  }

  // 4. Quick Demo Login Buttons Helper (Viva & Presentation Friendly)
  window.fillDemoLogin = (email, password) => {
    const emailInput = document.getElementById("loginEmail");
    const passwordInput = document.getElementById("loginPassword");
    if (emailInput && passwordInput) {
      emailInput.value = email;
      passwordInput.value = password;
      // Highlight briefly
      emailInput.style.borderColor = "#FFC000";
      passwordInput.style.borderColor = "#FFC000";
      setTimeout(() => {
        emailInput.style.borderColor = "";
        passwordInput.style.borderColor = "";
      }, 800);
    }
  };

  // 5. Review Modal Handler
  window.openReviewModal = (bookingId, carName) => {
    const modal = document.getElementById("reviewModal");
    const form = document.getElementById("reviewForm");
    const titleEl = document.getElementById("modalCarName");
    if (modal && form) {
      form.action = `/customer/review/${bookingId}`;
      if (titleEl) titleEl.innerText = carName;
      modal.classList.add("active");
    }
  };

  window.closeReviewModal = () => {
    const modal = document.getElementById("reviewModal");
    if (modal) modal.classList.remove("active");
  };
});
