// Script xem trước ảnh cho form bệnh nhân
document.addEventListener("DOMContentLoaded", function () {
  const avatarInput = document.getElementById("id_avatar"); // Crispy forms tự tạo id này
  const avatarPreview = document.getElementById("avatar-preview");

  avatarInput.addEventListener("change", function (event) {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = function (e) {
        avatarPreview.src = e.target.result;
      };
      reader.readAsDataURL(file);
    }
  });
});
