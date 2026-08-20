import time
import re
import unicodedata

from openai import (
    OpenAI,
    APIStatusError,
    RateLimitError,
    AuthenticationError,
    APIConnectionError,
)

from modules.config import OPENROUTER_API_KEYS
from modules.logger import logger


class AllKeysExhaustedError(Exception):
    """Tüm OpenRouter anahtarları tükendiğinde fırlatılır."""

    def __init__(self):
        super().__init__("Patates adamın parası bitti")


class EmptyModelResponseError(Exception):
    """
    Model API'den hata fırlatmadan ama icerik olmadan (choices bos/None)
    bir cevap dondurdugunde firlatilir. Genelde OpenRouter'daki ucretsiz
    modellerin o an kapasite/kesinti yasadigi durumlarda olur. Bu bir
    key sorunu degildir -- ama gecici oldugu icin kisa bir bekleme
    sonrasi tekrar denemek genelde cozer (bkz. _create_with_retry).
    """

    def __init__(self, model: str = ""):
        super().__init__(
            f"Model ({model or 'bilinmeyen'}) boş/geçersiz bir cevap "
            "döndürdü, muhtemelen o an kapasite sorunu yaşıyor. "
            "Tekrar denemen gerekebilir."
        )


class CorruptedModelResponseError(Exception):
    """
    Model, hata fırlatmadan ve bos da olmayan ama ICERIGI anlamsiz/
    bozuk (yabanci alfabelerden rastgele karakterler, kelime icine
    sikismis rastgele harf dizileri gibi) bir cevap dondurdugunde
    firlatilir. Bu da genelde ucretsiz modelin o an saglikli
    calismadigi bir ana isaret eder -- key sorunu degildir.
    """

    def __init__(self, model: str = ""):
        super().__init__(
            f"Model ({model or 'bilinmeyen'}) bozuk/anlamsız karakterler "
            "içeren bir cevap döndürdü, muhtemelen o an sağlıksız "
            "çalışıyor. Tekrar denemen gerekebilir."
        )


