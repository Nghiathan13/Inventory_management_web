// --- Biến toàn cục ---
let pickingQueue = [];
let currentIndex = 0;
let isBusy = false; // Khóa UI khi máy chạy
let socket = null;
let isWaitingForStoreCompletion = false; // Cờ chờ máy cất xong

// --- Khởi tạo ---
document.addEventListener("DOMContentLoaded", function () {
  initWebSocket();

  const btnStart = document.getElementById("btn-start-picking");
  if (btnStart) btnStart.addEventListener("click", startPickingProcess);

  // Polling trạng thái mỗi 500ms
  setInterval(checkCarouselStatus, 500);
});

// =======================================================
//  1. WEBSOCKET (GIAO TIẾP THỜI GIAN THỰC)
// =======================================================
function initWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
  const wsUrl = protocol + window.location.host + "/ws/control/";

  socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    console.log("WS Connected");
  };

  socket.onmessage = (e) => {
    const data = JSON.parse(e.data);

    // 1. FETCH_COMPLETE
    if (data.type === "UPDATE_FETCH") {
      isBusy = false;
      updateStatusBadge("Waiting for Pick", "primary");
      renderQueue();
    }

    // 2. STORE_COMPLETE (Worker báo xong -> Tự động chuyển tiếp)
    else if (data.type === "UPDATE_STORE") {
      console.log("Store Complete via Event. Next...");

      // Tự động chuyển món
      triggerNextItem();
    }

    // 3. STORE_STARTED
    else if (data.type === "STORE_STARTED") {
      updateStatusBadge("Storing...", "warning");
    }
  };
}
// =======================================================
//  2. POLLING (CHECK TRẠNG THÁI & TỰ ĐỘNG CHUYỂN)
// =======================================================
function checkCarouselStatus() {
  fetch(URLS.carouselStatus)
    .then((res) => res.json())
    .then((data) => {
      // 1. Cập nhật tên kệ
      const shelfDisplay = document.getElementById("current-shelf-display");
      if (shelfDisplay) shelfDisplay.innerText = data.current_shelf;

      // 2. LOGIC TỰ ĐỘNG CHUYỂN MÓN TIẾP THEO
      // Điều kiện: Đang chờ cất + Dropoff trống + Máy đã dừng
      if (isWaitingForStoreCompletion && !data.dropoff_data && !data.is_moving) {
        console.log(">> Cất xong. Chuyển sang món tiếp theo...");
        isWaitingForStoreCompletion = false; // Tắt cờ
        triggerNextItem(); // Gọi món tiếp
      }

      // 3. CẬP NHẬT BADGE TRẠNG THÁI (FIX LỖI HIỆN 2 CÁI)
      const sIdle = document.getElementById("status-idle");
      const sMoving = document.getElementById("status-moving");
      const sReady = document.getElementById("status-ready");

      // Ẩn tất cả trước
      if (sIdle) sIdle.classList.add("d-none");
      if (sMoving) sMoving.classList.add("d-none");
      if (sReady) sReady.classList.add("d-none");

      // Chỉ hiện 1 cái đúng nhất
      if (data.is_moving) {
        sMoving.classList.remove("d-none"); // Đang chạy
      } else {
        // Nếu máy dừng, kiểm tra xem đang làm gì
        if (isWaitingForStoreCompletion) {
          // Máy vừa dừng nhưng logic chưa xong -> Vẫn coi là Moving hoặc Ready
          sMoving.classList.remove("d-none");
        } else {
          sReady.classList.remove("d-none"); // Rảnh rỗi
        }
      }
    })
    .catch(() => {});
}

