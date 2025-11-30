# Install & Prime

## Read
frontend/.env.example (never read actual .env files)
backend/.env.example (never read actual .env files)

## Read and Execute
.claude/commands/prime.md

## Run
- Remove the existing git remote if needed: `git remote remove origin`
- Initialize a new git repository if needed: `git init`

### Backend Setup
- Navigate to backend: `cd backend`
- Create virtual environment: `python -m venv venv`
- Activate virtual environment: `source venv/bin/activate` (Mac/Linux) or `venv\Scripts\activate` (Windows)
- Install dependencies: `pip install -r requirements.txt`
- Return to root: `cd ..`

### Frontend Setup
- Navigate to frontend: `cd frontend`
- Install dependencies: `npm install`
- Return to root: `cd ..`

### Start Application
- On a background process, run `./scripts/start-dev.sh` with 'nohup' or a 'subshell' to start the servers so you don't get stuck
- Verify backend is running: `curl http://localhost:8000/docs` (should return Swagger UI)
- Verify frontend is running: open http://localhost:5173 in browser

## Report
- Output the work you've just done in a concise bullet point list.
- Instruct the user to fill out environment variables:
  - `frontend/.env` based on `frontend/.env.example` (Supabase URL, Anon Key, API URL)
  - `backend/.env` based on `backend/.env.example` (Supabase credentials, CORS origins)
- Mention the URLs:
  - Frontend: http://localhost:5173
  - Backend API: http://localhost:8000/api
  - API Docs: http://localhost:8000/docs
- Mention: 'To setup your AFK Agent, be sure to update the remote repo url and push to a new repo so you have access to git issues and git prs:
  ```
  git remote add origin <your-new-repo-url>
  git push -u origin main
  ```'
