// products/frontend/static/products/js/product_list.js

document.addEventListener("DOMContentLoaded", function () {
  /**
   * Khởi tạo các tooltip của Bootstrap cho các phần tử trên trang.
   */
  function initializeTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    [...tooltipTriggerList].map(
      (tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl)
    );
  }

  /**
   * Quản lý Modal thông báo, hiển thị các thông điệp thành công hoặc lỗi.
   */
  function setupInfoModal() {
    const infoModalElement = document.getElementById("infoModal");
    if (!infoModalElement) return;

    const infoModal = new bootstrap.Modal(infoModalElement);
    const infoModalTitle = document.getElementById("infoModalLabel");
    const infoModalBody = document.getElementById("infoModalBody");
    const infoModalActionBtn = document.getElementById("infoModalActionBtn");

    /**
     * Hiển thị Modal với nội dung tùy chỉnh.
     */
    function showInfoModal(title, body, actionUrl = "", actionText = "") {
      infoModalTitle.textContent = title;
      infoModalBody.textContent = body;

      if (actionUrl && actionText) {
        infoModalActionBtn.href = actionUrl;
        infoModalActionBtn.textContent = actionText;
        infoModalActionBtn.classList.remove("d-none");
      } else {
        infoModalActionBtn.classList.add("d-none");
      }
      infoModal.show();
    }

    // Gắn listener toàn cục để có thể gọi `showInfoModal` từ nơi khác nếu cần
    window.showInfoModal = showInfoModal;
  }

  /**
   * Xử lý các sự kiện click trên các nút "Di chuyển kệ".
   */
  function setupMoveShelfButtons() {
    const moveButtons = document.querySelectorAll(".move-to-shelf-btn");

    moveButtons.forEach((button) => {
      button.addEventListener("click", function () {
        const shelfName = this.dataset.shelfName;

        if (!shelfName) {
          window.showInfoModal("Lỗi", "Không tìm thấy thông tin kệ.");
          return;
        }

        const originalIconHTML = this.innerHTML;
        setButtonLoading(this, true);

        const formData = new FormData();
        formData.append("shelf_name", shelfName);

        fetch(moveToShelfApiUrl, {
          method: "POST",
          headers: { "X-CSRFToken": csrfToken },
          body: formData,
        })
          .then((response) => {
            if (!response.ok)
              return response.json().then((err) => {
                throw new Error(err.message || "Lỗi không xác định từ server.");
              });
            return response.json();
          })
          .then((data) => {
            if (data.status === "ok") {
              window.showInfoModal(
                "Thành Công",
                `Đã gửi lệnh di chuyển đến kệ ${shelfName}. Bạn có muốn chuyển đến trang điều khiển để theo dõi không?`,
                moveToShelfRedirectUrl,
                "Đến Trang Điều Khiển"
              );
            } else {
              throw new Error(data.message);
            }
          })
          .catch((error) => {
            window.showInfoModal("Lỗi", `Đã có lỗi xảy ra: ${error.message}`);
          })
          .finally(() => {
            setButtonLoading(this, false, originalIconHTML);
          });
      });
    });
  }

  /**
   * Bật/tắt trạng thái loading của một nút.
   */
  function setButtonLoading(button, isLoading, originalContent = "") {
    if (isLoading) {
      button.disabled = true;
      const spinner = document.createElement("span");
      spinner.className = "spinner-border spinner-border-sm";
      button.innerHTML = "";
      button.appendChild(spinner);
    } else {
      button.disabled = false;
      button.innerHTML = originalContent;
    }
  }

  /**
   * Gắn sự kiện cho nút hành động trên Modal.
   */
  function setupModalActionLink() {
    const infoModalActionBtn = document.getElementById("infoModalActionBtn");
    if (infoModalActionBtn) {
      infoModalActionBtn.addEventListener("click", function (e) {
        e.preventDefault();
        window.location.href = this.href;
      });
    }
  }

  // === KHỞI CHẠY TẤT CẢ CÁC HÀM ===
  initializeTooltips();
  setupInfoModal();
  setupMoveShelfButtons();
  setupModalActionLink();
});
