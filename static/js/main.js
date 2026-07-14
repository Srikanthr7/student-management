// EduTrack Pro - Core Javascript Implementation

document.addEventListener('DOMContentLoaded', () => {
    // ----------------------------------------------------
    // Theme Management (Light / Dark Mode)
    // ----------------------------------------------------
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');
    
    // Get stored theme or check system preference
    const getPreferredTheme = () => {
        const stored = localStorage.getItem('theme');
        if (stored) return stored;
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    };

    const applyTheme = (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        
        // Update icon class
        if (themeIcon) {
            if (theme === 'dark') {
                themeIcon.classList.remove('fa-moon');
                themeIcon.classList.add('fa-sun');
            } else {
                themeIcon.classList.remove('fa-sun');
                themeIcon.classList.add('fa-moon');
            }
        }
    };

    // Apply preferred theme on load
    applyTheme(getPreferredTheme());

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            applyTheme(newTheme);
        });
    }

    // ----------------------------------------------------
    // Sidebar Behavior & Responsiveness
    // ----------------------------------------------------
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const mainWrapper = document.getElementById('mainWrapper');

    const toggleSidebar = () => {
        if (window.innerWidth >= 992) {
            sidebar.classList.toggle('collapsed');
            mainWrapper.classList.toggle('collapsed');
        } else {
            sidebar.classList.toggle('show');
        }
    };

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleSidebar();
        });
    }

    // Close sidebar on mobile when clicking outside
    document.addEventListener('click', (e) => {
        if (window.innerWidth < 992 && sidebar && sidebar.classList.contains('show')) {
            if (!sidebar.contains(e.target) && e.target !== sidebarToggle && !sidebarToggle.contains(e.target)) {
                sidebar.classList.remove('show');
            }
        }
    });

    // ----------------------------------------------------
    // Notifications Loader
    // ----------------------------------------------------
    const notifBell = document.getElementById('notifBell');
    const notifList = document.getElementById('notifList');

    const loadNotifications = () => {
        if (!notifList) return;
        
        fetch('/notifications/api/recent')
            .then(res => res.json())
            .then(data => {
                if (data.length === 0) {
                    notifList.innerHTML = '<div class="text-center p-3 text-muted small">No new notifications.</div>';
                    return;
                }
                
                let html = '';
                data.forEach(n => {
                    const unreadClass = n.is_read ? '' : 'unread';
                    const iconColor = n.type === 'success' ? 'bg-success text-white' : 
                                      n.type === 'danger' ? 'bg-danger text-white' : 
                                      n.type === 'warning' ? 'bg-warning text-white' : 'bg-primary text-white';
                                      
                    const icon = n.type === 'success' ? 'fa-check' : 
                                 n.type === 'danger' ? 'fa-bug' : 
                                 n.type === 'warning' ? 'fa-exclamation' : 'fa-info';
                    
                    const time = new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                    
                    html += `
                        <a href="${n.link || '#'}" class="notif-item ${unreadClass}">
                            <div class="notif-icon ${iconColor}">
                                <i class="fas ${icon}"></i>
                            </div>
                            <div class="notif-details">
                                <div class="notif-title">${n.title}</div>
                                <div class="notif-desc">${n.message}</div>
                                <div class="notif-time">${time}</div>
                            </div>
                        </a>
                    `;
                });
                notifList.innerHTML = html;
            })
            .catch(err => {
                notifList.innerHTML = '<div class="text-center p-3 text-danger small">Error loading notifications.</div>';
            });
    };

    if (notifBell) {
        notifBell.addEventListener('show.bs.dropdown', loadNotifications);
    }

    // ----------------------------------------------------
    // Sidebar Quick Search Filter
    // ----------------------------------------------------
    const sidebarSearch = document.getElementById('sidebarSearch');
    if (sidebarSearch) {
        sidebarSearch.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            document.querySelectorAll('.sidebar-nav .nav-item').forEach(item => {
                const text = item.textContent.toLowerCase();
                if (text.includes(query)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }

    // ----------------------------------------------------
    // Realtime KPI Number Ticker (Micro-animation)
    // ----------------------------------------------------
    const tickers = document.querySelectorAll('.kpi-value[data-count]');
    tickers.forEach(ticker => {
        const target = parseFloat(ticker.getAttribute('data-count'));
        const duration = 1000; // ms
        const startTime = performance.now();
        
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const value = Math.floor(progress * target);
            ticker.textContent = value;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                ticker.textContent = target;
            }
        };
        requestAnimationFrame(animate);
    });
});
