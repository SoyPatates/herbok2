from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:

    BACKGROUND = (15, 15, 15)

    SURFACE = (28, 28, 28)
    SURFACE_LIGHT = (38, 38, 38)
    SURFACE_HOVER = (45, 45, 45)

    BORDER = (55, 55, 55)
    BORDER_LIGHT = (78, 78, 78)

    TEXT = (245, 245, 245)
    TEXT_SECONDARY = (170, 170, 170)
    TEXT_MUTED = (120, 120, 120)

    ACCENT = (62, 166, 255)
    GREEN = (61, 188, 94)
    ORANGE = (255, 181, 54)
    RED = (234, 67, 53)

    YOUTUBE_RED = (255, 0, 0)
    VERIFIED = (62, 166, 255)

    DURATION_BG = (0, 0, 0)
    DURATION_TEXT = (255, 255, 255)

    SCORE_GOOD = GREEN
    SCORE_MEDIUM = ORANGE
    SCORE_BAD = RED

    SHADOW = (0, 0, 0)
    SHADOW_ALPHA = 70

    THUMB_BORDER = (70, 70, 70)
    THUMB_RADIUS = 16

    AVATAR_BORDER = (80, 80, 80)
    AVATAR_SIZE = 48

    CARD_RADIUS = 18
    CARD_PADDING = 24

    BAR_BACKGROUND = (55, 55, 55)
    BAR_RADIUS = 8

    # -------------------------------------------------
    # Placeholder card colors (diger videolar icin)
    # -------------------------------------------------

    PLACEHOLDER_COLORS = [
        (40, 46, 58),
        (46, 40, 58),
        (40, 58, 50),
        (58, 46, 40),
        (40, 52, 58),
    ]