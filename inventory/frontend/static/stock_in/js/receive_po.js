document.addEventListener("DOMContentLoaded", function () {
  // =======================================================
  //        KHAI BÁO DOM & CẤU HÌNH
  // =======================================================
  const video = document.getElementById("qr-video");
  const productList = document.getElementById("product-list");

  // Feedback UI Elements
  const fbContainer = document.getElementById("feedback-container");
  const fbDefault = document.getElementById("feedback-default");
  const fbSuccess = document.getElementById("feedback-success");
  const fbError = document.getElementById("feedback-error");
  const fbComplete = document.getElementById("feedback-complete");
  const fbSuccessProductName = fbSuccess ? fbSuccess.querySelector(".product-name") : null;
  const fbErrorMessage = fbError ? fbError.querySelector(".error-message") : null;

  // Kiểm tra DOM
  if (!video || !productList || !fbContainer) {
    console.error("Error: Missing required DOM elements.");
    return;
  }

  const detailCodes = JSON.parse(document.getElementById("detail-codes-data").textContent);
  const scannedCodes = new Set();

  let stream = null;
  let isPaused = false;

  const canvasElement = document.createElement("canvas");
  const canvasCtx = canvasElement.getContext("2d", { willReadFrequently: true });

  // =======================================================
  //        KHỞI ĐỘNG CAMERA
  // =======================================================
  navigator.mediaDevices
    .getUserMedia({ video: { facingMode: "environment" } })
    .then(function (s) {
      stream = s;
      video.srcObject = s;
      video.setAttribute("playsinline", true);
      video.play();
      requestAnimationFrame(tick);
    })
    .catch(function (err) {
      console.error("Camera Access Error:", err);
      showError("Error: Camera access denied. Please check permissions.");
    });

  // =======================================================
  //        VÒNG LẶP QUÉT (SCAN LOOP)
  // =======================================================
  function tick() {
    if (isPaused || video.readyState !== video.HAVE_ENOUGH_DATA) {
      requestAnimationFrame(tick);
      return;
    }

    // Vẽ frame video lên canvas
    canvasElement.height = video.videoHeight;
    canvasElement.width = video.videoWidth;
    canvasCtx.drawImage(video, 0, 0, canvasElement.width, canvasElement.height);

    // Lấy dữ liệu ảnh
    const imageData = canvasCtx.getImageData(0, 0, canvasElement.width, canvasElement.height);

    // Giải mã QR (jsQR)
    const code = jsQR(imageData.data, imageData.width, imageData.height, {
      inversionAttempts: "dontInvert",
    });

    if (code) {
      handleScanResult(code.data);
    } else {
      requestAnimationFrame(tick);
    }
  }

  // =======================================================
  //        XỬ LÝ KẾT QUẢ QUÉT
  // =======================================================
  function handleScanResult(rawData) {
    // Bỏ qua nếu mã này đã quét rồi
    if (scannedCodes.has(rawData)) return;

    // Tạm dừng quét để xử lý
    isPaused = true;

    // Regex trích xuất UUID
    const uuidMatch = rawData.match(/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})/i);

    if (uuidMatch && uuidMatch[1]) {
      const detailCode = uuidMatch[1].toLowerCase();

      // Kiểm tra mã có trong đơn hàng không
      if (Object.prototype.hasOwnProperty.call(detailCodes, detailCode)) {
        scannedCodes.add(rawData);

        // Cập nhật UI & Server
        updateUIOnScanSuccess(detailCode, detailCodes[detailCode].product_name);
        updateStockOnServer(detailCode);
      } else {
        showError("Invalid Item! This product is not in the current order.");
      }
    } else {
      showError("Invalid QR Format.");
    }
  }

  // =======================================================
  //        CẬP NHẬT GIAO DIỆN (UI HELPER)
  // =======================================================
  function hideAllFeedbacks() {
    fbDefault.classList.add("d-none");
    fbSuccess.classList.add("d-none");
    fbError.classList.add("d-none");
    fbComplete.classList.add("d-none");
  }

  function showError(message) {
    hideAllFeedbacks();
    if (fbErrorMessage) fbErrorMessage.textContent = message;
    fbError.classList.remove("d-none");

    // Tự động ẩn lỗi sau 2.5s và tiếp tục quét
    setTimeout(() => {
      hideAllFeedbacks();
      fbDefault.classList.remove("d-none");
      isPaused = false;
      requestAnimationFrame(tick);
    }, 2500);
  }

  function updateUIOnScanSuccess(detailCode, productName) {
    hideAllFeedbacks();
    if (fbSuccessProductName) fbSuccessProductName.textContent = productName;
    fbSuccess.classList.remove("d-none");

    // Đánh dấu dòng sản phẩm trong danh sách
    const listItem = productList.querySelector(`[data-code="${detailCode}"]`);
    if (listItem) {
      listItem.classList.add("list-group-item-success");
      const icon = listItem.querySelector(".status-icon");
      if (icon) {
        icon.className = "status-icon text-success";
        icon.innerHTML = '<i class="fas fa-check-circle"></i>';
      }
    }
  }

  // =======================================================
  //        GỌI API (SERVER UPDATE)
  // =======================================================
  async function updateStockOnServer(detailCode) {
    const apiUrl = stockInProcessApiUrl.replace("00000000-0000-0000-0000-000000000000", detailCode);

    try {
      const response = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) throw new Error(`Server Error: ${response.status}`);

      const result = await response.json();
      console.log("Server Response:", result.message);

      // Kiểm tra hoàn tất đơn hàng
      if (scannedCodes.size === Object.keys(detailCodes).length) {
        hideAllFeedbacks();
        fbComplete.classList.remove("d-none");

        if (stream) {
          stream.getTracks().forEach((track) => track.stop());
          stream = null;
        }

        setTimeout(() => (window.location.href = redirectUrlAfterCompletion), 2000);
      } else {
        setTimeout(() => {
          hideAllFeedbacks();
          fbDefault.classList.remove("d-none");
          isPaused = false;
          requestAnimationFrame(tick);
        }, 1500);
      }
    } catch (error) {
      console.error("Update Stock Error:", error);
      showError(`Update Failed: ${error.message}`);
    }
  }
});
