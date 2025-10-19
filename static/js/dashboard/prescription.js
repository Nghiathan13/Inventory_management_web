function initializePrescriptionForm(products, uoms) {
  const addButton = document.getElementById("add-more");
  const container = document.getElementById("details-container");
  const formCountInput = document.getElementById("form-count");
  let formIndex = container.querySelectorAll(".detail-form").length;

  function updateDropdowns() {
    const selectedIds = new Set();
    const allSelects = container.querySelectorAll('select[name*="-product"]');
    allSelects.forEach((select) => {
      if (select.value) {
        selectedIds.add(select.value);
      }
    });
    allSelects.forEach((select) => {
      const currentSelectedValue = select.value;
      const options = select.querySelectorAll("option");
      options.forEach((option) => {
        if (option.value) {
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

  function addDetailForm() {
    const newFormHtml = `
            <div class="row mb-3 detail-form align-items-end" data-index="${formIndex}">
                <div class="col-md-5">
                    <label for="id_details-${formIndex}-product">Name</label>
                    <select name="details-${formIndex}-product" id="id_details-${formIndex}-product" class="form-control" required>
                        <option value="">---------</option>
                        ${products
                          .map(
                            (p) => `<option value="${p.id}">${p.name}</option>`
                          )
                          .join("")}
                    </select>
                </div>
                <div class="col-md-3">
                    <label for="id_details-${formIndex}-uom">Unit</label>
                    <select name="details-${formIndex}-uom" id="id_details-${formIndex}-uom" class="form-control" required>
                        <option value="">---------</option>
                        ${uoms
                          .map(
                            (u) => `<option value="${u.id}">${u.name}</option>`
                          )
                          .join("")}
                    </select>
                </div>
                <div class="col-md-2">
                    <label for="id_details-${formIndex}-quantity">Quantity</label>
                    <input type="number" name="details-${formIndex}-quantity" id="id_details-${formIndex}-quantity" class="form-control" min="1" required>
                </div>
                <div class="col-md-2 align-self-end">
                    <button type="button" class="btn btn-danger btn-sm remove-form w-100">Delete</button>
                </div>
            </div>`;
    container.insertAdjacentHTML("beforeend", newFormHtml);
    formIndex++;
    formCountInput.value = formIndex;
    updateDropdowns();
  }

  if (formIndex === 0) {
    addDetailForm();
  }
  if (addButton) {
    addButton.addEventListener("click", addDetailForm);
  }
  if (container) {
    container.addEventListener("click", function (e) {
      if (e.target && e.target.classList.contains("remove-form")) {
        e.target.closest(".detail-form").remove();
        updateDropdowns();
      }
    });
    container.addEventListener("change", function (e) {
      if (e.target && e.target.tagName === "SELECT") {
        updateDropdowns();
      }
    });
  }
  updateDropdowns();
}
