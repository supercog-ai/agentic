# Standard model identifiers
CLAUDE = "anthropic/claude-3-5-sonnet-latest"
CLAUDE_4_SONNET = "anthropic/claude-sonnet-4-20250514"
CLAUDE_4_OPUS = "anthropic/claude-opus-4-20250514"
CLAUDE_3_7 = "claude-3-7-sonnet-20250219"
GPT_4O_MINI = "gpt-4o-mini"  # Default model
GPT_4O = "openai/gpt-4o"
GPT_O1 = "openai/gpt-o1"
GEMINI_FLASH = "gemini/gemini-2.0-flash"
GEMINI_2_5_PRO_PREVIEW = "gemini/gemini-2.5-pro-preview-05-06"
GEMINI_2_5_FLASH_PREVIEW = "gemini/gemini-2.5-flash-preview-05-20"

# LM Studio model identifiers (using litellm's built-in support)
LMSTUDIO_QWEN = "lm_studio/qwen2.5-7b-instruct-1m"
LMSTUDIO_DEEPSEEK = "lm_studio/deepseek-r1-distill-qwen-7B"

# Default model (used when no model is specified)
DEFAULT_MODEL = GPT_4O_MINI

# Model families
ANTHROPIC_MODELS = {
    "claude-3-5-sonnet": CLAUDE,
    "claude-4-sonnet": CLAUDE_4_SONNET,
    "claude-4-opus": CLAUDE_4_OPUS,
    "claude-3-7-sonnet": CLAUDE_3_7,
}

OPENAI_MODELS = {
    "gpt-4o-mini": GPT_4O_MINI,
    "gpt-4o": GPT_4O,
    "gpt-o1": GPT_O1,
}

GEMINI_MODELS = {
    "gemini-2.0-flash": GEMINI_FLASH,
    "gemini-2.5-pro-preview": GEMINI_2_5_PRO_PREVIEW,
    "gemini-2.5-flash-preview": GEMINI_2_5_FLASH_PREVIEW,
}

LMSTUDIO_MODELS = {
    "qwen2.5": LMSTUDIO_QWEN,
    "deepseek-r1": LMSTUDIO_DEEPSEEK,
}

# Common model categories for reference
CHAT_MODELS = {
    **ANTHROPIC_MODELS,
    **OPENAI_MODELS,
    **GEMINI_MODELS,
    **LMSTUDIO_MODELS,
}

CHAT_MODELS["mock"] = "mock/default"

SPECIAL_MODEL_CONFIGS = {
    "lm_studio/": {
        "base_url": "http://localhost:1234/v1",
        "api_key": "",
        "custom_llm_provider": "openai"
    }
    # Add other special cases here only when needed
}


def get_special_model_params(model_id: str) -> dict:
    """Get special parameters for models that need them"""
    for prefix, config in SPECIAL_MODEL_CONFIGS.items():
        if model_id.startswith(prefix):
            return config
    return {}  # Default to no special parameters


# Import the mock provider implementation
from .custom_models.mock_provider import MockModelProvider

# Initialize global mock provider instance that will be used across the application
mock_provider = MockModelProvider()  # Initialize with default instance
