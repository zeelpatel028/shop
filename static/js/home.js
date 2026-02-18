document.addEventListener('DOMContentLoaded', function () {
    const sidebar = document.getElementById('sidebar');
    const toggleBtns = document.querySelectorAll('#toggle-sidebar, #toggle-sidebar-alt, #mobile-toggle');
    const closeBtn = document.getElementById('close-sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const mainContent = document.querySelector('.main-content');

    // Toggle Sidebar
    toggleBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            if (window.innerWidth > 768) {
                sidebar.classList.toggle('active');
            } else {
                sidebar.classList.toggle('mobile-active');
                if (overlay) overlay.classList.toggle('active');
            }
        });
    });

    // Close Sidebar on Mobile via Close Button or Overlay
    const closeSidebar = () => {
        sidebar.classList.remove('mobile-active');
        if (overlay) overlay.classList.remove('active');
    };

    if (closeBtn) {
        closeBtn.addEventListener('click', closeSidebar);
    }

    if (overlay) {
        overlay.addEventListener('click', closeSidebar);
    }

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function (event) {
        if (window.innerWidth <= 768) {
            const isClickInsideSidebar = sidebar.contains(event.target);
            const isClickOnToggle = Array.from(toggleBtns).some(btn => btn.contains(event.target));

            if (!isClickInsideSidebar && !isClickOnToggle && sidebar.classList.contains('mobile-active')) {
                sidebar.classList.remove('mobile-active');
            }
        }
    });

    // Handle Window Resize
    window.addEventListener('resize', function () {
        if (window.innerWidth > 768) {
            sidebar.classList.remove('mobile-active');
            if (overlay) overlay.classList.remove('active');
        } else {
            sidebar.classList.remove('active');
        }
    });
});
