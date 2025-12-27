# Hosting Aigis for Free (Render.com)

Aigis is designed to run on the **Free Tier** of Render.com.

## Prerequisites
1.  **GitHub Account**: You must have the Aigis code passed to your own GitHub repository (we did this).
2.  **Render Account**: Sign up at [render.com](https://render.com).

## Deployment Steps

### 1. Connect to Render
1.  Go to your Render Dashboard.
2.  Click **New +** -> **Web Service**.
3.  Connect your GitHub account and select the `Aigis` repository.

### 2. Configure the Service
Render should auto-detect some settings, but ensure these match:

*   **Name**: `aigis-core` (or anything you like)
*   **Region**: Closest to you (e.g., Singapore, Oregon).
*   **Branch**: `main`
*   **Root Directory**: `.` (Leave empty or dot)
*   **Runtime**: **Python 3** (IMPORTANT: We run Python + Node in the build script)
*   **Build Command**: `./build.sh`
*   **Start Command**: `cd server && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
*   **Plan**: **Free**

### 3. Environment Variables
Scroll down to "Environment Variables" and add:
*   `PYTHON_VERSION`: `3.10.0` (Recommended)
*   `node_version`: `20` (Render sometimes needs this hint)

### 4. Deploy
Click **Create Web Service**.
*   Render will clone your repo.
*   It will run `./build.sh` (Installs Python deps, Installs Node deps, Builds Next.js).
*   It will start the Uvicorn server.

## How it Works
*   The `build.sh` script compiles the Next.js frontend into *static files* (`out/` directory).
*   The FastAPI backend is configured to *serve* these static files.
*   This allows us to run a "Full Stack" app in a **single container**, which fits the Free Tier limits.

## Troubleshooting
*   **"Sleep Mode"**: The Free Tier sleeps after 15 minutes of inactivity. When you open the URL, it may take 30-50s to wake up ("Cold Start").
*   **Build Failures**: Check the logs. Usually it's a missing dependency.
