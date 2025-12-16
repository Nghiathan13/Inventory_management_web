document.addEventListener("DOMContentLoaded", function () {
  // =======================================================
  //        1. KHỞI TẠO BIỂU ĐỒ (INITIALIZATION)
  // =======================================================

  // --- Biểu đồ Tồn kho (Overview) ---
  const invEl = document.getElementById("inventoryBarChart");
  if (invEl) {
    const rawData = JSON.parse(document.getElementById("products-data-json").textContent);
    renderInventoryChart("inventoryBarChart", rawData);
  }

  // --- Biểu đồ Danh mục (Overview) ---
  const catEl = document.getElementById("categoryPieChart");
  if (catEl) {
    const rawData = JSON.parse(document.getElementById("category-data-json").textContent);
    renderCategoryChart("categoryPieChart", rawData);
  }

  // --- Biểu đồ Xuất kho (Dispense Analysis) ---
  const dispenseEl = document.getElementById("dispenseDoughnutChart");
  if (dispenseEl) {
    const rawData = JSON.parse(document.getElementById("dispense-data-json").textContent);
    renderDispenseChart("dispenseDoughnutChart", rawData);
  }

  // --- Biểu đồ Xu hướng (Dispense Analysis) ---
  const trendEl = document.getElementById("salesTrendLineChart");
  if (trendEl) {
    const rawData = JSON.parse(document.getElementById("sales-trend-data-json").textContent);
    renderSalesTrendChart("salesTrendLineChart", rawData);
  }
});

// =======================================================
//        2. HÀM VẼ BIỂU ĐỒ (RENDER FUNCTIONS)
// =======================================================

/**
 * Vẽ biểu đồ cột: Tồn kho
 */
function renderInventoryChart(canvasId, data) {
  const ctx = document.getElementById(canvasId).getContext("2d");

  // Xử lý dữ liệu
  const labels = data.map((p) => p.name);
  const values = data.map((p) => p.quantity);

  // Vẽ biểu đồ
  new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Stock Quantity",
          data: values,
          backgroundColor: "#0a9396",
          borderRadius: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: "Top 15 Highest Stock Products",
          font: { size: 16 },
        },
        legend: { display: false },
      },
      scales: {
        y: { beginAtZero: true },
      },
    },
  });
}

/**
 * Vẽ biểu đồ tròn: Phân bổ danh mục
 */
function renderCategoryChart(canvasId, data) {
  const ctx = document.getElementById(canvasId).getContext("2d");

  // Xử lý dữ liệu
  const labels = data.map((c) => c.name);
  const values = data.map((c) => c.count);

  // Vẽ biểu đồ
  new Chart(ctx, {
    type: "pie",
    data: {
      labels: labels,
      datasets: [
        {
          data: values,
          backgroundColor: ["#DE51A8", "#0a9396", "#ee9b00", "#94d2bd", "#6c5ce7", "#ff9f43", "#5f27cd"],
          hoverOffset: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: "Product Distribution by Category",
          font: { size: 16 },
        },
        legend: { position: "right" },
      },
    },
  });
}

/**
 * Vẽ biểu đồ vành khuyên: Top bán chạy
 */
function renderDispenseChart(canvasId, data) {
  const ctx = document.getElementById(canvasId).getContext("2d");

  // Xử lý dữ liệu
  const labels = data.map((p) => p.product__name);
  const values = data.map((p) => p.total_sold);

  // Vẽ biểu đồ
  new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Total Sold",
          data: values,
          backgroundColor: ["#DE51A8", "#0a9396", "#ee9b00", "#94d2bd", "#ca6702", "#ae2012", "#005f73"],
          hoverOffset: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: "Top 10 Best Selling Products",
          font: { size: 16 },
        },
      },
    },
  });
}

/**
 * Vẽ biểu đồ đường: Xu hướng bán hàng
 */
function renderSalesTrendChart(canvasId, data) {
  const ctx = document.getElementById(canvasId).getContext("2d");

  // Vẽ biểu đồ
  new Chart(ctx, {
    type: "line",
    data: {
      datasets: [
        {
          label: "Daily Prescriptions",
          data: data, // Dữ liệu dạng {x: date, y: count} từ Django
          borderColor: "#DE51A8",
          backgroundColor: "rgba(222, 81, 168, 0.1)",
          tension: 0.3,
          fill: true,
          pointRadius: 4,
          pointHoverRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: "Dispense Trend (Last 7 Days)",
          font: { size: 16 },
        },
      },
      scales: {
        x: {
          type: "time",
          time: { unit: "day", tooltipFormat: "dd/MM/yyyy" },
        },
        y: {
          beginAtZero: true,
          ticks: { stepSize: 1 },
        },
      },
    },
  });
}
