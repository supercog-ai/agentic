import os
import pytest

os.environ["AGENTIC_SIMPLE_ACTORS"] = "1"

def pytest_addoption(parser):
    parser.addoption(
        "--runrag", action="store_true", default=False, help="run RAG integration tests"
    )

def pytest_configure(config):
    config.addinivalue_line("markers", "rag: mark test as RAG integration test")
    config.addinivalue_line("markers", "requires_llm: marks tests that require calls to an llm to execute")
    config.addinivalue_line("markers", "requires_secrets: marks tests that require access to secrets")
    
def pytest_collection_modifyitems(config, items):
    if not config.getoption("--runrag"):
        skip_rag = pytest.mark.skip(reason="need --runrag option to run")
        for item in items:
            if "rag" in item.keywords:
                item.add_marker(skip_rag)
