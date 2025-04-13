// gem/static/js/input_tag.js

function initInputTag(containerElement) {
    if (!containerElement || containerElement.dataset.inputTagInitialized) return; // Prevent double init

    const containerId = containerElement.id;
    const name = containerId.replace('input-tag-', ''); // Extract name
    const hiddenInput = containerElement.querySelector(`#hidden-input-${name}`);
    const textInput = containerElement.querySelector(`#text-input-${name}`);
    const tagArea = containerElement.querySelector(`#tag-container-${name}`);
    // Use more specific selector for live region if ID is added
    const liveRegion = containerElement.querySelector(`#sr-${containerId}`);
    const maxLength = parseInt(textInput.getAttribute('maxlength') || '16', 10);

    console.log(`InputTag Init: Found container ${containerId}`); // Debug log

    if (!hiddenInput || !textInput || !tagArea || !liveRegion) {
        console.error("InputTag Error: Could not find all required elements for", containerId);
        return;
    }

    // --- Helper Functions ---
    function updateHiddenInput() {
        const tagElements = tagArea.querySelectorAll('.input-tag-item');
        const tagValues = Array.from(tagElements).map(tagEl => {
            const removeBtn = tagEl.querySelector('.input-tag-remove');
            return removeBtn ? removeBtn.getAttribute('data-value') : '';
        }).filter(value => value);
        hiddenInput.value = tagValues.join(',');
        console.log(`InputTag Update: Hidden value for ${name}: ${hiddenInput.value}`); // Debug log
        // *** Placeholder logic removed from here - always visible via Python render ***
    }

    function createTagElement(tagValue) {
        const tagSpan = document.createElement('span');
        tagSpan.className = "input-tag-item inline-flex items-center bg-gray-200 text-gray-800 rounded px-2 py-0.5 text-sm mr-1 mb-1";
        tagSpan.setAttribute('data-value', tagValue); // Add data-value to span too

        const textNode = document.createTextNode(tagValue + ' '); // Add space before button
        tagSpan.appendChild(textNode);

        const removeButton = document.createElement('button');
        removeButton.type = "button";
        removeButton.className = "input-tag-remove ml-1 text-red-500 hover:text-red-700 font-bold text-xs align-middle cursor-pointer";
        removeButton.innerHTML = "&times;";
        removeButton.setAttribute('aria-label', `Remove tag ${tagValue}`);
        removeButton.setAttribute('data-value', tagValue); // Keep on button too

        tagSpan.appendChild(removeButton);
        return tagSpan;
    }

    function addTag(tagValue) {
        tagValue = tagValue.trim().replace(/,/g, ''); // Trim and remove commas
        console.log(`InputTag Add: Attempting to add "${tagValue}"`); // Debug log

        // Validation
        if (!tagValue) {
            console.log("InputTag Add: Empty value ignored."); // Debug log
            return; // Ignore empty
        }
        if (tagValue.length > maxLength) {
            console.warn(`InputTag Add: Tag "${tagValue}" exceeds max length ${maxLength}`); // Debug log
            // Optional: Provide user feedback (e.g., flash input border red)
             textInput.classList.add('border-red-500');
             setTimeout(() => textInput.classList.remove('border-red-500'), 500);
            return;
        }
        // Check for duplicates (case-insensitive)
        const currentTags = (hiddenInput.value || "").toLowerCase().split(',').map(t => t.trim()).filter(t => t);
        if (currentTags.includes(tagValue.toLowerCase())) {
             console.warn(`InputTag Add: Duplicate tag "${tagValue}"`); // Debug log
             textInput.value = ""; // Clear input even if duplicate
             return;
        }

        const tagElement = createTagElement(tagValue);
        tagArea.insertBefore(tagElement, textInput);
        updateHiddenInput();
        liveRegion.textContent = `Tag ${tagValue} added.`;
        textInput.value = ""; // Clear input
        console.log(`InputTag Add: Added tag "${tagValue}"`); // Debug log
    }

    function removeTag(removeButtonElement) {
         const tagItem = removeButtonElement.closest('.input-tag-item');
         const tagValue = removeButtonElement.getAttribute('data-value');
         if (tagItem && tagValue) {
            console.log(`InputTag Remove: Removing tag "${tagValue}"`); // Debug log
            tagItem.remove();
            updateHiddenInput();
            liveRegion.textContent = `Tag ${tagValue} removed.`;
            textInput.focus();
         } else {
             console.error("InputTag Remove: Could not find tag item or value for button", removeButtonElement); // Debug log
         }
    }

    // --- Event Listeners ---
    textInput.addEventListener('keydown', (event) => {
        // console.log(`InputTag Keydown: Key = ${event.key}, Code = ${event.keyCode}`); // Intense debug log
        if (event.key === 'Enter' || event.key === ',') {
            event.preventDefault();
            addTag(textInput.value);
        } else if (event.key === 'Backspace' && textInput.value === '') {
             const lastTagRemoveBtn = tagArea.querySelector('.input-tag-item:last-of-type .input-tag-remove');
             if (lastTagRemoveBtn) {
                 const lastTagValue = lastTagRemoveBtn.getAttribute('data-value');
                 // Optional: Put value back in input? Current logic removes directly.
                 // Let's just remove it directly on backspace when empty.
                 removeTag(lastTagRemoveBtn);
             }
        }
    });

    tagArea.addEventListener('click', (event) => {
        if (event.target.classList.contains('input-tag-remove')) {
             console.log("InputTag Remove: Click detected"); // Debug log
             removeTag(event.target);
        }
        // Allow clicking container to focus input
        else if (event.target === tagArea || event.target === containerElement) {
             textInput.focus();
        }
    });

    // Mark as initialized
    containerElement.dataset.inputTagInitialized = true;
    console.log(`InputTag Init Complete: ${containerId}`); // Debug log
}

// Initialize existing tags on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log("InputTag: DOMContentLoaded"); // Debug log
    const inputTagContainers = document.querySelectorAll('.custom-input-tag-container');
     console.log(`InputTag: Found ${inputTagContainers.length} containers on load.`); // Debug log
    inputTagContainers.forEach(container => {
        initInputTag(container);
    });
});

// Handle tags loaded via HTMX
document.body.addEventListener('htmx:afterSettle', function(event) {
     console.log("InputTag: htmx:afterSettle"); // Debug log
    if (event.detail.target) {
        const newContainers = event.detail.target.querySelectorAll('.custom-input-tag-container');
         console.log(`InputTag: Found ${newContainers.length} new containers in swapped content.`); // Debug log
        newContainers.forEach(container => {
            initInputTag(container); // initInputTag now checks if already initialized
        });
        // Also check if the target itself is a container
        if (event.detail.target.classList.contains('custom-input-tag-container')) {
             console.log(`InputTag: Target itself is a container.`); // Debug log
             initInputTag(event.detail.target);
        }
    }
});