// Chuyển sang món tiếp theo hoặc Kết thúc
function triggerNextItem() {
  currentIndex++; // Tăng index

  if (currentIndex < pickingQueue.length) {
    // Còn thuốc -> Lấy tiếp
    // Delay 500ms để Worker kịp ổn định trạng thái
    setTimeout(() => {
      fetchCurrentItem();
    }, 500);
  } else {
    // Hết thuốc -> Kết thúc
    isBusy = false;
    updateStatusBadge("All Done", "success");
    renderQueue();
    alert("🎉 Đã lấy xong toàn bộ đơn thuốc! Hãy ấn 'Complete & Finish'.");
  }
}

// =======================================================
//  3. LOGIC CHÍNH (START & FETCH)
// =======================================================

function startPickingProcess() {
  const btnStart = document.getElementById("btn-start-picking");
  if (btnStart) {
    btnStart.disabled = true;
    btnStart.querySelector(".js-btn-text").classList.add("d-none");
    btnStart.querySelector(".js-btn-loading").classList.remove("d-none");
  }
  document.getElementById("btn-back-top")?.classList.add("d-none");

  fetch(URLS.calcPath)
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "ok") {
        pickingQueue = data.path;
        document.querySelector(".js-placeholder")?.classList.add("d-none");
        currentIndex = 0;
        renderQueue();
        if (pickingQueue.length > 0) fetchCurrentItem();
        else alert("Đơn thuốc rỗng.");
      } else alert("Lỗi: " + data.message);
    });
}

// Gửi lệnh Lấy khay (FETCH)
function fetchCurrentItem() {
  if (currentIndex >= pickingQueue.length) return;
  const item = pickingQueue[currentIndex];

  scrollToItem(currentIndex);
  isBusy = true;
  updateStatusBadge(`Fetching ${currentIndex + 1}/${pickingQueue.length}...`, "warning");
  renderQueue();

  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ command: "FETCH", shelf: item.shelf_name, tray: item.tray_level }));
  }
}

// =======================================================
//  4. LOGIC XÁC NHẬN (CONFIRM & STORE)
// =======================================================

function confirmItem(index) {
  if (index !== currentIndex) return;
  const item = pickingQueue[index];

  // Update UI nút bấm
  const btn = document.querySelector(`.picking-item[data-index="${index}"] .js-btn-confirm`);
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
  }

  fetch(URLS.confirmPick, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": CSRF_TOKEN },
    body: JSON.stringify({
      location_id: item.location_id,
      quantity: item.required_qty,
      detail_id: item.detail_id,
      uom_id: item.uom_id, // <--- THÊM DÒNG NÀY: Gửi ID đơn vị hiển thị
    }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "ok") {
        pickingQueue[index].is_picked = true;
        if (socket && socket.readyState === WebSocket.OPEN) {
          isBusy = true;
          updateStatusBadge("Storing...", "warning");
          renderQueue();
          socket.send(JSON.stringify({ command: "AUTO_STORE", dropoff_id: 1 }));
        }
      } else {
        alert(data.message);
        renderQueue();
      }
    });
}

