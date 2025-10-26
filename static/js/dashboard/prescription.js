function initializePrescriptionForm(products, uoms) {
  const addButton = document.getElementById("add-more");
  const container = document.getElementById("details-container");
  const formCountInput = document.getElementById("form-count");
  const template = document.getElementById("detail-form-template");

  if (!container || !template || !addButton || !formCountInput) {
    console.error("Required elements for prescription form not found.");
    return;
  }

  let formIndex = container.querySelectorAll(".detail-form").length;

  // Lọc và điền các lựa chọn cho dropdown đơn vị tính (uom)
  function updateUomDropdown(productSelect) {
    const selectedProductId = productSelect.value;
    const detailForm = productSelect.closest(".detail-form");
    const uomSelect = detailForm.querySelector('select[name*="-uom"]');

    const selectedProduct = products.find((p) => p.id == selectedProductId);

    uomSelect.innerHTML = "";

    if (selectedProduct && selectedProduct.uom_category_id) {
      uomSelect.add(new Option("---------", ""));

      const filteredUoms = uoms.filter(
        (u) => u.category_id == selectedProduct.uom_category_id
      );

      if (filteredUoms.length > 0) {
        filteredUoms.forEach((uom) => {
          uomSelect.add(new Option(uom.name, uom.id));
        });
        uomSelect.disabled = false; // KÍCH HOẠT DROPDOWN
      } else {
        uomSelect.innerHTML = '<option value="">Không có đơn vị</option>';
        uomSelect.disabled = true;
      }
    } else {
      uomSelect.innerHTML = '<option value="">Chọn sản phẩm trước</option>';
      uomSelect.disabled = true;
    }
  }

  // Vô hiệu hóa các sản phẩm đã được chọn trong các dropdown khác
  function updateProductDropdowns() {
    const selectedIds = new Set();
    const allSelects = container.querySelectorAll(".product-select");
    allSelects.forEach((select) => {
      if (select.value) selectedIds.add(select.value);
    });
    allSelects.forEach((select) => {
      const currentSelectedValue = select.value;
      select.querySelectorAll("option").forEach((option) => {
        if (option.value) {
          option.disabled =
            selectedIds.has(option.value) &&
            option.value !== currentSelectedValue;
        }
      });
    });
  }

  // Tạo và thêm một dòng form chi tiết thuốc mới từ template
  function addDetailForm() {
    const templateHtml = template.innerHTML.replace(/__prefix__/g, formIndex);
    const newFormFragment = document.createElement("div");
    newFormFragment.innerHTML = templateHtml;
    const newForm = newFormFragment.firstElementChild;

    const productSelect = newForm.querySelector(".product-select");
    if (productSelect) {
      const placeholder = new Option("---------", "");
      productSelect.add(placeholder);
      products.forEach((p) => {
        const option = new Option(p.name, p.id);
        productSelect.add(option);
      });
    }

    container.appendChild(newForm);
    formIndex++;
    formCountInput.value = formIndex;
    updateProductDropdowns();
  }

  // Khởi tạo form
  if (formIndex === 0) {
    addDetailForm();
  }

  // Gắn sự kiện cho các nút và input
  if (addButton) {
    addButton.addEventListener("click", addDetailForm);
  }

  if (container) {
    container.addEventListener("click", function (e) {
      if (e.target && e.target.classList.contains("remove-form")) {
        e.target.closest(".detail-form").remove();
        updateProductDropdowns();
      }
    });
    container.addEventListener("change", function (e) {
      if (e.target && e.target.classList.contains("product-select")) {
        updateProductDropdowns();
        updateUomDropdown(e.target);
      }
    });
  }
  updateProductDropdowns();
}
