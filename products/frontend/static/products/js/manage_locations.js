// document.addEventListener("DOMContentLoaded", function () {
//   // -----------------------------------------------------------
//   // 1. KHỞI TẠO & LẤY DỮ LIỆU
//   // -----------------------------------------------------------
//   const modalEl = document.getElementById("locationSettingsModal");
//   const modalObj = new bootstrap.Modal(modalEl);

//   // UI References
//   const ui = {
//     title: document.getElementById("locationModalLabel"),
//     productSelect: $("#modal-product"),
//     batchSelect: document.getElementById("modal-batch"),

//     batchPanel: document.getElementById("batch-info-panel"),
//     lblBatchName: document.getElementById("lblBatchName"),
//     lblBatchExpiry: document.getElementById("lblBatchExpiry"),
//     lblBatchTotal: document.getElementById("lblBatchTotal"),
//     lblBatchAllocated: document.getElementById("lblBatchAllocated"),
//     lblBatchUnallocated: document.getElementById("lblBatchUnallocated"),
//     lblBatchBaseUom: document.getElementById("lblBatchBaseUom"),

//     inputSection: document.getElementById("input-section"),
//     inpCap: document.getElementById("modal-capacity"),
//     selCapUom: document.getElementById("modal-capacity-uom"),
//     inpQty: document.getElementById("modal-quantity"),
//     selQtyUom: document.getElementById("modal-quantity-uom"),
//     warningBox: document.getElementById("capacity-warning"),
//     convertMsg: document.getElementById("convert-msg"),

//     btnSave: document.getElementById("modal-save-btn"),
//     btnRemove: document.getElementById("modal-remove-btn"),
//   };

//   let activeTrayId = null;
//   let currentBatchesData = [];
//   let currentProductInfo = null;

//   // Lấy dữ liệu từ HTML
//   const allProducts = JSON.parse(document.getElementById("all-products-data").textContent);
//   const uomsByCat = JSON.parse(document.getElementById("uoms-by-category").textContent);
//   const initialLocations = JSON.parse(document.getElementById("all-locations-data").textContent);
//   const allBoms = JSON.parse(document.getElementById("all-boms-data").textContent);

//   // Map Locations for quick access
//   let locationMap = new Map(initialLocations.map((loc) => [loc.tray_id.toString(), loc]));

//   // -----------------------------------------------------------
//   // 2. SETUP CHỌN TÊN SẢN PHẨM
//   // -----------------------------------------------------------

//   // Initialize Select2
//   ui.productSelect.select2({
//     theme: "bootstrap-5",
//     dropdownParent: $(modalEl),
//     placeholder: "Tìm sản phẩm...",
//     allowClear: true,
//     data: allProducts.map((p) => ({ id: p.id, text: `${p.name}` })),
//   });

//   // Render Visuals on Load
//   renderAllTrays();

//   // -----------------------------------------------------------
//   // 3. CÁC SỰ KIỆN (EVENTS)
//   // -----------------------------------------------------------
//   document.querySelector(".carousel-layout").addEventListener("click", (e) => {
//     const trayItem = e.target.closest(".tray-item");
//     if (trayItem) openModal(trayItem);
//   });

//   // Product Change
//   ui.productSelect.on("change", function () {
//     const pid = $(this).val();
//     handleProductChange(pid);
//   });

//   // Batch Change
//   ui.batchSelect.addEventListener("change", function () {
//     displayBatchInfo(this.value);
//   });

//   // Validate Capacity on Input Change
//   [ui.inpCap, ui.selCapUom, ui.inpQty, ui.selQtyUom].forEach((el) => {
//     el.addEventListener("change", validateCapacity);
//     el.addEventListener("keyup", validateCapacity);
//   });

//   // Save & Remove
//   ui.btnSave.addEventListener("click", saveSettings);
//   ui.btnRemove.addEventListener("click", clearTray);

//   // -----------------------------------------------------------
//   // 4. LOGIC FUNCTIONS
//   // -----------------------------------------------------------

//   function openModal(trayItem) {
//     activeTrayId = trayItem.dataset.trayId;
//     ui.title.innerText = `Vị trí: ${trayItem.dataset.trayName}`;

//     resetModal();

//     const loc = locationMap.get(activeTrayId);
//     if (loc && loc.product_id) {
//       ui.productSelect.val(loc.product_id).trigger("change");
//       setTimeout(() => {
//         if (loc.batch_id) {
//           ui.batchSelect.value = loc.batch_id;
//           displayBatchInfo(loc.batch_id);

