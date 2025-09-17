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
            // --- FINAL FIX: Explicitly set the value before dispatching the event ---
            onClose: function(selectedDates, dateStr, instance) {
                // 1. Force the correct value into the original input.
                //    `dateStr` is the date formatted as "Y-m".
                instance.element.value = dateStr;

                // 2. Trigger a 'change' event so the form validator sees the update.
                instance.element.dispatchEvent(new Event('change', { bubbles: true }));
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
            // --- FINAL FIX: Apply the same logic here ---
            onClose: function(selectedDates, dateStr, instance) {
                // 1. Force the value.
                instance.element.value = dateStr;
                // 2. Trigger the event.
                instance.element.dispatchEvent(new Event('change', { bubbles: true }));
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