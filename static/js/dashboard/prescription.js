function initializePrescriptionForm(products, uoms) {
    const addButton = document.getElementById("add-more");
    const container = document.getElementById("details-container");
    const formCountInput = document.getElementById("form-count");
    
    // Khởi tạo index dựa trên số lượng form đã có trên trang
    let formIndex = container.querySelectorAll('.detail-form').length;

    /**
     * Cập nhật tất cả các dropdown để vô hiệu hóa các thuốc đã được chọn.
     */
    function updateDropdowns() {
        const selectedIds = new Set();
        const allSelects = container.querySelectorAll('select[name*="-product"]');
        
        // 1. Lấy danh sách ID của tất cả các thuốc đã được chọn
        allSelects.forEach((select) => {
            if (select.value) {
                selectedIds.add(select.value);
            }
        });

        // 2. Lặp qua từng dropdown để cập nhật các option bên trong nó
        allSelects.forEach((select) => {
            const currentSelectedValue = select.value;
            const options = select.querySelectorAll("option");

            options.forEach((option) => {
                if (option.value) {
                    // Vô hiệu hóa option NẾU nó đã được chọn ở nơi khác VÀ không phải là giá trị hiện tại
                    if (
                        selectedIds.has(option.value) &&
                        option.value !== currentSelectedValue
                    ) {
                        option.disabled = true;
                    } else {
                        option.disabled = false;
                    }
                }
            });
        });
    }

    /**
     * Hàm để tạo và thêm một dòng form chi tiết thuốc mới.
     */
    function addDetailForm() {
        const newFormHtml = `
            <div class="row mb-3 detail-form align-items-end" data-index="${formIndex}">
                
                <!-- Ô CHỌN SẢN PHẨM -->
                <div class="col-md-5">
                    <label for="id_details-${formIndex}-product">Tên thuốc</label>
                    <select name="details-${formIndex}-product" id="id_details-${formIndex}-product" class="form-control" required>
                        <option value="">---------</option>
                        ${products.map(p => `<option value="${p.id}">${p.name}</option>`).join('')}
                    </select>
                </div>
                
                <!-- Ô CHỌN ĐƠN VỊ TÍNH -->
                <div class="col-md-3">
                    <label for="id_details-${formIndex}-uom">Đơn vị</label>
                    <select name="details-${formIndex}-uom" id="id_details-${formIndex}-uom" class="form-control" required>
                         ${uoms.map(u => `<option value="${u.id}">${u.name}</option>`).join('')}
                    </select>
                </div>
                
                <!-- Ô SỐ LƯỢNG -->
                <div class="col-md-2">
                    <label for="id_details-${formIndex}-quantity">Số lượng</label>
                    <input type="number" name="details-${formIndex}-quantity" id="id_details-${formIndex}-quantity" class="form-control" min="1" required>
                </div>
                
                <!-- NÚT XÓA -->
                <div class="col-md-2">
                    <button type="button" class="btn btn-danger btn-sm remove-form w-100">Xóa</button>
                </div>
            </div>`;
        
        container.insertAdjacentHTML('beforeend', newFormHtml);

        formIndex++;
        formCountInput.value = formIndex;
        updateDropdowns(); // Cập nhật lại các dropdown sau khi thêm
    }

    // Nếu không có form nào, thêm một form mặc định khi tải trang
    if (formIndex === 0) {
        addDetailForm();
    }

    // Gắn sự kiện click cho nút "Thêm thuốc"
    if (addButton) {
        addButton.addEventListener("click", addDetailForm);
    }

    // Gắn sự kiện cho toàn bộ container
    if (container) {
        container.addEventListener("click", function (e) {
            // Khi nút "Xóa" được nhấn
            if (e.target && e.target.classList.contains("remove-form")) {
                e.target.closest(".detail-form").remove();
                updateDropdowns(); // Cập nhật lại các dropdown sau khi xóa
            }
        });

        // Khi một lựa chọn trong dropdown thay đổi
        container.addEventListener("change", function (e) {
            if (e.target && e.target.tagName === "SELECT") {
                updateDropdowns(); // Cập nhật lại tất cả các dropdown
            }
        });
    }
    
    // Cập nhật lần đầu khi tải trang
    updateDropdowns();
}