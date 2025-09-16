// app/static/js/flatpickr_init.js

/**
 * Initializes Flatpickr month selection inputs.
 * @param {string} selector - CSS selector for the target input elements.
 */
function initFlatpickrMonthInput(selector) {
    if (typeof flatpickr === 'undefined' || typeof monthSelectPlugin === 'undefined') {
      console.error("Flatpickr or monthSelectPlugin not loaded");
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
            plugins: [
              new monthSelectPlugin({
                shorthand: false,
                dateFormat: "Y-m",
                altFormat: "F Y",
                theme: "light"
              })
            ],
            altInput: true,
            allowInput: true,
            // --- FIX: Add the onClose callback ---
            onClose: function(selectedDates, dateStr, instance) {
                // When the calendar closes, find the parent form and trigger a 'change' event.
                // This will make our form_validator script re-evaluate the form's state.
                const form = instance.input.closest('form');
                if (form) {
                    form.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }
            // --- END FIX ---
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
            altFormat: "d.m.Y",
            altInput: true,
            allowInput: false,
            maxDate: "today",
            // --- FIX: Add the onClose callback here as well ---
            onClose: function(selectedDates, dateStr, instance) {
                const form = instance.input.closest('form');
                if (form) {
                    form.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }
            // --- END FIX ---
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
    setTimeout(initializeAllPickers, 0);
  }
  
  document.body.addEventListener('htmx:afterSettle', function(event) {
    const target = event.detail.target;
    if (target && (target.querySelector('.flatpickr-month-input') || target.querySelector('.flatpickr-date-input') || target.classList.contains('flatpickr-month-input') || target.classList.contains('flatpickr-date-input'))) {
        initializeAllPickers();
    }
  });