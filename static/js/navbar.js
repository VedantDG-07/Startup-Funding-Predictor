document.addEventListener('DOMContentLoaded', () => {
    // Theme Toggle Logic (UI Only)
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const icon = themeToggleBtn.querySelector('i');
            if (icon.classList.contains('bi-moon')) {
                icon.classList.remove('bi-moon');
                icon.classList.add('bi-sun');
            } else {
                icon.classList.remove('bi-sun');
                icon.classList.add('bi-moon');
            }
        });
    }

    // Search Input focus animation (Scale effect)
    const searchInput = document.querySelector('.search-input');
    const searchContainer = document.querySelector('.search-container');
    
    if (searchInput && searchContainer) {
        searchInput.addEventListener('focus', () => {
            searchContainer.style.transform = 'scale(1.02)';
        });
        searchInput.addEventListener('blur', () => {
            searchContainer.style.transform = 'scale(1)';
        });
    }
});
