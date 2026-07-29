from enum import Enum

from modules.prompts import (
    FIRST_REVIEW_PROMPT,
    SUGGESTIONS_PROMPT,
    CTR_PROMPT,
    TITLE_PROMPT,
    COLOR_PROMPT,
    FONT_PROMPT,
    EFFECTS_PROMPT,
    COMPARE_PROMPT,
)


class ThumbnailMode(Enum):

    FIRST_REVIEW = 1
    SUGGESTIONS = 2
    CTR = 3
    TITLE = 4
    COLOR = 5
    FONT = 6
    EFFECTS = 7
    COMPARE = 8


class ThumbnailManager:

    def detect_mode(self, message):

        text = message.content.lower()

        if "karşılaştır" in text or "compare" in text:
            return ThumbnailMode.COMPARE

        if "ctr" in text:
            return ThumbnailMode.CTR

        if "başlık" in text or "title" in text:
            return ThumbnailMode.TITLE

        if "renk" in text:
            return ThumbnailMode.COLOR

        if "font" in text or "yazı" in text:
            return ThumbnailMode.FONT

        if "efekt" in text:
            return ThumbnailMode.EFFECTS

        if (
            "öner" in text
            or "geliştir" in text
            or "iyileştir" in text
        ):
            return ThumbnailMode.SUGGESTIONS

        return ThumbnailMode.FIRST_REVIEW

    def get_prompt(self, mode):

        prompts = {
            ThumbnailMode.FIRST_REVIEW: FIRST_REVIEW_PROMPT,
            ThumbnailMode.SUGGESTIONS: SUGGESTIONS_PROMPT,
            ThumbnailMode.CTR: CTR_PROMPT,
            ThumbnailMode.TITLE: TITLE_PROMPT,
            ThumbnailMode.COLOR: COLOR_PROMPT,
            ThumbnailMode.FONT: FONT_PROMPT,
            ThumbnailMode.EFFECTS: EFFECTS_PROMPT,
            ThumbnailMode.COMPARE: COMPARE_PROMPT,
        }

        return prompts[mode]