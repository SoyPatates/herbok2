from .theme import Theme
from .layout import Rect, Title
from .widgets import ThumbnailWidget, DurationWidget, VerifiedBadgeWidget
from .utils import fit_text


class GridCardRenderer:

    def __init__(self, image, draw, fonts):

        self.image = image
        self.draw = draw
        self.fonts = fonts

        self.thumbnail_widget = ThumbnailWidget(image, draw)
        self.duration_widget = DurationWidget(draw)
        self.verified_widget = VerifiedBadgeWidget(draw)

    # --------------------------------------------------
    # GERCEK VIDEO KARTI (kullanicinin kendi videosu)
    # --------------------------------------------------

    def draw_real_card(
        self,
        x,
        y,
        spec,
        thumbnail_image,
        avatar_image,
        duration,
        title,
        channel,
        meta,
        title_font_key,
        meta_font_key,
        verified=True,
    ):

        card = spec.card

        thumb_rect = Rect(x, y, card.width, card.thumb_height)

        self.thumbnail_widget.draw_thumbnail(thumbnail_image, thumb_rect)

        self.duration_widget.draw_duration(
            thumb_rect,
            duration,
            self.fonts[meta_font_key],
        )

        info_y = y + card.thumb_height + card.gap_thumb_info

        avatar = avatar_image.resize(
            (card.avatar_size, card.avatar_size)
        ).convert("RGBA")

        self.image.paste(avatar, (x, info_y), avatar)

        title_x = x + card.avatar_size + 14
        title_width = card.width - card.avatar_size - 14

        title_font = self.fonts[title_font_key]

        wrapped = fit_text(
            self.draw,
            title,
            title_font,
            title_width,
            max_lines=2,
        )

        self.draw.multiline_text(
            (title_x, info_y - 4),
            wrapped,
            font=title_font,
            fill=Theme.TEXT,
            spacing=Title.LINE_SPACING,
        )

        line_bbox = self.draw.textbbox((0, 0), "Ag", font=title_font)
        line_h = line_bbox[3] - line_bbox[1]
        line_count = wrapped.count("\n") + 1

        channel_y = (
            info_y
            - 4
            + line_count * (line_h + Title.LINE_SPACING)
            + 4
        )

        meta_font = self.fonts[meta_font_key]

        self.draw.text(
            (title_x, channel_y),
            channel,
            font=meta_font,
            fill=Theme.TEXT_SECONDARY,
        )

        if verified:

            bbox = self.draw.textbbox(
                (title_x, channel_y),
                channel,
                font=meta_font,
            )

            badge_size = 14

            self.verified_widget.draw_verified(
                bbox[2] + 6,
                channel_y + 1,
                size=badge_size,
            )

        meta_y = channel_y + line_h + 6

        self.draw.text(
            (title_x, meta_y),
            meta,
            font=meta_font,
            fill=Theme.TEXT_MUTED,
        )

    # --------------------------------------------------
    # PLACEHOLDER KART (diger/sahte videolar)
    # --------------------------------------------------

    def draw_placeholder_card(
        self,
        x,
        y,
        spec,
        color_index,
        title_font_key,
        meta_font_key,
    ):

        card = spec.card

        color = Theme.PLACEHOLDER_COLORS[
            color_index % len(Theme.PLACEHOLDER_COLORS)
        ]

        thumb_rect = Rect(x, y, card.width, card.thumb_height)

        self.draw.rounded_rectangle(
            (thumb_rect.x, thumb_rect.y, thumb_rect.right, thumb_rect.bottom),
            radius=16,
            fill=color,
            outline=Theme.THUMB_BORDER,
            width=1,
        )

        label = "Diger Video"
        label_font = self.fonts[meta_font_key]

        bbox = self.draw.textbbox((0, 0), label, font=label_font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        self.draw.text(
            (
                thumb_rect.x + (card.width - tw) / 2,
                thumb_rect.y + (card.thumb_height - th) / 2,
            ),
            label,
            font=label_font,
            fill=Theme.TEXT_MUTED,
        )

        info_y = y + card.thumb_height + card.gap_thumb_info

        self.draw.ellipse(
            (x, info_y, x + card.avatar_size, info_y + card.avatar_size),
            fill=Theme.SURFACE_LIGHT,
            outline=Theme.BORDER,
            width=1,
        )

        title_x = x + card.avatar_size + 14
        title_width = card.width - card.avatar_size - 14

        title_font = self.fonts[title_font_key]

        placeholder_title = "Video Basligi Ornegi"

        wrapped = fit_text(
            self.draw,
            placeholder_title,
            title_font,
            title_width,
            max_lines=2,
        )

        self.draw.multiline_text(
            (title_x, info_y - 4),
            wrapped,
            font=title_font,
            fill=Theme.TEXT_SECONDARY,
            spacing=Title.LINE_SPACING,
        )

        line_bbox = self.draw.textbbox((0, 0), "Ag", font=title_font)
        line_h = line_bbox[3] - line_bbox[1]
        line_count = wrapped.count("\n") + 1

        meta_y = (
            info_y
            - 4
            + line_count * (line_h + Title.LINE_SPACING)
            + 4
        )

        meta_font = self.fonts[meta_font_key]

        self.draw.text(
            (title_x, meta_y),
            "Kanal Adi",
            font=meta_font,
            fill=Theme.TEXT_MUTED,
        )