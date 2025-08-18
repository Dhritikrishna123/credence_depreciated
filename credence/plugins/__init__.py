from __future__ import annotations

from importlib import import_module
from typing import Any


def load_symbol(path: str) -> Any:
	"""Load a class or function from a dotted path like 'module:Symbol'."""
	if ":" not in path:
		raise ValueError(f"Invalid plugin path: {path}")
	module_path, symbol_name = path.split(":", 1)
	module = import_module(module_path)
	return getattr(module, symbol_name)


