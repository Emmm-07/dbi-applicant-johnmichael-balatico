# DBI Take-Home — Setup

Full instructions are in the brief you were emailed. This file only gets you
running.

If setup takes more than ten minutes, stop and email us — that is our bug, not
yours, and we will not count it against your time.

You need **Python 3.11 or newer**, **Node 20 or newer**, Git and a GitHub account.

## Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python pipeline.py               # Part 1 - this runs, but the numbers are wrong
uvicorn main:app --reload --port 8000
```

Check http://localhost:8000/api/health — it should return `{"status":"ok"}`.
Interactive docs at http://localhost:8000/docs.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The page shows the API status. `/api` is already
proxied to port 8000, and CORS is already configured — you should not need to
touch either.

## The data

`data/tenant_sales_raw.csv` — a monthly tenant sales export, roughly 1,500 rows
covering four malls from January 2024 to December 2025. It is synthetic; no
real tenant or mall figures are in it.

It is a realistic export from an ageing system, which means it is messy. The
pipeline you have been given does not handle all of that messiness correctly.

## What to do

| File | Part |
|---|---|
| `backend/pipeline.py` | 1 — find and fix the bugs |
| `backend/main.py` | 2 — build the three endpoints |
| `frontend/src/App.jsx` | 3 — one page |

All three parts are required.

## How to submit

1. On your own GitHub account, create a new, empty, **public** repository named
   `dbi-applicant-<firstname>-<lastname>`, all lowercase with hyphens for spaces
   (for example `dbi-applicant-juan-dela-cruz`). Don't add a README or licence.
2. **Clone this repository. Don't fork it.** Forks are listed publicly here, where
   other applicants would see your work.
3. Point your copy at your own repository and push it:

   ```bash
   git remote set-url origin <your repository URL>
   git push -u origin HEAD
   ```

   Your history now starts with our starter commit, so every later commit shows
   only your changes.
4. Fix each bug in **its own commit, with a one-line message saying what was
   wrong**. For example:

   ```
   fix: parenthesised amounts were parsed as positive, inflating sales totals
   fix: dedupe compared raw tenant codes, so T-1052 and t-1052 survived as two rows
   ```

5. Push, then reply to our email with your repository link. Don't push again
   after you've sent it.

We read the commits and the code. There's no write-up to fill in anywhere in
this exercise.

If you spot something that looks wrong and decide to leave it, say so in a
commit message or a code comment. That counts in your favour.
