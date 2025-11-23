document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("confirm-form");
  if (!form) return;

  const submitBtn = document.getElementById("submit-btn");
  const errorDiv = document.getElementById("form-error");

  // Modal instance (Bootstrap 5)
  let expiryModalObj = null;
  const modalEl = document.getElementById("expiryModal");
  if (modalEl) {
    expiryModalObj = new bootstrap.Modal(modalEl);
  }

  // =========================================================
  // 1. CÁC HÀM XỬ LÝ MODAL & GIAO DIỆN
  // =========================================================

  // Hàm được gọi khi user click nút "Nhập HSD" (Global function để HTML gọi được)
  window.openExpiryModal = function (detailId, productName) {
    document.getElementById("modal-detail-id").value = detailId;
    document.getElementById("modal-product-name").value = productName;

    // Lấy giá trị cũ nếu đã nhập trước đó
    const existingDate = document.getElementById(`input-expiry-${detailId}`).value;
    document.getElementById("modal-date-input").value = existingDate;

    // Mở modal
    expiryModalObj.show();
  };

  // Hàm được gọi khi user click "Lưu & Xác Nhận" trong Modal
  window.saveExpiryDate = function () {
    const detailId = document.getElementById("modal-detail-id").value;
    const dateValue = document.getElementById("modal-date-input").value;

    if (!dateValue) {
      alert("Vui lòng chọn ngày hết hạn!");
      return;
    }

    // 1. Cập nhật vào Input Ẩn của Form
    document.getElementById(`input-expiry-${detailId}`).value = dateValue;

    // 2. Cập nhật giao diện dòng (Text hiển thị)
    // Format ngày dd/mm/yyyy
    const dateObj = new Date(dateValue);
    const formattedDate = dateObj.toLocaleDateString("vi-VN"); // Hoặc 'en-GB'

    const displaySpan = document.getElementById(`display-expiry-${detailId}`);
    displaySpan.textContent = formattedDate;
    displaySpan.classList.remove("text-muted", "fst-italic");
    displaySpan.classList.add("fw-bold", "text-success");

    // 3. Tự động Tick Checkbox
    const checkbox = document.querySelector(`input[name="details"][value="${detailId}"]`);
    if (checkbox) checkbox.checked = true;

    // 4. Đổi màu dòng (Row) để báo hiệu thành công
    const row = document.getElementById(`row-${detailId}`);
    row.classList.add("table-success"); // Class xanh lá của Bootstrap

    // 5. Đóng Modal
    expiryModalObj.hide();

    // 6. Kiểm tra xem đã nhập hết chưa để mở khóa nút Submit
    checkCompletion();
  };

  // Hàm kiểm tra xem user đã nhập đủ tất cả các dòng chưa
  function checkCompletion() {
    const allCheckboxes = document.querySelectorAll(".item-checkbox");
    let allChecked = true;

    allCheckboxes.forEach((cb) => {
      if (!cb.checked) allChecked = false;
    });

    if (allChecked) {
      submitBtn.disabled = false;
      submitBtn.classList.remove("btn-secondary"); // Nếu muốn đổi màu
    } else {
      submitBtn.disabled = true;
    }
  }

  // =========================================================
  // 2. XỬ LÝ SUBMIT FORM (Gửi Ajax & Tải PDF)
  // =========================================================
  form.addEventListener("submit", function (event) {
    event.preventDefault();

    // UI Loading
    submitBtn.disabled = true;
    submitBtn.innerHTML =
      '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Đang xử lý...';
    errorDiv.classList.add("d-none");

    const formData = new FormData(form);
    // const csrfToken = formData.get("csrfmiddlewaretoken"); // FormData tự xử lý, hoặc lấy từ cookie nếu cần

    fetch(form.action, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest", // Báo hiệu cho Django đây là Ajax
        "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
      },
      body: formData,
    })
      .then((response) => {
        if (!response.ok) {
          return response.json().then((err) => {
            throw new Error(err.message || "Lỗi máy chủ.");
          });
        }
        return response.json();
      })
      .then((data) => {
        if (data.status === "success") {
          // Bước 1: Tự động tải file PDF
          if (data.download_url) {
            const link = document.createElement("a");
            link.href = data.download_url;
            link.download = ""; // Browser tự đặt tên theo Header server
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
          }

          // Bước 2: Chờ 1 chút rồi chuyển hướng về Dashboard
          setTimeout(() => {
            window.location.href = form.dataset.redirectUrl;
          }, 1500); // Delay 1.5s để user kịp thấy file tải xuống
        } else {
          throw new Error(data.message || "Có lỗi xảy ra.");
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        errorDiv.textContent = "Lỗi: " + error.message;
        errorDiv.classList.remove("d-none");

        // Reset nút
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-print me-1"></i> Hoàn Thành & In Phiếu';
      });
  });
});
