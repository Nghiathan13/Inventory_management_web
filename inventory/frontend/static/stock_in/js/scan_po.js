document.addEventListener("DOMContentLoaded", function () {
  // =======================================================
  //        KHAI BÁO DOM & BIẾN
  // =======================================================
  const video = document.getElementById("qr-video");
  const qrScanFeedback = document.getElementById("qr-scan-feedback");
  const qrScannerModalElement = document.getElementById("qr-scanner-modal");

  if (!video || !qrScanFeedback || !qrScannerModalElement) return;

  const qrScannerModal = new bootstrap.Modal(qrScannerModalElement);
  let stream = null;
  let animationFrameId; // Thêm biến để quản lý loop

  // Hàm vẽ khung đỏ (Tùy chọn, giữ lại từ code trước của bạn nếu muốn)
  const canvasElement = document.createElement("canvas");
  const canvas = canvasElement.getContext("2d");

  qrScannerModalElement.addEventListener("shown.bs.modal", function () {
    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: "environment" } })
      .then(function (s) {
        stream = s;
        video.srcObject = stream;
        video.setAttribute("playsinline", true);
        video.play();

        qrScanFeedback.textContent = "Hướng camera vào mã QR Phiếu Giao Hàng...";
        qrScanFeedback.className = "text-muted mt-3";

        requestAnimationFrame(tick);
      })
      .catch(function (err) {
        qrScanFeedback.textContent = "Lỗi Camera: " + err.name;
        qrScanFeedback.className = "alert alert-danger";
      });
  });

  qrScannerModalElement.addEventListener("hidden.bs.modal", function () {
    if (stream) stream.getTracks().forEach((track) => track.stop());
    cancelAnimationFrame(animationFrameId); // Dừng loop khi đóng modal
  });

  // =======================================================
  //        HÀM XỬ LÝ QUÉT (SCAN LOGIC)
  // =======================================================
  function tick() {
    if (video.readyState === video.HAVE_ENOUGH_DATA) {
      canvasElement.height = video.videoHeight;
      canvasElement.width = video.videoWidth;
      canvas.drawImage(video, 0, 0, canvasElement.width, canvasElement.height);
      const imageData = canvas.getImageData(0, 0, canvasElement.width, canvasElement.height);

      const code = jsQR(imageData.data, imageData.width, imageData.height, {
        inversionAttempts: "dontInvert",
      });

      if (code) {
        const scannedData = code.data;

        // === LOGIC VALIDATION MỚI ===
        // URL mẫu: .../inventory/stock-in/receive/UUID/
        if (scannedData.includes("stock-in/receive")) {
          qrScanFeedback.textContent = "Đã tìm thấy Đơn Nhập Hàng! Đang chuyển hướng...";
          qrScanFeedback.className = "alert alert-success fw-bold";

          if (stream) stream.getTracks().forEach((track) => track.stop());

          window.location.href = scannedData;
          return;
        } else if (scannedData.includes("dispense")) {
          // Nếu quét nhầm mã toa thuốc
          qrScanFeedback.textContent = "Lỗi: Đây là mã Toa thuốc, không phải Phiếu Giao Hàng (PO)!";
          qrScanFeedback.className = "alert alert-danger fw-bold";
        } else {
          // Mã rác
          qrScanFeedback.textContent = "Lỗi: Mã QR không hợp lệ.";
          qrScanFeedback.className = "alert alert-danger fw-bold";
        }
      }
    }
    animationFrameId = requestAnimationFrame(tick);
  }

  function handleQrFound(data) {
    isScanning = false;
    stopCamera();

    qrScanFeedback.textContent = "QR Code detected! Redirecting...";
    qrScanFeedback.className = "alert alert-success";
    qrScanFeedback.style.display = "block";

    console.log("QR Data:", data);
    setTimeout(() => {
      window.location.href = data;
    }, 500);
  }

  // =======================================================
  //        HÀM ĐIỀU KHIỂN CAMERA
  // =======================================================
  function startCamera() {
    qrScanFeedback.textContent = "Starting camera...";
    qrScanFeedback.className = "text-muted";

    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: "environment" } })
      .then(function (s) {
        stream = s;
        video.srcObject = stream;
        video.setAttribute("playsinline", true);
        video.play();

        isScanning = true;
        requestAnimationFrame(tick);

        qrScanFeedback.textContent = "Point camera at the QR code...";
      })
      .catch(function (err) {
        console.error("Camera Error:", err);
        qrScanFeedback.textContent = "Error: Camera access denied. Please allow permissions.";
        qrScanFeedback.className = "alert alert-danger";
      });
  }

  function stopCamera() {
    isScanning = false;
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      stream = null;
    }
  }

  // =======================================================
  //        SỰ KIỆN MODAL (BOOTSTRAP EVENTS)
  // =======================================================
  qrScannerModalElement.addEventListener("shown.bs.modal", startCamera);
  qrScannerModalElement.addEventListener("hidden.bs.modal", stopCamera);
});
