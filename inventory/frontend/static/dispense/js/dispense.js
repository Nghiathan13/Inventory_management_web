document.addEventListener("DOMContentLoaded", function () {
  const scannerModalElement = document.getElementById("qr-scanner-modal");
  const video = document.getElementById("qr-video");
  const feedback = document.getElementById("qr-scan-feedback");

  if (!scannerModalElement || !video || !feedback) return;

  const scannerModal = new bootstrap.Modal(scannerModalElement);
  let stream;
  let animationFrameId;

  function tick() {
    if (video.readyState === video.HAVE_ENOUGH_DATA) {
      const canvasElement = document.createElement("canvas");
      canvasElement.height = video.videoHeight;
      canvasElement.width = video.videoWidth;
      const canvas = canvasElement.getContext("2d");
      canvas.drawImage(video, 0, 0, canvasElement.width, canvasElement.height);
      const imageData = canvas.getImageData(0, 0, canvasElement.width, canvasElement.height);

      const code = jsQR(imageData.data, imageData.width, imageData.height, {
        inversionAttempts: "dontInvert",
      });

      if (code) {
        const scannedData = code.data;
        if (scannedData.includes("dispense/process")) {
          feedback.textContent = "Đã tìm thấy Toa Thuốc! Đang chuyển hướng...";
          feedback.className = "text-success fw-bold";

          stopScanning();
          window.location.href = scannedData;
          return;
        } else if (scannedData.includes("stock-in")) {
          // Nếu quét nhầm mã nhập hàng
          feedback.textContent = "Lỗi: Đây là mã Nhập hàng (PO), không phải Toa thuốc!";
          feedback.className = "text-danger fw-bold";
        } else {
          // Mã không xác định
          feedback.textContent = "Lỗi: Mã QR không hợp lệ hoặc không thuộc hệ thống.";
          feedback.className = "text-danger fw-bold";
        }
      }
    }
    animationFrameId = requestAnimationFrame(tick);
  }

  function startScanning() {
    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: "environment" } })
      .then(function (s) {
        stream = s;
        video.srcObject = stream;
        video.setAttribute("playsinline", true);
        video.play();

        feedback.textContent = "Hướng camera vào mã QR Toa Thuốc...";
        feedback.className = "text-muted";

        animationFrameId = requestAnimationFrame(tick);
      })
      .catch(function (err) {
        console.error(err);
        feedback.textContent = "Không thể truy cập camera.";
        feedback.className = "text-danger";
      });
  }

  function stopScanning() {
    if (animationFrameId) cancelAnimationFrame(animationFrameId);
    if (stream) stream.getTracks().forEach((track) => track.stop());
  }

  scannerModalElement.addEventListener("show.bs.modal", startScanning);
  scannerModalElement.addEventListener("hidden.bs.modal", stopScanning);
});
