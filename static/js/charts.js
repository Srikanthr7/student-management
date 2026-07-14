// EduTrack Pro - Chart.js Initializations

function initDashboardCharts(chartData) {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const gridColor = isDark ? '#1f2937' : '#e2e8f0';
    const textColor = isDark ? '#9ca3af' : '#475569';

    // Helper to get gradient
    const getGradient = (ctx, colorStart, colorEnd) => {
        const gradient = ctx.createLinearGradient(0, 0, 0, 200);
        gradient.addColorStop(0, colorStart);
        gradient.addColorStop(1, colorEnd);
        return gradient;
    };

    // 1. Enrollment Chart (Line)
    const enrollmentCtx = document.getElementById('enrollmentChart');
    if (enrollmentCtx) {
        const ctx = enrollmentCtx.getContext('2d');
        const grad = getGradient(ctx, 'rgba(79, 70, 229, 0.3)', 'rgba(79, 70, 229, 0)');
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.enrollment.labels,
                datasets: [{
                    label: 'New Registrations',
                    data: chartData.enrollment.data,
                    borderColor: '#4f46e5',
                    borderWidth: 3,
                    pointBackgroundColor: '#4f46e5',
                    pointHoverRadius: 6,
                    fill: true,
                    backgroundColor: grad,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: textColor }
                    },
                    y: {
                        grid: { color: gridColor },
                        ticks: { color: textColor, stepSize: 1 }
                    }
                }
            }
        });
    }

    // 2. Department Distribution Chart (Doughnut)
    const deptCtx = document.getElementById('deptChart');
    if (deptCtx) {
        new Chart(deptCtx, {
            type: 'doughnut',
            data: {
                labels: chartData.departments.labels,
                datasets: [{
                    data: chartData.departments.data,
                    backgroundColor: [
                        '#4f46e5', // CSE - Indigo
                        '#8b5cf6', // ECE - Purple
                        '#10b981', // ME - Green
                        '#f97316', // CE - Orange
                        '#06b6d4'  // IT - Cyan
                    ],
                    borderWidth: isDark ? 2 : 1,
                    borderColor: isDark ? '#111827' : '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: textColor,
                            boxWidth: 12,
                            padding: 15
                        }
                    }
                },
                cutout: '70%'
            }
        });
    }

    // 3. Grade Distribution Chart (Bar)
    const gradeCtx = document.getElementById('gradeChart');
    if (gradeCtx) {
        const ctx = gradeCtx.getContext('2d');
        const grad = getGradient(ctx, '#10b981', '#059669');
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: chartData.grades.labels,
                datasets: [{
                    label: 'Students Count',
                    data: chartData.grades.data,
                    backgroundColor: grad,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: textColor }
                    },
                    y: {
                        grid: { color: gridColor },
                        ticks: { color: textColor, stepSize: 5 }
                    }
                }
            }
        });
    }

    // 4. Asynchronous 7-Day Attendance Trend Chart (Area Line)
    const attCtx = document.getElementById('attendanceTrendChart');
    if (attCtx) {
        fetch('/dashboard/chart-data')
            .then(res => res.json())
            .then(data => {
                const trend = data.attendance_trend;
                const labels = trend.map(t => t.date);
                const values = trend.map(t => t.percentage);
                const ctx = attCtx.getContext('2d');
                const grad = getGradient(ctx, 'rgba(6, 182, 212, 0.25)', 'rgba(6, 182, 212, 0)');

                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Attendance Rate %',
                            data: values,
                            borderColor: '#06b6d4',
                            borderWidth: 3,
                            pointBackgroundColor: '#06b6d4',
                            fill: true,
                            backgroundColor: grad,
                            tension: 0.3
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false }
                        },
                        scales: {
                            x: {
                                grid: { display: false },
                                ticks: { color: textColor }
                            },
                            y: {
                                grid: { color: gridColor },
                                ticks: { color: textColor },
                                min: 0,
                                max: 100
                            }
                        }
                    }
                });
            })
            .catch(err => console.error("Error loading attendance trend chart: ", err));
    }
}
