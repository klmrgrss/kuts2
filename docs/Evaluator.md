# Evaluator Dashboard UX & Architecture

This document describes the intended behaviour and supporting architecture of the evaluator dashboard (the `/evaluator/d` route). It complements `ARCHITECTURE.md` by detailing how the three-panel layout, validation engine, and HTMX-driven interactions work together to give evaluators fast feedback while keeping the database as the source of truth.

## Layout Overview

The dashboard is composed of three coordinated panels:

1. **Left panel – Application navigator**
   * Lists applications surfaced by the evaluator search controller.
   * Uses HTMX (`hx_get`) to load a selected application into the centre panel and, via out-of-band swaps, refresh the right panel.
   * Does **not** send transient form state when switching between applications; each navigation request only carries the selected qualification identifier.
   * **Note:** Application IDs now use `:::` as a separator (e.g., `email:::level:::activity`) to avoid parsing errors with emails containing dashes.

2. **Centre panel – Compliance workspace**
   * Shows qualification metadata at the top, the compliance dashboard in the middle, and the final decision toolbox at the bottom.
   * The compliance dashboard visualises validation output returned by `ComplianceDashboardState`.
   * The decision toolbox allows the evaluator to choose a context (education, work experience, training, or decision) and enter comments or overrides that are persisted through the re-evaluation endpoint.

3. **Right panel – Evidence viewer**
   * Lists supporting documents and work-history records.
   * Updates alongside the centre panel so that the displayed evidence always matches the active application.

## Intended UX Flows

### Two-way context linking

* Each compliance section carries a `data-context` attribute that represents its logical bucket (`haridus`, `tookogemus`, `koolitus`, `otsus`).
* Buttons in the final decision toolbox use the same context identifiers.
* Clicking a context button highlights the matching compliance section and loads the associated comment into the textarea.
*   Each compliance section carries a `data-context` attribute that represents its logical bucket (`haridus`, `tookogemus`, `koolitus`, `otsus`).
*   Buttons in the final decision toolbox use the same context identifiers.
*   Clicking a context button highlights the matching compliance section and loads the associated comment into the textarea.
*   Clicking a compliance section applies the highlight to the section itself **and** lights up the matching button in the toolbox so that evaluators always see which context is active.
*   Highlighting persists after the compliance dashboard is re-rendered by HTMX.

### Persisting evaluator input

*   The final decision form posts to `/evaluator/d/re-evaluate/{qual_id}` using HTMX.
*   **Interaction Lifecycle:** Overrides (Dropdowns) fire immediate `change` events to update UI colors and persist status. Comments in the textarea are **ONLY** saved when the form is submitted (e.g., clicking the Paperplane button).
*   Every request contains:
    *   The currently active context (`active_context`).
    *   The comment typed by the evaluator (`main_comment`).
    *   Contextual overrides such as the selected education level or “old/foreign education” flag.
*   `EvaluatorWorkbenchController.re_evaluate_application` merges input into the latest state, re-validates when overrides change, and persists the state via `evaluations` table records (`evaluation_state_json`).
*   On reload, `EvaluatorController.show_v2_application_detail` reads the saved JSON and rehydrates the dashboard.

### Data Override Logic

When an evaluator selects a value from a dropdown (e.g., Education Level), it creates a **Manual Override**. 
*   This override takes precedence over the applicant's original data.
*   The system re-runs the validation engine against the overridden data.
*   If the override fails a rule (e.g., downgraded education), the corresponding UI section immediately reflects this (e.g., turns Red).

### Comment Field Mapping

| `data-context` | State Field | Database Persistence |
| --- | --- | --- |
| `haridus` | `haridus_comment` | `evaluation_state_json` |
| `tookogemus` | `tookogemus_comment` | `evaluation_state_json` |
| `koolitus` | `koolitus_comment` | `evaluation_state_json` |
| `otsus` | `otsus_comment` | `evaluation_state_json` |

## Key Components & Files

| Concern | File(s) | Notes |
| --- | --- | --- |
| Validation models | `app/logic/models.py` | Defines `ComplianceDashboardState` and `ComplianceCheck` dataclasses. |
| Validation engine | `app/logic/validator.py` | Produces dashboard states and rehydrates them from the database. |
| Dashboard rendering | `app/ui/evaluator_v2/center_panel.py` | Builds compliance sections, the decision toolbox, and the client-side linking script. |
| Navigation list | `app/ui/evaluator_v2/application_list.py` | Supplies HTMX anchors. |
| Persistence & re-evaluation | `app/controllers/evaluator_workbench_controller.py` | Handles HTMX submissions and updates the `evaluations` table. |
| Initial load | `app/controllers/evaluator.py` | Fetches saved evaluation state and renders panels. |

## Validation & Error Handling

* The server validates that the qualification identifier exists and that the evaluator is authorised.
* The workbench controller logs errors while keeping partial evaluator input intact.
* **Sync Constraint:** The Right Panel updates via OOB swaps but does not yet filter evidence based on the active selection in the Center Panel.
