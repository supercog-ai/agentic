import pytest
from unittest.mock import patch, MagicMock
from typing import Dict, Any
from jinja2 import Template
from pydantic import BaseModel

# Assuming these are imported from your module
from agentic.llm import llm_generate, llm_generate_with_format

@pytest.mark.requires_llm
def test_llm_generate_return_format():
    """Test different return format types"""
    class CalendarEvent(BaseModel):
        name: str
        date: str
        participants: list[str]

    prompt = "Create a calendar event for Scott, plus {{PARTS}}, on Dec 12"
    PARTS = "Alex, John, Jane"

    result = llm_generate_with_format(prompt, CalendarEvent, PARTS=PARTS)
    assert isinstance(result, CalendarEvent)
    assert 'meeting' in result.name.lower()
    assert "Alex" in result.participants
