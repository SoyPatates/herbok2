from PIL import Image, ImageDraw

from .theme import Theme
from .layout import Thumbnail


class CardWidget:

    def __init__(self, draw):
        self.draw = draw

    def draw_card(self, rect):

        self.draw.rounded_rectangle(
            (rect.x, rect.y, rect.right, rect.bottom),
            radius=18,
            fill=Theme.SURFACE,
            outline=Theme.BORDER,
            width=1,
        )


class DividerWidget:

    def __init__(self, draw):
        self.draw = draw

    def draw_divider(self, x, y, width):

        self.draw.line(
            (x, y, x + width, y),
            fill=Theme.BORDER,
            width=1,
        )


class BadgeWidget:

    def __init__(self, draw):
        self.draw = draw

    def draw_badge(
        self,
        x,
        y,
        text,
        font,
        bg=Theme.SURFACE_LIGHT,
        color=Theme.TEXT,
    ):

        bbox = self.draw.textbbox((0, 0), text, font=font)

        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        w = tw + 24
        h = th + 14

        self.draw.rounded_rectangle(
            (x, y, x + w, y + h),
            radius=10,
            fill=bg,
        )

        self.draw.text(
            (x + 12, y + 7),
            text,
            fill=color,
            font=font,
        )

        return w, h


class ProgressWidget:

    def __init__(self, draw):
        self.draw = draw

    def draw_progress(
        self,
        x,
        y,
        width,
        score,
        title,
        status,
        title_font,
        value_font,
    ):

        self.draw.text(
            (x, y),
            title,
            fill=Theme.TEXT,
            font=title_font,
        )

        bar_y = y + 34

        self.draw.rounded_rectangle(
            (x, bar_y, x + width, bar_y + 12),
            radius=6,
            fill=Theme.BAR_BACKGROUND,
        )

        value = max(0, min(100, score))

        fill = int(width * value / 100)

        color = Theme.GREEN

        if value < 50:
            color = Theme.RED
        elif value < 75:
            color = Theme.ORANGE

        self.draw.rounded_rectangle(
            (x, bar_y, x + fill, bar_y + 12),
            radius=6,
            fill=color,
        )

        self.draw.text(
            (x, bar_y + 20),
            f"{status}  •  {value}/100",
            fill=Theme.TEXT_SECONDARY,
            font=value_font,
        )

        return bar_y + 56


class ThumbnailWidget:

    def __init__(self, canvas, draw):
        self.canvas = canvas
        self.draw = draw

    def draw_thumbnail(self, image, rect):

        mask = Image.new("L", (rect.width, rect.height), 0)

        ImageDraw.Draw(mask).rounded_rectangle(
            (0, 0, rect.width, rect.height),
            radius=Thumbnail.RADIUS,
            fill=255,
        )

        thumb = image.resize(
            (rect.width, rect.height),
            Image.Resampling.LANCZOS,
        ).convert("RGBA")

        self.canvas.paste(thumb, (rect.x, rect.y), mask)

        self.draw.rounded_rectangle(
            (rect.x, rect.y, rect.right, rect.bottom),
            radius=Thumbnail.RADIUS,
            outline=Theme.THUMB_BORDER,
            width=1,
        )


class DurationWidget:

    def __init__(self, draw):
        self.draw = draw

    def draw_duration(self, rect, duration, font):

        bbox = self.draw.textbbox((0, 0), duration, font=font)

        tw = bbox[2] - bbox[0]

        w = tw + 16
        h = 26

        x = rect.right - w - Thumbnail.DURATION_MARGIN
        y = rect.bottom - h - Thumbnail.DURATION_MARGIN

        self.draw.rounded_rectangle(
            (x, y, x + w, y + h),
            radius=6,
            fill=Theme.DURATION_BG,
        )

        self.draw.text(
            (x + 8, y + 4),
            duration,
            fill=Theme.DURATION_TEXT,
            font=font,
        )


class VerifiedBadgeWidget:

    def __init__(self, draw):
        self.draw = draw

    def draw_verified(self, x, y, size=16):

        self.draw.ellipse(
            (x, y, x + size, y + size),
            fill=Theme.VERIFIED,
        )

        self.draw.text(
            (x + size * 0.25, y - 1),
            "✓",
            fill="white",
        )