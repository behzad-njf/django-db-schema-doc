"""Pytest + Django: use the demo project settings and SQLite schema."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DEMO_ROOT = REPO_ROOT / "examples" / "demo_project"

for path in (str(REPO_ROOT), str(DEMO_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Apply shop migrations once per test session."""
    with django_db_blocker.unblock():
        from django.core.management import call_command

        call_command("migrate", verbosity=0, interactive=False)