// =======================================================
//  5. RENDER UI & UTILS
// =======================================================
function renderQueue() {
  const container = document.getElementById("picking-queue");
  const template = document.getElementById("picking-item-template");
  Array.from(container.children).forEach((child) => {
    if (!child.classList.contains("js-placeholder")) container.removeChild(child);
  });

  pickingQueue.forEach((item, index) => {
    const clone = template.content.cloneNode(true);
    const root = clone.querySelector(".picking-item");
    root.setAttribute("data-index", index);
    clone.querySelector(".js-product-name").textContent = item.product_name;
    clone.querySelector(".js-item-shelf").textContent = item.shelf_name;
    clone.querySelector(".js-item-level").textContent = item.tray_level;
    clone.querySelector(".js-item-batch").textContent = item.batch_number;
    clone.querySelector(".js-item-quantity").textContent = `${item.required_qty} ${item.uom}`;
    clone.querySelector(".js-stock-at-shelf").textContent = `${item.stock_at_shelf} ${item.shelf_uom}`;

    const els = {
      pending: clone.querySelector(".js-icon-pending"),
      active: clone.querySelector(".js-icon-active"),
      done: clone.querySelector(".js-icon-done"),
      btnConfirm: clone.querySelector(".js-btn-confirm"),
      btnUndo: clone.querySelector(".js-btn-undo"),
    };
    Object.values(els).forEach((e) => e.classList.add("d-none"));

    if (item.is_picked) {
      root.classList.add("done");
      els.done.classList.remove("d-none");
      els.btnUndo.classList.remove("d-none");
      els.btnUndo.onclick = () => undoItem(index);
    } else if (index === currentIndex) {
      root.classList.add("active");
      if (isBusy) {
        els.active.classList.remove("d-none");
        els.btnConfirm.classList.remove("d-none");
        els.btnConfirm.disabled = true;
        els.btnConfirm.innerHTML = '<i class="fas fa-cog fa-spin"></i> Machine running...';
      } else {
        els.pending.classList.remove("d-none");
        els.btnConfirm.classList.remove("d-none");
        els.btnConfirm.disabled = false;
        els.btnConfirm.innerHTML = '<i class="fas fa-hand-holding-medical"></i> Confirm Picked';
        els.btnConfirm.onclick = () => confirmItem(index);
      }
    } else {
      els.pending.classList.remove("d-none");
    }
    container.appendChild(clone);
  });

  // Update nút Complete tổng
  const allDone = pickingQueue.length > 0 && pickingQueue.every((i) => i.is_picked);
  const btnComplete = document.getElementById("btn-complete");
  if (btnComplete) {
    btnComplete.disabled = !allDone;
    if (allDone) {
      btnComplete.classList.remove("btn-secondary");
      btnComplete.classList.add("btn-success");
    }
  }
}

// --- Helpers ---

function updateHardwareBadges(isMoving) {
  const sMoving = document.getElementById("status-moving");
  const sReady = document.getElementById("status-ready");
  if (!sMoving || !sReady) return;

  if (isMoving) {
    sMoving.classList.remove("d-none");
    sReady.classList.add("d-none");
  } else {
    sMoving.classList.add("d-none");
    sReady.classList.remove("d-none");
  }
}

function updateStatusBadge(text, color) {
  // Cập nhật text trạng thái nếu có element hiển thị (tùy chọn)
}

function toggleBtnLoading(btn, isLoading) {
  if (!btn) return;
  btn.disabled = isLoading;
  if (isLoading) {
    btn.querySelector(".js-btn-text").classList.add("d-none");
    btn.querySelector(".js-btn-loading").classList.remove("d-none");
  } else {
    btn.querySelector(".js-btn-text").classList.remove("d-none");
    btn.querySelector(".js-btn-loading").classList.add("d-none");
  }
}

function checkCompleteState() {
  const allDone = pickingQueue.length > 0 && pickingQueue.every((i) => i.is_picked);
  const btnComplete = document.getElementById("btn-complete");
  if (btnComplete) {
    btnComplete.disabled = !allDone;
    if (allDone) {
      btnComplete.classList.remove("btn-secondary");
      btnComplete.classList.add("btn-success", "pulse-animation");
      document.getElementById("btn-back-top")?.classList.remove("d-none");
    }
  }
}

function scrollToItem(index) {
  setTimeout(() => {
    const item = document.querySelector(`.picking-item[data-index="${index}"]`);
    if (item) item.scrollIntoView({ behavior: "smooth", block: "center" });
  }, 100);
}

function undoItem(index) {
  if (!confirm("Hoàn tác món này?")) return;
  const item = pickingQueue[index];
  fetch(URLS.undoPick, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": CSRF_TOKEN },
    body: JSON.stringify({ location_id: item.location_id, quantity: item.required_qty, detail_id: item.detail_id }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "ok") {
        pickingQueue[index].is_picked = false;
        currentIndex = index; // Quay lại món này
        fetchCurrentItem(); // Gọi máy lấy lại
      } else alert(data.message);
    });
}
