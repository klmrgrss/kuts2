# Smart-ID Integration Guide: From Demo to Production

This document outlines the necessary steps to transition the Smart-ID authentication feature from the current demo/testing environment to a live production environment. The current implementation is configured for testing and will not work with real user credentials.

## Overview of Environments

-   **Demo Environment**: Uses test credentials and a specific API endpoint provided by SK ID Solutions for development and testing. It works with a predefined set of test personal identity codes.
-   **Production Environment**: Uses live, real-world credentials and a production API endpoint. This is required for authenticating actual users.

---

## Configuration for Production

To switch to the production environment, you must first obtain production credentials from SK ID Solutions and then update the application's environment variables.

### 1. Obtain Production Credentials

Before you can go live, you need to register your application with SK ID Solutions. They will provide you with the following essential credentials for the production environment:

-   A production **Relying Party UUID**.
-   A production **Relying Party Name**.

### 2. Update Environment Variables

In your production deployment environment (e.g., your server's `.env` file or configuration service), you must set the following variables to the values you received from SK ID Solutions:

```bash
# The API endpoint for the live Smart-ID service.
SMARTID_API_HOST="[https://rp-api.smart-id.com/v2/](https://rp-api.smart-id.com/v2/)"

# Your production Relying Party UUID from SK ID Solutions.
SMARTID_RP_UUID="YOUR_PRODUCTION_UUID_HERE"

# Your production Relying Party Name from SK ID Solutions.
SMARTID_RP_NAME="YOUR_PRODUCTION_NAME_HERE"