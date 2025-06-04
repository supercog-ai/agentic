# ImageGeneratorTool

The `ImageGeneratorTool` provides capabilities for generating images using OpenAI's image generation models. This tool allows agents to create images based on text prompts and return accessible URLs.

## Features

- Generate images from text descriptions
- Automatic storage of generated images
- Return markdown-formatted image URLs
- Integration with OpenAI's image generation API

## Authentication

Requires an OpenAI API key with access to image generation features. You may have already set this key while setting up agentic. It can be:

- Passed to the tool during initialization
- Set in the environment as `OPENAI_API_KEY` 
- Stored in Agentic's secrets system as `OPENAI_API_KEY`

## Methods

### generate_image

```python
async def generate_image(prompt: str, thread_context: RunContext) -> str
```

Generates an image based on the given text prompt.

**Parameters:**

- `prompt (str)`: Text description of the image to generate
- `thread_context (RunContext)`: The execution context

**Returns:**
A markdown-formatted string with the URL to the generated image, or an error message.

## Example Usage

```python
from agentic.common import Agent
from agentic.tools import ImageGeneratorTool

# Create an agent with image generation capabilities
image_agent = Agent(
    name="Image Creator",
    instructions="You create images based on user descriptions.",
    tools=[ImageGeneratorTool()]
)

# Use the agent to generate an image
response = image_agent << "Create an image of a futuristic city with flying cars and tall glass buildings"
print(response)

# Output will include: [image result](https://image-url.com)
```

## Behind the Scenes

The tool works by:

1. Taking a text prompt describing the desired image
2. Calling OpenAI's image generation API
3. Receiving the generated image URL or data
4. Formatting the result as a markdown link that can be displayed inline

## Image Storage

The tool can store generated images in one of two ways:

1. Using the direct URL provided by OpenAI's API
2. Downloading and storing the image in a specified S3 bucket, then returning a public URL

## Error Handling

The tool handles various error conditions:

- Missing API key: Will prompt the user for credentials
- Generation failures: Returns a descriptive error message
- Storage issues: Provides details on what went wrong

## Notes

- Image quality and accuracy depend on the clarity and specificity of the prompt
- Uses OpenAI's standard image generation model (DALL-E)
- Generated images comply with OpenAI's content policy
- The API key must have sufficient credits for image generation
- Images are publicly accessible through the returned URLs
