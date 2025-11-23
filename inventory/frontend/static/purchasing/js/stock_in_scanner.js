document.addEventListener("DOMContentLoaded", function () {
  const scannerModalElement = document.getElementById("qr-scanner-modal");
  const video = document.getElementById("qr-video");
  const feedback = document.getElementById("qr-scan-feedback");

  // Thoát sớm nếu các phần tử cần thiết không tồn tại
  if (!scannerModalElement || !video || !feedback) {
    console.error("Scanner elements not found on this page.");
    return;
  }

  // =======================================================
  //          THAY ĐỔI CHÍNH: Khởi tạo Modal bằng cú pháp Bootstrap 5
  // =======================================================
  const scannerModal = new bootstrap.Modal(scannerModalElement);

  let stream;
  let animationFrameId;

  /**
   * Vòng lặp liên tục quét ảnh từ video.
   */
  function tick() {
    if (video.readyState === video.HAVE_ENOUGH_DATA) {
      const canvasElement = document.createElement("canvas");
      canvasElement.height = video.videoHeight;
      canvasElement.width = video.videoWidth;
      const canvas = canvasElement.getContext("2d");
      canvas.drawImage(video, 0, 0, canvasElement.width, canvasElement.height);
      const imageData = canvas.getImageData(
        0,
        0,
        canvasElement.width,
        canvasElement.height
      );
      const code = jsQR(imageData.data, imageData.width, imageData.height, {
        inversionAttempts: "dontInvert",
      });

      if (code) {
        feedback.textContent = "Found QR Code! Redirecting...";
        feedback.classList.remove("text-muted");
        feedback.classList.add("text-success");

        stopScanning();
        window.location.href = code.data;
        return;
      }
    }
    animationFrameId = requestAnimationFrame(tick);
  }

  /**
   * Bắt đầu quá trình quét: bật camera và khởi động vòng lặp.
   */
  function startScanning() {
    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: "environment" } })
      .then((s) => {
        stream = s;
        video.srcObject = s;
        video.play();
        feedback.textContent = "Point your camera at the QR code...";
        feedback.classList.add("text-muted");
        feedback.classList.remove("text-success");
        animationFrameId = requestAnimationFrame(tick);
      })
      .catch((err) => {
        console.error("Camera Error:", err);
        // Đóng modal một cách an toàn bằng instance đã có
        scannerModal.hide();
        setTimeout(() => {
          if (
            err.name === "NotAllowedError" ||
            err.name === "PermissionDeniedError"
          ) {
            alert(
              "Camera access was denied. Please allow camera access in your browser settings and try again."
            );
          } else if (
            err.name === "NotFoundError" ||
            err.name === "DevicesNotFoundError"
          ) {
            alert("No camera found on your device.");
          } else {
            alert("Could not access camera. Error: " + err.name);
          }
        }, 500);
      });
  }

  /**
   * Dừng quá trình quét: tắt camera và dừng vòng lặp.
   */
  function stopScanning() {
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId);
    }
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      video.srcObject = null; // Giải phóng tài nguyên video
    }
  }

  // Gắn sự kiện vào Modal của Bootstrap 5
  // Khi modal bắt đầu được MỞ
  scannerModalElement.addEventListener("show.bs.modal", startScanning);

  // Khi modal đã được ĐÓNG (bằng bất kỳ cách nào)
  scannerModalElement.addEventListener("hidden.bs.modal", stopScanning);
});
