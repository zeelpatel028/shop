document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const toggleBtns = document.querySelectorAll('#toggle-sidebar, #toggle-sidebar-alt');
    const closeBtn = document.getElementById('close-sidebar');
    const mainContent = document.querySelector('.main-content');

    // Toggle Sidebar
    toggleBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            if (window.innerWidth > 768) {
                sidebar.classList.toggle('active');
            } else {
                sidebar.classList.toggle('mobile-active');
            }
        });
    });

    // Close Sidebar on Mobile
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            sidebar.classList.remove('mobile-active');
        });
    }

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(event) {
        if (window.innerWidth <= 768) {
            const isClickInsideSidebar = sidebar.contains(event.target);
            const isClickOnToggle = toggleBtn.contains(event.target);

            if (!isClickInsideSidebar && !isClickOnToggle && sidebar.classList.contains('mobile-active')) {
                sidebar.classList.remove('mobile-active');
            }
        }
    });

    // Handle Window Resize
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            sidebar.classList.remove('mobile-active');
        } else {
            sidebar.classList.remove('active');
        }
    });
});
