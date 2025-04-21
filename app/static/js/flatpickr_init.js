// app/static/js/flatpickr_init.js

/**
 * Initializes Flatpickr month selection inputs.
 * @param {string} selector - CSS selector for the target input elements.
 */
function initFlatpickrMonthInput(selector) {
    // Use optional chaining ?. just in case flatpickr or monthSelectPlugin aren't loaded
    if (typeof flatpickr === 'undefined' || typeof monthSelectPlugin === 'undefined') {
      console.error("Flatpickr or monthSelectPlugin not loaded");
      return;
    }
  
    const elements = document.querySelectorAll(selector);
    elements.forEach(el => {
      // Prevent re-initialization if the element already has a flatpickr instance
      if (el._flatpickr) {
          // console.log("Flatpickr already initialized for:", el);
          return;
      }
      try {
          flatpickr(el, {
            locale: "et", // Use Estonian locale loaded via separate script
            plugins: [
              new monthSelectPlugin({
                shorthand: false, // Use full Estonian month names
                dateFormat: "Y-m", // Store value as YYYY-MM
                altFormat: "F Y", // Display as Kuu AAAA
                theme: "light" // Optional: theme, can be "dark", "material_blue", etc.
              })
            ],
            altInput: true, // Create a user-friendly alternate input
            allowInput: true // Disallow manual typing into the date field
            // wrap: true // Enable this if you wrap your input element in a div for styling/icons
          });
      } catch (e) {
          console.error("Error initializing Flatpickr month input for:", el, e);
      }
    });
    // console.log(`Flatpickr Month inputs initialized for selector: ${selector}`);
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
          // console.log("Flatpickr already initialized for:", el);
          return;
      }
      try {
          flatpickr(el, {
            locale: "et", // Use Estonian locale
            dateFormat: "Y-m-d", // Store value as YYYY-MM-DD
            altFormat: "d.m.Y", // Display as DD.MM.YYYY
            altInput: true,
            allowInput: false,
            maxDate: "today" // Good default for birthday inputs
          });
      } catch (e) {
          console.error("Error initializing Flatpickr date input for:", el, e);
      }
    });
    // console.log(`Flatpickr Date inputs initialized for selector: ${selector}`);
  }
  
  /**
   * Initializes all Flatpickr inputs based on their CSS classes.
   */
  function initializeAllPickers() {
      // console.log("Initializing all Flatpickr pickers...");
      initFlatpickrMonthInput('.flatpickr-month-input');
      initFlatpickrDateInput('.flatpickr-date-input');
  }
  
  // --- Initialization Triggers ---
  
  // Run on initial page load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAllPickers);
  } else {
    // If DOM is already ready, run immediately.
    // Use a small timeout to ensure libraries might be ready if loaded async/deferred.
    setTimeout(initializeAllPickers, 0);
  }
  
  // Re-run after HTMX swaps content to initialize pickers in new content
  // Using htmx:afterSettle ensures the DOM is stable after swaps.
  document.body.addEventListener('htmx:afterSettle', function(event) {
    // console.log("HTMX settle detected, re-initializing Flatpickr inputs if necessary.");
    // Check if the target of the swap actually contains relevant inputs
    // This avoids unnecessary calls if irrelevant content was swapped.
    const target = event.detail.target;
    if (target && (target.querySelector('.flatpickr-month-input') || target.querySelector('.flatpickr-date-input') || target.classList.contains('flatpickr-month-input') || target.classList.contains('flatpickr-date-input'))) {
        initializeAllPickers();
    }
  });