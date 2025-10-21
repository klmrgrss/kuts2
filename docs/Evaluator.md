# Evaluator Dashboard UX & Architecture

This document describes the intended behaviour and supporting architecture of the evaluator dashboard (the `/evaluator/d` route). It complements `ARCHITECTURE.md` by detailing how the three-panel layout, validation engine, and HTMX-driven interactions work together to give evaluators fast feedback while keeping the database as the source of truth.

## Layout Overview

The dashboard is composed of three coordinated panels:

1. **Left panel – Application navigator**
   * Lists applications surfaced by the evaluator search controller.
   * Uses HTMX (`hx_get`) to load a selected application into the centre panel and, via out-of-band swaps, refresh the right panel.
   * Does **not** send transient form state when switching between applications; each navigation request only carries the selected qualification identifier.

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
* Clicking a compliance section applies the highlight to the section itself **and** lights up the matching button in the toolbox so that evaluators always see which context is active.
* Highlighting persists after the compliance dashboard is re-rendered by HTMX.

### Persisting evaluator input

* The final decision form posts to `/evaluator/d/re-evaluate/{qual_id}` using HTMX.
* Every request contains:
  * The currently active context (`active_context`).
  * The comment typed by the evaluator (`main_comment`).
  * Contextual overrides such as the selected education level or “old/foreign education” flag.
* `EvaluatorWorkbenchController.re_evaluate_application` merges the evaluator input into the latest validation state, re-validates when overrides change, and then persists the state via `evaluations` table records (`evaluation_state_json`).
* On reload, `EvaluatorController.show_v2_application_detail` reads the saved JSON, reconstructs `ComplianceDashboardState`, and rehydrates comment fields together with the compliance checks so that both the compliance cards and the textarea reflect what was last submitted.

### Auto-validation and visual feedback

* The validation engine recalculates compliance whenever the evaluator toggles overrides that influence eligibility (e.g., education level or age of the diploma).
* Compliance cards display aggregated pass/fail state through coloured borders, icons, and copy that summarises how many sub-requirements are satisfied.
* Comment bubbles under each section display the persisted comment, defaulting to “Kommentaarid...” when empty.
* The textarea always reflects the latest comment for the active context and clears when no context is selected, preventing accidental edits to the wrong section.

## Key Components & Files

| Concern | File(s) | Notes |
| --- | --- | --- |
| Validation models | `app/logic/models.py` | Defines `ComplianceDashboardState` and `ComplianceCheck` dataclasses. |
| Validation engine | `app/logic/validator.py` | Produces dashboard states and rehydrates them from the database. |
| Dashboard rendering | `app/ui/evaluator_v2/center_panel.py` | Builds compliance sections, the decision toolbox, and the client-side linking script. |
| Navigation list | `app/ui/evaluator_v2/application_list.py` | Supplies HTMX anchors that load new applications without leaking transient form data. |
| Persistence & re-evaluation | `app/controllers/evaluator_workbench_controller.py` | Handles HTMX form submissions, updates state, and saves it to `evaluations`. |
| Initial load | `app/controllers/evaluator.py` | Fetches saved evaluation state (if any) and renders the centre/right panels. |

## Interaction Lifecycle

1. The evaluator selects an application from the left panel. The centre and right panels render using the latest persisted state.
2. They pick a context in the decision toolbox (or click a compliance section). Highlighting synchronises both areas, and the textarea is populated with the stored comment.
3. Typing into the textarea triggers a debounced HTMX POST that saves the comment and returns updated compliance markup. The highlight is re-applied, ensuring continuity.
4. Adjusting dropdown overrides (education level, final decision) fires change events that submit the form, recompute validation if necessary, and redisplay the dashboard with new compliance statuses.
5. Reloading the page or navigating away and back reads the saved JSON state so comments, overrides, and highlights remain intact.

## Validation & Error Handling Expectations

* The server validates that the qualification identifier exists and that the evaluator is authorised before serving data.
* The workbench controller logs and surfaces validation errors while keeping partial evaluator input intact.
* Client-side code does not silently swallow errors; in development the console logs context activations to aid debugging, and the UI retains a neutral state if a context cannot be resolved.

Maintaining this contract ensures evaluators experience predictable linking, immediate visual feedback, and durable persistence across sessions.
