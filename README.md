# WebBeds Canvas Generator - Vercel V3

This build intentionally has no `webapp/static` or `webapp/templates` dependency.
The HTML/CSS is embedded in Python and the Excel canvas template is embedded as base64.

Vercel entrypoint: `app.py`
Health check: `/api/health`
