# Vercel deployment

This project is prepared for Vercel's zero-configuration FastAPI support.

## Important fix
The original project had a stray `\` character as the first line of several Python files (`main.py`, `parser.py`, `generator.py`, `rules.py`). That causes Python to fail during import and can surface on Vercel as `FUNCTION_INVOCATION_FAILED`.

The corrected project also provides a root-level `app.py` entrypoint, which exposes the FastAPI application as `app` for Vercel.

## Deploy
1. Replace the files in your GitHub repository with the contents of this folder.
2. Commit and push to GitHub.
3. In Vercel, open the project and trigger **Redeploy** (or let the Git push deploy automatically).
4. Framework Preset can remain auto-detected.
5. Root Directory should be the repository root (the folder containing `app.py`, `pyproject.toml`, and `requirements.txt`).

No custom Build Command or Output Directory is needed.
