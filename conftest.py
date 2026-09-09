"""Marks the repository root for pytest.

pytest inserts the directory holding the topmost conftest.py onto sys.path, which
is what lets the tests write `from src import config` without an editable install
or a PYTHONPATH incantation.  The file is intentionally empty otherwise.
"""
