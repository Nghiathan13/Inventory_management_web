document.addEventListener('DOMContentLoaded', function() {
    const formatPrice = (input) => {
        let value = input.value.replace(/\./g, '').replace(/\D/g, '');
        if (value) {
            input.value = Number(value).toLocaleString('vi-VN');
        } else {
            input.value = '';
        }
    };

    const priceInputs = document.querySelectorAll('input[name="import_price"], input[name="sale_price"]');
    priceInputs.forEach(input => {
        formatPrice(input);
        input.addEventListener('input', function() {
            formatPrice(this);
        });
    });
});