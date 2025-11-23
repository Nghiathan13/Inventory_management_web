document.addEventListener("DOMContentLoaded", function () {
  // === LẤY CÁC ELEMENT TỪ HTML ===
  const currentShelfDisplay = document.getElementById("current-shelf-display");
  const statusIndicator = document.getElementById("status-indicator");
  const statusText = document.getElementById("status-text");
  const homingBtn = document.getElementById("homing-btn");
  const moveButtonsContainer = document.getElementById("move-buttons");

  let animationInterval = null; // Biến để quản lý animation

  // === CÁC HÀM CẬP NHẬT GIAO DIỆN ===

  function updateFullUI(state) {
    currentShelfDisplay.textContent = state.current_shelf;
    document.querySelectorAll(".shelf-card").forEach((card) => card.classList.remove("active"));
    const activeCard = document.getElementById(`shelf-card-${state.current_shelf}`);
    if (activeCard) activeCard.classList.add("active");

    const isMoving = state.is_moving;
    homingBtn.disabled = isMoving;
    moveButtonsContainer.querySelectorAll(".move-btn").forEach((btn) => (btn.disabled = isMoving));

    if (isMoving) {
      statusIndicator.className = "status-moving";
      statusText.textContent = `Đang di chuyển đến ${state.target_shelf}...`;
    } else {
      statusIndicator.className = "status-ready";
      statusText.textContent = "Sẵn sàng";
      if (animationInterval) {
        clearInterval(animationInterval);
        animationInterval = null;
      }
    }
  }

  function animateMovement(fullPath, durationPerStep) {
    if (animationInterval) clearInterval(animationInterval);
    if (!fullPath || fullPath.length <= 1) return; // Không cần animate nếu chỉ có 1 điểm

    let currentStepIndex = 0;

    // Cập nhật giao diện ngay lập tức đến điểm bắt đầu
    updateVisualStep(fullPath[currentStepIndex]);
    currentStepIndex++;

    animationInterval = setInterval(() => {
      if (currentStepIndex >= fullPath.length) {
        clearInterval(animationInterval);
        animationInterval = null;
        setTimeout(fetchStatus, 100);
        return;
      }
      const nextShelf = fullPath[currentStepIndex];
      updateVisualStep(nextShelf);
      currentStepIndex++;
    }, durationPerStep);
  }

  // Hàm phụ chỉ để cập nhật hình ảnh, không thay đổi trạng thái nút
  function updateVisualStep(shelfName) {
    currentShelfDisplay.textContent = shelfName;
    document.querySelectorAll(".shelf-card").forEach((card) => card.classList.remove("active"));
    const activeCard = document.getElementById(`shelf-card-${shelfName}`);
    if (activeCard) activeCard.classList.add("active");
  }

  // === CÁC HÀM GỌI API ===

  async function postCommand(url, data) {
    if (animationInterval) return;

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken },
        body: data,
      });
      const result = await response.json();

      if (response.ok && result.status === "ok") {
        console.log("Server response:", result.message);

        // Cập nhật giao diện sang trạng thái "Đang di chuyển"
        updateFullUI({
          is_moving: true,
          current_shelf: result.start_shelf,
          target_shelf: result.target_shelf,
        });

        // SỬA ĐỔI: Xây dựng lộ trình đầy đủ và gọi animateMovement đúng cách
        const fullPath = [result.start_shelf, ...result.path];
        animateMovement(fullPath, result.duration_per_step);
      } else {
        alert(`Lỗi: ${result.message}`);
        fetchStatus();
      }
    } catch (error) {
      console.error("Connection Error:", error);
      alert("Lỗi kết nối đến server.");
      fetchStatus();
    }
  }

  async function fetchStatus() {
    if (animationInterval) return;
    try {
      const response = await fetch(URLS.getStatus);
      const state = await response.json();
      updateFullUI(state);
    } catch (error) {
      console.error("Lỗi khi lấy trạng thái:", error);
    }
  }

  // === GẮN SỰ KIỆN VÀ KHỞI CHẠY ===
  homingBtn.addEventListener("click", () => postCommand(URLS.homing, new FormData()));
  moveButtonsContainer.addEventListener("click", (e) => {
    if (e.target.classList.contains("move-btn")) {
      const formData = new FormData();
      formData.append("shelf_name", e.target.dataset.shelf);
      postCommand(URLS.moveToShelf, formData);
    }
  });

  setInterval(fetchStatus, 2000);
  fetchStatus();
});
