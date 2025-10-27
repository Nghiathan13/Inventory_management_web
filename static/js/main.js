document.addEventListener("DOMContentLoaded", function () {
  const brandText = document.querySelector(".brand-text");
  if (brandText) {
    const text = "Adoo Medicine!";
    let index = 0;
    let isDeleting = false;

    function type() {
      // Kiểm tra lại một lần nữa để an toàn
      if (!brandText) return;

      const currentText = text.substring(0, index);
      brandText.textContent = currentText;

      if (isDeleting) {
        index--;
      } else {
        index++;
      }

      if (index > text.length) {
        isDeleting = true;
        setTimeout(type, 2000); // Tạm dừng trước khi xóa
      } else if (index === 0) {
        isDeleting = false;
        setTimeout(type, 500); // Tạm dừng trước khi gõ lại
      } else {
        const typingSpeed = isDeleting ? 100 : 200;
        setTimeout(type, typingSpeed);
      }
    }

    // Bắt đầu hiệu ứng
    type();
  }
  const tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
});
