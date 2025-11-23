document.addEventListener("DOMContentLoaded", function () {
  const scannerModalElement = document.getElementById("qr-scanner-modal");
  const video = document.getElementById("qr-video");
  const feedback = document.getElementById("qr-scan-feedback");

  // Thoát sớm nếu các phần tử cần thiết không tồn tại
  if (!scannerModalElement || !video || !feedback) {
    return;
  }

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
        // Nếu tìm thấy mã QR
        feedback.textContent = "Đã tìm thấy mã! Đang chuyển hướng...";
        feedback.classList.remove("text-muted");
        feedback.classList.add("text-success");

        stopScanning(); // Dừng camera ngay lập tức

        // Chuyển hướng đến URL trong mã QR
        window.location.href = code.data;
        return; // Dừng vòng lặp quét
      }
    }
    // Tiếp tục quét ở frame tiếp theo
    animationFrameId = requestAnimationFrame(tick);
  }

  /**
   * Bắt đầu quá trình quét: bật camera và khởi động vòng lặp tick().
   */
  function startScanning() {
    // Yêu cầu quyền truy cập camera
    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: "environment" } })
      .then(function (s) {
        stream = s;
        video.srcObject = stream;
        video.setAttribute("playsinline", true);
        video.play();

        // Reset thông báo
        feedback.textContent = "Hướng camera của bạn vào mã QR...";
        feedback.classList.add("text-muted");
        feedback.classList.remove("text-success");

        // Bắt đầu vòng lặp quét
        animationFrameId = requestAnimationFrame(tick);
      })
      .catch(function (err) {
        console.error("Lỗi Camera:", err);
        scannerModal.hide(); // Ẩn modal nếu có lỗi
        alert(
          "Không thể truy cập camera. Vui lòng kiểm tra quyền truy cập trong cài đặt trình duyệt."
        );
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
    }
  }

  // Gắn sự kiện vào Modal của Bootstrap
  // Khi modal bắt đầu được MỞ
  scannerModalElement.addEventListener("show.bs.modal", function () {
    startScanning();
  });

  // Khi modal đã được ĐÓNG (bằng bất kỳ cách nào)
  scannerModalElement.addEventListener("hidden.bs.modal", function () {
    stopScanning();
  });
});
