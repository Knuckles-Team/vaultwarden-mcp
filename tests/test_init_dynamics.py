import importlib

import pytest


@pytest.mark.concept("VW-OS.init.package-public-api")
def test_package_imports():
    """Top-level package exposes its public API. CONCEPT:VW-OS.init.package-public-api"""
    module = importlib.import_module("vaultwarden_mcp")
    assert hasattr(module, "__all__")
