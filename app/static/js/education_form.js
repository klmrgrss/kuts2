// static/js/education_form.js

function setupEducationOtherInput() {
    const educationForm = document.getElementById('education-form');
    // Exit immediately if the form itself isn't present
    if (!educationForm) {
        // console.log("Education form not found, skipping setup."); // Optional log
        return;
    }

    // --- Find elements WITHIN the form ---
    const radioGroupName = 'education_level';
    const otherTextInputId = 'other_education_text_input'; // ID of the text input

    const radios = educationForm.querySelectorAll(`input[type="radio"][name="${radioGroupName}"]`);
    const otherInput = educationForm.querySelector(`#${otherTextInputId}`); // Find input within the form
    let otherRadio = null;

    radios.forEach(radio => {
        if (radio.value === 'Muu haridus') {
            otherRadio = radio;
        }
    });

    // --- More Robust Check ---
    // Ensure BOTH the specific "Muu haridus" radio button AND the text input exist
    // before adding event listeners that depend on them.
    if (!otherRadio || !otherInput) {
        console.warn("Education form: Could not find required 'Muu haridus' radio or text input within #education-form. Skipping event listener setup for 'other' logic.");
        // Return early to avoid errors trying to add listeners to null elements
        return;
    }
    // --- End Check ---

    // Function to toggle input visibility (safe to define even if elements were missing)
    const toggleOtherInputVisibility = () => {
        // Double-check elements exist before accessing properties
        if (otherRadio && otherInput) {
            if (otherRadio.checked) {
                otherInput.style.display = 'block'; // Show
            } else {
                otherInput.style.display = 'none'; // Hide
                // Optional: Clear the input value when hiding
                // otherInput.value = '';
            }
        }
    };

    // Initial check when the script runs (will only run if elements were found above)
    toggleOtherInputVisibility();

    // Add change listeners to ALL radio buttons in the group
    radios.forEach(radio => {
        // Check if radio element actually exists before adding listener (belt-and-suspenders)
        if (radio) {
            radio.addEventListener('change', toggleOtherInputVisibility);
        }
    });

     // Add listener to the 'other' text input (we know it exists from check above)
     otherInput.addEventListener('focus', () => {
        if (otherRadio && !otherRadio.checked) { // Check otherRadio exists again just in case
             otherRadio.checked = true;
             toggleOtherInputVisibility(); // Update visibility immediately
             // Manually trigger change event if needed by other logic
             // otherRadio.dispatchEvent(new Event('change'));
        }
     });

    console.log("Education 'Other' input handler setup complete.");
}

// --- Event Listeners for Initialization ---

// Run on initial load ONLY if the form exists then
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
         // Check if the education form exists on the page before calling setup
         if (document.getElementById('education-form')) {
             setupEducationOtherInput();
         }
    });
} else {
     // Run immediately if already loaded AND form exists
     if (document.getElementById('education-form')) {
         setupEducationOtherInput();
     }
}

// Re-run after HTMX swaps ONLY if the swapped content contains the form
document.body.addEventListener('htmx:afterSwap', function(event) {
    const educationForm = document.getElementById('education-form');
    // Check if the form exists AND if the swapped target contained it (or is the form itself)
    // This ensures setup is only called when the relevant form content is potentially added or updated.
    if (educationForm && event.detail.target && (event.detail.target.contains(educationForm) || event.detail.target === educationForm || event.detail.target.id === 'tab-content-container') ) {
         console.log("Re-initializing education 'Other' input handler after HTMX swap.");
         // Timeout helps ensure DOM is fully ready after swap in some complex cases
         setTimeout(setupEducationOtherInput, 0);
    }
});

// REMOVE any old form 'submit' listener if it existed below this line.