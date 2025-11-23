// Script xem trước ảnh cho form bệnh nhân
document.addEventListener("DOMContentLoaded", function () {
  // Tìm đến ô input file và khung ảnh preview
  const avatarInput = document.getElementById("id_avatar"); // Crispy forms tự tạo id này
  const avatarPreview = document.getElementById("avatar-preview");

  // Lắng nghe sự kiện "change" trên ô input file
  avatarInput.addEventListener("change", function (event) {
    // Lấy file mà người dùng đã chọn
    const file = event.target.files[0];

    // Nếu người dùng đã chọn một file
    if (file) {
      // Tạo một đối tượng FileReader để đọc nội dung file
      const reader = new FileReader();

      // Thiết lập hàm callback để chạy khi file được đọc xong
      reader.onload = function (e) {
        // Cập nhật thuộc tính 'src' của thẻ img bằng dữ liệu của ảnh mới
        avatarPreview.src = e.target.result;
      };

      // Bắt đầu đọc file ảnh
      reader.readAsDataURL(file);
    }
  });
});
