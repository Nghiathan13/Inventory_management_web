document.addEventListener("DOMContentLoaded", function () {
  const csrfMeta = document.querySelector('meta[name="csrf-token"]');
  const csrfToken = csrfMeta ? csrfMeta.getAttribute("content") : "";

  // =======================================================
  //        HÀM HỖ TRỢ (HELPERS)
  // =======================================================

  // Chuyển đổi trạng thái nút (Loading/Normal)
  function toggleButtonState(button, isLoading) {
    const btnText = button.querySelector(".btn-text");
    const btnLoading = button.querySelector(".btn-loading");

    button.disabled = isLoading;

    if (isLoading) {
      if (btnText) btnText.classList.add("d-none");
      if (btnLoading) btnLoading.classList.remove("d-none");
    } else {
      if (btnText) btnText.classList.remove("d-none");
      if (btnLoading) btnLoading.classList.add("d-none");
    }
  }

  // Tải file xuống trình duyệt
  function downloadFile(url, filename) {
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  // =======================================================
  //        XỬ LÝ SỰ KIỆN (EVENT HANDLERS)
  // =======================================================

  const confirmButtons = document.querySelectorAll(".confirm-order-btn");

  confirmButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const { orderId, url } = this.dataset;

      if (!confirm(`Are you sure you want to confirm Order #${orderId}?`)) return;

      toggleButtonState(this, true);

      fetch(url, {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken,
          "Content-Type": "application/json",
        },
      })
        .then((response) => {
          if (!response.ok) throw new Error(`Server Error: ${response.status}`);
          return response.json();
        })
        .then((data) => {
          if (data.status === "success") {
            if (data.download_url) {
              if (confirm(`${data.message}\n\nDo you want to download the shipping label now?`)) {
                downloadFile(data.download_url, `label_order_${orderId}.pdf`);
              }
            }
            window.location.reload();
          } else {
            throw new Error(data.message);
          }
        })
        .catch((error) => {
          console.error("Error:", error);
          alert(`Error: ${error.message}`);
          toggleButtonState(this, false);
        });
    });
  });
});
