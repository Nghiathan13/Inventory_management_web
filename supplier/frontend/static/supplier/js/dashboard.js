document.addEventListener("DOMContentLoaded", function () {
  // Lấy CSRF token từ một thẻ meta trong HTML (chúng ta sẽ thêm thẻ này sau)
  const csrfToken = document
    .querySelector('meta[name="csrf-token"]')
    .getAttribute("content");

  const confirmButtons = document.querySelectorAll(".confirm-order-btn");

  confirmButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const orderId = this.dataset.orderId;
      const url = this.dataset.url;

      if (confirm(`Bạn có chắc muốn xác nhận đơn hàng #${orderId} không?`)) {
        // Hiển thị spinner hoặc vô hiệu hóa nút để người dùng biết đang xử lý
        this.disabled = true;
        this.innerHTML =
          '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Đang xử lý...';

        fetch(url, {
          method: "POST",
          headers: {
            "X-CSRFToken": csrfToken,
            "Content-Type": "application/json",
          },
        })
          .then((response) => {
            if (!response.ok) {
              // Ném lỗi nếu server trả về status không phải 2xx
              throw new Error(`Lỗi Server: ${response.status}`);
            }
            return response.json();
          })
          .then((data) => {
            if (data.status === "success") {
              // Hiển thị pop-up hỏi người dùng có muốn tải file không
              if (
                confirm(
                  data.message +
                    "\n\nBạn có muốn tải về phiếu tem nhãn sản phẩm ngay bây giờ không?"
                )
              ) {
                // Nếu có, tạo một link ẩn và click vào nó để tải file
                const downloadLink = document.createElement("a");
                downloadLink.href = data.download_url;
                downloadLink.download = `tem_nhan_san_pham_${orderId}.pdf`; // Tên file mặc định
                document.body.appendChild(downloadLink);
                downloadLink.click();
                document.body.removeChild(downloadLink);
              }
              // Tải lại trang để cập nhật danh sách
              window.location.reload();
            } else {
              // Hiển thị thông báo lỗi từ server
              alert("Lỗi: " + data.message);
              // Kích hoạt lại nút
              this.disabled = false;
              this.innerHTML =
                '<i class="fas fa-check-circle me-1"></i> Xác Nhận';
            }
          })
          .catch((error) => {
            console.error("Error:", error);
            alert("Đã có lỗi kết nối hoặc xử lý xảy ra. Vui lòng thử lại.");
            // Kích hoạt lại nút
            this.disabled = false;
            this.innerHTML =
              '<i class="fas fa-check-circle me-1"></i> Xác Nhận';
          });
      }
    });
  });
});