//           // Fill inputs
//           ui.inpQty.value = loc.quantity;
//           ui.inpCap.value = loc.capacity;

//           // Set lại UoM nếu có dữ liệu cũ (cần check option tồn tại)
//           // (Lưu ý: Giả sử backend chưa trả về uom_id trong loc, nếu có thì thêm vào đây)
//         }
//       }, 600);
//     } else {
//       ui.productSelect.val(null).trigger("change");
//     }

//     modalObj.show();
//   }

//   function resetModal() {
//     ui.batchSelect.innerHTML = '<option value="">-- Vui lòng chọn sản phẩm trước --</option>';
//     ui.batchSelect.disabled = true;
//     ui.batchPanel.classList.add("d-none");
//     ui.inputSection.style.opacity = "0.5";
//     ui.inputSection.style.pointerEvents = "none";
//     ui.inpQty.value = 0;
//     ui.inpCap.value = 50;
//     ui.warningBox.classList.add("d-none");
//     ui.btnSave.disabled = false;
//   }

//   function handleProductChange(productId) {
//     if (!productId) {
//       resetModal();
//       currentProductInfo = null;
//       return;
//     }

//     currentProductInfo = allProducts.find((p) => p.id == productId);

//     // 1. Populate UoM Dropdowns (Filter by Category)
//     const catId = currentProductInfo.uom_category_id;
//     const uoms = catId ? uomsByCat[catId] : [];

//     let uomHtml = "";
//     if (uoms && uoms.length > 0) {
//       uoms.forEach((u) => (uomHtml += `<option value="${u.id}">${u.name}</option>`));
//     } else {
//       // Fallback to Base UoM
//       uomHtml = `<option value="${currentProductInfo.base_uom_id}">${currentProductInfo.base_uom__name}</option>`;
//     }

//     ui.selQtyUom.innerHTML = uomHtml;
//     ui.selCapUom.innerHTML = uomHtml;

//     // Default select Base UoM
//     ui.selQtyUom.value = currentProductInfo.base_uom_id;
//     ui.selCapUom.value = currentProductInfo.base_uom_id;

//     // 2. Load Batches via API
//     loadBatches(productId);
//   }

//   function loadBatches(productId) {
//     ui.batchSelect.innerHTML = "<option>Đang tải...</option>";
//     ui.batchSelect.disabled = true;

//     fetch(`${URL_GET_BATCHES}?product_id=${productId}`)
//       .then((res) => res.json())
//       .then((data) => {
//         if (data.status === "ok") {
//           currentBatchesData = data.batches;
//           let html = '<option value="">-- Chọn Lô --</option>';
//           data.batches.forEach((b) => {
//             html += `<option value="${b.id}">Lô ${b.batch_number} (HSD: ${b.expiry})</option>`;
//           });
//           ui.batchSelect.innerHTML = html;
//           ui.batchSelect.disabled = false;

//           if (data.base_uom) {
//             ui.lblBatchBaseUom.innerText = data.base_uom;
//           }
//         }
//       });
//   }

//   function displayBatchInfo(batchId) {
//     const batch = currentBatchesData.find((b) => b.id == batchId);
//     if (batch) {
//       ui.lblBatchName.innerText = batch.batch_number;
//       ui.lblBatchExpiry.innerText = batch.expiry;

//       const baseUomName = currentProductInfo.base_uom__name || "";
//       ui.lblBatchTotal.innerText = `${batch.total} ${baseUomName}`;
//       ui.lblBatchAllocated.innerText = `${batch.allocated} ${baseUomName}`;
//       ui.lblBatchUnallocated.innerText = batch.unallocated;

//       ui.batchPanel.classList.remove("d-none");
//       ui.inputSection.style.opacity = "1";
//       ui.inputSection.style.pointerEvents = "auto";

//       validateCapacity(); // Re-validate
//     } else {
//       ui.batchPanel.classList.add("d-none");
//       ui.inputSection.style.opacity = "0.5";
//       ui.inputSection.style.pointerEvents = "none";
//     }
//   }

//   // -----------------------------------------------------------
//   // 5. VALIDATION LOGIC (BOM CONVERSION)
//   // -----------------------------------------------------------