class OpenRouterManager:

    BASE_URL = "https://openrouter.ai/api/v1"

    # Bos/bozuk cevap icin, AYNI anahtarla kac kez ve kac saniye
    # arayla tekrar denenecegi.
    EMPTY_RESPONSE_RETRIES = 2
    EMPTY_RESPONSE_DELAY = 1.5

    # Bir cevabin "bozuk" sayilmasi icin gereken supheli (beklenmeyen
    # alfabeden) karakter sayisi esigi. Not: bazi alfabelerde (orn.
    # Devanagari) sesli isaretleri Python'da "harf" sayilmiyor, bu
    # yuzden esik dusuk tutuluyor.
    CORRUPTION_THRESHOLD = 2

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

        if isinstance(error, (EmptyModelResponseError, CorruptedModelResponseError)):
            # Ayni key ile birkac kez denendi (_create_with_retry
            # icinde), hala sorunluysa artik bir sonraki key'e
            # gecmeyi deneyebiliriz -- key farkli bir OpenRouter
            # saglayicisina yonlendirebilir, tamamen imkansiz degil.
            return True

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

    def _looks_corrupted(self, text: str) -> bool:
        """
        Cevabin icinde, Turkce/Discord sohbeti icin beklenmeyen
        alfabelerden (Devanagari, Kiril, CJK, Tay vb.) gelen karakterler
        varsa, bu genelde modelin o an bozuk/rastgele token urettigini
        gosterir (orn. "vaşیlan", "punyaie" gibi anlamsiz karisimlar).

        Latin harfler (Turkce dahil), rakamlar, yaygin noktalama ve
        emoji serbesttir. Esik degerinden fazla "yabanci" harf varsa
        cevap bozuk sayilir.
        """

        suspicious = 0

        for ch in text:

            if ch.isspace() or ch.isdigit():
                continue

            if not ch.isalpha():
                continue

            code_point = ord(ch)

            # Yaygin emoji araliklarini gormezden gel.
            if 0x1F000 <= code_point <= 0x1FFFF or 0x2600 <= code_point <= 0x27BF:
                continue

            try:
                name = unicodedata.name(ch)
            except ValueError:
                continue

            if "LATIN" in name:
                continue

            suspicious += 1

            if suspicious >= self.CORRUPTION_THRESHOLD:
                return True

        if self._has_special_token_leak(text):
            return True

        if self._has_degenerate_repetition(text):
            return True

        return False

    # Model tokenizer'ina ait, kullaniciya ASLA gorunmemesi gereken
    # ozel/kontrol tokenlari. Bunlardan biri cevapta gecerse, model
    # o an bozuk/hatali calisiyor demektir (orn. "<pad>" binlerce kez
    # tekrarlanan bir cevap).
    SPECIAL_TOKEN_MARKERS = (
        "<pad>", "[pad]", "<|pad|>",
        "<|endoftext|>",
        "<|im_start|>", "<|im_end|>",
        "<|assistant|>", "<|user|>", "<|system|>",
        "<unk>", "[unk]",
    )

    def _has_special_token_leak(self, text: str) -> bool:

        lowered = text.lower()

        return any(
            marker in lowered
            for marker in self.SPECIAL_TOKEN_MARKERS
        )

    def _has_degenerate_repetition(self, text: str) -> bool:
        """
        Model bazen (ozellikle kucuk/ucretsiz modellerde) bir "dongu"ye
        girip ayni kisa kalibi (bir kelime, bir token, bir noktalama
        grubu) onlarca/yuzlerce kez ust uste tekrarlayan bozuk bir
        cevap uretebilir. Bu, 2-40 karakterlik bir kalibin en az 8 kez
        ust uste tekrarlanip tekrarlanmadigina bakarak yakalanir.
        """

        pattern = re.compile(r"(.{2,40}?)\1{7,}", re.DOTALL)

        return bool(pattern.search(text))

    def _create_with_retry(self, client, kwargs, model_name):
        """
        client.chat.completions.create(**kwargs) cagirir. Eger model
        bos/gecersiz (choices yok) ya da BOZUK/anlamsiz karakterler
        iceren bir cevap donerse, AYNI anahtarla kisa bir bekleme
        sonrasi birkac kez daha dener -- bu genelde ucretsiz modelin
        gecici bir kapasite/saglik sorunu yasadigi anlamina gelir,
        cogu zaman 1-2 saniye icinde duzelir.

        Tum denemeler de basarisizsa ilgili hatayi firlatir.
        """

        last_error = None

        for attempt in range(1, self.EMPTY_RESPONSE_RETRIES + 2):

            result = client.chat.completions.create(**kwargs)

            if not getattr(result, "choices", None):

                logger.warning(
                    "chat_completions_create: model=%s bos/None choices "
                    "dondurdu (deneme %d/%d, ayni key).",
                    model_name,
                    attempt,
                    self.EMPTY_RESPONSE_RETRIES + 1,
                )

                last_error = EmptyModelResponseError(model_name)

                if attempt <= self.EMPTY_RESPONSE_RETRIES:
                    time.sleep(self.EMPTY_RESPONSE_DELAY)

                continue

            content = result.choices[0].message.content or ""

            if self._looks_corrupted(content):

                logger.warning(
                    "chat_completions_create: model=%s bozuk/anlamsiz "
                    "karakterler iceren bir cevap dondurdu (deneme "
                    "%d/%d, ayni key). Ilk 200 karakter: %r",
                    model_name,
                    attempt,
                    self.EMPTY_RESPONSE_RETRIES + 1,
                    content[:200],
                )

                last_error = CorruptedModelResponseError(model_name)

                if attempt <= self.EMPTY_RESPONSE_RETRIES:
                    time.sleep(self.EMPTY_RESPONSE_DELAY)

                continue

            return result

        raise last_error

    def chat_completions_create(self, **kwargs):
        last_error = None
        model_name = kwargs.get("model", "")

        for i in range(len(self.api_keys)):
            idx = (self.current_index + i) % len(self.api_keys)

            try:
                client = OpenAI(
                    api_key=self.api_keys[idx],
                    base_url=self.BASE_URL,
                )

                result = self._create_with_retry(client, kwargs, model_name)

                self.current_index = idx
                return result

            except Exception as error:
                last_error = error

                logger.warning(
                    "chat_completions_create: key #%d basarisiz "
                    "(model=%s). Hata turu: %s. Mesaj: %s",
                    idx,
                    model_name,
                    type(error).__name__,
                    str(error)[:500],
                )

                if not self._should_rotate(error):
                    logger.error(
                        "chat_completions_create: hata rotasyon "
                        "gerektirmiyor (key ile alakasiz), direkt "
                        "firlatiliyor. Hata turu: %s",
                        type(error).__name__,
                    )
                    raise

        logger.error(
            "chat_completions_create: TUM anahtarlar (%d adet) "
            "denendi, hepsi basarisiz oldu (model=%s). Son hata: "
            "%s: %s",
            len(self.api_keys),
            model_name,
            type(last_error).__name__ if last_error else "bilinmiyor",
            str(last_error)[:500] if last_error else "",
        )

        raise AllKeysExhaustedError() from last_error


manager = OpenRouterManager(OPENROUTER_API_KEYS)