// app/static/js/evaluator_ui.js
function toggleEvaluatorPanel(panel) {
    const container = document.getElementById('evaluator-v2-container');
    if (!container) return;

    const leftPanelClass = 'left-panel-open';
    const rightPanelClass = 'right-panel-open';

    if (panel === 'left') {
        const isLeftOpen = container.classList.contains(leftPanelClass);
        // Close right panel if it's open
        if (container.classList.contains(rightPanelClass)) {
            container.classList.remove(rightPanelClass);
        }
        // Toggle left panel
        if (!isLeftOpen) {
            container.classList.add(leftPanelClass);
        }
    } else if (panel === 'right') {
        const isRightOpen = container.classList.contains(rightPanelClass);
         // Close left panel if it's open
        if (container.classList.contains(leftPanelClass)) {
            container.classList.remove(leftPanelClass);
        }
        // Toggle right panel
        if (!isRightOpen) {
            container.classList.add(rightPanelClass);
        }
    }
}

function closeAllEvaluatorPanels() {
    const container = document.getElementById('evaluator-v2-container');
    if (container) {
        container.classList.remove('left-panel-open');
        container.classList.remove('right-panel-open');
    }
}

// Ensure functions are globally accessible
window.toggleEvaluatorPanel = toggleEvaluatorPanel;
window.closeAllEvaluatorPanels = closeAllEvaluatorPanels;