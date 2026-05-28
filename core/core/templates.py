"""Jinja2 template loader — shared utility used across the codebase.

Templates (prompts, text fragments) live next to the module that uses them in a
`templates/` subdirectory by convention, keeping prompt content out of code while
sitting close to it.

Usage:
    from core.templates import get_jinja_template

    system_prompt = get_jinja_template("templates/translate.md").render()
    # or with variables:
    system_prompt = get_jinja_template("templates/translate.md").render(name="ira")

If `directory` is omitted, the template is resolved relative to the **caller's** file —
so each module references its own `templates/` without passing paths around.

Globals available in every template: `current_datetime` (a UTC datetime, fixed at the
moment `get_jinja_template` is called).
"""

import inspect
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Template


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_jinja_template(filename: str, directory: str | Path | None = None) -> Template:
    """Load a Jinja template; resolves relative to the caller's directory by default."""
    directory = directory or Path(inspect.stack()[1].filename).parent
    env = Environment(loader=FileSystemLoader(directory))
    env.globals = {"current_datetime": utc_now()}
    return env.get_template(filename)
