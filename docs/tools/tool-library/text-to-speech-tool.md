# TextToSpeechTool

The `TextToSpeechTool` converts text to speech using OpenAI's text-to-speech API. This tool allows agents to generate natural-sounding audio from text input with different voice options.

## Features

- Convert text to speech with multiple voice options
- Handle long texts by splitting into chunks
- Combine audio segments into a single file
- Output MP3 files accessible via URL or file path

## Authentication

Requires an OpenAI API key, which can be stored in Agentic's secrets system as `OPENAI_API_KEY`. You likely already have this set up if you've used Agentic before.

## Methods

### generate_speech_file_from_text

```python
def generate_speech_file_from_text(voice: str, text: Optional[str] = None, input_file_name: Optional[str] = None) -> str
```

Generate speech from the given text or input file and save it to a file.

**Parameters:**

- `voice (str)`: Voice type to use (one of: alloy, echo, fable, onyx, nova, shimmer)
- `text (Optional[str])`: The text to be converted to speech
- `input_file_name (Optional[str])`: Optional name of a file to read text from

**Returns:**
A JSON string containing the URL or file path to the generated audio file.

## Voice Options

The tool supports the following OpenAI TTS-1 voices:

- `alloy`: Versatile, neutral voice
- `echo`: An older, deeper voice with gravitas
- `fable`: An accented, narrative voice
- `onyx`: A deep, authoritative voice
- `nova`: A professional, clear voice
- `shimmer`: A gentler, lighter voice

## Example Usage

```python
from agentic.common import Agent
from agentic.tools.text_to_speech_tool import TextToSpeechTool

# Create an agent with text-to-speech capabilities
tts_agent = Agent(
    name="Voice Generator",
    instructions="You convert text to spoken audio with natural-sounding voices.",
    tools=[TextToSpeechTool()]
)

# Generate speech from direct text input
response = tts_agent << 'Convert this text to speech using the "nova" voice: "Welcome to Agentic, the framework for building intelligent agents. This audio was generated using OpenAI\'s text-to-speech API."'
print(response)

# Generate speech from a text file
response = tts_agent << 'Read the contents of "speech_script.txt" using the "echo" voice'
print(response)

# Generate speech with specific instructions
response = tts_agent << 'Create a narration for this short story using the "fable" voice: "Once upon a time in a digital realm, agents and humans worked together to solve complex problems..."'
print(response)
```

## How It Works

The tool works as follows:

1. Takes input text directly or reads from a file
2. If text exceeds OpenAI's TTS limits, splits it into chunks
3. Generates audio for each chunk using OpenAI's TTS API
4. Combines audio segments into a single MP3 file
5. Returns a URL or file path to access the audio

## Technical Implementation

The tool uses:

- OpenAI's TTS-1 model
- Pydub for audio processing and concatenation
- Async operations for efficient processing
- Temporary storage for intermediate audio files

## Notes

- Maximum text length is limited by OpenAI's API (4096 characters per chunk)
- Long texts are automatically split into appropriate chunks
- MP3 format is used for all audio files
- File paths in the format `file:///path/to/audio.mp3` are returned for local files
- For production use, files can be uploaded to S3 for web accessibility
- The tool requires the pydub library for audio processing
