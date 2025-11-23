// Hàm này sẽ được gọi khi toàn bộ trang đã tải xong
document.addEventListener("DOMContentLoaded", function () {
  // --- LOGIC CHO TRANG OVERVIEW ---
  if (document.getElementById("inventoryBarChart")) {
    // 1. Đọc dữ liệu từ thẻ script do Django tạo ra
    const productsData = JSON.parse(
      document.getElementById("products-data-json").textContent
    );
    // 2. Gọi hàm vẽ biểu đồ
    drawInventoryChart(
      productsData.map((p) => p.name),
      productsData.map((p) => p.quantity)
    );
  }

  if (document.getElementById("categoryPieChart")) {
    const categoryData = JSON.parse(
      document.getElementById("category-data-json").textContent
    );
    drawCategoryChart(categoryData);
  }

  // --- LOGIC CHO TRANG DISPENSE ANALYSIS ---
  if (document.getElementById("dispenseDoughnutChart")) {
    const dispenseData = JSON.parse(
      document.getElementById("dispense-data-json").textContent
    );
    drawDispenseChart(dispenseData);
  }

  if (document.getElementById("salesTrendLineChart")) {
    const salesTrendData = JSON.parse(
      document.getElementById("sales-trend-data-json").textContent
    );
    drawSalesTrendChart(salesTrendData);
  }
});

// =======================================================
//        CÁC HÀM VẼ BIỂU ĐỒ CHUNG
// =======================================================

// Hàm vẽ biểu đồ Tồn kho (Bar)
function drawInventoryChart(chartId, data) {
  const ctx = document.getElementById(chartId);
  if (!ctx) return;

  const labels = data.map((p) => p.name);
  const quantities = data.map((p) => p.quantity);

  new Chart(ctx.getContext("2d"), {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Số Lượng Tồn Kho",
          data: quantities,
          backgroundColor: "#0a9396",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: "Top 15 Sản Phẩm Tồn Kho Nhiều Nhất",
          font: { size: 16 },
        },
        legend: { display: false },
      },
      scales: { y: { beginAtZero: true } },
    },
  });
}

// Hàm vẽ biểu đồ Danh mục (Pie)
function drawCategoryChart(chartId, data) {
  const ctx = document.getElementById(chartId);
  if (!ctx) return;

  const labels = data.map((c) => c.name);
  const counts = data.map((c) => c.count);

  new Chart(ctx.getContext("2d"), {
    type: "pie",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Số Lượng Sản Phẩm",
          data: counts,
          backgroundColor: [
            "#DE51A8",
            "#0a9396",
            "#ee9b00",
            "#94d2bd",
            "#6c5ce7",
          ],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: "Phân Bổ Sản Phẩm Theo Nhóm",
          font: { size: 16 },
        },
      },
    },
  });
}

// Hàm vẽ biểu đồ Tỉ lệ Xuất kho (Doughnut)
function drawDispenseChart(chartId, data) {
  const ctx = document.getElementById(chartId);
  if (!ctx) return;

  const labels = data.map((p) => p.product__name);
  const totals = data.map((p) => p.total_sold);

  new Chart(ctx.getContext("2d"), {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Tổng Số Lượng Đã Bán",
          data: totals,
          backgroundColor: [
            "#DE51A8",
            "#0a9396",
            "#ee9b00",
            "#94d2bd",
            "#ca6702",
            "#ae2012",
            "#005f73",
          ],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: "Top 10 Sản Phẩm Bán Chạy Nhất",
          font: { size: 16 },
        },
      },
    },
  });
}

// Hàm vẽ biểu đồ Xu hướng Bán hàng (Line)
function drawSalesTrendChart(chartId, data) {
  const ctx = document.getElementById(chartId);
  if (!ctx) return;

  new Chart(ctx.getContext("2d"), {
    type: "line",
    data: {
      datasets: [
        {
          label: "Số Lượng Toa Thuốc Hàng Ngày",
          data: data,
          borderColor: "#DE51A8",
          tension: 0.1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: "Xu Hướng Cấp Phát 7 Ngày Qua",
          font: { size: 16 },
        },
      },
      scales: {
        x: { type: "time", time: { unit: "day" } },
        y: { beginAtZero: true, ticks: { stepSize: 1 } },
      },
    },
  });
}