//   function findBomFactor(fromId, toId) {
//     if (fromId == toId) return 1;

//     // Tìm chiều xuôi (From -> To)
//     const forward = allBoms.find(
//       (b) => b.product_id == currentProductInfo.id && b.uom_from_id == fromId && b.uom_to_id == toId
//     );
//     if (forward) return parseFloat(forward.conversion_factor);

//     // Tìm chiều ngược (To -> From)
//     const reverse = allBoms.find(
//       (b) => b.product_id == currentProductInfo.id && b.uom_from_id == toId && b.uom_to_id == fromId
//     );
//     if (reverse) return 1 / parseFloat(reverse.conversion_factor);

//     return null; // Không tìm thấy quy đổi trực tiếp
//   }

//   /**
//    * Quy đổi một đơn vị bất kỳ về Base Unit của sản phẩm.
//    * Hỗ trợ bắc cầu nếu cần (nhưng ở đây ta giả định BOM luôn define về Base hoặc từ Base).
//    */
//   function toBaseUnit(qty, uomId) {
//     const baseId = currentProductInfo.base_uom_id;

//     // 1. Nếu trùng Base Unit
//     if (uomId == baseId) return qty;

//     // 2. Tìm quy đổi trực tiếp
//     const factor = findBomFactor(uomId, baseId);
//     if (factor !== null) {
//       return qty * factor;
//     }

//     // Fallback: Nếu không tìm thấy rule, coi như 1:1 (hoặc có thể báo lỗi)
//     console.warn("Không tìm thấy BOM rule giữa UoM", uomId, "và Base", baseId);
//     return qty;
//   }

//   function validateCapacity() {
//     if (!currentProductInfo) return;

//     const qtyInput = parseFloat(ui.inpQty.value) || 0;
//     const qtyUomId = ui.selQtyUom.value;

//     const capInput = parseFloat(ui.inpCap.value) || 0;
//     const capUomId = ui.selCapUom.value;

//     // QUY ĐỔI TẤT CẢ VỀ BASE UNIT ĐỂ SO SÁNH
//     // Ví dụ: Base=Viên. Capacity=5 Hộp (1 Hộp=10 Viên) -> 50 Viên.
//     // Qty=50 Vỉ (1 Vỉ=10 Viên) -> 500 Viên. -> Lỗi
//     // Ví dụ đúng: Capacity=5 Hộp (50 Viên). Qty=5 Vỉ (50 Viên) -> OK.

//     const qtyInBase = toBaseUnit(qtyInput, qtyUomId);
//     const capInBase = toBaseUnit(capInput, capUomId);

//     // Cho phép sai số nhỏ do số thực (epsilon)
//     if (qtyInBase > capInBase + 0.0001) {
//       ui.warningBox.classList.remove("d-none");

//       // Hiển thị thông báo rõ ràng
//       const baseName = currentProductInfo.base_uom__name;
//       ui.convertMsg.innerText = `Quy đổi: ${qtyInBase.toFixed(2)} > ${capInBase.toFixed(2)} (${baseName})`;
//       ui.btnSave.disabled = true;
//     } else {
//       ui.warningBox.classList.add("d-none");
//       ui.btnSave.disabled = false;
//     }
//   }

//   // -----------------------------------------------------------
//   // 6. SAVE & RENDER
//   // -----------------------------------------------------------

//   async function saveSettings() {
//     const payload = {
//       tray_id: activeTrayId,
//       batch_id: ui.batchSelect.value,
//       quantity: ui.inpQty.value,
//       quantity_uom_id: ui.selQtyUom.value,
//       capacity: ui.inpCap.value,
//       capacity_uom_id: ui.selCapUom.value,
//     };

//     if (!payload.batch_id) {
//       alert("Chưa chọn Lô!");
//       return;
//     }

//     try {
//       const res = await fetch(URL_SAVE, {
//         method: "POST",
//         headers: { "Content-Type": "application/json", "X-CSRFToken": CSRF_TOKEN },
//         body: JSON.stringify(payload),
//       });
//       const d = await res.json();
//       if (d.status === "ok") window.location.reload();
//       else alert(d.message);
//     } catch (e) {
//       console.error(e);
//     }
//   }

//   function clearTray() {
//     if (!confirm("Xóa khay?")) return;
//     fetch(URL_SAVE, {
//       method: "POST",
//       headers: { "Content-Type": "application/json", "X-CSRFToken": CSRF_TOKEN },
//       body: JSON.stringify({ tray_id: activeTrayId, batch_id: null }),
//     }).then(() => window.location.reload());
//   }

