#!/usr/bin/env python

import importlib
import inspect
import warnings

warnings.filterwarnings("ignore", message=".*urllib3.*or chardet.*")

__all__: list[str] = []

CORE_MODULES = [
    "vaultwarden_mcp.api",
    "vaultwarden_mcp.error_authority",
]

OPTIONAL_MODULES = {
    "vaultwarden_mcp.mcp_server": "mcp",
}


def _import_module_safely(module_name: str):
    """Try to import a module and return it, or None if not available."""
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None


def _expose_members(module):
    """Expose public classes and functions from a module into globals and __all__."""
    for name, obj in inspect.getmembers(module):
        if (inspect.isclass(obj) or inspect.isfunction(obj)) and not name.startswith(
            "_"
        ):
            globals()[name] = obj
            __all__.append(name)


for module_name in CORE_MODULES:
    try:
        module = importlib.import_module(module_name)
        _expose_members(module)
    except ImportError:
        pass

for module_name, extra_name in OPTIONAL_MODULES.items():
    module = _import_module_safely(module_name)
    if module is not None:
        _expose_members(module)
        globals()[f"_{extra_name.upper()}_AVAILABLE"] = True
    else:
        globals()[f"_{extra_name.upper()}_AVAILABLE"] = False

__all__.extend(["_MCP_AVAILABLE"])

from agent_connector_sdk.connector import Connector

from vaultwarden_mcp.api import VaultwardenApi
from vaultwarden_mcp.api._operation_manifest import OPERATIONS
from vaultwarden_mcp.auth import get_client

connector = Connector(
    tools="vaultwarden_mcp.mcp",
    instructions="Vaultwarden MCP Server — intent and verbose tool surfaces.",
    verbose_targets=(
        {
            "client_cls": VaultwardenApi,
            "get_client": get_client,
            "manifest": OPERATIONS,
        },
    ),
)

__all__ = ["connector"]
