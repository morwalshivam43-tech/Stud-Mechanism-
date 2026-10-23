# StudyMate AI — AI Study Buddy

A student-focused study web app built with **Python Flask, SQLite, HTML, CSS and JavaScript**. It includes an AI tutor (Google Gemini API, optional), notes library, PDF/TXT note import, quiz practice, study planner, dashboard and learning insights.

## Features

- Responsive dashboard and learning statistics
- AI tutor with Gemini API integration; demo answers work without a key
- Save and search study notes; import text-based PDF or TXT files
- Practice quiz with saved results
- Study planner with task completion and deletion
- English, Marathi, Hindi and mixed-language preference
- SQLite database created automatically on startup
- Ready for GitHub and deployment to Render

## Run locally (Windows)

Install Python 3.10+ from https://www.python.org/downloads/ and then:

1. Download and extract this project.
2. Open Command Prompt or PowerShell in the extracted project folder.
3. Create a virtual environment:

   ```powershell
   python -m venv .venv
   .venv\\Scripts\\Activate.ps1
   ```

   If PowerShell blocks activation, use Command Prompt and run `.venv\\Scripts\\activate.bat`.

4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Optional: copy `.env.example` to `.env` and add your Gemini API key. **Never upload `.env` or your API key to GitHub.** You can run in demo mode without a key.

6. Start the app:

   ```bash
   python app.py
   ```

7. Visit http://127.0.0.1:5000

## Publish the code to GitHub

1. Create a new empty repository on https://github.com/new.
2. Extract this ZIP on your computer.
3. Upload the **contents of the extracted project folder** to the repository (not just the ZIP file). Make sure `app.py`, `requirements.txt`, `Procfile`, `render.yaml`, `templates/` and `static/` are at the repository root.
4. Commit the files. Do not add `.env`, your API key, or the generated SQLite database.

GitHub stores your code; **GitHub Pages cannot run this Flask/Python backend**. To make the full website accessible on the internet, deploy it using the Render steps below.

## Deploy the website on Render

1. Push the project files to GitHub.
2. Sign in at https://render.com and choose **New → Blueprint** (or create a Python Web Service).
3. Connect your GitHub repository. Render will read `render.yaml` and install dependencies.
4. In Render's environment settings, set `GEMINI_API_KEY` to your own key from Google AI Studio if you want live AI answers. Keep it private. The app also works in demo mode without it.
5. Deploy. Once the deployment finishes, open the `.onrender.com` URL Render provides.

`render.yaml` generates a `SECRET_KEY` automatically. If you create the service manually instead of using the Blueprint, use `pip install -r requirements.txt` as the build command and `gunicorn app:app` as the start command. Add `SECRET_KEY` and optionally `GEMINI_API_KEY` as environment variables.

## Important hosting notes

- The included SQLite database is created automatically. On many basic cloud deployments, local files can be temporary and may be cleared on redeploy/restart. For durable online data, attach a persistent disk and set `DATABASE_PATH` to a file on that disk, or migrate to a managed PostgreSQL database.
- This is a college-project prototype. It does not include user login or per-user data separation; anyone who can access a public deployment may be able to see or modify shared study data. Use a private/local demo unless you add authentication and authorization before inviting real users.
- AI answers can be inaccurate. Verify exam-critical information with your course notes.
- Text-based PDFs are supported; scanned image PDFs may not contain extractable text and require OCR.
- A Gemini API key is optional. Keep it on the server as an environment variable, never in browser JavaScript or GitHub.

## Project structure

```text
.
├── app.py
├── requirements.txt
├── Procfile
├── render.yaml
├── .env.example
├── .gitignore
├── README.md
├── templates/
│   └── index.html
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── app.js
```

## Troubleshooting

- **`python` not found:** install Python and enable “Add Python to PATH”, then reopen the terminal.
- **Gemini errors:** confirm `GEMINI_API_KEY` is valid and the selected model is available for your account.
- **PDF text not extracted:** try a text-based PDF or paste the notes manually.
- **Website shows a build error:** check Render's deploy logs and confirm all project files are committed at the repository root.


## Professional UI + GitHub Pages option

The `github-pages/` folder contains a static frontend build with corrected asset paths
and demo persistence. If you want GitHub Pages, upload the *contents* of that folder
to the repository root (not the folder itself). GitHub Pages cannot execute Flask/Python.

For the complete backend version, deploy the project root to a Python host using
`render.yaml`; then configure `GEMINI_API_KEY` in the host's environment settings.
Do not expose your API key in frontend JavaScript.
