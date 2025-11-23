document.addEventListener("DOMContentLoaded", function () {
  // =======================================================
  //   MODULE 1: LOGIC LỌC ĐƠN VỊ TÍNH (UOM)
  // =======================================================
  function setupUomFiltering() {
    const uomsByCatData = document.getElementById("uoms-by-category");
    const uomCategorySelect = document.getElementById("id_uom_category");
    const baseUomSelect = document.getElementById("id_base_uom");

    // Kiểm tra các element bắt buộc
    if (!uomsByCatData || !uomCategorySelect || !baseUomSelect) {
      console.warn("Thiếu dữ liệu UoM hoặc Dropdown. Bỏ qua logic lọc.");
      return;
    }

    const uomsByCat = JSON.parse(uomsByCatData.textContent || "{}");

    const filterAllUomOptions = () => {
      const selectedCategoryId = uomCategorySelect.value;
      const currentBaseUomValue = baseUomSelect.value;

      // Reset Dropdown
      baseUomSelect.innerHTML = "<option value=''>---------</option>";

      if (selectedCategoryId && uomsByCat[selectedCategoryId]) {
        uomsByCat[selectedCategoryId].forEach((uom) => {
          const option = new Option(uom.name, uom.id);
          if (uom.id == currentBaseUomValue) option.selected = true;
          baseUomSelect.add(option);
        });
        baseUomSelect.disabled = false;
      } else {
        baseUomSelect.disabled = true;
      }
    };

    uomCategorySelect.addEventListener("change", filterAllUomOptions);

    // Chạy ngay lần đầu để lọc khi Edit
    if (uomCategorySelect.value) {
      filterAllUomOptions();
    } else {
      baseUomSelect.disabled = true;
    }
  }

  // =======================================================
  //   MODULE 2: ĐỊNH DẠNG Ô NHẬP GIÁ
  // =======================================================
  function setupPriceFormatting() {
    const inputs = document.querySelectorAll('input[name="import_price"], input[name="sale_price"]');

    inputs.forEach((input) => {
      // 1. KHI LOAD: Format giá trị từ DB
      if (input.value) {
        // Loại bỏ ký tự không phải số (nếu có)
        const rawValue = input.value.replace(/[^0-9.]/g, "");
        const floatVal = parseFloat(rawValue);

        if (!isNaN(floatVal)) {
          // Format thành tiền tệ (tự động bỏ .00 nếu là số chẵn)
          input.value = floatVal.toLocaleString("en-US", {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
          });
        }
      }

      // 2. KHI NHẬP LIỆU (INPUT): Format realtime
      input.addEventListener("input", function () {
        // Lấy vị trí con trỏ
        let cursorPosition = this.selectionStart;

        // Xóa hết ký tự không phải số
        let rawValue = this.value.replace(/[^0-9]/g, "");

        if (rawValue) {
          const number = parseInt(rawValue, 10);
          // Format lại có dấu phẩy
          const formattedValue = number.toLocaleString("en-US");

          // Cập nhật giá trị
          this.value = formattedValue;
        } else {
          this.value = "";
        }
      });
    });

    // Trước khi submit: Xóa dấu phẩy để gửi số nguyên lên server
    const form = document.querySelector("form");
    if (form) {
      form.addEventListener("submit", function () {
        inputs.forEach((input) => {
          input.value = input.value.replace(/,/g, "");
        });
      });
    }
  }
  // =======================================================
  //   MODULE 3: XEM TRƯỚC HÌNH ẢNH SẢN PHẨM
  // =======================================================
  function setupImagePreview() {
    const imageInput = document.getElementById("id_image");
    const imagePreview = document.getElementById("image-preview");
    if (!imageInput || !imagePreview) return;
    imageInput.addEventListener("change", (event) => {
      const file = event.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
          imagePreview.src = e.target.result;
        };
        reader.readAsDataURL(file);
      }
    });
  }

  // =======================================================
  //   KHỞI CHẠY TẤT CẢ CÁC MODULE JAVASCRIPT
  // =======================================================
  setupUomFiltering();
  setupPriceFormatting();
  setupImagePreview();
});
