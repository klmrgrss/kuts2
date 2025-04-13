// static/js/vis_timeline_init.js
document.addEventListener('DOMContentLoaded', function () {
    const container = document.getElementById('vis-timeline-container');

    // **** ADDED CHECK AT THE TOP ****
    // If the container doesn't exist on this page, stop execution for this script.
    if (!container) {
        console.log("Vis.js timeline container not found, skipping initialization."); // Optional log
        return; // Exit the DOMContentLoaded listener early
    }
    // **** END CHECK ****

    // --- The rest of the code only runs if the container was found ---
    console.log("DEBUG: Initializing Vis.js Timeline.");

    let timelineItemsData = [];
    try {
        // Use container.dataset (since container is guaranteed to exist here)
        timelineItemsData = JSON.parse(container.dataset.timelineItems || '[]');
        console.log(`DEBUG: Parsed ${timelineItemsData.length} timeline items.`);
    } catch (e) {
        console.error("Error parsing timeline data from dataset:", e);
        container.innerHTML = "<p style='color: red;'>Error loading timeline data.</p>";
        return; // Stop if data parsing fails
    }

    if (timelineItemsData.length === 0) {
        console.log("DEBUG: No timeline items to display.");
        // Display a message directly in the container if no items
        container.innerHTML = '<p style="padding: 10px; color: #888; text-align: center;">Töökogemuse ajajoon kuvatakse siin, kui andmed on sisestatud.</p>';
        return; // Don't initialize the timeline object if no data
    }

    // Create Vis.js DataSets
    // Ensure 'vis' object is available (it should be if the library loaded)
    if (typeof vis === 'undefined') {
        console.error("ERROR: Vis.js library (vis object) not found. Ensure it's included before this script.");
        container.innerHTML = "<p style='color: red;'>Error: Timeline library not loaded.</p>";
        return;
    }

    const items = new vis.DataSet(timelineItemsData);
    const groups = new vis.DataSet(
        // Ensure group exists before mapping, provide default content
        timelineItemsData.map(item => ({ id: item.group || item.id, content: '' }))
    );

    // Configuration options
    const options = {
        stack: false,
        zoomable: false,
        horizontalScroll: false,
        moveable: true,
        orientation: { axis: "top" },
        margin: { item: 10, axis: 20 },
        tooltip: {
            followMouse: true,
            overflowMethod: "flip"
        },
        minHeight: '150px', // Adjust as needed
        maxHeight: '400px', // Adjust as needed
        showCurrentTime: false, // Disable default current time line
        // Consider adding explicit start/end if data range might be very small
        // start: new Date(new Date().getFullYear() - 6, 0, 1), // Example: 6 years ago
        // end: new Date(new Date().getFullYear() + 1, 0, 1)     // Example: Start of next year
    };

    // Initialize the timeline
    try {
        const timeline = new vis.Timeline(container, items, groups, options);
        console.log("DEBUG: Vis.js Timeline initialized.");

        // Add red vertical line at current date
        const currentDate = new Date();
        try {
            timeline.addCustomTime(currentDate, 'current-time'); // Use built-in ID if desired
            console.log("DEBUG: Added red vertical line at current date:", currentDate);
        } catch (e) {
            console.error("Error adding current time marker:", e);
        }


        // Add blue vertical line 5 years before
        const fiveYearsBefore = new Date(currentDate);
        fiveYearsBefore.setFullYear(currentDate.getFullYear() - 5);
        try {
            timeline.addCustomTime(fiveYearsBefore, 'five-years-before'); // Custom ID
            console.log("DEBUG: Added blue vertical line at:", fiveYearsBefore);
        } catch (e) {
            console.error("Error adding 5-year marker:", e);
        }


        // Fit timeline to the data range initially, only if items exist
        if (items.length > 0) {
            timeline.fit();
        }

    } catch (error) {
        console.error("ERROR: Failed to initialize Vis.js Timeline:", error);
        container.innerHTML = "<p style='color: red;'>Error initializing timeline component.</p>";
    }
});