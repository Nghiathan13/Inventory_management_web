document.addEventListener("DOMContentLoaded", function () {
  const brandText = document.querySelector(".brand-text");
  const text = "Adoo Medicine!";
  let index = 0;
  let isDeleting = false;

  function type() {
    const currentText = text.substring(0, index);
    brandText.textContent = currentText;

    if (isDeleting) {
      index--;
    } else {
      index++;
    }

    if (index > text.length) {
      isDeleting = true;
      setTimeout(type, 2000); // Pause before deleting
    } else if (index === 0) {
      isDeleting = false;
      setTimeout(type, 500); // Pause before re-typing
    } else {
      const typingSpeed = isDeleting ? 100 : 200;
      setTimeout(type, typingSpeed);
    }
  }

  type();
});
