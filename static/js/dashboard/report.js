// Hàm vẽ biểu đồ Tồn kho (Bar)
function drawInventoryChart(labels, quantities) {
    const ctx = document.getElementById('inventoryBarChart');
    if (!ctx) return;
    new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Inventory Quantity',
                data: quantities,
                backgroundColor: '#005f73',
                borderRadius: 4, 
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Top 15 Most In-Stock Products',
                    font: { size: 16 }
                },
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Hàm vẽ biểu đồ Danh mục (Pie)
function drawCategoryChart(categoryData) {
    const ctx = document.getElementById('categoryPieChart');
    if (!ctx) return;
    new Chart(ctx.getContext('2d'), {
        type: 'pie',
        data: {
            labels: categoryData.map(c => c.category || "Unclassified"),
            datasets: [{
                label: 'Quantity of medicine',
                data: categoryData.map(c => c.count),
                backgroundColor: ['#DE51A8', '#0a9396', '#ee9b00', '#94d2bd', '#6c5ce7'],
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Product distribution by category',
                    font: { size: 16 }
                }
            }
        }
    });
}

// Hàm vẽ biểu đồ Tỉ lệ Xuất kho (Doughnut)
function drawDispenseChart(dispenseData) {
    const ctx = document.getElementById('dispenseDoughnutChart');
    if (!ctx) return;
    new Chart(ctx.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: dispenseData.map(p => p.product__name),
            datasets: [{
                label: 'Total prescriptions prescribed',
                data: dispenseData.map(p => p.total_sold),
                backgroundColor: ['#DE51A8', '#0a9396', '#ee9b00', '#94d2bd', '#ca6702'],
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Top 10 Best-Selling Medications',
                    font: { size: 16 }
                }
            }
        }
    });
}

// Hàm vẽ biểu đồ Xu hướng Bán hàng (Line)
function drawSalesTrendChart(trendData) {
    const ctx = document.getElementById('salesTrendLineChart');
    if (!ctx) return;
    new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: trendData.map(d => new Date(d.date_sold).toLocaleDateString('vi-VN')),
            datasets: [{
                label: 'Daily number of prescriptions issued (last 7 days)',
                data: trendData.map(d => d.count),
                borderColor: '#DE51A8',
                tension: 0.4,
                fill: false,
                pointBackgroundColor: '#DE51A8',
                pointRadius: 5,
                pointHoverRadius: 7,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Medicine dispensing trends',
                    font: { size: 16 }
                }
            },

            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                    }
                }
            }
        }
    });
}