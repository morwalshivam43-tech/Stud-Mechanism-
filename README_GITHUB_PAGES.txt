STUDYMATE AI — GITHUB PAGES FRONTEND

1. Open your GitHub repository.
2. Upload the CONTENTS of this github-pages folder into the repository root:
   - index.html
   - static/ (folder)
   - README_GITHUB_PAGES.txt
3. Commit the changes.
4. In GitHub: Settings → Pages → deploy from your main branch and root folder.
5. Open the published site and hard-refresh with Ctrl+F5.

This static edition includes a responsive UI and demo/localStorage behavior for notes,
tasks and quizzes. It cannot run Python/Flask or securely call Gemini from GitHub Pages.
For real AI responses and server-backed data, deploy the Flask app from the project root
to a Python host such as Render. Add GEMINI_API_KEY as a server environment variable;
never place a private API key in browser JavaScript.

The full Flask application is in the project root:
- app.py
- templates/
- static/
- requirements.txt
- render.yaml
