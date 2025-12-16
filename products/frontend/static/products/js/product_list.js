document.addEventListener("DOMContentLoaded", function () {
  // Khởi tạo Tooltips Bootstrap
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  [...tooltipTriggerList].map((el) => new bootstrap.Tooltip(el));

  // =======================================================
  //        QUẢN LÝ MODAL THÔNG BÁO
  // =======================================================
  const infoModalElement = document.getElementById("infoModal");
  let infoModalInstance = null;

  if (infoModalElement) {
    infoModalInstance = new bootstrap.Modal(infoModalElement);

    const modalTitle = document.getElementById("infoModalLabel");
    const modalBody = document.getElementById("infoModalBody");
    const modalBtn = document.getElementById("infoModalActionBtn");

    // Hàm hiển thị Modal (Global)
    window.showInfoModal = (title, body, actionUrl = "", actionText = "") => {
      modalTitle.textContent = title;
      modalBody.textContent = body;

      if (actionUrl && actionText) {
        modalBtn.href = actionUrl;
        modalBtn.textContent = actionText;
        modalBtn.classList.remove("d-none");
      } else {
        modalBtn.classList.add("d-none");
      }
      infoModalInstance.show();
    };

    // Sự kiện click nút hành động trong Modal
    if (modalBtn) {
      modalBtn.addEventListener("click", function (e) {
        e.preventDefault();
        window.location.href = this.href;
      });
    }
  }

  // =======================================================
  //        HÀM TIỆN ÍCH UI
  // =======================================================

  // Bật/Tắt trạng thái Loading cho nút
  function toggleButtonLoading(button, isLoading, originalContent = "") {
    if (isLoading) {
      button.disabled = true;
      button.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
    } else {
      button.disabled = false;
      button.innerHTML = originalContent;
    }
  }

  // =======================================================
  //        XỬ LÝ DI CHUYỂN KỆ (API CALL)
  // =======================================================
  const moveButtons = document.querySelectorAll(".move-to-shelf-btn");

  moveButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const shelfName = this.dataset.shelfName;

      if (!shelfName) {
        window.showInfoModal("Error", "Shelf information missing.");
        return;
      }

      const originalIconHTML = this.innerHTML;
      toggleButtonLoading(this, true);

      const formData = new FormData();
      formData.append("shelf_name", shelfName);

      // Gọi API Backend
      fetch(moveToShelfApiUrl, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken },
        body: formData,
      })
        .then((response) => {
          if (!response.ok)
            return response.json().then((err) => {
              throw new Error(err.message || "Unknown server error.");
            });
          return response.json();
        })
        .then((data) => {
          if (data.status === "ok") {
            window.showInfoModal(
              "Success",
              `Move command sent to Shelf ${shelfName}. Go to Control Panel to monitor?`,
              moveToShelfRedirectUrl,
              "Go to Control Panel"
            );
          } else {
            throw new Error(data.message);
          }
        })
        .catch((error) => {
          window.showInfoModal("Error", `An error occurred: ${error.message}`);
        })
        .finally(() => {
          toggleButtonLoading(this, false, originalIconHTML);
        });
    });
  });
});
