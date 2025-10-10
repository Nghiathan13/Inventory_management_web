function initializePrescriptionForm(products) {
  // DOMContentLoaded không cần thiết ở đây vì hàm này được gọi sau khi DOM đã tải.
  const addButton = document.getElementById("add-more");
  const container = document.getElementById("details-container");
  const formCountInput = document.getElementById("form-count");

  // Đếm số lượng form chi tiết đã có sẵn trên trang (nếu có)
  let formIndex = container.children.length;

  /**
   * Hàm để tạo và thêm một dòng form chi tiết thuốc mới.
   */
  function addDetailForm() {
    const newFormHtml = `
            <div class="row mb-3 detail-form align-items-end" data-index="${formIndex}">
                <div class="col-md-6">
                    <label for="id_details-${formIndex}-product">Tên thuốc</label>
                    <select name="details-${formIndex}-product" id="id_details-${formIndex}-product" class="form-control" required>
                        <option value="">---------</option>
                        ${products
                          .map((p) => `<option value="${p.id}">${p.name}</option>`)
                          .join("")}
                    </select>
                </div>
                <div class="col-md-4">
                    <label for="id_details-${formIndex}-quantity">Số lượng</label>
                    <input type="number" name="details-${formIndex}-quantity" id="id_details-${formIndex}-quantity" class="form-control" min="1" required>
                </div>
                <div class="col-md-2">
                    <button type="button" class="btn btn-danger remove-form w-100">Xóa</button>
                </div>
            </div>`;

    container.insertAdjacentHTML("beforeend", newFormHtml);
    formIndex++;
    formCountInput.value = formIndex;
  }

  // Nếu không có form nào, thêm một form mặc định khi tải trang
  if (formIndex === 0) {
    addDetailForm();
  }

  // Gắn sự kiện click cho nút "Thêm thuốc"
  if (addButton) {
    addButton.addEventListener("click", addDetailForm);
  }

  // Gắn sự kiện click cho các nút "Xóa" (sử dụng event delegation)
  if (container) {
    container.addEventListener("click", function (e) {
      if (e.target && e.target.classList.contains("remove-form")) {
        e.target.closest(".detail-form").remove();
      }
    });
  }
}
