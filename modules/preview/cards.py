from PIL import ImageDraw

from .theme import Theme
from .layout import (
    HomePage,
    SmallCards,
    Thumbnail,
    Avatar,
    Title,
    Channel,
    Meta,
)

from .widgets import (
    ThumbnailWidget,
    DurationWidget,
    VerifiedBadgeWidget,
)

from .utils import fit_text


class Cards:

    def __init__(
        self,
        canvas,
        draw,
        fonts,
        thumbnail,
        avatar,
        title,
        channel,
        duration,
    ):

        self.canvas = canvas
        self.draw = draw

        self.fonts = fonts

        self.thumbnail = thumbnail
        self.avatar = avatar

        self.title = title
        self.channel = channel
        self.duration = duration

        self.thumbnail_widget = ThumbnailWidget(
            canvas,
            draw,
        )

        self.duration_widget = DurationWidget(
            draw,
        )

        self.verified_widget = VerifiedBadgeWidget(
            draw,
        )

    # --------------------------------------------------

    def render(self):

        self.draw_homepage()

        self.draw_small_homepage()

        self.draw_suggested()

    # --------------------------------------------------

    def draw_homepage(self):

        self.thumbnail_widget.draw_thumbnail(
            self.thumbnail,
            HomePage.THUMBNAIL,
        )

        self.duration_widget.draw_duration(
            HomePage.THUMBNAIL,
            self.duration,
            self.fonts["small"],
        )

        self.draw_avatar(
            HomePage.AVATAR_X,
            HomePage.AVATAR_Y,
            Avatar.SIZE,
        )

        self.draw_title(
            self.title,
            HomePage.TITLE_X,
            HomePage.TITLE_Y,
            Title.MAX_WIDTH,
        )

        self.draw_channel(
            HomePage.CHANNEL_X,
            HomePage.CHANNEL_Y,
        )

        self.draw_meta(
            HomePage.META_X,
            HomePage.META_Y,
        )

    # --------------------------------------------------

    def draw_small_homepage(self):

        self.draw_small_card(
            SmallCards.LEFT,
            "Ana Sayfa",
        )

    # --------------------------------------------------

    def draw_suggested(self):

        self.draw_small_card(
            SmallCards.RIGHT,
            "Önerilen Videolar",
        )
    # --------------------------------------------------

    def draw_small_card(
        self,
        rect,
        label,
    ):

        thumb_h = SmallCards.THUMB_HEIGHT

        thumb_rect = type(rect)(
            rect.x,
            rect.y,
            rect.width,
            thumb_h,
        )

        self.thumbnail_widget.draw_thumbnail(
            self.thumbnail,
            thumb_rect,
        )

        self.duration_widget.draw_duration(
            thumb_rect,
            self.duration,
            self.fonts["tiny"],
        )

        avatar_x = rect.x
        avatar_y = thumb_rect.bottom + 14

        self.draw_avatar(
            avatar_x,
            avatar_y,
            SmallCards.AVATAR_SIZE,
        )

        title_x = avatar_x + SmallCards.AVATAR_SIZE + 14
        title_y = avatar_y

        self.draw_title(
            self.title,
            title_x,
            title_y,
            rect.width - SmallCards.AVATAR_SIZE - 20,
            max_lines=2,
            font=self.fonts["small"],
        )

        channel_y = (
            title_y
            + SmallCards.TITLE_OFFSET
            + 30
        )

        self.draw_channel(
            title_x,
            channel_y,
            font=self.fonts["tiny"],
        )

        meta_y = (
            title_y
            + SmallCards.META_OFFSET
        )

        self.draw_meta(
            title_x,
            meta_y,
            font=self.fonts["tiny"],
        )

    # --------------------------------------------------

    def draw_avatar(
        self,
        x,
        y,
        size,
    ):

        avatar = self.avatar.resize(
            (
                size,
                size,
            )
        ).convert("RGBA")

        self.canvas.paste(
            avatar,
            (
                x,
                y,
            ),
            avatar,
        )

    # --------------------------------------------------

    def draw_title(
        self,
        text,
        x,
        y,
        width,
        max_lines=2,
        font=None,
    ):

        if font is None:
            font = self.fonts["title"]

        wrapped = fit_text(
            self.draw,
            text,
            font,
            width,
            max_lines=max_lines,
        )

        self.draw.multiline_text(
            (
                x,
                y,
            ),
            wrapped,
            font=font,
            fill=Theme.TEXT,
            spacing=Title.LINE_SPACING,
        )

    # --------------------------------------------------

    def draw_channel(
        self,
        x,
        y,
        font=None,
    ):

        if font is None:
            font = self.fonts["small"]

        self.draw.text(
            (
                x,
                y,
            ),
            self.channel,
            font=font,
            fill=Theme.TEXT,
        )

        bbox = self.draw.textbbox(
            (x, y),
            self.channel,
            font=font,
        )

        badge_x = (
            bbox[2]
            + Channel.VERIFIED_MARGIN
        )

        badge_y = y + 2

        self.verified_widget.draw_verified(
            badge_x,
            badge_y,
        )
    # --------------------------------------------------

    def draw_meta(
        self,
        x,
        y,
        font=None,
    ):

        if font is None:
            font = self.fonts["tiny"]

        meta = "182 B görüntüleme • 2 gün önce"

        self.draw.text(
            (
                x,
                y,
            ),
            meta,
            font=font,
            fill=Theme.TEXT_SECONDARY,
        )

    # --------------------------------------------------

    def draw_duration(
        self,
        rect,
    ):

        self.duration_widget.draw_duration(
            rect,
            self.duration,
            self.fonts["tiny"],
        )

    # --------------------------------------------------

    def draw_verified(
        self,
        x,
        y,
    ):

        self.verified_widget.draw_verified(
            x,
            y,
        )

    # --------------------------------------------------

    def draw_thumbnail(
        self,
        rect,
    ):

        self.thumbnail_widget.draw_thumbnail(
            self.thumbnail,
            rect,
        )

        self.duration_widget.draw_duration(
            rect,
            self.duration,
            self.fonts["tiny"],
        )

    # --------------------------------------------------

    def measure_text_height(
        self,
        text,
        font,
        width,
        max_lines=2,
    ):

        wrapped = fit_text(
            self.draw,
            text,
            font,
            width,
            max_lines=max_lines,
        )

        bbox = self.draw.multiline_textbbox(
            (0, 0),
            wrapped,
            font=font,
            spacing=Title.LINE_SPACING,
        )

        return bbox[3] - bbox[1]

    # --------------------------------------------------

    def text_width(
        self,
        text,
        font,
    ):

        bbox = self.draw.textbbox(
            (0, 0),
            text,
            font=font,
        )

        return bbox[2] - bbox[0]

    # --------------------------------------------------

    def text_height(
        self,
        text,
        font,
    ):

        bbox = self.draw.textbbox(
            (0, 0),
            text,
            font=font,
        )

        return bbox[3] - bbox[1]