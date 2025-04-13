// app/static/js/ag_grid_dashboard.js

document.addEventListener('DOMContentLoaded', function () {
    console.log("DEBUG: DOMContentLoaded event fired for AG Grid Dashboard.");

    // Find the container div rendered by evaluator.py show_dashboard
    const gridDiv = document.getElementById('ag-grid-dashboard');

    if (!gridDiv) {
        console.error("FATAL: AG Grid container div '#ag-grid-dashboard' not found!");
        return;
    }

    // --- Get Application Data ---
    let rowData = [];
    let rawDataAttribute = gridDiv.dataset.applications || ''; // Get raw string or empty

    // Add logging for the raw attribute content
    console.log("DEBUG JS: Raw data-applications attribute content:", rawDataAttribute.substring(0, 500) + "...");

    try {
        // Parse the raw string
        const parsedData = JSON.parse(rawDataAttribute || '[]');
        console.log("DEBUG JS: Result after JSON.parse:", parsedData); // Log the parsed object/array
        rowData = parsedData; // Assign to rowData

        console.log(`DEBUG: Parsed ${rowData.length} application rows for dashboard.`);
    } catch (e) {
        console.error("Error parsing application data from dataset:", e);
        gridDiv.innerHTML = "<p style='color: red;'>Error loading table data.</p>";
        return;
    }

    // --- Define AG Grid Columns for Dashboard ---
    const columnDefs = [
        {
            headerName: "Taotluse kuupäev",
            field: "submission_date", // Matches key from _get_dashboard_data
            width: 150,
            sortable: true // Make date sortable
        },
        {
            headerName: "Taotleja nimi",
            field: "full_name", // Matches key from _get_dashboard_data
            width: 250,
            resizable: true,
            sortable: true,
            filter: true // Allow filtering by name
        },
        {
            headerName: "Taotletavad kvalifikatsioonid",
            field: "qualifications_summary", // Matches key from _get_dashboard_data
            flex: 1, // Allow this column to grow
            wrapText: false, // Enable text wrapping if summary is long
            autoHeight: true, // Adjust row height for wrapped text
            resizable: false,
            sortable: false // Sorting might not make sense on summary
        }
        // Note: 'email' is in the rowData but not shown as a column
    ];

    // --- Define AG Grid Options for Dashboard ---
    const gridOptions = {
        rowData: rowData,
        columnDefs: columnDefs,
        domLayout: 'auto', // Adjusts height to fit rows

        defaultColDef: { // Default settings for all columns
            resizable: false,
            filter: false,
            sortable: false,
            wrapHeaderText: true,
            autoHeaderHeight: true,
        },

        // Use object format for rowSelection (or remove if not needed)
        rowSelection: 'single', // Keeps single selection behavior
        suppressCellFocus: true,

        // --- Event Listener for Row Click Navigation ---
        onRowClicked: (event) => {
            // event.data contains the data for the clicked row
            console.log("AG Grid Dashboard: Row Clicked:", event.data);
            if (event.data && typeof event.data.email !== 'undefined') {
                const userEmail = event.data.email;
                if (userEmail) {
                    const targetUrl = `/evaluator/application/${userEmail}`;
                    console.log("AG Grid Dashboard: Navigating to:", targetUrl);
                    window.location.href = targetUrl; // Navigate to the detail page
                } else {
                     console.warn("AG Grid Dashboard: email field exists but is empty.");
                     alert("Cannot navigate: Applicant email is missing.");
                }
            } else {
                console.error("AG Grid Dashboard: Could not get 'email' field from clicked row data:", event.data);
                alert("Error: Could not get applicant identifier from this row.");
            }
        }, // end onRowClicked

    }; // end gridOptions

    // --- Initialize AG Grid ---
    try {
        console.log("DEBUG: Initializing AG Grid for Dashboard...");
        const gridApi = agGrid.createGrid(gridDiv, gridOptions);
        console.log("DEBUG: AG Grid Dashboard Initialized successfully.");
    } catch (error) {
        console.error("FATAL: Error initializing AG Grid Dashboard:", error);
        gridDiv.innerHTML = "<p style='color: red;'>Error initializing data grid. Check console.</p>";
    }

}); // End DOMContentLoaded