from typing import Callable
from litellm import image_generation

# required packages:

from .base import BaseAgenticTool
from agentic.common import RunContext, PauseForInputResult
from .s3_utils import S3Utility


class OpenAIImageGenerator(BaseAgenticTool):
    api_key: str
    """
    A tool for generating images using OpenAI's GPT-4V model and storing them in an S3 bucket.
    """

    def __init__(self):
        self.api_key = None
        pass

    def get_tools(self) -> list[Callable]:
        return [
            self.generate_image,
        ]

    async def generate_image(self, prompt: str, run_context: RunContext) -> str:
        """
        Generates an image based on the given text prompt using OpenAI's API,
        stores it in an S3 bucket, and returns a publicly accessible URL for the image.
        """
        api_key = run_context.get_secret("OPENAI_API_KEY", self.api_key)

        if not api_key:
            return PauseForInputResult(
                {"OPENAI_API_KEY": "Please supply your OpenAI API key"}
            )

        try:
            response = image_generation(prompt)

            image_url = response["data"][0]["url"]

            return f"[image result]({image_url})"

        except Exception as e:
            return f"Error generating or storing image: {str(e)}"
