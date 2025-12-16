document.addEventListener("DOMContentLoaded", function () {
  // ============================================================
  // 1. KHỞI TẠO BIẾN & DOM ELEMENTS
  // ============================================================

  // --- Elements chính ---
  const statusSpan = document.getElementById("connection-status");
  const shelfDisplay = document.getElementById("current-shelf-display");
  const stateBadge = document.getElementById("system-state-badge");
  const carouselLayout = document.querySelector(".carousel-layout");
  const dropoffBox = document.getElementById("dropoff-1");

  // Biến lưu trạng thái hệ thống
  let isSystemMoving = false;

  // Lưu thông tin khay đang ở Dropoff: { shelf: 1, tray: 2 } (SỐ NGUYÊN)
  // Dùng để biết khi ấn nút Cất thì cất về đâu
  let currentDropoffItem = null;

  // --- Elements Modal (Cấu hình hàng hóa) ---
  const modalEl = document.getElementById("locationSettingsModal");
  let modalObj = null;
  if (modalEl) modalObj = new bootstrap.Modal(modalEl);

  const uiModal = {
    title: document.getElementById("locationModalLabel"),
    productSelect: $("#modal-product"), // jQuery object
    batchSelect: document.getElementById("modal-batch"),
    batchPanel: document.getElementById("batch-info-panel"),
    lblBatchName: document.getElementById("lblBatchName"),
    lblBatchExpiry: document.getElementById("lblBatchExpiry"),
    lblBatchTotal: document.getElementById("lblBatchTotal"),
    lblBatchAllocated: document.getElementById("lblBatchAllocated"),
    lblBatchUnallocated: document.getElementById("lblBatchUnallocated"),
    inputSection: document.getElementById("input-section"),
    inpCap: document.getElementById("modal-capacity"),
    selCapUom: document.getElementById("modal-capacity-uom"),
    inpQty: document.getElementById("modal-quantity"),
    selQtyUom: document.getElementById("modal-quantity-uom"),
    warningBox: document.getElementById("capacity-warning"),
    convertMsg: document.getElementById("convert-msg"),
    btnSave: document.getElementById("modal-save-btn"),
    btnRemove: document.getElementById("modal-remove-btn"),
  };

  // --- Dữ liệu từ Server (JSON Script) ---
  function parseData(id) {
    const el = document.getElementById(id);
    if (!el) return [];
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      return [];
    }
  }

  const allProducts = parseData("all-products-data");
  const uomsByCat = parseData("uoms-by-category-data");
  const initialLocations = parseData("all-locations-data");
  const allBoms = parseData("all-boms-data");

  // Map dữ liệu vị trí
  let locationMap = new Map();
  if (Array.isArray(initialLocations)) {
    locationMap = new Map(initialLocations.map((loc) => [loc.tray_id.toString(), loc]));
  }

  // Biến trạng thái cục bộ cho Modal
  let currentBatchesData = [];
  let currentProductInfo = null;
  let activeTrayId = null;

  // ============================================================
  // 2. WEBSOCKET & LOGIC ĐIỀU KHIỂN
  // ============================================================

  const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
  const socket = new WebSocket(protocol + window.location.host + "/ws/control/");

  socket.onopen = () => {
    if (statusSpan) {
      statusSpan.innerText = "Online";
      statusSpan.className = "badge bg-success";
    }
    console.log("WebSocket Connected");
    if (!isSystemMoving) {
      setSystemState(false);
    }
  };

  socket.onmessage = (e) => {
    const data = JSON.parse(e.data);
    console.log("WS RX:", data);

    // --- 1. UPDATE VỊ TRÍ KỆ REAL-TIME (Cảm biến/Simulation) ---
    if (data.type === "shelf_update") {
      const currentShelfNum = data.shelf;

      // Cập nhật text hiển thị
      if (shelfDisplay) shelfDisplay.innerText = "Kệ " + currentShelfNum;

      // Highlight thẻ kệ tương ứng trong danh sách
      document.querySelectorAll(".shelf-card").forEach((c) => c.classList.remove("active"));
      const activeCard = document.getElementById(`shelf-card-${currentShelfNum}`);
      if (activeCard) {
        activeCard.classList.add("active");
        // Tự động cuộn tới kệ đang active
        activeCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
    }

    // --- 2. KHI LẤY XONG (FETCH COMPLETE) ---
    else if (data.type === "UPDATE_FETCH") {
      setSystemState(false); // Tắt badge MOVING
      updateTrayVisual(data.shelf, data.tray, true);

      // Lúc này Dropoff có hàng -> Gọi isActive = true
      // Icon sẽ thành cái hộp tĩnh, không xoay nữa
      const labelText = `Kệ ${data.shelf} - Tầng ${data.tray}`;
      updateDropoffVisual(true, labelText);

      currentDropoffItem = {
        shelf: parseInt(data.shelf),
        tray: parseInt(data.tray),
      };
    }

    // --- 3. KHI CẤT XONG (STORE COMPLETE) ---
    else if (data.type === "UPDATE_STORE") {
      setSystemState(false); // Tắt badge MOVING
      updateTrayVisual(data.shelf, data.tray, false);

      // Reset Dropoff -> Gọi isActive = false
      // Icon sẽ thành hộp mở tĩnh, không xoay nữa
      updateDropoffVisual(false, "TRỐNG");

      currentDropoffItem = null;
    } else if (data.type === "HOMING_COMPLETE") {
      console.log("Homing Done -> Reset to Ready");
      setSystemState(false); // <--- QUAN TRỌNG: Lệnh này tắt chữ MOVING

      // Cập nhật lại số kệ (nếu server có gửi kèm)
      if (data.shelf) {
        if (shelfDisplay) shelfDisplay.innerText = "Kệ " + data.shelf;

        // Highlight lại thẻ kệ
        document.querySelectorAll(".shelf-card").forEach((c) => c.classList.remove("active"));
        const activeCard = document.getElementById(`shelf-card-${data.shelf}`);
        if (activeCard) {
          activeCard.classList.add("active");
          activeCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
      }
    }

    // --- 4. TRẠNG THÁI MOVING ---
    else if (data.type === "SYSTEM_MOVING") {
      setSystemState(true);
    }
    // --- 5. BÁO LỖI ---
    else if (data.type === "ERROR") {
      alert("Lỗi: " + data.message);
      setSystemState(false);
    }
  };

  socket.onclose = () => {
    if (statusSpan) {
      statusSpan.innerText = "Offline";
      statusSpan.className = "badge bg-danger";
    }
  };

  // --- Helper Set Trạng Thái Visual ---

  function updateTrayVisual(shelfNum, trayNum, isOut) {
    // ID HTML: tray-1-1 (Số)
    const elId = `tray-${shelfNum}-${trayNum}`;
    const el = document.getElementById(elId);

    if (el) {
      if (isOut) {
        el.classList.add("is-out"); // Class làm mờ
        // Thêm badge OUT nếu chưa có
        let badge = el.querySelector(".status-badge-out");
        if (!badge) {
          badge = document.createElement("div");
          badge.className = "status-badge-out position-absolute top-50 start-50 translate-middle badge bg-danger";
          badge.innerText = "OUT";
          el.appendChild(badge);
        }
      } else {
        el.classList.remove("is-out"); // Class bình thường
        const badge = el.querySelector(".status-badge-out");
        if (badge) badge.remove();
      }
    }
  }

  function updateDropoffVisual(isActive, text) {
    if (!dropoffBox) return;
    const contentText = dropoffBox.querySelector(".content-text");
    const icon = dropoffBox.querySelector(".icon-state");

    // Reset sạch class của icon trước khi gán mới
    if (icon) icon.className = "";

    if (isActive) {
      // --- CÓ HÀNG (Sáng vàng) ---
      dropoffBox.classList.add("occupied", "bg-warning", "text-dark");
      dropoffBox.classList.remove("bg-light", "text-muted");

      if (contentText) contentText.innerText = text;

      // Icon: Hộp đóng (Tĩnh)
      if (icon) icon.className = "fas fa-box fa-2x mb-2 icon-state";
    } else {
      // --- TRỐNG (Màu xám) ---
      dropoffBox.classList.remove("occupied", "bg-warning", "text-dark");
      dropoffBox.classList.add("bg-light", "text-muted");

      if (contentText) contentText.innerText = "TRỐNG";

      // Icon: Hộp mở nắp (Tĩnh)
      if (icon) icon.className = "fas fa-box-open fa-2x mb-2 icon-state";
    }
  }

  function setSystemState(moving) {
    isSystemMoving = moving;
    if (stateBadge) {
      if (moving) {
        stateBadge.innerHTML =
          '<span class="badge bg-warning text-dark px-3 py-2"><i class="fas fa-spinner fa-spin"></i> MOVING...</span>';
        carouselLayout.classList.add("system-locked"); // CSS chặn click
      } else {
        stateBadge.innerHTML = '<span class="badge bg-success px-3 py-2">READY</span>';
        carouselLayout.classList.remove("system-locked");
      }
    }
  }

  // ============================================================
  // 3. HÀM GỬI LỆNH (USER ACTIONS)
  // ============================================================

  // Hàm này gắn vào HTML onclick="sendFetch(1, 2)"
  window.sendFetch = function (shelfNum, trayNum) {
    if (isSystemMoving) {
      alert("Hệ thống đang chạy, vui lòng chờ!");
      return;
    }

    if (currentDropoffItem !== null) {
      alert(`Đang có khay ${currentDropoffItem.shelf}-${currentDropoffItem.tray} ở cửa lấy. Hãy cất nó trước.`);
      return;
    }

    const el = document.getElementById(`tray-${shelfNum}-${trayNum}`);
    if (el && el.classList.contains("is-out")) {
      alert("Khay này đang ở ngoài!");
      return;
    }

    // Gửi lệnh FETCH
    const payload = {
      command: "FETCH",
      shelf: parseInt(shelfNum),
      tray: parseInt(trayNum),
    };
    socket.send(JSON.stringify(payload));
    setSystemState(true);
  };

  // Click Dropoff để cất hàng (Gửi lệnh STORE)
  if (dropoffBox) {
    dropoffBox.addEventListener("click", function () {
      // 1. Chặn nếu đang chạy
      if (isSystemMoving) {
        alert("Hệ thống đang di chuyển, vui lòng chờ!");
        return;
      }

      // 2. Chỉ thực hiện khi Dropoff có hàng
      if (dropoffBox.classList.contains("occupied")) {
        // Kiểm tra dữ liệu
        if (!currentDropoffItem || !currentDropoffItem.shelf || !currentDropoffItem.tray) {
          alert("Lỗi: Mất thông tin khay. Hãy tải lại trang!");
          return;
        }

        // 3. Xác nhận
        if (confirm(`Bạn muốn cất khay về Kệ ${currentDropoffItem.shelf} - Tầng ${currentDropoffItem.tray}?`)) {
          // --- Gửi lệnh ---
          const payload = {
            command: "STORE",
            shelf: currentDropoffItem.shelf,
            tray: currentDropoffItem.tray,
          };
          socket.send(JSON.stringify(payload));
          console.log("TX Store:", payload);
          setSystemState(true);

          // --- CẬP NHẬT UI (ĐƠN GIẢN) ---
          // Tắt sáng Dropoff ngay
          dropoffBox.classList.remove("occupied", "bg-warning", "text-dark");
          dropoffBox.classList.add("bg-light", "text-muted");

          const contentText = dropoffBox.querySelector(".content-text");
          // Chỉ đổi chữ, KHÔNG đổi icon thành xoay nữa
          if (contentText) contentText.innerText = "ĐANG CẤT...";
        }
      }
    });
  }

  // Thêm hàm này vào control_panel.js để nút Reset hoạt động
  window.sendReset = function () {
    if (!confirm("Bạn có chắc chắn muốn Reset hệ thống (Về Home)?")) return;

    // Gửi lệnh RESET hoặc HOMING tùy theo logic backend của bạn
    // Giả sử backend nhận lệnh type: "RESET" hoặc "HOMING"
    const payload = {
      command: "RESET", // Hoặc "HOMING" tùy code python
    };
    socket.send(JSON.stringify(payload));
    console.log("Sent Reset command");
  };

  // ============================================================
  // 4. SYNC TRẠNG THÁI KHI LOAD TRANG
  // ============================================================

  fetchCarouselStatus();

  function fetchCarouselStatus() {
    fetch("/carousel/api/status/")
      .then((r) => r.json())
      .then((d) => {
        // 1. Cập nhật kệ hiện tại
        if (d.current_shelf) {
          if (shelfDisplay) shelfDisplay.innerText = "Kệ " + d.current_shelf;
          // Highlight
          document.querySelectorAll(".shelf-card").forEach((c) => c.classList.remove("active"));
          const activeCard = document.getElementById(`shelf-card-${d.current_shelf}`);
          if (activeCard) activeCard.classList.add("active");
        }

        // 2. Cập nhật các khay đang OUT
        if (d.grid_out && Array.isArray(d.grid_out)) {
          d.grid_out.forEach((item) => {
            updateTrayVisual(item.shelf, item.tray, true);
          });
        }

        // 3. Cập nhật Dropoff (Nếu reload trang mà dropoff đang có hàng)
        if (d.dropoff_data) {
          currentDropoffItem = {
            shelf: parseInt(d.dropoff_data.shelf),
            tray: parseInt(d.dropoff_data.tray),
          };
          updateDropoffVisual(true, `Kệ ${d.dropoff_data.shelf} - Tầng ${d.dropoff_data.tray}`);
        } else {
          currentDropoffItem = null;
          updateDropoffVisual(false, null);
        }

        // 4. Trạng thái Moving
        if (d.is_moving) setSystemState(true);
      })
      .catch((err) => console.error("Lỗi sync status:", err));
  }

  // ============================================================
  // 5. MODAL CONFIGURATION & BOM LOGIC (Giữ nguyên)
  // ============================================================

  window.openSettingsModalByBtn = function (btnElement) {
    const wrapper = btnElement.closest(".tray-wrapper");
    if (wrapper) openSettingsModal(wrapper);
  };

  function openSettingsModal(trayElement) {
    activeTrayId = trayElement.dataset.trayId;
    let titleText = `Cấu hình: ${trayElement.dataset.trayName}`;
    if (trayElement.classList.contains("is-out")) titleText += " (ĐANG Ở CỬA)";
    uiModal.title.innerText = titleText;

    resetModal();
    const loc = locationMap.get(activeTrayId);
    if (loc && loc.product_id) {
      uiModal.productSelect.val(loc.product_id).trigger("change");
      setTimeout(() => {
        if (loc.batch_id) {
          uiModal.batchSelect.value = loc.batch_id;
          displayBatchInfo(loc.batch_id);
          uiModal.inpQty.value = loc.quantity;
          uiModal.inpCap.value = loc.capacity;
          if (loc.quantity_uom_id) uiModal.selQtyUom.value = loc.quantity_uom_id;
          if (loc.capacity_uom_id) uiModal.selCapUom.value = loc.capacity_uom_id;
          validateCapacity();
        }
      }, 500);
    } else {
      uiModal.productSelect.val(null).trigger("change");
    }
    modalObj.show();
  }

  // --- Logic BOM BFS ---
  function buildBomGraph(productId) {
    const graph = {};
    const rules = allBoms.filter((b) => b.product_id == productId);
    rules.forEach((r) => {
      if (!graph[r.uom_from_id]) graph[r.uom_from_id] = [];
      graph[r.uom_from_id].push({
        to: r.uom_to_id,
        factor: r.conversion_factor,
      });

      if (!graph[r.uom_to_id]) graph[r.uom_to_id] = [];
      graph[r.uom_to_id].push({
        to: r.uom_from_id,
        factor: 1.0 / r.conversion_factor,
      });
    });
    return graph;
  }

  function getConversionFactor(productId, fromId, toId) {
    if (fromId == toId) return 1;
    const graph = buildBomGraph(productId);
    let queue = [{ id: parseInt(fromId), factor: 1 }];
    let visited = new Set();
    while (queue.length > 0) {
      let curr = queue.shift();
      if (curr.id == toId) return curr.factor;
      visited.add(curr.id);
      if (graph[curr.id]) {
        for (let neighbor of graph[curr.id]) {
          if (!visited.has(neighbor.to)) {
            queue.push({
              id: neighbor.to,
              factor: curr.factor * neighbor.factor,
            });
          }
        }
      }
    }
    return null;
  }

  function validateCapacity() {
    if (!currentProductInfo) return;
    uiModal.warningBox.classList.add("d-none");
    uiModal.btnSave.disabled = false;

    const qty = parseFloat(uiModal.inpQty.value) || 0;
    const qtyUomId = uiModal.selQtyUom.value;
    const cap = parseFloat(uiModal.inpCap.value) || 0;
    const capUomId = uiModal.selCapUom.value;

    if (!qtyUomId || !capUomId) return;

    const baseId = currentProductInfo.base_uom_id;
    const qtyFactor = getConversionFactor(currentProductInfo.id, qtyUomId, baseId);
    const capFactor = getConversionFactor(currentProductInfo.id, capUomId, baseId);

    if (qtyFactor === null || capFactor === null) {
      uiModal.warningBox.classList.remove("d-none");
      if (uiModal.convertMsg) uiModal.convertMsg.innerText = "Không thể quy đổi (Thiếu BOM)";
      uiModal.btnSave.disabled = true;
      return;
    }

    const qtyBase = qty * qtyFactor;
    const capBase = cap * capFactor;

    if (qtyBase > capBase + 0.0001) {
      uiModal.warningBox.classList.remove("d-none");
      const baseName = currentProductInfo.base_uom__name || "";
      const msg = `Vượt quá sức chứa! (${qtyBase.toFixed(1)} > ${capBase.toFixed(1)} ${baseName})`;
      if (uiModal.convertMsg) {
        uiModal.convertMsg.innerText = msg;
      } else {
        uiModal.warningBox.innerText = msg;
      }
      uiModal.btnSave.disabled = true;
    }
  }

  // --- Init Select2 & Events ---
  uiModal.productSelect.select2({
    theme: "bootstrap-5",
    dropdownParent: $(modalEl),
    placeholder: "Tìm sản phẩm...",
    allowClear: true,
    data: allProducts.map((p) => ({
      id: p.id,
      text: p.code ? `${p.code} - ${p.name}` : p.name,
    })),
  });

  uiModal.productSelect.on("change", function () {
    handleProductChange($(this).val());
  });
  uiModal.batchSelect.addEventListener("change", function () {
    displayBatchInfo(this.value);
  });
  uiModal.btnSave.addEventListener("click", saveSettings);
  uiModal.btnRemove.addEventListener("click", clearTraySettings);

  [uiModal.inpCap, uiModal.selCapUom, uiModal.inpQty, uiModal.selQtyUom].forEach((el) => {
    el.addEventListener("change", validateCapacity);
    el.addEventListener("keyup", validateCapacity);
  });

  function handleProductChange(pid) {
    if (!pid) {
      resetModal();
      currentProductInfo = null;
      return;
    }
    currentProductInfo = allProducts.find((p) => p.id == pid);
    const catId = currentProductInfo.uom_category_id;
    const uoms = catId ? uomsByCat[catId] : [];
    let uomHtml = "";
    if (uoms && uoms.length > 0) uoms.forEach((u) => (uomHtml += `<option value="${u.id}">${u.name}</option>`));
    else uomHtml = `<option value="${currentProductInfo.base_uom_id}">${currentProductInfo.base_uom__name}</option>`;

    uiModal.selQtyUom.innerHTML = uomHtml;
    uiModal.selCapUom.innerHTML = uomHtml;
    uiModal.selQtyUom.value = currentProductInfo.base_uom_id;
    uiModal.selCapUom.value = currentProductInfo.base_uom_id;

    uiModal.batchSelect.innerHTML = "<option>Loading...</option>";
    uiModal.batchSelect.disabled = true;
    fetch(`${URLS.getBatches}?product_id=${pid}`)
      .then((r) => r.json())
      .then((d) => {
        if (d.status === "ok") {
          currentBatchesData = d.batches;
          let h = '<option value="">-- Chọn Lô --</option>';
          d.batches.forEach((b) => (h += `<option value="${b.id}">${b.batch_number} (Exp: ${b.expiry})</option>`));
          uiModal.batchSelect.innerHTML = h;
          uiModal.batchSelect.disabled = false;
        }
      });
  }

  function displayBatchInfo(bid) {
    const b = currentBatchesData.find((x) => x.id == bid);
    if (b) {
      uiModal.lblBatchName.innerText = b.batch_number;
      uiModal.lblBatchExpiry.innerText = b.expiry;
      const baseName = currentProductInfo.base_uom__name || "";
      uiModal.lblBatchTotal.innerHTML = `${b.total} <small class="text-muted">${baseName}</small>`;
      uiModal.lblBatchAllocated.innerHTML = `${b.allocated} <small class="text-muted">${baseName}</small>`;
      uiModal.lblBatchUnallocated.innerHTML = `${b.unallocated} <small class="text-muted">${baseName}</small>`;
      uiModal.batchPanel.classList.remove("d-none");
      uiModal.inputSection.style.opacity = "1";
      uiModal.inputSection.style.pointerEvents = "auto";
      validateCapacity();
    }
  }

  function resetModal() {
    uiModal.batchSelect.innerHTML = '<option value="">-- Chọn sản phẩm trước --</option>';
    uiModal.batchSelect.disabled = true;
    uiModal.batchPanel.classList.add("d-none");
    uiModal.inputSection.style.opacity = "0.5";
    uiModal.inputSection.style.pointerEvents = "none";
    uiModal.inpQty.value = 0;
    uiModal.inpCap.value = 50;
    uiModal.warningBox.classList.add("d-none");
    uiModal.btnSave.disabled = false;
  }

  function saveSettings() {
    const payload = {
      tray_id: activeTrayId,
      batch_id: uiModal.batchSelect.value,
      quantity: uiModal.inpQty.value,
      quantity_uom_id: uiModal.selQtyUom.value,
      capacity: uiModal.inpCap.value,
      capacity_uom_id: uiModal.selCapUom.value,
    };
    if (!payload.batch_id) {
      alert("Chọn Lô!");
      return;
    }
    fetch(URLS.saveLocation, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": CSRF_TOKEN,
      },
      body: JSON.stringify(payload),
    })
      .then((r) => r.json())
      .then((d) => {
        if (d.status === "ok") location.reload();
        else alert(d.message);
      });
  }

  function clearTraySettings() {
    if (!confirm("Xóa cấu hình khay này?")) return;
    fetch(URLS.saveLocation, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": CSRF_TOKEN,
      },
      body: JSON.stringify({ tray_id: activeTrayId, batch_id: null }),
    }).then(() => location.reload());
  }
});
