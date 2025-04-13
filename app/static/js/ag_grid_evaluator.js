// app/static/js/ag_grid_evaluator.js

document.addEventListener('DOMContentLoaded', function () {
    console.log("DEBUG: DOMContentLoaded event fired for AG Grid Evaluator.");

    // --- Grid API References ---
    let gridApiQuals;
    let gridApiWorkExp;
    let gridApiReferences; // References grid API

    // --- Data Stores ---
    let rowDataQuals = [];
    let allWorkExperienceData = [];
    let applicantEmail = '';

    // --- Find Grid Containers ---
    const gridDivQuals = document.getElementById('ag-grid-qualifications');
    const gridDivWorkExp = document.getElementById('ag-grid-work-experience');
    const gridDivReferences = document.getElementById('ag-grid-references'); // Find References grid

    // --- Error checking for containers ---
    if (!gridDivQuals) console.error("FATAL: AG Grid container div '#ag-grid-qualifications' not found!");
    if (!gridDivWorkExp) console.warn("WARN: AG Grid container div '#ag-grid-work-experience' not found!");
    if (!gridDivReferences) {
        console.error("ERROR: AG Grid container div '#ag-grid-references' not found! Cannot initialize references grid.");
    }

    // --- Get Initial Data from Attributes ---
    try {
        if (gridDivQuals) {
            rowDataQuals = JSON.parse(gridDivQuals.dataset.qualifications || '[]');
            applicantEmail = gridDivQuals.dataset.applicantEmail || '';
        }
        if (gridDivWorkExp) {
             allWorkExperienceData = JSON.parse(gridDivWorkExp.dataset.workExperience || '[]');
        }
    } catch (e) { console.error("Error parsing initial data from dataset:", e); return; }

    // --- Editor Options ---
    const statusOptions = ['Not Evaluated', 'LLM: Compliant', 'LLM: Not Compliant', 'LLM: Unsure', 'Evaluated: Compliant', 'Evaluated: Not Compliant'];
    const decisionOptions = ['Otsus tegemata', 'Vastab', 'Ei vasta', 'Vajab lisainfot'];

    // --- Helper Function for Link Renderer ---
    const ariregisterBaseUrl = "https://ariregister.rik.ee/eng/company/";
    function ariregisterLinkRenderer(params) {
        const code = params.value;
        if (code) {
            const url = ariregisterBaseUrl + encodeURIComponent(code);
            return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="link">${code}</a>`;
        }
        return code || '';
    }

    // --- Column Definitions (Unchanged) ---
    const columnDefsQuals = [
        { headerName: "E/TT", field: "is_renewal", width: 70, valueFormatter: params => params.value ? "TT" : "E", editable: false, sortable: false },
        { headerName: "Tase", field: "level_abbr", tooltipField: "level", width: 70, editable: false, sortable: true },
        { headerName: "Tegevusala", field: "qualification_abbr", tooltipField: "qualification_name", width: 90, editable: false, sortable: true },
        { headerName: "Spetsialiseerumine", field: "specialisation", tooltipField: "specialisation", width: 180, editable: false, sortable: true },
        { headerName: "Haridus", field: "eval_education_status", editable: true, width: 180, cellEditor: 'agSelectCellEditor', cellEditorParams: { values: statusOptions } },
        { headerName: "Täiendkoolitus", field: "eval_training_status", editable: true, width: 150, cellEditor: 'agSelectCellEditor', cellEditorParams: { values: statusOptions } },
        { headerName: "Töökogemus", field: "eval_experience_status", editable: true, width: 150, cellEditor: 'agSelectCellEditor', cellEditorParams: { values: statusOptions } },
        { headerName: "Kommentaar", field: "eval_comment", editable: true, width: 190, resizable: true, wrapText: true, autoHeight: true, cellEditor: 'agLargeTextCellEditor', cellEditorPopup: true },
        {
            headerName: "Otsus",
            field: "eval_decision",
            editable: true,
            flex: 1,
            minWidth: 160,
            cellEditor: 'agSelectCellEditor',
            cellEditorParams: { values: decisionOptions }
        },
    ];
    const columnDefsWorkExp = [
        { headerName: "Aadress", field: "object_address", width: 180, resizable: true, sortable: true },
        { headerName: "Kasutusotstarve", field: "object_purpose", width: 130, resizable: true },
        { headerName: "EHR kood", field: "ehr_code", width: 110, resizable: true, cellRenderer: params => { const ehrCode = params.value; if (ehrCode) { const ehrUrl = `https://livekluster.ehr.ee/ui/ehr/v1/building/${ehrCode}`; return `<a href="${ehrUrl}" target="_blank" rel="noopener noreferrer" class="link">${ehrCode}</a>`; } else { return ehrCode || ''; } } },
        { headerName: "Ehitusluba", field: "permit_required", width: 90, cellStyle: { textAlign: 'center' }, cellRenderer: params => { if (params.value === 1) { return '<span style="color: green; font-weight: bold;">✓</span>'; } else { return '-'; } } },
        { headerName: "Roll", field: "role", width: 130, resizable: true },
        { headerName: "Ehitustöö kirjeldus", field: "work_keywords", flex: 1, wrapText: false, autoHeight: true, resizable: true, minWidth: 150 },
    ];
    const columnDefsReferences = [
        { headerName: "", field: "role_title", width: 90, suppressMovable: true, cellStyle: { fontWeight: 'bold', fontSize: '0.8rem' } },
        { headerName: "Nimi", field: "name", width: 120, tooltipField: "name" },
        { headerName: "Reg.kood", field: "code", width: 90, cellRenderer: ariregisterLinkRenderer },
        { headerName: "Kontakt", field: "contact", width: 120, tooltipField: "contact" },
        { headerName: "E-post", field: "email", width: 150, cellRenderer: params => {
            const email = params.value;
            if (email) { return `<a href="mailto:${email}" class="link">${email}</a>`; }
            return '';
        } },
        { headerName: "Tel.", field: "phone", flex: 1 }
    ];
    // --- END Column Definitions ---

    // --- Default Grid Options ---
    // Define common defaults for all columns
    const defaultColDef = {
        resizable: true,
        editable: false,
        sortable: true,
        filter: false, // Filtering disabled globally
        wrapHeaderText: false,
        autoHeaderHeight: false,
        checkboxSelection: false, // Explicitly disable checkbox column in default col def
        suppressMenu: true // Optionally hide column menu if not needed
    };

    // --- Grid Options ---

    // Qualifications Grid Options
    const gridOptionsQuals = {
        // Specific Grid Options
        columnDefs: columnDefsQuals,
        rowData: rowDataQuals,
        domLayout: 'normal',     // Keep as per user's last code version
        rowSelection: 'single',      // Use simple 'single'
        // suppressRowClickSelection: true, <<< REMOVED
        // rowMultiSelectWithClick: false, <<< REMOVED
        suppressCellFocus: true,
        tooltipShowDelay: 300,
        popupParent: document.body, // Keep for comment editor popup fix
        rowHeight: 28,
        headerHeight: 32,

        // Default Column Definitions Applied Here
        defaultColDef: defaultColDef,

        // Event Handlers
        onFirstDataRendered: (params) => {
            console.log("DEBUG: Qualifications grid first data rendered.");
            if (params.api && params.api.getDisplayedRowCount() > 0) {
                const firstNode = params.api.getDisplayedRowAtIndex(0);
                if (firstNode) {
                    console.log("DEBUG: Selecting first qualification row.");
                    firstNode.setSelected(true);
                } else {
                    console.log("DEBUG: First qualification node not found.");
                }
            } else {
                console.log("DEBUG: No rows in qualification grid or API not ready on first render.");
            }
        },
        onCellValueChanged: (params) => {
            const fieldName = params.colDef.field;
            const newValue = params.newValue;
            const oldValue = params.oldValue;
            const recordId = params.data.id;
            if (newValue === oldValue || !applicantEmail || typeof recordId === 'undefined') return;
            const updateUrl = `/evaluator/application/${applicantEmail}/qualification/${recordId}/update`;
            const payload = { field: fieldName, value: newValue };
            fetch(updateUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
                .then(response => {
                    if (!response.ok) {
                        response.json().then(err => {
                            console.error(`Save Error Qual ID ${recordId}: ${response.status}`, err);
                            alert(`Error saving ${fieldName}: ${err.error || response.statusText}`);
                        }).catch(() => {
                            console.error(`Save Error Qual ID ${recordId}: ${response.status}`, response.statusText);
                            alert(`Error saving ${fieldName}: ${response.statusText}`);
                        });
                    } else {
                        console.log(`Save OK Qual ID ${recordId}`);
                        params.api.flashCells({ rowNodes: [params.node], columns: [fieldName], flashDuration: 500, fadeDuration: 500 });
                    }
                })
                .catch(error => {
                    console.error(`Workspace error Qual ID ${recordId}:`, error);
                    alert(`Network error saving ${fieldName}.`);
                });
        },
        onSelectionChanged: (event) => {
            console.log("DEBUG: Qualification selection changed.");
            const selectedNodes = event.api.getSelectedNodes();
            let filteredWorkExp = [];

            if (selectedNodes.length === 1) {
                const selectedQualification = selectedNodes[0].data;
                const selectedActivity = selectedQualification?.qualification_name;
                // const selectedSpecialisation = selectedQualification?.specialisation; // Keep if needed for filtering later
                console.log(`DEBUG: Selected Qual Activity: ${selectedActivity}`);
                if (selectedActivity) {
                    filteredWorkExp = allWorkExperienceData.filter(exp => exp.associated_activity === selectedActivity);
                    console.log(`DEBUG: Filtered Work Exp based on activity '${selectedActivity}'. Found: ${filteredWorkExp.length}`);
                } else {
                    console.log("DEBUG: No selected activity found in qualification data.");
                }
            } else {
                console.log("DEBUG: No single qualification selected or multiple selected.");
            }

            if (gridApiWorkExp) {
                gridApiWorkExp.setGridOption('rowData', filteredWorkExp);
                console.log(`DEBUG: Set Work Exp grid data. ${filteredWorkExp.length} rows.`);

                if (filteredWorkExp.length === 0) {
                    gridApiWorkExp.showNoRowsOverlay();
                    console.log("DEBUG: Showing 'No Rows' overlay in Work Exp grid.");
                } else {
                    gridApiWorkExp.hideOverlay();
                    console.log("DEBUG: Hiding overlay in Work Exp grid.");
                    gridApiWorkExp.ensureIndexVisible(0);
                    const firstWorkExpNode = gridApiWorkExp.getDisplayedRowAtIndex(0);
                    if (firstWorkExpNode) {
                        console.log("DEBUG: Selecting first row in Work Exp grid.");
                        firstWorkExpNode.setSelected(true);
                    } else {
                        console.warn("DEBUG: Could not find first row node in Work Exp grid after setting data.");
                    }
                }
            } else {
                console.warn("WARN: gridApiWorkExp not available when trying to update.");
            }

            if (gridApiReferences) {
                console.log("DEBUG: Qualification changed, clearing references grid.");
                gridApiReferences.setGridOption('rowData', []);
                gridApiReferences.showNoRowsOverlay();
            }
        }
    };

    // Work Experience Grid Options
    const gridOptionsWorkExp = {
        // Specific Grid Options
        columnDefs: columnDefsWorkExp,
        rowData: [],
        domLayout: 'normal',     // Keep as per user's last code version
        rowSelection: 'single',      // Use simple 'single'
        // suppressRowClickSelection: true, <<< REMOVED
        // rowMultiSelectWithClick: false, <<< REMOVED
        suppressCellFocus: true,
        overlayNoRowsTemplate: '<span style="padding: 10px; color: #888;">Vali kvalifikatsioonirida, et näha seotud töökogemusi.</span>',
        rowHeight: 28,
        headerHeight: 32,

        // Default Column Definitions Applied Here
        defaultColDef: defaultColDef,

        // Event Handlers
        onSelectionChanged: (event) => {
            console.log("DEBUG: Work Exp selection changed.");
            const selectedNodes = event.api.getSelectedNodes();
            let referenceData = [];

            if (selectedNodes.length === 1) {
                const selectedExp = selectedNodes[0].data;
                console.log("DEBUG: Work Exp selected, constructing referenceData:", selectedExp);
                referenceData = [
                    { role_title: "TEOSTAJA", name: selectedExp.company_name || '', code: selectedExp.company_code || '', contact: selectedExp.company_contact || '', phone: selectedExp.company_phone || '', email: selectedExp.company_email || '' },
                    { role_title: "TELLIJA", name: selectedExp.client_name || '', code: selectedExp.client_code || '', contact: selectedExp.client_contact || '', phone: selectedExp.client_phone || '', email: selectedExp.client_email || '' }
                ];
                console.log("DEBUG: Constructed referenceData:", referenceData);
            } else {
                console.log("DEBUG: No work exp selected, referenceData is empty.");
            }

            if (gridApiReferences) {
                console.log("DEBUG: Setting references grid rowData...");
                gridApiReferences.setGridOption('rowData', referenceData);
                console.log("DEBUG: References grid rowData set.");
                const hasImplementerInfo = referenceData[0]?.name || referenceData[0]?.code || referenceData[0]?.contact || referenceData[0]?.phone || referenceData[0]?.email;
                const hasClientInfo = referenceData[1]?.name || referenceData[1]?.code || referenceData[1]?.contact || referenceData[1]?.phone || referenceData[1]?.email;

                if (referenceData.length === 0 || (!hasImplementerInfo && !hasClientInfo)) {
                    console.log("DEBUG: Showing 'No Rows' overlay in References grid.");
                    gridApiReferences.showNoRowsOverlay();
                } else {
                    console.log("DEBUG: Hiding overlay in References grid.");
                    gridApiReferences.hideOverlay();
                }
            } else {
                console.warn("WARN: gridApiReferences not available.");
            }
        }
    };

    // References Grid Options
    const gridOptionsReferences = {
        // Specific Grid Options
        columnDefs: columnDefsReferences,
        rowData: [],
        domLayout: 'normal',     // Keep as per user's last code version
        suppressHorizontalScroll: true,
        overlayNoRowsTemplate: '<span style="padding: 10px; color: #888;">Vali töökogemus, et näha kontakte.</span>',
        rowHeight: 28,
        headerHeight: 32,

        // Default Column Definitions Applied Here
        defaultColDef: {
             ...defaultColDef, // Start with common defaults
             sortable: false,  // Override: references don't usually need sorting
             resizable: false // Override: Keep fixed layout
        },
    };
    // --- END Grid Options ---

    // --- Initialize ALL Grids (Unchanged) ---
    try {
        if (gridDivQuals) {
            gridApiQuals = agGrid.createGrid(gridDivQuals, gridOptionsQuals);
            console.log("DEBUG JS: Qualifications grid initialized.");
        }
        if (gridDivWorkExp) {
            gridApiWorkExp = agGrid.createGrid(gridDivWorkExp, gridOptionsWorkExp);
            gridApiWorkExp.showNoRowsOverlay();
            console.log("DEBUG JS: Work Experience grid initialized.");
        }
        if (gridDivReferences) {
            try {
                gridApiReferences = agGrid.createGrid(gridDivReferences, gridOptionsReferences);
                console.log("DEBUG JS: References grid initialized successfully. API:", gridApiReferences);
                if (gridApiReferences) {
                    gridApiReferences.showNoRowsOverlay();
                } else {
                    console.error("ERROR: createGrid for references returned undefined/null API.");
                }
            } catch (initError) {
                console.error("ERROR: Exception during References grid initialization:", initError);
                gridDivReferences.innerHTML = "<p style='color:red;'>Error initializing references grid. Check console.</p>";
            }
        } else {
            console.error("ERROR: References grid container #ag-grid-references not found in DOM.");
        }
    } catch (error) {
        console.error("ERROR: General error during AG Grid initialization:", error);
    }
}); // End DOMContentLoaded