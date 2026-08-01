import json

from modules.config import (
    TEMPERATURE,
    MAX_OUTPUT_TOKENS,
)
from modules.openrouter_manager import manager

CHAT_MODEL = "google/gemma-4-26b-a4b-it:free"
VISION_MODEL = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"


class AIClient:

    def __init__(self):
        self.manager = manager

    # -----------------------------------------------------

    def chat(
        self,
        messages: list,
        model: str = CHAT_MODEL,
        max_tokens: int = MAX_OUTPUT_TOKENS,
        temperature: float = TEMPERATURE,
        timeout: int = 30,
    ) -> str:

        response = self.manager.chat_completions_create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )

        return response.choices[0].message.content.strip()

    # -----------------------------------------------------

    def ask(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:

        return self.chat(
            [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ]
        )

    # -----------------------------------------------------

    def analyze_image_url(
        self,
        image_url: str,
        prompt: str,
    ) -> str:

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url,
                        },
                    },
                ],
            }
        ]

        return self.chat(
            messages=messages,
            model=VISION_MODEL,
            timeout=60,
        )

    # -----------------------------------------------------

    def analyze_image_with_context(
        self,
        image_url: str,
        system_prompt: str,
        user_text: str,
    ) -> str:
        """
        analyze_image_url ile ayni calisan yapiyi kullanir (TEK user
        mesaji, ayri bir system rolu YOK). Bazi ucretsiz vision
        modelleri ayri bir system mesaji + gorsel kombinasyonunda
        gorseli yok sayip sadece system prompt'a gore cevap
        uretebiliyor -- bu yuzden hepsini tek metne birlestiriyoruz.
        """

        combined_text = system_prompt.format(user_text=user_text) \
            if "{user_text}" in system_prompt else \
            f"{system_prompt}\n\nKullanıcının mesajı: {user_text}"

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": combined_text,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url,
                        },
                    },
                ],
            },
        ]

        return self.chat(
            messages=messages,
            model=VISION_MODEL,
            timeout=60,
        )

    # -----------------------------------------------------

    def extract_profile_info(
        self,
        text: str,
        prompt: str,
    ) -> dict:

        content = self.chat(
            [
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": text,
                },
            ]
        )

        content = content.replace("```json", "")
        content = content.replace("```", "")
        content = content.strip()

        try:
            data = json.loads(content)

        except Exception:

            return {
                "interests": [],
                "projects": [],
                "preferences": [],
                "facts": [],
            }

        return {
            "interests": data.get("interests", []),
            "projects": data.get("projects", []),
            "preferences": data.get("preferences", []),
            "facts": data.get("facts", []),
        }

    # -----------------------------------------------------

    def compare_images(
        self,
        first_image_url: str,
        second_image_url: str,
        prompt: str,
    ) -> str:

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": first_image_url,
                        },
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": second_image_url,
                        },
                    },
                ],
            }
        ]

        return self.chat(
            messages=messages,
            model=VISION_MODEL,
            timeout=60,
        )