from .theme import Theme
from .layout import Layout, RowsLayout, Thumbnail, Title, Rect
from .widgets import (
    ThumbnailWidget,
    DurationWidget,
    VerifiedBadgeWidget,
    BadgeWidget,
)
from .utils import fit_text


class Rows:

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

        self.thumbnail_widget = ThumbnailWidget(canvas, draw)
        self.duration_widget = DurationWidget(draw)
        self.verified_widget = VerifiedBadgeWidget(draw)
        self.badge_widget = BadgeWidget(draw)

    # --------------------------------------------------

    def render(self):

        for index, spec in enumerate(RowsLayout.ROWS):

            rect = RowsLayout.row_rect(index)
            thumb_size = RowsLayout.thumb_size(index)

            self._draw_row_card(rect)
            self._draw_left(rect, spec)
            self._draw_right(rect, thumb_size)

    # --------------------------------------------------

    def _draw_row_card(self, rect):

        self.draw.rounded_rectangle(
            (rect.x, rect.y, rect.right, rect.bottom),
            radius=18,
            fill=Theme.SURFACE,
            outline=Theme.BORDER,
            width=1,
        )

    # --------------------------------------------------

    def _draw_icon(self, x, y, kind):

        size = RowsLayout.ICON_SIZE

        self.draw.rounded_rectangle(
            (x, y, x + size, y + size),
            radius=12,
            outline=Theme.YOUTUBE_RED,
            width=2,
        )

        cx = x + size / 2
        cy = y + size / 2

        if kind == "home":

            self.draw.polygon(
                [
                    (cx, cy - size * 0.22),
                    (cx - size * 0.22, cy + size * 0.02),
                    (cx + size * 0.22, cy + size * 0.02),
                ],
                fill=Theme.YOUTUBE_RED,
            )

            self.draw.rectangle(
                (cx - size * 0.16, cy, cx + size * 0.16, cy + size * 0.2),
                fill=Theme.YOUTUBE_RED,
            )

        elif kind == "monitor":

            self.draw.rounded_rectangle(
                (
                    cx - size * 0.22,
                    cy - size * 0.16,
                    cx + size * 0.22,
                    cy + size * 0.12,
                ),
                radius=3,
                outline=Theme.YOUTUBE_RED,
                width=2,
            )

            self.draw.line(
                (cx - size * 0.1, cy + size * 0.22, cx + size * 0.1, cy + size * 0.22),
                fill=Theme.YOUTUBE_RED,
                width=2,
            )

        else:  # play

            self.draw.polygon(
                [
                    (cx - size * 0.14, cy - size * 0.18),
                    (cx - size * 0.14, cy + size * 0.18),
                    (cx + size * 0.18, cy),
                ],
                fill=Theme.YOUTUBE_RED,
            )

    # --------------------------------------------------

    def _draw_left(self, rect, spec):

        x = rect.x + RowsLayout.PADDING
        y = rect.y + RowsLayout.PADDING

        self._draw_icon(x, y, spec["icon"])

        label_x = x + RowsLayout.ICON_SIZE + 18
        label_y = y + 4

        self.draw.text(
            (label_x, label_y),
            spec["label"],
            font=self.fonts["row_label"],
            fill=Theme.TEXT,
        )

        badge_y = label_y + 40

        self.badge_widget.draw_badge(
            label_x,
            badge_y,
            spec["size_label"],
            self.fonts["tiny"],
            bg=(58, 30, 30),
            color=(255, 140, 130),
        )

        desc_y = y + RowsLayout.ICON_SIZE + 22

        desc_font = self.fonts["small"]

        wrapped = fit_text(
            self.draw,
            spec["description"],
            desc_font,
            RowsLayout.LEFT_WIDTH,
            max_lines=2,
        )

        self.draw.multiline_text(
            (x, desc_y),
            wrapped,
            font=desc_font,
            fill=Theme.TEXT_SECONDARY,
            spacing=8,
        )

    # --------------------------------------------------

    def _draw_right(self, rect, thumb_size):

        thumb_w, thumb_h = thumb_size

        thumb_x = rect.x + RowsLayout.LEFT_WIDTH + RowsLayout.INFO_GAP

        # Thumbnail'i satirin dikey ortasina hizala (kucuk boyutlarda
        # bosluk asagida degil, ust-alt dengeli kalsin).
        thumb_y = rect.y + (rect.height - thumb_h) // 2

        thumb_rect = Rect(
            thumb_x,
            thumb_y,
            thumb_w,
            thumb_h,
        )

        self.thumbnail_widget.draw_thumbnail(self.thumbnail, thumb_rect)

        self.duration_widget.draw_duration(
            thumb_rect,
            self.duration,
            self.fonts["tiny"],
        )

        info_x = thumb_rect.right + 28
        info_width = rect.right - RowsLayout.PADDING - info_x

        title_font = self.fonts["card_title"]

        wrapped = fit_text(
            self.draw,
            self.title,
            title_font,
            info_width,
            max_lines=2,
        )

        # Baslik her zaman satirin ustune hizali kalsin, thumbnail
        # kucuk olsa bile (dikey ortada) metin bloklari sabit dursun.
        title_y = rect.y + RowsLayout.PADDING

        self.draw.multiline_text(
            (info_x, title_y),
            wrapped,
            font=title_font,
            fill=Theme.TEXT,
            spacing=Title.LINE_SPACING,
        )

        line_bbox = self.draw.textbbox((0, 0), "Ag", font=title_font)
        line_h = line_bbox[3] - line_bbox[1]
        line_count = wrapped.count("\n") + 1

        channel_y = title_y + line_count * (line_h + Title.LINE_SPACING) + 16

        channel_font = self.fonts["small"]

        self.draw.text(
            (info_x, channel_y),
            self.channel,
            font=channel_font,
            fill=Theme.TEXT_SECONDARY,
        )

        bbox = self.draw.textbbox((info_x, channel_y), self.channel, font=channel_font)

        self.verified_widget.draw_verified(
            bbox[2] + 8,
            channel_y + 2,
            size=16,
        )

        meta_y = channel_y + line_h + 14

        self.draw.text(
            (info_x, meta_y),
            "127 B görüntülenme • 2 gün önce",
            font=self.fonts["small"],
            fill=Theme.TEXT_MUTED,
        )

        self._draw_menu_dots(rect)

    # --------------------------------------------------

    def _draw_menu_dots(self, rect):

        x = rect.right - RowsLayout.PADDING - 4
        y = rect.y + RowsLayout.PADDING + 8

        for i in range(3):

            self.draw.ellipse(
                (x, y + i * 8, x + 4, y + 4 + i * 8),
                fill=Theme.TEXT_MUTED,
            )