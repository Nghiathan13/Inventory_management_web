document.addEventListener("DOMContentLoaded", function () {
  // =======================================================
  //        KHAI BÁO DOM & BIẾN (DOM ELEMENTS)
  // =======================================================
  const form = document.getElementById("confirm-form");
  if (!form) return;

  const btnSubmit = document.getElementById("submit-btn");
  const txtNormal = btnSubmit.querySelector(".btn-text-normal");
  const txtLoading = btnSubmit.querySelector(".btn-text-loading");
  const boxError = document.getElementById("form-error");
  const modalEl = document.getElementById("expiryModal");
  let modalInstance = modalEl ? new bootstrap.Modal(modalEl) : null;

  // =======================================================
  //        XỬ LÝ MODAL (MODAL HANDLERS)
  // =======================================================

  /** Mở Modal nhập liệu */
  window.openExpiryModal = function (detailId, productName) {
    document.getElementById("modal-detail-id").value = detailId;
    document.getElementById("modal-product-name").value = productName;

    // Lấy giá trị cũ nếu có
    const currentVal = document.getElementById(`input-expiry-${detailId}`).value;
    document.getElementById("modal-date-input").value = currentVal;

    if (modalInstance) modalInstance.show();
  };

  /** Lưu ngày & Cập nhật giao diện */
  window.saveExpiryDate = function () {
    const id = document.getElementById("modal-detail-id").value;
    const dateVal = document.getElementById("modal-date-input").value;

    if (!dateVal) {
      alert("Please select an expiry date.");
      return;
    }

    // 1. Cập nhật Input ẩn
    document.getElementById(`input-expiry-${id}`).value = dateVal;

    // 2. Cập nhật hiển thị (Format: DD/MM/YYYY)
    const dateObj = new Date(dateVal);
    const displayStr = dateObj.toLocaleDateString("en-GB");

    const spanDisplay = document.getElementById(`display-expiry-${id}`);
    spanDisplay.textContent = displayStr;
    spanDisplay.classList.remove("text-muted", "fst-italic");
    spanDisplay.classList.add("fw-bold", "text-success");

    // 3. Đánh dấu Checkbox & Row
    const checkbox = document.querySelector(`input[name="details"][value="${id}"]`);
    if (checkbox) checkbox.checked = true;

    document.getElementById(`row-${id}`).classList.add("table-success");

    // 4. Đóng Modal & Kiểm tra nút Submit
    if (modalInstance) modalInstance.hide();
    checkAllCompleted();
  };

  /** Kiểm tra hoàn tất toàn bộ */
  function checkAllCompleted() {
    const checkboxes = document.querySelectorAll(".item-checkbox");
    const isAllChecked = Array.from(checkboxes).every((cb) => cb.checked);

    btnSubmit.disabled = !isAllChecked;
    if (isAllChecked) {
      btnSubmit.classList.remove("btn-secondary");
      btnSubmit.classList.add("btn-success");
    }
  }

  // =======================================================
  //        XỬ LÝ SUBMIT (FORM SUBMISSION)
  // =======================================================
  form.addEventListener("submit", function (e) {
    e.preventDefault();

    btnSubmit.disabled = true;
    txtNormal.classList.add("d-none");
    txtLoading.classList.remove("d-none");
    boxError.classList.add("d-none");

    const formData = new FormData(form);

    fetch(form.action, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
      },
      body: formData,
    })
      .then((res) => {
        if (!res.ok)
          return res.json().then((err) => {
            throw new Error(err.message || "Server Error");
          });
        return res.json();
      })
      .then((data) => {
        if (data.status === "success") {
          // Tự động tải PDF
          if (data.download_url) {
            const link = document.createElement("a");
            link.href = data.download_url;
            link.download = "";
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
          }

          setTimeout(() => {
            window.location.href = form.dataset.redirectUrl;
          }, 1500);
        } else {
          throw new Error(data.message || "Unknown Error");
        }
      })
      .catch((err) => {
        console.error("Submit Error:", err);
        boxError.textContent = `Error: ${err.message}`;
        boxError.classList.remove("d-none");

        // Reset UI
        btnSubmit.disabled = false;
        txtNormal.classList.remove("d-none");
        txtLoading.classList.add("d-none");
      });
  });
});
