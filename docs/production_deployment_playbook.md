# Addendum: Production Deployment Preparation

## Objective
Prepare the OrchestraAI monorepo (FastAPI backend + Next.js frontend) for live production deployment on Railway (Backend/Database) and Vercel (Frontend). 

## Instructions for Cursor AI

Please act as a Senior DevOps Engineer and execute the following codebase preparations. Do not proceed to the final step until all code adjustments are made.

### Step 1: Dynamic CORS Configuration (Backend)
- Open `src/orchestra/main.py`.
- Ensure the `CORSMiddleware` allows origins dynamically based on a `FRONTEND_URL` environment variable, falling back to `http://localhost:3000` for local dev. 
- Example logic: `allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")]`.

### Step 2: Production Dockerfile Audit
- Audit the existing `Dockerfile` at the root of the project.
- Ensure the final command respects dynamic port injection (required by Railway and Render).
- The CMD should look like: `CMD ["sh", "-c", "uvicorn orchestra.main:app --host 0.0.0.0 --port ${PORT:-8000}"]`.
- Ensure the `stripe` package is explicitly included in the `pyproject.toml` or `requirements.txt` so the Docker build doesn't fail.

### Step 3: Frontend Environment Variables
- Open `frontend/src/lib/apiClient.ts` (or wherever the base API URL is defined).
- Ensure the API URL perfectly respects the `NEXT_PUBLIC_API_URL` environment variable, so Vercel can point the frontend to the live Railway backend instead of `localhost`.

### Step 4: Generate the Go-Live User Checklist
Once the code is prepped, generate a new file named `GO_LIVE_CHECKLIST.md` for the user. It must contain the exact manual steps they need to take in their browser to deploy:

1. **Database (Railway):** How to provision a Postgres database and grab the `DATABASE_URL`.
2. **Backend (Railway):** How to deploy the GitHub repo, set the Root Directory (if needed), input the production `.env` variables (including the DB URL), and get the live API URL (e.g., `https://api.orchestraai.dev`).
3. **Frontend (Vercel):** How to import the GitHub repo, set the Framework Preset to Next.js, set the Root Directory to `frontend`, input the `NEXT_PUBLIC_API_URL`, and deploy.
4. **Stripe (Live Mode):** How to toggle "Test Mode" off in Stripe, create live prices, create a live webhook pointing to the new Railway URL, and update the Railway environment variables with the live keys.
