from openai import (
    OpenAI,
    APIStatusError,
    RateLimitError,
    AuthenticationError,
    APIConnectionError,
)

from modules.config import OPENROUTER_API_KEYS


class AllKeysExhaustedError(Exception):
    """Tüm OpenRouter anahtarları tükendiğinde fırlatılır."""

    def __init__(self):
        super().__init__("Patates adamın parası bitti")


class OpenRouterManager:

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, api_keys: list[str]):
        if not api_keys:
            raise RuntimeError("OPENROUTER_API_KEYS boş.")

        self.api_keys = api_keys
        self.current_index = 0

    def get_client(self) -> OpenAI:
        return OpenAI(
            api_key=self.api_keys[self.current_index],
            base_url=self.BASE_URL,
        )

    def _should_rotate(self, error: Exception) -> bool:
        if isinstance(error, (RateLimitError, AuthenticationError, APIConnectionError)):
            return True

        if isinstance(error, APIStatusError):
            if error.status_code in (401, 402, 403, 429, 503):
                return True

        msg = str(error).lower()
        keywords = (
            "credit",
            "quota",
            "balance",
            "insufficient",
            "rate limit",
            "billing",
            "exceeded",
        )

        return any(keyword in msg for keyword in keywords)

    def chat_completions_create(self, **kwargs):
        last_error = None

        for i in range(len(self.api_keys)):
            idx = (self.current_index + i) % len(self.api_keys)

            try:
                client = OpenAI(
                    api_key=self.api_keys[idx],
                    base_url=self.BASE_URL,
                )
                result = client.chat.completions.create(**kwargs)
                self.current_index = idx
                return result

            except Exception as error:
                last_error = error

                if not self._should_rotate(error):
                    raise

        raise AllKeysExhaustedError() from last_error


manager = OpenRouterManager(OPENROUTER_API_KEYS)
