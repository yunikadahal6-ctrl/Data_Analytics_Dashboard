const chartData = JSON.parse(document.getElementById("chart-data").textContent);

const chartColors = ["#2563eb", "#14b8a6", "#f97316", "#8b5cf6", "#eab308"];

new Chart(document.getElementById("product-chart"), {
    type: "bar",
    data: {
        labels: chartData.products.labels,
        datasets: [{
            label: "Units sold",
            data: chartData.products.values,
            backgroundColor: "#2563eb",
            borderRadius: 6,
        }],
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
    },
});

new Chart(document.getElementById("region-chart"), {
    type: "doughnut",
    data: {
        labels: chartData.regions.labels,
        datasets: [{
            label: "Units sold",
            data: chartData.regions.values,
            backgroundColor: chartColors,
            borderColor: "#ffffff",
            borderWidth: 3,
        }],
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: "bottom" } },
    },
});

new Chart(document.getElementById("time-chart"), {
    type: "line",
    data: {
        labels: chartData.daily_sales.labels,
        datasets: [{
            label: "Units sold",
            data: chartData.daily_sales.values,
            borderColor: "#0f766e",
            backgroundColor: "rgb(20 184 166 / 18%)",
            pointBackgroundColor: "#0f766e",
            pointRadius: 4,
            fill: true,
            tension: 0.3,
        }],
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
    },
});
