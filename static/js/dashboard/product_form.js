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
