let pickingQueue = [];
let currentIndex = 0;
let isCarouselMoving = false;

document.addEventListener("DOMContentLoaded", function () {
  // Gắn sự kiện click cho nút Start
  const btnStart = document.getElementById("btn-start-picking");
  if (btnStart) btnStart.addEventListener("click", startPickingProcess);

  // Polling trạng thái kệ
  setInterval(checkCarouselStatus, 2000);
});

// -------------------------------------------------------
// 1. BẮT ĐẦU QUY TRÌNH
// -------------------------------------------------------
function startPickingProcess() {
  const btnStart = document.getElementById("btn-start-picking");
  const btnBack = document.getElementById("btn-back-top"); // Nút Back

  // UI Update
  btnStart.disabled = true;
  btnStart.querySelector(".js-btn-text").classList.add("d-none");
  btnStart.querySelector(".js-btn-loading").classList.remove("d-none");

  // Ẩn nút Back khi bắt đầu
  if (btnBack) btnBack.classList.add("d-none");

  fetch(URLS.calcPath)
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "ok") {
        pickingQueue = data.path;
        const placeholder = document.querySelector(".js-placeholder");
        if (placeholder) placeholder.classList.add("d-none");

        renderQueue();

        if (pickingQueue.length > 0) {
          moveCarouselToItem(0);
        }
      } else {
        alert("Lỗi: " + data.message);
        btnStart.disabled = false;
        // Hiện lại nút Back nếu lỗi
        if (btnBack) btnBack.classList.remove("d-none");
      }
    });
}

// -------------------------------------------------------
// 2. RENDER DANH SÁCH TỪ TEMPLATE
// -------------------------------------------------------
function renderQueue() {
  const container = document.getElementById("picking-queue");
  const template = document.getElementById("picking-item-template");

  // Clear old items
  Array.from(container.children).forEach((child) => {
    if (!child.classList.contains("js-placeholder")) container.removeChild(child);
  });

  pickingQueue.forEach((item, index) => {
    const clone = template.content.cloneNode(true);
    const rootItem = clone.querySelector(".picking-item");

    // --- ĐIỀN DỮ LIỆU MỚI ---
    clone.querySelector(".js-product-name").textContent = item.product_name;
    clone.querySelector(".js-item-shelf").textContent = item.shelf_name;
    clone.querySelector(".js-item-level").textContent = item.tray_level;

    // Số lượng cần lấy ở bước này
    clone.querySelector(".js-item-quantity").textContent = `${item.required_qty} ${item.uom}`;

    // Số lượng tồn kho tại kệ này (MỚI)
    clone.querySelector(".js-stock-at-shelf").textContent = `${item.stock_at_shelf} ${item.uom}`;

    // Nếu đây chưa phải bước cuối của thuốc này -> Hiện thông báo Split
    if (!item.is_last_step) {
      clone.querySelector(".js-split-msg").classList.remove("d-none");
    }

    // --- LOGIC ẨN HIỆN NÚT ---
    const iconPending = clone.querySelector(".js-icon-pending");
    const iconActive = clone.querySelector(".js-icon-active");
    const iconDone = clone.querySelector(".js-icon-done");
    const btnConfirm = clone.querySelector(".js-btn-confirm");
    const btnUndo = clone.querySelector(".js-btn-undo");
    const textConfirm = clone.querySelector(".js-text-confirm");
    const textWait = clone.querySelector(".js-text-wait");

    if (item.is_picked) {
      rootItem.classList.add("done");
      iconDone.classList.remove("d-none");
      btnUndo.classList.remove("d-none");
      btnUndo.onclick = () => undoItem(index);
    } else if (index === currentIndex) {
      rootItem.classList.add("active");
      iconActive.classList.remove("d-none");
      btnConfirm.classList.remove("d-none");

      if (isCarouselMoving) {
        btnConfirm.disabled = true;
        textConfirm.classList.add("d-none");
        textWait.classList.remove("d-none");
      } else {
        btnConfirm.disabled = false;
        textConfirm.classList.remove("d-none");
        textWait.classList.add("d-none");
      }
      btnConfirm.onclick = () => confirmItem(index);
    } else {
      iconPending.classList.remove("d-none");
    }

    container.appendChild(clone);
  });

  // Check hoàn thành tất cả
  const allDone = pickingQueue.length > 0 && pickingQueue.every((i) => i.is_picked);
  const btnComplete = document.getElementById("btn-complete");
  const btnBack = document.getElementById("btn-back-top");

  if (btnComplete) {
    btnComplete.disabled = !allDone;
    if (allDone) {
      btnComplete.classList.remove("btn-secondary");
      btnComplete.classList.add("btn-success", "pulse-animation");
      // Hiện lại nút Back khi xong hết
      if (btnBack) btnBack.classList.remove("d-none");
    } else {
      btnComplete.classList.remove("btn-success", "pulse-animation");
      btnComplete.classList.add("btn-secondary");
    }
  }
}

