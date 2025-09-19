// static/js/qualification_scroll.js
function attachQualFormScroll() {
    // Look up the qualification form by its ID.
    const form = document.getElementById('qualification-form');
    if (!form) {
        // If the form isn't on the page, do nothing.
        return;
    }
    // Remove any existing listener to avoid duplicate handlers.
    form.removeEventListener('submit', scrollToTopHandler);
    form.addEventListener('submit', scrollToTopHandler);
}

// Handler that scrolls the page to the top when the form submits.
function scrollToTopHandler(event) {
    // Wait until the swap finishes; immediate scroll can race the swap.
    setTimeout(() => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }, 0);
}

// Hook into DOM load and HTMX swaps.
document.addEventListener('DOMContentLoaded', attachQualFormScroll);
document.body.addEventListener('htmx:afterSwap', (event) => {
    // Re‑attach only if the swapped content contains the tab content container.
    if (event.detail.target && event.detail.target.id === 'tab-content-container') {
        attachQualFormScroll();
    }
});
