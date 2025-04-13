// static/js/education_form.js
function setupEducationOtherInput() {
    // Find the radio button group and the specific text input
    const radioGroupName = 'education_level';
    const otherTextInputId = 'other_education_text_input'; // ID of the text input

    const radios = document.querySelectorAll(`input[type="radio"][name="${radioGroupName}"]`);
    const otherInput = document.getElementById(otherTextInputId);
    let otherRadio = null;

    if (!otherInput) {
        // console.error("Education form: Could not find 'other' text input.");
        return; // Exit if the text input isn't found (might not be on this specific render)
    }

    // Find the specific "Muu haridus" radio button
    radios.forEach(radio => {
        if (radio.value === 'Muu haridus') {
            otherRadio = radio;
        }
    });

    if (!otherRadio) {
        console.error("Education form: Could not find 'Muu haridus' radio button.");
        return; // Exit if the specific radio isn't found
    }

    // Function to toggle input visibility
    const toggleOtherInputVisibility = () => {
        if (otherRadio.checked) {
            otherInput.style.display = 'block'; // Show
        } else {
            otherInput.style.display = 'none'; // Hide
            // Optional: Clear the input value when hiding
            // otherInput.value = '';
        }
    };

    // Initial check when the script runs
    toggleOtherInputVisibility();

    // Add change listeners to ALL radio buttons in the group
    radios.forEach(radio => {
        radio.addEventListener('change', toggleOtherInputVisibility);
    });

     // Optional: Select "Muu" radio if the user starts typing in the input
     otherInput.addEventListener('focus', () => {
        if (!otherRadio.checked) {
             otherRadio.checked = true;
             // Manually trigger change event if needed by other logic
             // otherRadio.dispatchEvent(new Event('change'));
        }
     });

    console.log("Education 'Other' input handler setup complete.");
}

// Run on initial load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupEducationOtherInput);
} else {
    setupEducationOtherInput(); // Run immediately if already loaded
}

// Re-run after HTMX swaps if the form container might be replaced
// Adjust the target selector if necessary
document.body.addEventListener('htmx:afterSwap', function(event) {
    // Check if the swapped content contains the education form or its container
    const educationForm = document.getElementById('education-form');
    if (educationForm && event.detail.target.contains(educationForm)) {
         console.log("Re-initializing education 'Other' input handler after HTMX swap.");
         setupEducationOtherInput();
    }
});

// REMOVE the form 'submit' listener that modified the radio value.