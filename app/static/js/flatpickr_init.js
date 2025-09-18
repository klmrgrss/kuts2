// app/static/js/flatpickr_init.js

/**
 * Initializes Flatpickr month selection inputs with a simplified, robust configuration.
 * @param {string} selector - CSS selector for the target input elements.
 */
function initFlatpickrMonthInput(selector) {
    if (typeof flatpickr === 'undefined' || typeof monthSelectPlugin === 'undefined') {
      console.error("Flatpickr or monthSelectPlugin not loaded");
      return;
    }
  
    const elements = document.querySelectorAll(selector);
    elements.forEach(el => {
      // Don't re-initialize existing instances
      if (el._flatpickr) {
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
            // --- CORE FIX: Simplify the configuration ---
            altInput: false,      // DO NOT create a second, alternate input
            allowInput: false,    // Prevent manual typing to ensure valid format
            
            // This event is still useful to ensure the form validator runs
            onChange: function(selectedDates, dateStr, instance) {
                instance.element.dispatchEvent(new Event('change', { bubbles: true }));
            }
          });
      } catch (e) {
          console.error("Error initializing Flatpickr month input for:", el, e);
      }
    });
  }
  
  /**
   * Initializes Flatpickr standard date selection inputs.
   * @param {string} selector - CSS selector for the target input elements.
   */
  function initFlatpickrDateInput(selector) {
    if (typeof flatpickr === 'undefined') {
      console.error("Flatpickr not loaded");
      return;
    }
  
    const elements = document.querySelectorAll(selector);
    elements.forEach(el => {
      if (el._flatpickr) {
          return;
      }
      try {
          flatpickr(el, {
            locale: "et",
            dateFormat: "Y-m-d",
            altInput: false, // Simplify here as well
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
   * Initializes all Flatpickr inputs based on their CSS classes.
   */
  function initializeAllPickers() {
      initFlatpickrMonthInput('.flatpickr-month-input');
      initFlatpickrDateInput('.flatpickr-date-input');
  }
  
  // --- Initialization Triggers ---
  
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAllPickers);
  } else {
    // Use a small timeout to ensure other scripts might run first
    setTimeout(initializeAllPickers, 0);
  }
  
  document.body.addEventListener('htmx:afterSettle', function(event) {
    const target = event.detail.target;
    // Check if the swapped content contains a picker or is a picker itself
    if (target && (target.querySelector('.flatpickr-month-input, .flatpickr-date-input') || target.matches('.flatpickr-month-input, .flatpickr-date-input'))) {
        initializeAllPickers();
    }
  });