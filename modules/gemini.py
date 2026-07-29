from google import genai
from google.genai import types

from modules.config import (
    GEMINI_API_KEY,
    MODEL_NAME,
    TEMPERATURE,
    MAX_OUTPUT_TOKENS,
)


class GeminiClient:

    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def ask(self, system_prompt: str, user_prompt: str) -> str:

        response = self.client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(
                            text=user_prompt
                        )
                    ],
                )
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=TEMPERATURE,
                max_output_tokens=MAX_OUTPUT_TOKENS,
            ),
        )

        return response.text