document.addEventListener("DOMContentLoaded", function () {
  // --- Lấy các element từ DOM ---
  const video = document.getElementById("qr-video");
  const productList = document.getElementById("product-list");

  // Element cho các thông báo
  const feedbackContainer = document.getElementById("feedback-container");
  const fbDefault = document.getElementById("feedback-default");
  const fbSuccess = document.getElementById("feedback-success");
  const fbError = document.getElementById("feedback-error");
  const fbComplete = document.getElementById("feedback-complete");

  // Placeholder cho dữ liệu động
  const fbSuccessProductName = fbSuccess.querySelector(".product-name");
  const fbErrorMessage = fbError.querySelector(".error-message");

  if (!video || !productList || !feedbackContainer) {
    console.error("Các element cần thiết không tồn tại.");
    return;
  }

  // --- Lấy dữ liệu từ các thẻ script trong HTML ---
  const detailCodes = JSON.parse(
    document.getElementById("detail-codes-data").textContent
  );

  const scannedCodes = new Set();
  let stream = null;
  let isPaused = false;

  // --- Khởi động Camera ---
  navigator.mediaDevices
    .getUserMedia({ video: { facingMode: "environment" } })
    .then(function (s) {
      stream = s;
      video.srcObject = s;
      video.play();
      requestAnimationFrame(tick);
    })
    .catch(function (err) {
      console.error("Không thể truy cập camera:", err);
      feedback.textContent = "Lỗi: Không thể truy cập camera.";
      feedback.className = "alert alert-danger mt-3";
    });

  function tick() {
    if (
      stream &&
      !video.paused &&
      video.readyState === video.HAVE_ENOUGH_DATA
    ) {
      const canvasElement = document.createElement("canvas");
      const canvas = canvasElement.getContext("2d");
      canvasElement.height = video.videoHeight;
      canvasElement.width = video.videoWidth;
      canvas.drawImage(video, 0, 0, canvasElement.width, canvasElement.height);
      const imageData = canvas.getImageData(
        0,
        0,
        canvasElement.width,
        canvasElement.height
      );
      const code = jsQR(imageData.data, imageData.width, imageData.height);

      if (code && !scannedCodes.has(code.data)) {
        isPaused = true;

        // Dùng Regex để trích xuất UUID một cách an toàn
        const uuidMatch = code.data.match(
          /([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})/i
        );

        if (uuidMatch && uuidMatch[1]) {
          const detailCode = uuidMatch[1].toLowerCase();

          if (Object.prototype.hasOwnProperty.call(detailCodes, detailCode)) {
            scannedCodes.add(code.data);
            updateUIOnScanSuccess(
              detailCode,
              detailCodes[detailCode].product_name
            );
            updateStockOnServer(detailCode);
          } else {
            showError(
              "Mã không hợp lệ! Vui lòng quét đúng sản phẩm của đơn hàng."
            );
          }
        } else {
          showError("Mã QR không đúng định dạng.");
        }
      }
    }
    if (stream) {
      requestAnimationFrame(tick);
    }
  }

  // Hàm ẩn tất cả các thông báo phản hồi
  function hideAllFeedbacks() {
    fbDefault.classList.add("d-none");
    fbSuccess.classList.add("d-none");
    fbError.classList.add("d-none");
    fbComplete.classList.add("d-none");
  }

  // Hàm hiển thị lỗi quét mã
  function showError(message) {
    hideAllFeedbacks();
    fbErrorMessage.textContent = message;
    fbError.classList.remove("d-none");

    setTimeout(() => {
      hideAllFeedbacks();
      fbDefault.classList.remove("d-none");
      isPaused = false;
    }, 2500);
  }

  // Hàm cập nhật giao diện khi quét thành công
  function updateUIOnScanSuccess(detailCode, productName) {
    hideAllFeedbacks();
    fbSuccessProductName.textContent = productName;
    fbSuccess.classList.remove("d-none");

    const listItem = productList.querySelector(`[data-code="${detailCode}"]`);
    if (listItem) {
      listItem.classList.add("list-group-item-success");
      const icon = listItem.querySelector(".status-icon");
      icon.className = "status-icon text-success";
      icon.innerHTML = '<i class="fas fa-check-circle"></i>';
    }

    setTimeout(() => {
      hideAllFeedbacks();
      fbDefault.classList.remove("d-none"); // Quay về thông báo mặc định
      isPaused = false; // Cho phép quét lại
    }, 2000);
  }

  // Hàm gọi API để cập nhật tồn kho trên server
  async function updateStockOnServer(detailCode) {
    const apiUrl = stockInProcessApiUrl.replace(
      "00000000-0000-0000-0000-000000000000",
      detailCode
    );
    try {
      const response = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken,
          "Content-Type": "application/json",
        },
      });
      if (!response.ok) {
        throw new Error(`Lỗi server: ${response.status}`);
      }
      const result = await response.json();
      console.log("Phản hồi từ server:", result.message);

      if (scannedCodes.size === Object.keys(detailCodes).length) {
        hideAllFeedbacks();
        fbComplete.classList.remove("d-none");

        if (stream) {
          stream.getTracks().forEach((track) => track.stop());
          stream = null;
        }
        setTimeout(
          () => (window.location.href = redirectUrlAfterCompletion),
          2500
        );
      }
    } catch (error) {
      console.error("Lỗi khi cập nhật tồn kho:", error);
      showError(`Lỗi khi cập nhật tồn kho: ${error.message}`);
    }
  }
  requestAnimationFrame(tick);
});
