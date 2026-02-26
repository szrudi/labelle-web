import os
import sys
import tempfile

import pytest

# Add server directory to path so tests can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Provide a temporary directory for virtual printer output."""
    return str(tmp_path / "output")


@pytest.fixture
def virtual_printer_env(tmp_path):
    """Set VIRTUAL_PRINTERS env var with a valid config pointing to tmp dirs."""
    import json

    output1 = str(tmp_path / "printer1")
    output2 = str(tmp_path / "printer2")
    config = [
        {"name": "Test Printer", "path": output1, "output": "image"},
        {"name": "Office (2nd Floor)", "path": output2, "output": "both"},
    ]
    old = os.environ.get("VIRTUAL_PRINTERS")
    os.environ["VIRTUAL_PRINTERS"] = json.dumps(config)
    yield config
    if old is None:
        os.environ.pop("VIRTUAL_PRINTERS", None)
    else:
        os.environ["VIRTUAL_PRINTERS"] = old


@pytest.fixture
def no_virtual_printers_env():
    """Ensure VIRTUAL_PRINTERS is unset."""
    old = os.environ.get("VIRTUAL_PRINTERS")
    os.environ.pop("VIRTUAL_PRINTERS", None)
    yield
    if old is not None:
        os.environ["VIRTUAL_PRINTERS"] = old