//   function renderAllTrays() {
//     document.querySelectorAll(".tray-item").forEach((item) => {
//       const tid = item.dataset.trayId;
//       const loc = locationMap.get(tid);

//       const divProd = item.querySelector(".tray-product");
//       const divBatch = item.querySelector(".tray-batch");
//       const divQty = item.querySelector(".tray-qty");
//       const bar = item.querySelector(".progress-bar");

//       if (loc && loc.batch_id) {
//         item.classList.add("tray-filled");
//         const pInfo = allProducts.find((p) => p.id == loc.product_id);
//         divProd.textContent = pInfo ? pInfo.name : `ID:${loc.product_id}`;
//         divBatch.textContent = `Lô: ${loc.batch_number}`;
//         divQty.textContent = `${loc.quantity} / ${loc.capacity} ${loc.quantity_uom_name}`;

//         let pct = 0;
//         if (loc.capacity > 0) pct = (loc.quantity / loc.capacity) * 100;

//         bar.style.width = `${pct}%`;
//         bar.className = `progress-bar ${pct > 90 ? "bg-danger" : "bg-success"}`;
//       } else {
//         item.classList.remove("tray-filled");
//         divProd.textContent = "-- Trống --";
//       }
//     });
//   }
// });

document.addEventListener("DOMContentLoaded", function () {
  // -----------------------------------------------------------
  // 1. KHỞI TẠO & LẤY DỮ LIỆU
  // -----------------------------------------------------------
  const modalEl = document.getElementById("locationSettingsModal");
  const modalObj = new bootstrap.Modal(modalEl);

  const ui = {
    title: document.getElementById("locationModalLabel"),
    productSelect: $("#modal-product"),
    batchSelect: document.getElementById("modal-batch"),

    // Batch Panel
    batchPanel: document.getElementById("batch-info-panel"),
    lblBatchName: document.getElementById("lblBatchName"),
    lblBatchExpiry: document.getElementById("lblBatchExpiry"),
    lblBatchTotal: document.getElementById("lblBatchTotal"),
    lblBatchAllocated: document.getElementById("lblBatchAllocated"),
    lblBatchUnallocated: document.getElementById("lblBatchUnallocated"),
    lblBatchBaseUom: document.getElementById("lblBatchBaseUom"),

    // Input Section
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

  let activeTrayId = null;
  let currentBatchesData = [];
  let currentProductInfo = null;

  // Biến lưu đồ thị quy đổi cho sản phẩm hiện tại
  let conversionGraph = {};

  // Load Data
  const allProducts = JSON.parse(document.getElementById("all-products-data").textContent);
  const uomsByCat = JSON.parse(document.getElementById("uoms-by-category").textContent);
  const initialLocations = JSON.parse(document.getElementById("all-locations-data").textContent);
  const allBoms = JSON.parse(document.getElementById("all-boms-data").textContent);

  let locationMap = new Map(initialLocations.map((loc) => [loc.tray_id.toString(), loc]));

  // -----------------------------------------------------------
  // 2. CẤU HÌNH SELECT2 & EVENTS
  // -----------------------------------------------------------
  ui.productSelect.select2({
    theme: "bootstrap-5",
    dropdownParent: $(modalEl),
    placeholder: "Tìm sản phẩm...",
    allowClear: true,
    data: allProducts.map((p) => ({
      id: p.id,
      text: p.code ? `${p.code} - ${p.name}` : p.name,
    })),
  });

  // Render ban đầu (Cần tính toán % đúng trước khi vẽ)
  // Chúng ta sẽ render sau khi xử lý xong logic graph cơ bản (tạm thời render visual thô)
  // Nhưng để đúng màu progress bar ngay từ đầu, ta cần build graph cho từng item (hơi nặng),
  // hoặc đơn giản là vẽ lại khi user click vào khay.
  // Ở đây ta vẽ sơ bộ, logic chính xác sẽ chạy trong renderAllTraysWithLogic()

  // Gắn Events
  document.querySelector(".carousel-layout").addEventListener("click", (e) => {
    const trayItem = e.target.closest(".tray-item");
    if (trayItem) openModal(trayItem);
  });

  ui.productSelect.on("change", function () {
    handleProductChange($(this).val());
  });

  ui.batchSelect.addEventListener("change", function () {
    displayBatchInfo(this.value);
  });

  // Validate Realtime
  [ui.inpCap, ui.selCapUom, ui.inpQty, ui.selQtyUom].forEach((el) => {
    el.addEventListener("change", validateCapacity);
    el.addEventListener("keyup", validateCapacity);
  });

  ui.btnSave.addEventListener("click", saveSettings);
  ui.btnRemove.addEventListener("click", clearTray);

  // Render lần đầu
  requestAnimationFrame(() => renderAllTraysWithLogic());

  // -----------------------------------------------------------
  // 3. THUẬT TOÁN TÌM ĐƯỜNG (SMART BOM SOLVER)
  // -----------------------------------------------------------

  /**
   * Xây dựng đồ thị quy đổi cho 1 sản phẩm cụ thể.
   * Node = UoM ID, Edge = Conversion Factor.
   */
  function buildBomGraph(productId) {
    const graph = {};
    // Lọc các rule của sản phẩm này
    const rules = allBoms.filter((b) => b.product_id == productId);

    rules.forEach((r) => {
      // Chiều xuôi: From -> To (Factor)
      if (!graph[r.uom_from_id]) graph[r.uom_from_id] = [];
      graph[r.uom_from_id].push({ to: r.uom_to_id, factor: r.conversion_factor });

      // Chiều ngược: To -> From (1 / Factor)
      if (!graph[r.uom_to_id]) graph[r.uom_to_id] = [];
      graph[r.uom_to_id].push({ to: r.uom_from_id, factor: 1.0 / r.conversion_factor });
    });
    return graph;
  }

  /**
   * Tìm hệ số quy đổi từ `sourceUomId` sang `targetUomId` bằng BFS.
   * Trả về factor hoặc null nếu không tìm thấy đường đi.
   */
  function getSmartConversionFactor(graph, sourceUomId, targetUomId) {
    // 1. Nếu cùng đơn vị
    if (sourceUomId == targetUomId) return 1;

    // 2. BFS
    let queue = [{ id: parseInt(sourceUomId), factor: 1 }];
    let visited = new Set();

    while (queue.length > 0) {
      let current = queue.shift();

      if (current.id == targetUomId) {
        return current.factor; // Tìm thấy!
      }

      visited.add(current.id);

      const neighbors = graph[current.id];
      if (neighbors) {
        for (let neighbor of neighbors) {
          if (!visited.has(neighbor.to)) {
            queue.push({
              id: neighbor.to,
              factor: current.factor * neighbor.factor, // Tích lũy hệ số
            });
          }
        }
      }
    }
    return null; // Không có đường đi
  }

  // -----------------------------------------------------------
  // 4. LOGIC MODAL & VALIDATION
  // -----------------------------------------------------------

  function openModal(trayItem) {
    activeTrayId = trayItem.dataset.trayId;
    ui.title.innerText = `Vị trí: ${trayItem.dataset.trayName}`;
    resetModal();

    const loc = locationMap.get(activeTrayId);
    if (loc && loc.product_id) {
      // 1. Load Product & Build Graph
      ui.productSelect.val(loc.product_id).trigger("change");

      setTimeout(() => {
        // 2. Load Batch
        if (loc.batch_id) {
          ui.batchSelect.value = loc.batch_id;
          displayBatchInfo(loc.batch_id);

          // 3. Fill Data
          ui.inpQty.value = loc.quantity;
          ui.inpCap.value = loc.capacity;

          // 4. Set UoM chính xác (FIX LỖI TỰ ĐỔI ĐƠN VỊ)
          if (loc.quantity_uom_id) ui.selQtyUom.value = loc.quantity_uom_id;
          if (loc.capacity_uom_id) ui.selCapUom.value = loc.capacity_uom_id;

          // Re-validate để check logic ngay khi mở
          validateCapacity();
        }
      }, 500);
    } else {
      ui.productSelect.val(null).trigger("change");
    }
    modalObj.show();
  }

  function resetModal() {
    ui.batchSelect.innerHTML = '<option value="">-- Chọn sản phẩm trước --</option>';
    ui.batchSelect.disabled = true;
    ui.batchPanel.classList.add("d-none");
    ui.inputSection.style.opacity = "0.5";
    ui.inputSection.style.pointerEvents = "none";
    ui.inpQty.value = 0;
    ui.inpCap.value = 50;
    ui.warningBox.classList.add("d-none");
    ui.btnSave.disabled = false;
  }

  function handleProductChange(productId) {
    if (!productId) {
      resetModal();
      currentProductInfo = null;
      conversionGraph = {};
      return;
    }

    currentProductInfo = allProducts.find((p) => p.id == productId);

    // Xây dựng đồ thị quy đổi ngay khi chọn sản phẩm
    conversionGraph = buildBomGraph(productId);

    // Populate UoM Dropdown
    const catId = currentProductInfo.uom_category_id;
    const uoms = catId ? uomsByCat[catId] : [];

    let uomHtml = "";
    if (uoms && uoms.length > 0) {
      uoms.forEach((u) => (uomHtml += `<option value="${u.id}">${u.name}</option>`));
    } else {
      uomHtml = `<option value="${currentProductInfo.base_uom_id}">${currentProductInfo.base_uom__name}</option>`;
    }

    ui.selQtyUom.innerHTML = uomHtml;
    ui.selCapUom.innerHTML = uomHtml;

    // Default select Base UoM
    ui.selQtyUom.value = currentProductInfo.base_uom_id;
    ui.selCapUom.value = currentProductInfo.base_uom_id;

    loadBatches(productId);
  }

  function loadBatches(productId) {
    ui.batchSelect.innerHTML = "<option>Đang tải...</option>";
    ui.batchSelect.disabled = true;

    fetch(`${URL_GET_BATCHES}?product_id=${productId}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "ok") {
          currentBatchesData = data.batches;
          let html = '<option value="">-- Chọn Lô --</option>';
          data.batches.forEach((b) => {
            html += `<option value="${b.id}">Lô ${b.batch_number} (HSD: ${b.expiry})</option>`;
          });
          ui.batchSelect.innerHTML = html;
          ui.batchSelect.disabled = false;

          // FIX LỖI: Hiển thị đơn vị cho tổng
          if (data.base_uom) {
            ui.lblBatchBaseUom.innerText = data.base_uom;
          }
        }
      });
  }

  function displayBatchInfo(batchId) {
    const batch = currentBatchesData.find((b) => b.id == batchId);
    if (batch) {
      ui.lblBatchName.innerText = batch.batch_number;
      ui.lblBatchExpiry.innerText = batch.expiry;

      const baseUomName = currentProductInfo.base_uom__name || "";
      ui.lblBatchTotal.innerText = `${batch.total} ${baseUomName}`;
      ui.lblBatchAllocated.innerText = `${batch.allocated} ${baseUomName}`;
      ui.lblBatchUnallocated.innerText = batch.unallocated;

      ui.batchPanel.classList.remove("d-none");
      ui.inputSection.style.opacity = "1";
      ui.inputSection.style.pointerEvents = "auto";

      validateCapacity();
    } else {
      ui.batchPanel.classList.add("d-none");
      ui.inputSection.style.opacity = "0.5";
      ui.inputSection.style.pointerEvents = "none";
    }
  }

  function validateCapacity() {
    if (!currentProductInfo) return;

    const qtyInput = parseFloat(ui.inpQty.value) || 0;
    const qtyUomId = ui.selQtyUom.value;

    const capInput = parseFloat(ui.inpCap.value) || 0;
    const capUomId = ui.selCapUom.value;

    // QUY ĐỔI THÔNG MINH (DÙNG GRAPH)
    // Quy đổi Quantity -> Capacity Unit (hoặc Base Unit)
    // Tốt nhất là quy đổi Quantity về cùng đơn vị với Capacity để so sánh trực tiếp

    const conversionFactor = getSmartConversionFactor(conversionGraph, qtyUomId, capUomId);

    if (conversionFactor === null) {
      // Không tìm thấy đường quy đổi
      ui.warningBox.classList.remove("d-none");
      ui.convertMsg.innerText = `Không thể quy đổi giữa 2 đơn vị này! Hãy thiết lập BOM.`;
      ui.btnSave.disabled = true;
      return;
    }

    const qtyConverted = qtyInput * conversionFactor;

    // So sánh: 100 Viên (Qty) vs 50 Vỉ (Cap)
    // 1 Vỉ = 10 Viên => 100 Viên = 10 Vỉ.
    // Factor (Viên->Vỉ) = 0.1.
    // QtyConverted = 100 * 0.1 = 10.
    // 10 <= 50 => OK.

    // So sánh với sai số nhỏ
    if (qtyConverted > capInput + 0.0001) {
      ui.warningBox.classList.remove("d-none");

      // Lấy tên đơn vị để hiển thị cảnh báo dễ hiểu
      const capUomName = ui.selCapUom.options[ui.selCapUom.selectedIndex].text;

      ui.convertMsg.innerText = `${qtyInput} (đã đổi) = ${qtyConverted.toFixed(
        2
      )} ${capUomName} > ${capInput} ${capUomName}`;
      ui.btnSave.disabled = true;
    } else {
      ui.warningBox.classList.add("d-none");
      ui.btnSave.disabled = false;
    }
  }

  // -----------------------------------------------------------
  // 5. RENDER VISUALS
  // -----------------------------------------------------------

  function renderAllTraysWithLogic() {
    document.querySelectorAll(".tray-item").forEach((item) => {
      const tid = item.dataset.trayId;
      const loc = locationMap.get(tid);

      const divProd = item.querySelector(".tray-product");
      const divBatch = item.querySelector(".tray-batch");
      const divQty = item.querySelector(".tray-qty");
      const bar = item.querySelector(".progress-bar");
      const spanPercent = item.querySelector(".tray-percent");

      if (loc && loc.batch_id) {
        item.classList.add("tray-filled");

        const pInfo = allProducts.find((p) => p.id == loc.product_id);
        const pName = pInfo ? (pInfo.code ? `${pInfo.code}-${pInfo.name}` : pInfo.name) : `ID:${loc.product_id}`;

        divProd.textContent = pName;
        divBatch.textContent = `Lô: ${loc.batch_number}`;

        // Hiển thị text rõ ràng: 100 Viên / 50 Vỉ
        divQty.textContent = `${loc.quantity} ${loc.quantity_uom_name} / ${loc.capacity} ${loc.capacity_uom_name}`;

        // --- TÍNH % THÔNG MINH ---
        // Phải build graph cho sản phẩm này để quy đổi
        const graph = buildBomGraph(loc.product_id);
        const factor = getSmartConversionFactor(graph, loc.quantity_uom_id, loc.capacity_uom_id);

        let pct = 0;
        if (loc.capacity > 0 && factor !== null) {
          // Quy đổi Qty về đơn vị của Capacity
          const convertedQty = loc.quantity * factor;
          pct = (convertedQty / loc.capacity) * 100;
        } else if (loc.capacity > 0) {
          pct = (loc.quantity / loc.capacity) * 100;
        }

        bar.style.width = `${Math.min(pct, 100)}%`;
        bar.className = `progress-bar ${pct > 90 ? "bg-danger" : pct > 50 ? "bg-warning" : "bg-success"}`;
        if (pct > 0) {
          spanPercent.textContent = `${pct.toFixed(1)}%`;
        } else {
          spanPercent.textContent = "";
        }

        // Tooltip chi tiết
        item.title = `Đã dùng: ${pct.toFixed(1)}% sức chứa`;
      } else {
        item.classList.remove("tray-filled");
        divProd.textContent = "-- Trống --";
        divBatch.textContent = "";
        divQty.textContent = "";
        bar.style.width = "0%";
      }
    });
  }

  // -----------------------------------------------------------
  // 6. SAVE ACTIONS
  // -----------------------------------------------------------

  async function saveSettings() {
    const payload = {
      tray_id: activeTrayId,
      batch_id: ui.batchSelect.value,
      quantity: ui.inpQty.value,
      quantity_uom_id: ui.selQtyUom.value,
      capacity: ui.inpCap.value,
      capacity_uom_id: ui.selCapUom.value,
    };

    if (!payload.batch_id) {
      alert("Chưa chọn Lô!");
      return;
    }

    try {
      const res = await fetch(URL_SAVE, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": CSRF_TOKEN },
        body: JSON.stringify(payload),
      });
      const d = await res.json();
      if (d.status === "ok") window.location.reload();
      else alert(d.message);
    } catch (e) {
      console.error(e);
    }
  }

  function clearTray() {
    if (!confirm("Xóa khay?")) return;
    fetch(URL_SAVE, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": CSRF_TOKEN },
      body: JSON.stringify({ tray_id: activeTrayId, batch_id: null }),
    }).then(() => window.location.reload());
  }
});
