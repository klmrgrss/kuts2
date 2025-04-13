// gem/static/js/tab_scroll.js

function ensureActiveTabVisible() {
    // Find the scrollable container using the ID we added
    const tabContainer = document.getElementById('tab-list-container');
    if (!tabContainer) {
        // console.warn('Tab scroll: Container not found.');
        return;
    }

    // Find the active tab link using the 'tab-active' class we added
    const activeTabLink = tabContainer.querySelector('a.tab-active');
    const activeTabListItem = activeTabLink ? activeTabLink.closest('li') : null;

    if (!activeTabListItem) {
        // console.warn('Tab scroll: Active tab list item not found.');
        return; // No active tab found (or class mismatch)
    }

    // Use scrollIntoView to bring the active tab (list item) into view
    activeTabListItem.scrollIntoView({
        behavior: 'smooth', // Use smooth scrolling
        block: 'nearest',   // Scroll vertically minimally
        inline: 'nearest'   // Scroll horizontally minimally
    });

    // console.log('Tab scroll: Ensured active tab is visible.');
}

// --- Event Listeners ---

// Use DOMContentLoaded to ensure elements are ready before attaching listeners or running code
document.addEventListener('DOMContentLoaded', () => {
    // console.log('Tab scroll: DOMContentLoaded fired.');

    // 1. Run on initial page load
    ensureActiveTabVisible();

    // 2. *** MOVED LISTENER ATTACHMENT INSIDE DOMContentLoaded ***
    //    Run after HTMX swaps content/nav using htmx:afterSettle
    if (document.body) { // Extra safety check, though DOMContentLoaded should guarantee body exists
        document.body.addEventListener('htmx:afterSettle', function(event) {
            const swapTargetId = event.detail.target.id;
            const tabContentContainerId = 'tab-content-container';

            // Check if the original swap target was the content, implying a tab change request
            if (swapTargetId === tabContentContainerId) {
                // console.log(`Tab scroll: HTMX settle detected after swap on target '#${swapTargetId}', ensuring active tab visible.`);
                ensureActiveTabVisible(); // No timeout needed with afterSettle
            }
        });
        // console.log('Tab scroll: htmx:afterSettle listener attached to body.');
    } else {
        console.error('Tab scroll: document.body not found even after DOMContentLoaded!');
    }

    // 3. Optional: Re-run on window resize (Unchanged)
    // let resizeTimeout;
    // window.addEventListener('resize', () => {
    //     clearTimeout(resizeTimeout);
    //     resizeTimeout = setTimeout(() => {
    //         console.log('Tab scroll: Window resized, ensuring active tab visible.');
    //         ensureActiveTabVisible();
    //     }, 250);
    // });

}); // End of DOMContentLoaded listener