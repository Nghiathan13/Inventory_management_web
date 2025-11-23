document.addEventListener("DOMContentLoaded", function () {
  const video = document.getElementById("qr-video");
  const qrScanFeedback = document.getElementById("qr-scan-feedback");
  const qrScannerModalElement = document.getElementById("qr-scanner-modal");

  // Kiểm tra xem các element có tồn tại không
  if (!video || !qrScanFeedback || !qrScannerModalElement) {
    console.error(
      "Một trong các element cần thiết cho QR scanner không tồn tại."
    );
    return;
  }

  const qrScannerModal = new bootstrap.Modal(qrScannerModalElement);
  let stream = null;

  // Sự kiện được kích hoạt khi modal bắt đầu hiển thị
  qrScannerModalElement.addEventListener("shown.bs.modal", function () {
    // Yêu cầu truy cập camera sau của thiết bị
    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: "environment" } })
      .then(function (s) {
        stream = s;
        video.srcObject = stream;
        video.play();
        // Bắt đầu vòng lặp quét
        requestAnimationFrame(tick);
      })
      .catch(function (err) {
        console.error("Không thể truy cập camera:", err);
        qrScanFeedback.textContent =
          "Lỗi: Không thể truy cập camera. Vui lòng cấp quyền trong trình duyệt.";
        qrScanFeedback.className = "alert alert-danger";
      });
  });

  // Sự kiện được kích hoạt khi modal đã được đóng hoàn toàn
  qrScannerModalElement.addEventListener("hidden.bs.modal", function () {
    // Dừng stream camera để tắt đèn và tiết kiệm pin
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
    }
  });

  function tick() {
    // Chỉ xử lý khi video đã sẵn sàng
    if (video.readyState === video.HAVE_ENOUGH_DATA) {
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

      // Sử dụng thư viện jsQR để tìm mã trong ảnh
      const code = jsQR(imageData.data, imageData.width, imageData.height, {
        inversionAttempts: "dontInvert",
      });

      if (code) {
        // --- ĐÃ TÌM THẤY MÃ QR ---

        // Dừng camera
        stream.getTracks().forEach((track) => track.stop());

        // Cung cấp phản hồi cho người dùng
        qrScanFeedback.textContent = `Đã tìm thấy mã! Đang chuyển hướng...`;
        qrScanFeedback.className = "alert alert-success";

        // Chuyển hướng trình duyệt đến URL chứa trong mã QR
        window.location.href = code.data;

        return; // Dừng vòng lặp quét
      }
    }
    // Tiếp tục quét ở frame tiếp theo
    requestAnimationFrame(tick);
  }
});
