// app/static/js/form_validator.js

function setupFormValidator(formElement) {
    if (!formElement || formElement.dataset.validatorInitialized === 'true') {
        return;
    }
    console.log(`[Validator] Setting up for form: #${formElement.id}`);
    formElement.dataset.validatorInitialized = 'true';

    const formId = formElement.id;
    const actionBar = document.querySelector(`.sticky-action-bar[data-form-id="${formId}"]`);
    if (!actionBar) return;

    const saveButton = actionBar.querySelector('button[type="submit"]');
    const cancelButton = actionBar.querySelector('a.btn-secondary, button.btn-secondary');
    if (!saveButton) return;

    const validationMode = formElement.dataset.validationMode || 'required';
    let initialInputStates = new Map();

    const recordInitialState = () => {
        initialInputStates.clear();
        formElement.querySelectorAll('input, select, textarea').forEach(input => {
            const key = input.name || input.id;
            if (key) {
                const state = (input.type === 'checkbox' || input.type === 'radio') ? input.checked : input.value;
                initialInputStates.set(key, state);
            }
        });
    };

    const isFormDirty = () => {
        if (formElement.dataset.isDirty === 'true') return true;
        for (const [key, initialState] of initialInputStates.entries()) {
            if (!key) continue;
            const input = formElement.querySelector(`[name="${key}"], #${key}`);
            if (input) {
                const currentState = (input.type === 'checkbox' || input.type === 'radio') ? input.checked : input.value;
                if (initialState !== currentState) {
                    formElement.dataset.isDirty = 'true';
                    return true;
                }
            }
        }
        return false;
    };

    const validate = () => {
        console.log(`[Validator] Event triggered. Running validation for #${formId}...`);
        let isFormValid = false;

        if (validationMode === 'dirty') {
            isFormValid = isFormDirty();
        } else { // 'required' mode
            const requiredInputs = Array.from(formElement.querySelectorAll('[required]'));
            console.log(`[Validator] --- Checking ${requiredInputs.length} Required Inputs ---`);
            
            isFormValid = requiredInputs.every(input => {
                let isValid = false;
                const inputName = input.name || input.id;

                if (input.type === 'radio') {
                    isValid = formElement.querySelector(`input[name="${input.name}"]:checked`) !== null;
                    console.log(`  - Input (Radio Group) '${inputName}': has selection? ${isValid}`);
                } else if (input.type === 'checkbox') {
                    isValid = input.checked;
                    console.log(`  - Input (Checkbox) '${inputName}': checked? ${isValid}`);
                } else {
                    isValid = input.value.trim() !== '';
                    console.log(`  - Input '${inputName}': value='${input.value}', valid? ${isValid}`);
                }
                
                if (!isValid) {
                    input.style.borderColor = 'red';
                } else {
                    input.style.borderColor = '';
                }
                return isValid;
            });
            console.log(`[Validator] --- End of Checks ---`);
        }

        console.log(`%c[Validator] Overall form valid? ${isFormValid}. Setting saveButton.disabled to: ${!isFormValid}`, 'color: blue; font-weight: bold;');
        saveButton.disabled = !isFormValid;
        
        // --- FIX: Decouple the cancel button from the 'dirty' check ---
        // If the action bar is visible, the cancel button should always be active.
        if (cancelButton) {
            cancelButton.classList.remove('disabled');
            cancelButton.style.pointerEvents = 'auto';
        }
    };

    const attachListeners = () => {
        formElement.querySelectorAll('input, select, textarea').forEach(input => {
            input.removeEventListener('input', validate);
            input.removeEventListener('change', validate);
            input.addEventListener('input', validate);
            input.addEventListener('change', validate);
        });
    };

    recordInitialState();
    attachListeners();
    validate();
}

function initializeAllValidators() {
    document.querySelectorAll('.validated-form').forEach(form => {
        form.dataset.validatorInitialized = 'false';
        setupFormValidator(form);
    });
}

document.addEventListener('DOMContentLoaded', initializeAllValidators);
document.body.addEventListener('htmx:afterSettle', initializeAllValidators);