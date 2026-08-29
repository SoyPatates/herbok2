import json

from modules.config import (
    TEMPERATURE,
    MAX_OUTPUT_TOKENS,
)
from modules.openrouter_manager import manager
from modules.logger import logger

CHAT_MODEL = "google/gemma-4-26b-a4b-it:free"
VISION_MODEL = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"

EMPTY_CATEGORY_DICT = {
    "interests": [],
    "projects": [],
    "preferences": [],
    "facts": [],
}


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

        raw_content = content

        content = content.replace("```json", "")
        content = content.replace("```", "")
        content = content.strip()

        try:
            data = json.loads(content)

        except Exception as e:

            logger.warning(
                "extract_profile_info: JSON parse basarisiz (%s). "
                "Ham model cevabi: %r",
                e,
                raw_content[:1000],
            )

            return {
                "interests": [],
                "projects": [],
                "preferences": [],
                "facts": [],
            }

        result = {
            "interests": data.get("interests", []),
            "projects": data.get("projects", []),
            "preferences": data.get("preferences", []),
            "facts": data.get("facts", []),
        }

        total = sum(len(v) for v in result.values())

        if total == 0:
            logger.debug(
                "extract_profile_info: model gecerli JSON dondurdu ama "
                "hicbir kategori dolu degil. Ham cevap: %r",
                raw_content[:500],
            )
        else:
            logger.info(
                "extract_profile_info: %d bilgi cikarildi -> %s",
                total,
                result,
            )

        return result

    # -----------------------------------------------------

    def extract_combined_profile_info(
        self,
        text: str,
        prompt: str,
        target_names: list,
    ) -> dict:
        """
        extract_profile_info ile ayni is ama TEK cagrida hem mesaji
        yazanin kendi hakkindaki bilgisini HEM DE mesajda etiketlenen
        kisi(ler) hakkindaki bilgiyi birlikte cikarir. Onceden bunlar
        1 + N ayri AI cagrisiydi (N = etiketlenen kisi sayisi), bu da
        API kullanimini gereksiz yere artiriyordu.

        Donen deger:
        {
            "self": {"interests": [...], "projects": [...], ...},
            "targets": {
                "<isim>": {"interests": [...], ...},
                ...
            }
        }

        target_names, prompt icindeki {target_names} yerine zaten
        gecirilmis olmali (bkz. COMBINED_MEMORY_EXTRACTION_PROMPT) --
        burada sadece JSON'daki "targets" altinda hangi isimlerin
        bekledigini bilmek icin (parse hatasinda dogru bos yapiyi
        kurabilmek icin) kullanilir.
        """

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

        raw_content = content

        content = content.replace("```json", "")
        content = content.replace("```", "")
        content = content.strip()

        empty_targets = {
            name: dict(EMPTY_CATEGORY_DICT)
            for name in target_names
        }

        try:
            data = json.loads(content)

        except Exception as e:

            logger.warning(
                "extract_combined_profile_info: JSON parse basarisiz "
                "(%s). Ham model cevabi: %r",
                e,
                raw_content[:1000],
            )

            return {
                "self": dict(EMPTY_CATEGORY_DICT),
                "targets": empty_targets,
            }

        self_data = data.get("self", {})

        result_self = {
            "interests": self_data.get("interests", []),
            "projects": self_data.get("projects", []),
            "preferences": self_data.get("preferences", []),
            "facts": self_data.get("facts", []),
        }

        targets_data = data.get("targets", {})

        result_targets = {}

        for name in target_names:

            t = targets_data.get(name, {})

            result_targets[name] = {
                "interests": t.get("interests", []),
                "projects": t.get("projects", []),
                "preferences": t.get("preferences", []),
                "facts": t.get("facts", []),
            }

        total = (
            sum(len(v) for v in result_self.values())
            + sum(
                len(v)
                for t in result_targets.values()
                for v in t.values()
            )
        )

        if total == 0:
            logger.debug(
                "extract_combined_profile_info: gecerli JSON ama "
                "hicbir kategori dolu degil. Ham cevap: %r",
                raw_content[:500],
            )
        else:
            logger.info(
                "extract_combined_profile_info: %d bilgi cikarildi -> "
                "self=%s targets=%s",
                total,
                result_self,
                result_targets,
            )

        return {
            "self": result_self,
            "targets": result_targets,
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