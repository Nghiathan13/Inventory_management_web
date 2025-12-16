document.addEventListener("DOMContentLoaded", function () {
  // =======================================================
  //        KHAI BÁO DOM & BIẾN
  // =======================================================
  const scannerModalElement = document.getElementById("qr-scanner-modal");
  const video = document.getElementById("qr-video");
  const feedback = document.getElementById("qr-scan-feedback");

  if (!scannerModalElement || !video || !feedback) {
    console.error("Error: Scanner elements missing.");
    return;
  }

  const scannerModal = new bootstrap.Modal(scannerModalElement);

  let stream = null;
  let animationFrameId = null;
  let isScanning = false;

  const canvasElement = document.createElement("canvas");
  const canvasCtx = canvasElement.getContext("2d", { willReadFrequently: true });

  // =======================================================
  //        VÒNG LẶP QUÉT (SCAN LOOP)
  // =======================================================
  function tick() {
    if (!isScanning) return;

    if (video.readyState === video.HAVE_ENOUGH_DATA) {
      canvasElement.height = video.videoHeight;
      canvasElement.width = video.videoWidth;
      canvasCtx.drawImage(video, 0, 0, canvasElement.width, canvasElement.height);

      const imageData = canvasCtx.getImageData(0, 0, canvasElement.width, canvasElement.height);
      const code = jsQR(imageData.data, imageData.width, imageData.height, {
        inversionAttempts: "dontInvert",
      });

      if (code) {
        handleScanSuccess(code.data);
        return;
      }
    }

    animationFrameId = requestAnimationFrame(tick);
  }

  // =======================================================
  //        XỬ LÝ KẾT QUẢ
  // =======================================================
  function handleScanSuccess(url) {
    feedback.textContent = "QR Code Found! Redirecting...";
    feedback.className = "text-success fw-bold";

    stopScanning();
    window.location.href = url;
  }

  // =======================================================
  //        ĐIỀU KHIỂN CAMERA
  // =======================================================
  function startScanning() {
    isScanning = true;

    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: "environment" } })
      .then((s) => {
        stream = s;
        video.srcObject = s;
        video.setAttribute("playsinline", true);
        video.play();

        feedback.textContent = "Point camera at the QR code...";
        feedback.className = "text-muted";

        animationFrameId = requestAnimationFrame(tick);
      })
      .catch((err) => {
        console.error("Camera Error:", err);
        scannerModal.hide();
        handleCameraError(err);
      });
  }

  function stopScanning() {
    isScanning = false;
    if (animationFrameId) cancelAnimationFrame(animationFrameId);

    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      stream = null;
      video.srcObject = null;
    }
  }

  function handleCameraError(err) {
    setTimeout(() => {
      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        alert("Camera access denied. Please update browser settings.");
      } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
        alert("No camera found.");
      } else {
        alert(`Camera Error: ${err.name}`);
      }
    }, 500);
  }

  // =======================================================
  //        SỰ KIỆN MODAL (EVENTS)
  // =======================================================

  scannerModalElement.addEventListener("shown.bs.modal", startScanning);
  scannerModalElement.addEventListener("hidden.bs.modal", stopScanning);
});
