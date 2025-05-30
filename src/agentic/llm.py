# Utility functions for doing "LLM as coder" in your programs.
import os
import re
from typing import Optional, Type

from .settings import settings
from .agentic_secrets import agentic_secrets
from litellm import completion
import litellm
from litellm import token_counter
from jinja2 import Template
from dataclasses import dataclass
from pydantic import BaseModel

DEFAULT_MODEL = settings.get("DEFAULT_CODE_LLM", "openai/gpt-4o-mini")

CLAUDE_DEFAULT_MODEL = "anthropic/claude-sonnet-4-20250514"
GPT_DEFAULT_MODEL = "openai/gpt-4o-mini"
GEMINI_DEFAULT_MODEL = "gemini/gemini-2.5-flash-preview-05-20"


@dataclass
class LLMUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""

    def __str__(self) -> str:
        return f"[{self.model}: {self.input_tokens} --> {self.output_tokens}]"


def setup_model_key(model: str):
    """Loads the model key from secrets and ensures its in the environment, or checks
    that is there already."""

    # Write a match statement that matches by regular expressions
    key_name = None
    if re.match(r"^gpt-\d+", model) or model.startswith("openai/"):
        # Code to handle GPT models
        key_name = "OPENAI_API_KEY"
    elif re.match(r"^claude-\w+", model) or model.startswith("anthropic/"):
        # Code to handle Claude models
        key_name = "ANTHROPIC_API_KEY"
    elif re.match(r"^replicate/", model) or model.startswith("replicate/"):
        key_name = "REPLICATE_API_KEY"
    elif re.match(r"^gemini/", model) or model.startswith("google/"):
        key_name = "GEMINI_API_KEY"
    else:
        raise ValueError(f"Unknown model {model}")

    value = agentic_secrets.get_secret(key_name, os.environ.get(key_name))
    if value:
        os.environ[key_name] = value
        return value
    else:
        raise RuntimeError(f"Missing API key {key_name} to use {model}")


def llm_generate(prompt: str, **kwargs) -> str:
    """Core LLM call utility. Takes a prompt, potential
    Jinja template variables to substitute, and calls the
    default LLM to generate a completion. Pass a 'usage' object (LLMUsage) as an argument to get usage info back.
    It will be populated with 'model', 'input_tokens' and 'output_tokens' keys."""

    model = kwargs.get("model") or DEFAULT_MODEL
    setup_model_key(model)
    template = Template(prompt)
    prompt = template.render(**kwargs)

    msg = {"content": prompt, "role": "user"}
    response = completion(model=model, messages=[msg])
    response_text = response.choices[0].message.content or ""

    if "usage" in kwargs:
        usage: LLMUsage = kwargs["usage"]
        if not isinstance(usage, LLMUsage):
            print(f"Error! Bad usage object pass to llm_generate: {usage}")
        else:
            usage.input_tokens = token_counter(DEFAULT_MODEL, messages=[msg])
            if response_text:
                usage.output_tokens = token_counter(DEFAULT_MODEL, text=response_text)
            else:
                usage.output_tokens = 0
            usage.model = model

    return response_text


from typing import TypeVar, Generic

T = TypeVar("T", bound=BaseModel)


def llm_generate_with_format(prompt: str, return_format: Type[T], **kwargs) -> T:
    """Core LLM call utility. Takes a prompt, potential
    Jinja template variables to substitute, and calls the
    default LLM to generate a completion. Pass a 'usage' object (LLMUsage) as an argument to get usage info back.
    It will be populated with 'model', 'input_tokens' and 'output_tokens' keys."""

    model = kwargs.get("model") or DEFAULT_MODEL
    setup_model_key(model)
    template = Template(prompt)
    prompt = template.render(**kwargs)

    msg = {"content": prompt, "role": "user"}

    resp = completion(model=model, messages=[msg], response_format=return_format)
    return return_format.model_validate_json(resp.choices[0].message.content)
