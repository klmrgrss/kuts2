# Deploying to Railway

This guide walks you through deploying the Application to Railway and setting up the initial administrator.

## Prerequisites

1.  **Railway Account**: Sign up at [railway.app](https://railway.app).
2.  **Railway CLI** (Optional but recommended): `npm i -g @railway/cli` or install via their website instructions.
3.  **GitHub Repo**: Ensure your code is pushed to a GitHub repository.

## Step 1: Create Project & Deploy

1.  **New Project**: In Railway Dashboard, click **New Project** -> **Deploy from GitHub repo** -> Select your repository.
2.  **Add Service**: It will automatically detect the `Dockerfile` and start building.

## Step 2: Configure Environment Variables

Go to your Project -> Select Service -> **Variables**. Add the following:

| Variable | Value | Description |
| :--- | :--- | :--- |
| `SESSION_SECRET_KEY` | *(Generate a long random string)* | Used for signing session cookies. |
| `ADMIN_ID_CODE` | `49001010000` *(Replace with YOUR Personal ID)* | **CRITICAL**: The ID code that will automatically get ADMIN access on login. |
| `ALLOWED_ORIGINS` | `https://your-project.up.railway.app` | (Optional) If you have CORS issues. |

*Note: You also need your Smart-ID credentials if configured via env vars (e.g., `SMART_ID_RP_UUID`, `SMART_ID_RP_NAME`).*

## Step 3: Configure Persistent Storage

By default, Railway files are ephemeral (deleted on restart). To keep your database (`app.db`) and uploads safe, create a Volume.

1.  Go to Project -> **New** -> **Volume**.
2.  Click firmly on the new Volume to open its settings.
3.  Click **Mount Volume** (or Connect Service).
4.  Select your Service.
5.  **Mount Path**: `/app/data`
    *   *Why?* The `Dockerfile` and `database.py` are configured to look for the DB at `/app/data/app.db` if the volume is mounted there.

## Step 4: Verification

1.  Wait for the deployment to finish (Status: **Active**).
2.  Open the public URL (e.g., `https://web-production-xxxx.up.railway.app`).
3.  **Log in** with Smart-ID using the ID code you set in `ADMIN_ID_CODE`.
4.  You should be redirected to the **Administraatori Töölaud** (Admin Dashboard).
5.  From there, you can add other evaluators.

## Troubleshooting

-   **Database Resetting?** Ensure you mounted the volume at `/app/data`.
-   **Not Admin?** Double-check `ADMIN_ID_CODE` matches your Smart-ID Personal Code exactly. Check logs in Railway for "Sync Role" messages.
