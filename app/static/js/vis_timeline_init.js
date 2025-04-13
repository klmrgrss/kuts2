document.addEventListener('DOMContentLoaded', function () {
    console.log("DEBUG: Initializing Vis.js Timeline.");
    const container = document.getElementById('vis-timeline-container');

    if (!container) {
        console.error("ERROR: Vis.js timeline container '#vis-timeline-container' not found.");
        return;
    }

    let timelineItemsData = [];
    try {
        timelineItemsData = JSON.parse(container.dataset.timelineItems || '[]');
        console.log(`DEBUG: Parsed ${timelineItemsData.length} timeline items.`);
    } catch (e) {
        console.error("Error parsing timeline data from dataset:", e);
        container.innerHTML = "<p style='color: red;'>Error loading timeline data.</p>";
        return;
    }

    if (timelineItemsData.length === 0) {
        console.log("DEBUG: No timeline items to display.");
        return; // Don't initialize if no data
    }

    // Create Vis.js DataSets
    const items = new vis.DataSet(timelineItemsData);
    const groups = new vis.DataSet(
        timelineItemsData.map(item => ({ id: item.group, content: '' }))
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
        minHeight: '150px',
        maxHeight: '400px',
        showCurrentTime: false, // Disable default current time line
    };

    // Initialize the timeline
    try {
        const timeline = new vis.Timeline(container, items, groups, options);
        console.log("DEBUG: Vis.js Timeline initialized.");

        // Add red vertical line at current date
        const currentDate = new Date(); // Today, e.g., April 12, 2025
        timeline.addCustomTime(currentDate, 'current-time');
        console.log("DEBUG: Added red vertical line at current date:", currentDate);

        // Add blue vertical line 5 years before
        const fiveYearsBefore = new Date(currentDate);
        fiveYearsBefore.setFullYear(currentDate.getFullYear() - 5); // e.g., April 12, 2020
        timeline.addCustomTime(fiveYearsBefore, 'five-years-before');
        console.log("DEBUG: Added blue vertical line at:", fiveYearsBefore);

        // Fit timeline to the data range initially
        timeline.fit();

    } catch (error) {
        console.error("ERROR: Failed to initialize Vis.js Timeline:", error);
        container.innerHTML = "<p style='color: red;'>Error initializing timeline component.</p>";
    }
});