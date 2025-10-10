function initializeReportCharts(products, orders) {
    // === BIỂU ĐỒ 1: SỐ LƯỢNG TỒN KHO ===
    const productLabels = products.map(p => p.name);
    const productQuantities = products.map(p => p.quantity);

    const ctx1 = document.getElementById('productQuantityChart');
    if (ctx1) {
        new Chart(ctx1.getContext('2d'), {
            type: 'bar',
            data: {
                labels: productLabels,
                datasets: [{
                    label: 'Số Lượng Tồn Kho',
                    data: productQuantities,
                    backgroundColor: '#005f73',
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Số Lượng Thuốc Hiện Có Trong Kho',
                        font: { size: 16 }
                    }
                },
                scales: { y: { beginAtZero: true } }
            }
        });
    }

    // === BIỂU ĐỒ 2: PHÂN BỐ ĐƠN HÀNG ĐÃ XUẤT ===
    // Xử lý dữ liệu để tổng hợp số lượng xuất kho cho mỗi sản phẩm
    const orderData = {};
    orders.forEach(order => {
        if (orderData[order.product_name]) {
            orderData[order.product_name] += order.quantity;
        } else {
            orderData[order.product_name] = order.quantity;
        }
    });
    
    const orderLabels = Object.keys(orderData);
    const orderQuantities = Object.values(orderData);

    const ctx2 = document.getElementById('orderDistributionChart');
    if (ctx2) {
        new Chart(ctx2.getContext('2d'), {
            type: 'pie',
            data: {
                labels: orderLabels,
                datasets: [{
                    label: 'Số lượng đã xuất',
                    data: orderQuantities,
                    backgroundColor: ['#DE51A8', '#0a9396', '#ee9b00', '#94d2bd', '#005f73', '#e9d8a6', '#ca6702'],
                    borderColor: '#ffffff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Tỉ Lệ Các Loại Thuốc Đã Được Cấp Phát',
                        font: { size: 16 }
                    }
                }
            }
        });
    }
}