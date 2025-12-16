document.addEventListener("DOMContentLoaded", function () {
  // =======================================================
  //           LỌC ĐƠN VỊ TÍNH (UOM FILTERING)
  // =======================================================
  function initUomFilter() {
    const elData = document.getElementById("uoms-by-category");
    const selCategory = document.getElementById("id_uom_category");
    const selBaseUom = document.getElementById("id_base_uom");

    // Kiểm tra phần tử DOM
    if (!elData || !selCategory || !selBaseUom) {
      console.warn("Warning: Missing UoM data elements.");
      return;
    }

    const uomData = JSON.parse(elData.textContent || "{}");

    // Hàm cập nhật Dropdown
    const updateOptions = () => {
      const catId = selCategory.value;
      const currentVal = selBaseUom.value;

      // Xóa danh sách cũ
      selBaseUom.innerHTML = "<option value=''>---------</option>";

      if (catId && uomData[catId]) {
        // Thêm option mới
        uomData[catId].forEach((uom) => {
          const opt = new Option(uom.name, uom.id);
          if (uom.id == currentVal) opt.selected = true;
          selBaseUom.add(opt);
        });
        selBaseUom.disabled = false;
      } else {
        selBaseUom.disabled = true;
      }
    };

    // Sự kiện thay đổi danh mục
    selCategory.addEventListener("change", updateOptions);

    // Chạy lần đầu (Chế độ Edit)
    if (selCategory.value) updateOptions();
    else selBaseUom.disabled = true;
  }

  // =======================================================
  //          ĐỊNH DẠNG TIỀN TỆ (CURRENCY FORMAT)
  // =======================================================
  function initPriceFormat() {
    const inputs = document.querySelectorAll('input[name="import_price"], input[name="sale_price"]');
    const form = document.querySelector("form");

    if (!inputs.length) return;

    // Hàm định dạng số (1000 -> 1,000)
    const formatNum = (val) => {
      if (!val) return "";
      return parseInt(val, 10).toLocaleString("en-US");
    };

    inputs.forEach((input) => {
      // 1. Format khi tải trang (Load)
      if (input.value) {
        const cleanVal = input.value.replace(/[^0-9.]/g, "");
        const floatVal = parseFloat(cleanVal);
        if (!isNaN(floatVal)) {
          input.value = floatVal.toLocaleString("en-US", { maximumFractionDigits: 0 });
        }
      }

      // 2. Format khi nhập liệu (Input)
      input.addEventListener("input", function () {
        const raw = this.value.replace(/[^0-9]/g, "");
        this.value = raw ? formatNum(raw) : "";
      });
    });

    // 3. Xử lý trước khi Submit (Xóa dấu phẩy)
    if (form) {
      form.addEventListener("submit", function () {
        inputs.forEach((input) => {
          input.value = input.value.replace(/,/g, "");
        });
      });
    }
  }

  // =======================================================
  //         XEM TRƯỚC ẢNH (IMAGE PREVIEW)
  // =======================================================
  function initImagePreview() {
    const inpFile = document.getElementById("id_image");
    const imgPreview = document.getElementById("image-preview");

    if (!inpFile || !imgPreview) return;

    // Sự kiện chọn file
    inpFile.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (ev) => {
          imgPreview.src = ev.target.result;
          imgPreview.style.display = "block";
        };
        reader.readAsDataURL(file);
      }
    });
  }

  // =======================================================
  //        KHỞI CHẠY (INIT)
  // =======================================================
  initUomFilter();
  initPriceFormat();
  initImagePreview();
});
