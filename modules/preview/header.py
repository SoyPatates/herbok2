from .theme import Theme
from .layout import Layout, HeaderLayout
from .widgets import BadgeWidget


class Header:

    def __init__(
        self,
        draw,
        fonts,
    ):

        self.draw = draw
        self.fonts = fonts

        self.badge = BadgeWidget(draw)

    # --------------------------------------------------

    def render(self):

        self._accent()

        self._brand()

        self._title()

        self._subtitle()

        self._badge()

        self._divider()

    # --------------------------------------------------

    def _accent(self):

        x = Layout.HEADER.x

        self.draw.rounded_rectangle(
            (
                x,
                Layout.HEADER.y + 8,
                x + 8,
                Layout.HEADER.bottom - 8,
            ),
            radius=4,
            fill=Theme.GREEN,
        )

    # --------------------------------------------------

    def _brand(self):

        self.draw.text(
            (
                HeaderLayout.TITLE_X,
                HeaderLayout.TITLE_Y,
            ),
            "SoyTasarım",
            font=self.fonts["title"],
            fill=Theme.TEXT,
        )

    # --------------------------------------------------

    def _subtitle(self):

        self.draw.text(
            (
                HeaderLayout.SUBTITLE_X,
                HeaderLayout.SUBTITLE_Y,
            ),
            "Video Kapak Ön İzleme",
            font=self.fonts["small"],
            fill=Theme.TEXT_SECONDARY,
        )

    # --------------------------------------------------

    def _title(self):

        text = "YouTube"

        bbox = self.draw.textbbox(
            (0, 0),
            "SoyTasarım",
            font=self.fonts["title"],
        )

        x = bbox[2] + 34
        y = HeaderLayout.TITLE_Y

        self.draw.text(
            (
                x,
                y,
            ),
            text,
            font=self.fonts["title"],
            fill=Theme.YOUTUBE_RED,
        )

    # --------------------------------------------------

    def _badge(self):

        text = "PNG • 1920×1080"

        bbox = self.draw.textbbox(
            (0, 0),
            text,
            font=self.fonts["tiny"],
        )

        width = bbox[2] - bbox[0]

        x = (
            Layout.HEADER.right
            - width
            - 44
        )

        y = Layout.HEADER.y + 18

        self.badge.draw_badge(
            x,
            y,
            text,
            self.fonts["tiny"],
            bg=Theme.SURFACE_LIGHT,
            color=Theme.TEXT,
        )

    # --------------------------------------------------

    def _divider(self):

        y = Layout.HEADER.bottom + 12

        self.draw.line(
            (
                Layout.CONTENT.x,
                y,
                Layout.SIDEBAR.right,
                y,
            ),
            fill=Theme.BORDER,
            width=1,
        )