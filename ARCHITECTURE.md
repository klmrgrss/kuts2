# Architecture Overview

This document outlines the architecture of the professional qualification application.

## High-Level Overview

This is a web application built with the **FastHTML** Python framework. It allows applicants to submit and manage their professional qualifications, and for evaluators to review and assess these applications.

## Architecture Pattern

The application follows a Model-View-Controller (MVC) like architecture:

*   **Models:** The database schema is defined in `app/models.py`.
*   **Views:** The user interface components are located in the `app/ui/` directory. These are Python classes that generate HTML.
*   **Controllers:** The application's business logic resides in the `app/controllers/` directory.

## Technology Stack

*   **Web Framework:** [FastHTML](https://github.com/AnswerDotAI/fasthtml)
*   **UI Library:** [MonsterUI](https://github.com/AnswerDotAI/monster-ui)
*   **ASGI Server:** [Starlette](https://www.starlette.io/) / [Uvicorn](https://www.uvicorn.org/)
*   **Database:** SQLite (via `apsw`)

## Directory Structure

-   `app/`: The main application directory.
    -   `main.py`: The entry point of the application. It initializes the app, sets up routes, and middleware.
    -   `database.py`: Contains database setup and connection logic.
    -   `models.py`: Defines the database tables and relationships.
    -   `controllers/`: Contains the business logic for different parts of the application (e.g., authentication, applicant data, etc.).
    -   `ui/`: Contains the UI components used to build the front-end.
    -   `static/`: Holds static assets like JavaScript, CSS, and images.
-   `data/`: Intended for storing data files, such as uploads.
-   `requirements.txt`: A list of Python dependencies for the project.

## Data Flow

1.  A user request hits a URL defined in `app/main.py`.
2.  The route calls a method in the corresponding controller from the `app/controllers/` directory.
3.  The controller interacts with the database via the models (`app/models.py`) to fetch or save data.
4.  The controller then uses components from `app/ui/` to construct an HTML response.
5.  The response is sent back to the user's browser.

## Default Accounts

The application can automatically provision evaluator or applicant accounts on
start-up.  Set the `DEFAULT_USERS` environment variable to a JSON array, for
example:

```json
[
  {"email": "evaluator@example.com", "password": "Secret123!", "role": "evaluator"},
  {"email": "applicant@example.com", "password": "Secret456!"}
]
```

Entries may also be supplied in a simple `email|password|role` format separated
by commas, semicolons, or newlines for environments where JSON is awkward.  For
legacy compatibility the `EVALUATOR_EMAILS` / `DEFAULT_EVALUATOR_PASSWORD`
variables continue to work.  Password resets for existing accounts can be
disabled by setting `DEFAULT_USERS_FORCE_RESET=false`.

## Domain-Specific Concepts

*(This section is a placeholder for you to add more details about the business logic.)*

*   **Professional Qualifications:** What are the rules and data associated with a qualification?
*   **Evaluation Process:** How are applications evaluated? What are the different statuses an application can have?
