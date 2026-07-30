from .theme import Theme
from .layout import Layout, SidebarLayout
from .widgets import ProgressWidget, DividerWidget


class Sidebar:

    def __init__(
        self,
        draw,
        fonts,
    ):

        self.draw = draw
        self.fonts = fonts

        self.progress = ProgressWidget(draw)
        self.divider = DividerWidget(draw)

    # --------------------------------------------------

    def render(self):

        self._panel()

        self._header()

        self._scores()

    # --------------------------------------------------

    def _panel(self):

        self.draw.rounded_rectangle(
            (
                Layout.SIDEBAR.x,
                Layout.SIDEBAR.y,
                Layout.SIDEBAR.right,
                Layout.SIDEBAR.bottom,
            ),
            radius=18,
            fill=Theme.SURFACE,
            outline=Theme.BORDER,
            width=1,
        )

    # --------------------------------------------------

    def _header(self):

        x = Layout.SIDEBAR.x + SidebarLayout.PADDING

        self.draw.text(
            (
                x,
                SidebarLayout.TITLE_Y,
            ),
            "RAPOR",
            font=self.fonts["title"],
            fill=Theme.TEXT,
        )

        self.divider.draw_divider(
            x,
            SidebarLayout.DIVIDER_Y,
            Layout.SIDEBAR.width - SidebarLayout.PADDING * 2,
        )

    # --------------------------------------------------

    def _scores(self):

        x = Layout.SIDEBAR.x + SidebarLayout.PADDING

        y = SidebarLayout.DIVIDER_Y + 28

        scores = [
            ("YAZI OKUNABİLİRLİĞİ", 92, "Mükemmel"),
            ("KÜÇÜK BOYUTTA GÖRÜNÜRLÜK", 87, "Çok İyi"),
            ("DİKKAT ÇEKİCİLİĞİ", 94, "Harika"),
            ("RENK KONTRASTI", 89, "Çok İyi"),
            ("YÜZ GÖRÜNÜRLÜĞÜ", 96, "Mükemmel"),
            ("NESNE YOĞUNLUĞU", 74, "İyi"),
        ]

        for title, value, status in scores:

            y = self.progress.draw_progress(
                x=x,
                y=y,
                width=SidebarLayout.BAR_WIDTH,
                score=value,
                title=title,
                status=status,
                title_font=self.fonts["tiny"],
                value_font=self.fonts["tiny"],
            )

            y += 28