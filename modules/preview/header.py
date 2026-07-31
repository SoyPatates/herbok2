from .theme import Theme
from .layout import Layout, HeaderLayout


class Header:

    def __init__(self, draw, fonts):
        self.draw = draw
        self.fonts = fonts

    def render(self):

        self._logo()
        self._brand()
        self._divider_dot()
        self._headline()
        self._subtitle()
        self._bottom_divider()

    # --------------------------------------------------

    def _logo(self):

        size = HeaderLayout.LOGO_SIZE

        self.draw.rounded_rectangle(
            (
                HeaderLayout.LOGO_X,
                HeaderLayout.LOGO_Y,
                HeaderLayout.LOGO_X + size,
                HeaderLayout.LOGO_Y + size,
            ),
            radius=14,
            fill=Theme.YOUTUBE_RED,
        )

        self.draw.polygon(
            [
                (HeaderLayout.LOGO_X + size * 0.38, HeaderLayout.LOGO_Y + size * 0.28),
                (HeaderLayout.LOGO_X + size * 0.38, HeaderLayout.LOGO_Y + size * 0.72),
                (HeaderLayout.LOGO_X + size * 0.74, HeaderLayout.LOGO_Y + size * 0.5),
            ],
            fill="white",
        )

    # --------------------------------------------------

    def _brand(self):

        self.draw.text(
            (HeaderLayout.TITLE_X, HeaderLayout.TITLE_Y),
            "Soy",
            font=self.fonts["brand"],
            fill=Theme.TEXT,
        )

        bbox = self.draw.textbbox(
            (HeaderLayout.TITLE_X, HeaderLayout.TITLE_Y),
            "Soy",
            font=self.fonts["brand"],
        )

        self.draw.text(
            (bbox[2], HeaderLayout.TITLE_Y),
            "Tasarım",
            font=self.fonts["brand"],
            fill=Theme.YOUTUBE_RED,
        )

    # --------------------------------------------------

    def _divider_dot(self):

        x = HeaderLayout.DIVIDER_X

        self.draw.line(
            (x, Layout.HEADER.y + 4, x, Layout.HEADER.y + HeaderLayout.LOGO_SIZE - 4),
            fill=Theme.BORDER_LIGHT,
            width=2,
        )

    # --------------------------------------------------

    def _headline(self):

        self.draw.text(
            (HeaderLayout.HEADLINE_X, HeaderLayout.HEADLINE_Y),
            "YouTube Önizleme Raporu",
            font=self.fonts["headline"],
            fill=Theme.TEXT,
        )

    # --------------------------------------------------

    def _subtitle(self):

        self.draw.text(
            (HeaderLayout.SUBTITLE_X, HeaderLayout.SUBTITLE_Y),
            "Küçük boyutlarda videonuzun nasıl göründüğünü görün",
            font=self.fonts["small"],
            fill=Theme.TEXT_SECONDARY,
        )

    # --------------------------------------------------

    def _bottom_divider(self):

        y = Layout.HEADER.bottom + 12

        self.draw.line(
            (Layout.CONTENT.x, y, Layout.SIDEBAR.right, y),
            fill=Theme.BORDER,
            width=1,
        )