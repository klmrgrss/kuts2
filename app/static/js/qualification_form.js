// app/static/js/qualification_form.js



/**
 * This function finds all qualification sections on the page and initializes
 * the logic to sync the 'Tervik' toggle switch with its checkboxes.
 */
function initializeQualificationSync() {
    const sections = document.querySelectorAll('[id^="qual-section-"]');
    if (sections.length === 0) {
        return;
    }

    function setupSyncForSection(sectionId) {
        const container = document.getElementById(`qual-section-${sectionId}`);
        if (!container) return;

        const checkboxes = container.querySelectorAll(`#checkbox-group-${sectionId} input[type="checkbox"]`);
        const toggle = container.querySelector(`#toggle-${sectionId}`);
        if (!toggle || checkboxes.length === 0) return;

        function updateToggleState() {
            const allChecked = Array.from(checkboxes).every(cb => cb.checked);
            if (toggle.checked !== allChecked) {
                toggle.checked = allChecked;
            }
        }

        checkboxes.forEach(checkbox => {
            checkbox.removeEventListener('change', updateToggleState);
            checkbox.addEventListener('change', updateToggleState);
        });
        
        updateToggleState();
    }

    sections.forEach(section => {
        const sectionId = section.id.replace('qual-section-', '');
        setupSyncForSection(sectionId);
    });
}

// --- MODIFIED & CORRECTED EXECUTION ---
// We wrap EVERYTHING inside a single DOMContentLoaded listener.
// This guarantees that the document, including the <body> tag, is fully loaded
// before we try to attach any event listeners to it, fixing the TypeError.
document.addEventListener('DOMContentLoaded', function() {
    // Run for the initial page load
    initializeQualificationSync();

    // Now it's safe to add the listener for subsequent HTMX swaps
    document.body.addEventListener('htmx:afterSwap', initializeQualificationSync);
});// klmrgrss/kuts2/kuts2-sticky-bar/app/static/js/qualification_form.js

/**
 * This function finds all qualification sections on the page and initializes
 * the logic to sync the 'Tervik' toggle switch with its checkboxes.
 */
function initializeQualificationSync() {
    const sections = document.querySelectorAll('[id^="qual-section-"]');
    if (sections.length === 0) {
        return;
    }

    function setupSyncForSection(sectionId) {
        const container = document.getElementById(`qual-section-${sectionId}`);
        if (!container) return;

        const checkboxes = container.querySelectorAll(`#checkbox-group-${sectionId} input[type="checkbox"]`);
        const toggle = container.querySelector(`#toggle-${sectionId}`);
        if (!toggle || checkboxes.length === 0) return;

        function updateToggleState() {
            const allChecked = Array.from(checkboxes).every(cb => cb.checked);
            if (toggle.checked !== allChecked) {
                toggle.checked = allChecked;
            }
        }

        checkboxes.forEach(checkbox => {
            checkbox.removeEventListener('change', updateToggleState);
            checkbox.addEventListener('change', updateToggleState);
        });
        
        updateToggleState();
    }

    sections.forEach(section => {
        const sectionId = section.id.replace('qual-section-', '');
        setupSyncForSection(sectionId);
    });
}

// --- CORRECTED EXECUTION ---
// We wrap EVERYTHING inside a single DOMContentLoaded listener.
// This guarantees that the document, including the <body> tag, is fully loaded
// before we try to attach any event listeners to it, fixing the TypeError.
document.addEventListener('DOMContentLoaded', function() {
    // Run for the initial page load
    initializeQualificationSync();

    // Now it's safe to add the listener for subsequent HTMX swaps
    document.body.addEventListener('htmx:afterSwap', initializeQualificationSync);
});