// -------------------------------------------------------
// 3. DI CHUYỂN KỆ
// -------------------------------------------------------
function moveCarouselToItem(index) {
  if (index >= pickingQueue.length) return;
  const item = pickingQueue[index];
  const targetShelf = item.shelf_name;
  isCarouselMoving = true;
  renderQueue();
  const formData = new FormData();
  formData.append("shelf_name", targetShelf);
  fetch(URLS.moveCarousel, {
    method: "POST",
    headers: { "X-CSRFToken": CSRF_TOKEN },
    body: formData,
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.status !== "ok") {
        alert("Error moving: " + data.message);
        isCarouselMoving = false;
        renderQueue();
      }
    });
}

// -------------------------------------------------------
// 4. CONFIRM (LẤY THUỐC)
// -------------------------------------------------------
function confirmItem(index) {
  const item = pickingQueue[index];
  fetch(URLS.confirmPick, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": CSRF_TOKEN },
    body: JSON.stringify({ location_id: item.location_id, quantity: item.required_qty, detail_id: item.detail_id }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "ok") {
        pickingQueue[index].is_picked = true;
        currentIndex++;
        renderQueue();
        if (currentIndex < pickingQueue.length) {
          moveCarouselToItem(currentIndex);
        } else {
          alert("All items picked! Please verify and click Complete.");
        }
      } else {
        alert(data.message);
      }
    });
}

// -------------------------------------------------------
// 5. UNDO (HOÀN TÁC)
// -------------------------------------------------------
function undoItem(index) {
  if (!confirm("Undo this pick?")) return;
  const item = pickingQueue[index];
  fetch(URLS.undoPick, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": CSRF_TOKEN },
    body: JSON.stringify({ location_id: item.location_id, quantity: item.required_qty }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "ok") {
        pickingQueue[index].is_picked = false;
        currentIndex = index;
        moveCarouselToItem(index);
      } else {
        alert(data.message);
      }
    });
}

// -------------------------------------------------------
// 6. POLLING TRẠNG THÁI
// -------------------------------------------------------
function checkCarouselStatus() {
  fetch(URLS.carouselStatus)
    .then((res) => res.json())
    .then((data) => {
      const shelfDisplay = document.getElementById("current-shelf-display");
      const badgeIdle = document.getElementById("status-idle");
      const badgeMoving = document.getElementById("status-moving");
      const badgeReady = document.getElementById("status-ready");

      if (shelfDisplay) shelfDisplay.textContent = data.current_shelf;

      // Ẩn tất cả badge
      if (badgeIdle) badgeIdle.classList.add("d-none");
      if (badgeMoving) badgeMoving.classList.add("d-none");
      if (badgeReady) badgeReady.classList.add("d-none");

      if (data.is_moving) {
        if (badgeMoving) badgeMoving.classList.remove("d-none");
        isCarouselMoving = true;
      } else {
        if (badgeReady) badgeReady.classList.remove("d-none");

        // Kệ vừa dừng lại -> update UI để enable nút lấy thuốc
        if (isCarouselMoving) {
          isCarouselMoving = false;
          renderQueue();
        }
      }
    })
    .catch((err) => console.log("Polling inactive"));
}
