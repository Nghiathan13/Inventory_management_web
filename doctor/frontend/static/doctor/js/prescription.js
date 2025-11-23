document.addEventListener("DOMContentLoaded", function () {
  // =======================================================
  //   KHỞI TẠO BIẾN VÀ LẤY DỮ LIỆU
  // =======================================================
  const productsData = JSON.parse(document.getElementById("products-data-json")?.textContent || "[]");
  const uomsData = JSON.parse(document.getElementById("uoms-data-json")?.textContent || "[]");

  // --- Lấy các element template ---
  const detailFormTemplate = document.getElementById("detail-form-template");
  const productOptionTemplate = document.getElementById("product-option-template");
  const uomOptionTemplate = document.getElementById("uom-option-template");
  const uomPlaceholderTemplate = document.getElementById("uom-placeholder-template");

  // --- Lấy các element chính của form ---
  const addButton = document.getElementById("add-more");
  const container = document.getElementById("details-container");

  if (!container || !detailFormTemplate || !addButton) {
    console.error("Các element cần thiết cho form kê đơn không tồn tại.");
    return;
  }

  // Xử lý trường hợp không có sản phẩm
  if (!productsData || productsData.length === 0) {
    addButton.disabled = true;
    const alertDiv = document.createElement("div");
    alertDiv.className = "alert alert-warning text-center";
    alertDiv.textContent = "Không có sản phẩm nào trong kho để kê đơn.";
    container.appendChild(alertDiv);
    return;
  }

  let formIndexCounter = 0;

  // =======================================================
  //   CÁC HÀM XỬ LÝ LOGIC
  // =======================================================

  // Hàm Sắp xếp lại index của các form.
  function reindexForms() {
    let currentIndex = 0;
    container.querySelectorAll(".detail-form").forEach((form) => {
      form.querySelectorAll("input, select").forEach((input) => {
        const name = input.getAttribute("name");
        if (name) {
          input.setAttribute("name", name.replace(/details-\d+-/, `details-${currentIndex}-`));
        }
        const id = input.getAttribute("id");
        if (id) {
          input.setAttribute("id", id.replace(/details-\d+-/, `details-${currentIndex}-`));
        }
      });
      currentIndex++;
    });
    formIndexCounter = currentIndex;
  }

  // Hàm cập nhật dropdown đơn vị tính
  function updateUomDropdown(productSelect) {
    const selectedProductId = productSelect.value;
    const detailForm = productSelect.closest(".detail-form");
    const uomSelect = detailForm.querySelector(".uom-select");
    uomSelect.innerHTML = "";

    const selectedProduct = productsData.find((p) => p.id == parseInt(selectedProductId, 10));

    if (selectedProduct && selectedProduct.uom_category_id) {
      uomSelect.add(new Option("---------", ""));
      const filteredUoms = uomsData.filter((u) => u.category_id == selectedProduct.uom_category_id);

      if (filteredUoms.length > 0) {
        filteredUoms.forEach((uom) => {
          const optionHtml = uomOptionTemplate.innerHTML.replace("__ID__", uom.id).replace("__NAME__", uom.name);
          uomSelect.insertAdjacentHTML("beforeend", optionHtml);
        });
        uomSelect.disabled = false;
      } else {
        uomSelect.insertAdjacentHTML("beforeend", '<option value="">Không có đơn vị</option>');
        uomSelect.disabled = true;
      }
    } else {
      uomSelect.innerHTML = uomPlaceholderTemplate.innerHTML;
      uomSelect.disabled = true;
    }
  }

  // Hàm cập nhật dropdown sản phẩm
  function updateProductDropdowns() {
    const selectedIds = new Set();
    container.querySelectorAll(".product-select").forEach((select) => {
      if (select.value) selectedIds.add(select.value);
    });
    container.querySelectorAll(".product-select").forEach((select) => {
      const currentVal = select.value;
      select.querySelectorAll("option").forEach((option) => {
        if (option.value) {
          option.disabled = selectedIds.has(option.value) && option.value !== currentVal;
        }
      });
    });
  }

  // Hàm thêm một dòng form chi tiết mới
  function addDetailForm() {
    const templateHtml = detailFormTemplate.innerHTML.replace(/__prefix__/g, formIndexCounter);
    const newForm = document.createElement("div");
    newForm.innerHTML = templateHtml;
    const newFormElement = newForm.firstElementChild;

    // Điền các sản phẩm vào dropdown
    const productSelect = newFormElement.querySelector(".product-select");
    if (productSelect) {
      productSelect.add(new Option("---------", ""));
      productsData.forEach((p) => {
        const optionHtml = productOptionTemplate.innerHTML
          .replace("__ID__", p.id)
          .replace("__NAME__", p.name)
          .replace("__QUANTITY__", p.quantity);
        productSelect.insertAdjacentHTML("beforeend", optionHtml);
      });
    }

    container.appendChild(newFormElement);
    formIndexCounter++;
    updateProductDropdowns();
  }

  /** Xóa một dòng form chi tiết thuốc. */
  function removeDetailForm(button) {
    button.closest(".detail-form").remove();
    reindexForms();
    updateProductDropdowns();
  }

  // =======================================================
  //   KHỞI TẠO VÀ GẮN SỰ KIỆN
  // =======================================================

  if (container.querySelectorAll(".detail-form").length === 0) {
    addDetailForm();
  } else {
    reindexForms();
  }
  addButton.addEventListener("click", addDetailForm);

  container.addEventListener("change", function (e) {
    if (e.target && e.target.classList.contains("product-select")) {
      updateProductDropdowns();
      updateUomDropdown(e.target);
    }
  });

  container.addEventListener("click", function (e) {
    const removeButton = e.target.closest(".remove-form");
    if (removeButton) {
      removeDetailForm(removeButton);
    }
  });

  updateProductDropdowns();
});
