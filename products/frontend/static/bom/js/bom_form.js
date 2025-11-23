function initializeBomForm(productsWithUomCat, uomsByCat) {
  const productSelect = document.getElementById("id_product");
  const uomFromSelect = document.getElementById("id_uom_from");
  const uomToSelect = document.getElementById("id_uom_to");

  if (!productSelect || !uomFromSelect || !uomToSelect) {
    console.error("One or more select fields for BOM form are missing.");
    return;
  }

  /**
   * Hàm để lọc và điền các lựa chọn cho dropdown UoM.
   */
  function filterUomDropdowns() {
    const selectedProductId = productSelect.value;
    const selectedProductInfo = productsWithUomCat.find(
      (p) => p.id == selectedProductId
    );

    // Xóa sạch các option cũ
    uomFromSelect.innerHTML = '<option value="">---------</option>';
    uomToSelect.innerHTML = '<option value="">---------</option>';

    // Nếu đã chọn sản phẩm và sản phẩm đó có nhóm UoM
    if (selectedProductInfo && selectedProductInfo.uom_category_id) {
      const uomCategoryId = selectedProductInfo.uom_category_id;
      const relevantUoms = uomsByCat[uomCategoryId] || [];

      relevantUoms.forEach((uom) => {
        uomFromSelect.add(new Option(uom.name, uom.id));
        uomToSelect.add(new Option(uom.name, uom.id));
      });
      uomFromSelect.disabled = false;
      uomToSelect.disabled = false;
    } else {
      uomFromSelect.disabled = true;
      uomToSelect.disabled = true;
    }
  }

  // Gắn sự kiện "change" cho dropdown sản phẩm
  productSelect.addEventListener("change", filterUomDropdowns);

  if (productSelect.value) {
    filterUomDropdowns();
  } else {
    uomFromSelect.disabled = true;
    uomToSelect.disabled = true;
  }
}
