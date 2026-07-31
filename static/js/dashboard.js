document.addEventListener('DOMContentLoaded', () => {
    // Dynamically set today's date in the top right header
    const dateContainer = document.getElementById('currentDate');
    if (dateContainer) {
        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        const today = new Date();
        dateContainer.textContent = today.toLocaleDateString('en-US', options);
    }
    
    // Fade-in Stagger Animation for Dashboard Cards
    const cards = document.querySelectorAll('.dashboard-container .card');
    
    cards.forEach((card, index) => {
        // Initial hidden state
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        // Set transition for the entrance animation
        card.style.transition = 'opacity 0.5s ease-out, transform 0.5s ease-out';
        
        // Staggered trigger
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
            
            // Wait for entrance animation to finish, then restore hover transitions defined in CSS
            setTimeout(() => {
                // Remove inline transition to fallback to CSS hover definitions
                card.style.transition = '';
            }, 500);
            
        }, index * 40); // 40ms stagger delay
    });
});
