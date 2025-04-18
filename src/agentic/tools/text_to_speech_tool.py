import os
import traceback
import json
import os
from datetime import datetime
from typing import List, Callable, Optional, Literal

from openai import OpenAI

from agentic.tools.base import BaseAgenticTool
from agentic.tools.utils.registry import tool_registry, Dependency, ConfigRequirement

from agentic.agentic_secrets import agentic_secrets

with tool_registry.safe_imports():
    from pydub import AudioSegment


@tool_registry.register(
    name="TextToSpeechTool",
    description="Convert text to speech with different voices",
    dependencies=[
        Dependency(
            name="pydub",
            type="pip",
            version="0.25.1"
        ),
    ],
    config_requirements=[
        ConfigRequirement(
            key="OPENAI_API_KEY",
            description="OpenAI API key",
            required=True
        ),
    ],
)
class TextToSpeechTool(BaseAgenticTool):
    openai_api_key: str = ""

    def __init__(self):
        return super().__init__()

    def get_tools(self) -> List[Callable]:
        return [
            self.generate_speech_file_from_text,
        ]

    def _save_audio_to_s3(self, voice: str, audio_data) -> str:
        """
        Save audio data to a local file and then upload it to an S3 bucket.

        Args:
            voice (str): The voice identifier used to generate the filename.
            audio_data: The raw audio data to be saved and uploaded.

        Returns:
            str: A JSON string containing either the audio URL or an error message.

        Raises:
            ValueError: If the created file is empty.
            FileNotFoundError: If the file does not exist after an attempted write.
        """
        try:
            # Generate a unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"speech_{voice}_{timestamp}.mp3"
            # Define the path where the file will be saved
            save_path = os.path.join("audio", filename)
            print(f"Audio file path: {save_path}")

            # Ensure the directory exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # Write the raw audio data directly to file
            with open(save_path, "wb") as f:
                f.write(audio_data)

            # Verify file existence and size
            if os.path.exists(save_path):
                file_size = os.path.getsize(save_path)
                print(f"File exists. Size: {file_size} bytes")

                if file_size == 0:
                    raise ValueError("File was created but is empty")

                # Upload to S3
                raw_url = self.run_context.upload_user_file_to_s3(
                    file_name=filename, original_folder="audio", mime_type="audio/mpeg"
                )
                print(
                    f"generate_speech_file_from_text:Speech saved successfully:Raw_url -> {raw_url}"
                )
                # Get the correct URL
                audio_url = self.run_context.get_file_url(filename, "audio")
                print(f"generate_speech_file_from_text: correct URL -> {audio_url}")

                # Clean up the local file after successful upload
                os.remove(save_path)
                print(
                    f"generate_speech_file_from_text:Local file removed -> {save_path}"
                )

                # Return the URL as a JSON string
                return json.dumps(
                    {"content_type": "audio/mpeg", "audio_url": audio_url.get("url")}
                )
            else:
                raise FileNotFoundError(
                    f"File does not exist after attempted write: {save_path}"
                )
        except Exception as e:
            error_message = f"Error saving audio file to s3: {str(e)}"
            print(error_message)
            return json.dumps({"error": error_message})

    def split_text(self, text, max_length):
        chunks = []
        while len(text) > max_length:
            chunk = text[:max_length]
            text = text[max_length:]
            chunks.append(chunk)
        chunks.append(text)
        return chunks

    def text_to_speech(
        self,
        text,
        filepath,
        voice: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"] = "nova",
    ):
        client = OpenAI(api_key=self.openai_api_key)
        response = client.audio.speech.create(model="tts-1", voice=voice, input=text)
        with open(filepath, "wb") as f:
            for chunk in response.iter_bytes():
                f.write(chunk)

    def generate_speech_file_from_text(
        self,
        voice: str,
        text: Optional[str] = None,
        input_file_name: Optional[str] = None,
    ) -> str:
        """
        Generate speech from the given text or input file using OpenAI's Text-to-Speech API and save it to a file.

        :param voice: str one of: alloy, echo, fable, onyx, nova, and shimmer
        :param text: str
            The text to be converted to speech.
        :param input_file_name: Optional name of a file to read text from.
        :return: str
            The URL of the generated audio file.
        """
        self.openai_api_key = agentic_secrets.get_required_secret("OPENAI_API_KEY")

        if input_file_name:
            text = (text or "") + open(input_file_name, "r").read()

        try:
            max_length = 4096
            chunks = self.split_text(text, max_length)

            audio_files = []
            for i, chunk in enumerate(chunks):
                chunk_filename = f"chunk_{i}.mp3"
                self.text_to_speech(chunk, chunk_filename, voice)
                audio_files.append(chunk_filename)

            combined = AudioSegment.empty()
            for file in audio_files:
                combined += AudioSegment.from_mp3(file)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"speech_{voice}_{timestamp}.mp3"
            # Define the path where the file will be saved
            save_path = filename
            combined.export(save_path, format="mp3")

            # raw_url = self.run_context.upload_user_file_to_s3(
            #     file_name=filename, original_folder="audio", mime_type="audio/mpeg"
            # )
            # print(
            #     f"generate_speech_file_from_text:Speech saved successfully:Raw_url -> {raw_url}"
            # )
            # # Get the correct URL
            # audio_url = self.run_context.get_file_url(filename, "audio")
            # print(f"generate_speech_file_from_text: correct URL -> {audio_url}")

            # # Clean up the local file after successful upload
            # os.remove(save_path)
            # print(f"generate_speech_file_from_text:Local file removed -> {save_path}")

            # Return the URL as a JSON string
            return json.dumps(
                {"content_type": "audio/mpeg", "audio_url": f"file:///{save_path}"}
            )
        except Exception as e:
            traceback.print_exc()
            error_message = f"Error generating speech: {str(e)}"
            print(error_message)
            return json.dumps({"error": error_message})
        return return_str
