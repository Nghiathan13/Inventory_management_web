function initializeProductForm(uomsByCat) {
  // --- PHẦN 1: LOGIC LỌC ĐƠN VỊ TÍNH (UOM FILTERING) ---
  const uomCategorySelect = document.getElementById("id_uom_category");
  const baseUomSelect = document.getElementById("id_base_uom");

  function filterUoMOptions() {
    const selectedCategoryId = uomCategorySelect.value;
    // Lưu lại giá trị đang được chọn của Base UoM (quan trọng cho trang Edit)
    const currentBaseUomValue = baseUomSelect.value;

    baseUomSelect.innerHTML = ""; // Xóa tất cả các option cũ
    baseUomSelect.add(new Option("---------", "")); // Thêm option placeholder

    if (selectedCategoryId && uomsByCat[selectedCategoryId]) {
      const uoms = uomsByCat[selectedCategoryId];
      uoms.forEach((uom) => {
        const option = new Option(uom.name, uom.id);
        // Nếu option này trùng với giá trị đã chọn trước đó, chọn lại nó
        if (uom.id == currentBaseUomValue) {
          option.selected = true;
        }
        baseUomSelect.add(option);
      });
      baseUomSelect.disabled = false;
    } else {
      baseUomSelect.disabled = true;
    }
  }

  if (uomCategorySelect && baseUomSelect) {
    uomCategorySelect.addEventListener("change", filterUoMOptions);
    // Chạy hàm lọc lần đầu khi trang tải để xử lý giá trị ban đầu (nếu có)
    filterUoMOptions();
  }

  // --- PHẦN 2: ĐỊNH DẠNG GIÁ VỚI DẤU PHẨY NGHÌN (PRICE FORMATTING) ---
  document.addEventListener("DOMContentLoaded", function () {
    const formatPriceWithCommas = (input) => {
      let numericValue = input.value.replace(/[^0-9]/g, "");

      if (numericValue) {
        input.value = Number(numericValue).toLocaleString("en-US");
      } else {
        input.value = "";
      }
    };

    const priceInputs = document.querySelectorAll(
      'input[name="import_price"], input[name="sale_price"]'
    );

    priceInputs.forEach((input) => {
      let initialValue = input.value;
      if (initialValue.includes(".")) {
        initialValue = initialValue.split(".")[0];
      }
      input.value = initialValue;
      formatPriceWithCommas(input);
      input.addEventListener("input", function () {
        formatPriceWithCommas(this);
      });
    });
  });
}

const imageInput = document.getElementById("id_image");
const imagePreview = document.getElementById("image-preview");
if (imageInput && imagePreview) {
  imageInput.addEventListener("change", function (event) {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = function (e) {
        imagePreview.src = e.target.result;
      };
      reader.readAsDataURL(file);
    }
  });
}
