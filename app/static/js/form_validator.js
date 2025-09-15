// app/static/js/form_validator.js

function setupFormValidator(formElement) {
    if (!formElement) return;

    const submitButton = formElement.querySelector('button[type="submit"], input[type="submit"]');
    if (!submitButton) {
        console.warn("Form validator: Could not find a submit button for form:", formElement.id);
        return;
    }

    const requiredInputs = Array.from(formElement.querySelectorAll('[required]'));
    if (requiredInputs.length === 0) {
        submitButton.disabled = false;
        return;
    }

    const validate = () => {
        const allValid = requiredInputs.every(input => {
            if (input.type === 'checkbox' || input.type === 'radio') {
                if (input.type === 'radio') {
                    const radioGroup = formElement.querySelectorAll(`input[name="${input.name}"]:checked`);
                    return radioGroup.length > 0;
                }
                return input.checked;
            }
            return input.value.trim() !== '';
        });
        submitButton.disabled = !allValid;
    };

    requiredInputs.forEach(input => {
        input.addEventListener('input', validate);
        input.addEventListener('change', validate);
    });

    validate();
}

document.addEventListener('DOMContentLoaded', () => {
    const formsToValidate = document.querySelectorAll('.validated-form');
    formsToValidate.forEach(setupFormValidator);
});

document.body.addEventListener('htmx:afterSwap', function(event) {
    const target = event.detail.target;
    if (target) {
        const newForms = target.querySelectorAll('.validated-form');
        newForms.forEach(setupFormValidator);
        if (target.classList.contains('validated-form')) {
            setupFormValidator(target);
        }
    }
});
