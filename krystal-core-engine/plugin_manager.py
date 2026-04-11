"""
Dynamic plugin discovery and routing for the Krystal engine.

Plugins are ordinary Python modules placed in the ``plugins/`` directory. Each
plugin module **must** define:

- ``NAME`` (``str``): Slash-command identifier, with or without a leading ``/``
  (e.g. ``"search"`` or ``"/search"`` for user input ``/search ...``).
- ``DESCRIPTION`` (``str``): Human-readable summary for listings or help.
- ``run(query, **kwargs)`` (callable): Entry point. ``query`` is the text after
  the command token; return value should be a string (non-strings are coerced).

Modules named ``__init__.py`` are ignored. Only ``.py`` files are scanned.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any


class PluginManager:
    """
    Scan ``plugins/``, load candidate modules with ``importlib``, and register
    those that satisfy the required interface.
    """

    @staticmethod
    def _normalize_command_key(fragment: str) -> str:
        """Lowercase, trim, and strip a single leading ``/`` from a command token."""
        return str(fragment).strip().lower().lstrip("/")

    def __init__(self, plugins_dir: str | Path | None = None) -> None:
        """
        Args:
            plugins_dir: Directory containing plugin ``.py`` files. Defaults to
                ``<project_root>/plugins`` (sibling of ``krystal-core-engine``).
        """
        base = Path(__file__).resolve().parent.parent
        self._plugins_dir = Path(plugins_dir) if plugins_dir is not None else base / "plugins"
        self._plugins: dict[str, ModuleType] = {}
        self.load_errors: list[str] = []
        self.load_plugins()

    @property
    def plugins_dir(self) -> Path:
        return self._plugins_dir

    def load_plugins(self) -> None:
        """Clear registry, rescan ``plugins_dir``, and repopulate registered plugins."""
        self._plugins.clear()
        self.load_errors.clear()
        directory = self._plugins_dir
        if not directory.is_dir():
            self.load_errors.append(f"Plugin directory missing or not a directory: {directory}")
            return

        py_files = sorted(
            p for p in directory.iterdir() if p.suffix == ".py" and p.name != "__init__.py"
        )
        for path in py_files:
            self._try_register_file(path)

    def _try_register_file(self, path: Path) -> None:
        module_name = f"krystal_plugin_{path.stem}"
        try:
            module = self._load_module(module_name, path)
        except Exception as exc:  # noqa: BLE001 — isolate bad files
            self.load_errors.append(f"{path.name}: failed to import ({type(exc).__name__}: {exc})")
            return

        valid, reason = self._validate_plugin_module(module)
        if not valid:
            self.load_errors.append(f"{path.name}: {reason}")
            return

        name_key = self._normalize_command_key(str(getattr(module, "NAME")))
        if not name_key:
            self.load_errors.append(f"{path.name}: NAME is empty after normalization")
            return
        if name_key in self._plugins:
            self.load_errors.append(
                f"{path.name}: duplicate NAME {name_key!r} (already registered; skipping)"
            )
            return

        self._plugins[name_key] = module

    @staticmethod
    def _load_module(module_name: str, path: Path) -> ModuleType:
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not create import spec for {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    @staticmethod
    def _validate_plugin_module(module: ModuleType) -> tuple[bool, str]:
        name = getattr(module, "NAME", None)
        desc = getattr(module, "DESCRIPTION", None)
        run_fn = getattr(module, "run", None)

        if not isinstance(name, str):
            return False, "missing or invalid NAME (required non-empty str)"
        if not isinstance(desc, str):
            return False, "missing or invalid DESCRIPTION (required str)"
        if not callable(run_fn):
            return False, "missing or invalid run (required callable)"

        if not str(name).strip():
            return False, "NAME must be non-empty"

        return True, ""

    def registered_names(self) -> list[str]:
        """Sorted list of registered slash-command names (lowercase keys)."""
        return sorted(self._plugins.keys())
    
    def get_plugins_info(self) -> dict[str, dict[str, str]]:
        """Get information about all registered plugins."""
        plugins_info = {}
        for cmd, module in self._plugins.items():
            name = getattr(module, "NAME", "")
            description = getattr(module, "DESCRIPTION", "")
            plugins_info[f"/{cmd}"] = {
                "name": name,
                "description": description
            }
        return plugins_info

    def route_to_plugin(self, query: str, **kwargs: Any) -> str | None:
        """
        If ``query`` starts with a slash command that matches a registered plugin,
        invoke ``run`` and return a string result.

        Returns:
            ``None`` if the input is not a slash command or no plugin matches.
            Otherwise the plugin result (or an error message if the plugin raised).
        """
        stripped = query.strip()
        if not stripped.startswith("/"):
            return None

        parts = stripped.split(None, 1)
        token = parts[0]
        rest = parts[1] if len(parts) > 1 else ""

        cmd = self._normalize_command_key(token[1:])
        if not cmd:
            return None

        module = self._plugins.get(cmd)
        if module is None:
            return None

        run_fn = getattr(module, "run")
        try:
            raw = run_fn(rest, **kwargs)
        except Exception as exc:  # noqa: BLE001 — must not crash the engine
            return f"[Plugin {cmd!r} error] {type(exc).__name__}: {exc}"

        if raw is None:
            return ""
        if isinstance(raw, str):
            return raw
        try:
            return str(raw)
        except Exception:  # noqa: BLE001
            return f"[Plugin {cmd!r} error] run() returned a non-string value that could not be coerced."
