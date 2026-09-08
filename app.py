"""Vercel entrypoint. No static/template directory dependency."""
from webapp.main import app

__all__ = ["app"]
