// app/static/js/flatpickr_init.js

/**
 * Initializes Flatpickr month selection inputs found within a specific root element.
 * @param {Element} root - The element to search within for inputs.
 */
function initFlatpickrMonthInputsIn(root) {
    if (typeof flatpickr === 'undefined' || typeof monthSelectPlugin === 'undefined') {
        console.error("Flatpickr or monthSelectPlugin not loaded");
        return;
    }

    const elements = root.querySelectorAll('.flatpickr-month-input');
    elements.forEach(el => {
        if (el._flatpickr) { // Don't re-initialize existing instances
            return;
        }
        try {
            flatpickr(el, {
                locale: "et",
                plugins: [
                    new monthSelectPlugin({
                        shorthand: true, // Use MMM format like "Jan", "Feb"
                        dateFormat: "Y-m", // The value that will be submitted (e.g., "2024-01")
                    })
                ],
                altInput: false,
                allowInput: false,
                onChange: function(selectedDates, dateStr, instance) {
                    // Dispatch a 'change' event to trigger form validation
                    instance.element.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });
        } catch (e) {
            console.error("Error initializing Flatpickr month input for:", el, e);
        }
    });
}

/**
 * Initializes Flatpickr standard date selection inputs found within a specific root element.
 * @param {Element} root - The element to search within for inputs.
 */
function initFlatpickrDateInputsIn(root) {
    if (typeof flatpickr === 'undefined') {
        console.error("Flatpickr not loaded");
        return;
    }

    const elements = root.querySelectorAll('.flatpickr-date-input');
    elements.forEach(el => {
        if (el._flatpickr) { // Don't re-initialize
            return;
        }
        try {
            flatpickr(el, {
                locale: "et",
                dateFormat: "Y-m",
                altInput: false,
                allowInput: false,
                maxDate: "today",
                onChange: function(selectedDates, dateStr, instance) {
                    instance.element.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });
        } catch (e) {
            console.error("Error initializing Flatpickr date input for:", el, e);
        }
    });
}

/**
 * Initializes all Flatpickr inputs found within a given root element.
 * @param {Element} rootElement - The element to scan for date pickers.
 */
function initializeAllPickersIn(rootElement) {
    // Initialize month pickers
    initFlatpickrMonthInputsIn(rootElement);
    if (rootElement.matches && rootElement.matches('.flatpickr-month-input')) {
        initFlatpickrMonthInputsIn(rootElement.parentElement || document);
    }

    // Initialize date pickers
    initFlatpickrDateInputsIn(rootElement);
    if (rootElement.matches && rootElement.matches('.flatpickr-date-input')) {
        initFlatpickrDateInputsIn(rootElement.parentElement || document);
    }
}

// --- Initialization Triggers ---

// Run once on initial page load, scanning the entire document
document.addEventListener('DOMContentLoaded', () => initializeAllPickersIn(document));

// Run after each HTMX swap, scanning only the newly added content
document.body.addEventListener('htmx:afterSettle', function(event) {
    if (event.detail.target) {
        initializeAllPickersIn(event.detail.target);
    }
});