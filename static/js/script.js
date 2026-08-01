document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const mobileCloseBtn = document.getElementById('sidebarToggle');
    const desktopToggleBtn = document.getElementById('desktopSidebarToggle');
    
    // Desktop Collapse Toggle
    if (desktopToggleBtn) {
        desktopToggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
        });
    }

    // Function to handle mobile toggle
    function toggleMobileSidebar() {
        if(sidebar) sidebar.classList.toggle('show');
        if(overlay) overlay.classList.toggle('show');
    }

    // Bind Mobile Close events
    if (mobileCloseBtn) {
        mobileCloseBtn.addEventListener('click', toggleMobileSidebar);
    }
    if (overlay) {
        overlay.addEventListener('click', toggleMobileSidebar);
    }

    // Accessibility: Close sidebar on ESC key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && sidebar && sidebar.classList.contains('show')) {
            toggleMobileSidebar();
        }
    });

    // Export toggle function globally so it can be called from navbar
    window.toggleMobileSidebar = toggleMobileSidebar;

    // Handle Active state based on current URL path
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar-link');
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        const href = link.getAttribute('href');
        
        // Exact match or root match
        if (href === currentPath || (currentPath === '/' && href === '/')) {
            link.classList.add('active');
        }
    });
});
