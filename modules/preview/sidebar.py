import random
from datetime import datetime

from .theme import Theme
from .layout import Layout, SidebarLayout
from .widgets import DividerWidget


class Sidebar:

    def __init__(self, draw, fonts, seed=None):

        self.draw = draw
        self.fonts = fonts

        # Ayni tasarim (ayni gorsel + baslik) her zaman AYNI analiz
        # sonucunu versin -- farkli tasarimlar farkli analiz alsin.
        # Bunun icin global 'random' yerine bu seed'e bagli ayri bir
        # rastgele uretici kullaniyoruz.
        self.rng = random.Random(seed)

        self.divider = DividerWidget(draw)

    # --------------------------------------------------

    def render(self):

        self._panel()
        self._mini_header()

        y = SidebarLayout.SECTION_START_Y

        y = self._section_image_info(y)
        y += SidebarLayout.SECTION_GAP

        y = self._section_scores(y)
        y += SidebarLayout.SECTION_GAP

        y = self._section_generated(y)

        self._tagline()

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

    def _mini_header(self):

        size = SidebarLayout.LOGO_SIZE

        self.draw.rounded_rectangle(
            (
                SidebarLayout.LOGO_X,
                SidebarLayout.LOGO_Y,
                SidebarLayout.LOGO_X + size,
                SidebarLayout.LOGO_Y + size,
            ),
            radius=11,
            fill=Theme.YOUTUBE_RED,
        )

        self.draw.polygon(
            [
                (SidebarLayout.LOGO_X + size * 0.38, SidebarLayout.LOGO_Y + size * 0.28),
                (SidebarLayout.LOGO_X + size * 0.38, SidebarLayout.LOGO_Y + size * 0.72),
                (SidebarLayout.LOGO_X + size * 0.74, SidebarLayout.LOGO_Y + size * 0.5),
            ],
            fill="white",
        )

        self.draw.text(
            (SidebarLayout.TITLE_X, SidebarLayout.TITLE_Y),
            "Soy",
            font=self.fonts["sidebar_brand"],
            fill=Theme.TEXT,
        )

        bbox = self.draw.textbbox(
            (SidebarLayout.TITLE_X, SidebarLayout.TITLE_Y),
            "Soy",
            font=self.fonts["sidebar_brand"],
        )

        self.draw.text(
            (bbox[2], SidebarLayout.TITLE_Y),
            "Tasarım",
            font=self.fonts["sidebar_brand"],
            fill=Theme.YOUTUBE_RED,
        )

        self.draw.text(
            (SidebarLayout.SUBTITLE_X, SidebarLayout.SUBTITLE_Y),
            "YouTube Önizleme Raporu",
            font=self.fonts["tiny"],
            fill=Theme.TEXT_SECONDARY,
        )

    # --------------------------------------------------

    def _section_title(self, x, y, text):

        self.draw.text(
            (x, y),
            text,
            font=self.fonts["section_title"],
            fill=Theme.YOUTUBE_RED,
        )

        return y + 34

    # --------------------------------------------------

    def _section_image_info(self, y):

        x = Layout.SIDEBAR.x + SidebarLayout.PADDING

        y = self._section_title(x, y, "GÖRSEL BİLGİLERİ")

        rows = [
            ("Çözünürlük", f"{Layout.WIDTH} × {Layout.HEIGHT}"),
            ("Dosya Türü", "PNG"),
        ]

        for label, value in rows:

            self.draw.text(
                (x, y),
                label,
                font=self.fonts["small"],
                fill=Theme.TEXT_SECONDARY,
            )

            self.draw.text(
                (x, y + 24),
                value,
                font=self.fonts["value"],
                fill=Theme.TEXT,
            )

            y += 62

        self.divider.draw_divider(
            x,
            y - 6,
            SidebarLayout.BAR_WIDTH,
        )

        return y + 6

    # --------------------------------------------------

    # Olasi analiz basliklari -- her uretimde bunlardan rastgele
    # bir kismi secilip rastgele skorla gosterilir, boylece ayni
    # video icin bile her cikti farkli analiz sunar.
    METRIC_POOL = [
        "Yazı Okunabilirliği",
        "Küçük Boyutta Görünürlük",
        "Dikkat Çekiciliği",
        "Renk Kontrastı",
        "Yüz Görünürlüğü",
        "Nesne Yoğunluğu",
        "Başlık Netliği",
        "Duygu Yoğunluğu",
    ]

    @staticmethod
    def _status_for(value):

        if value >= 90:
            return "YÜKSEK"
        elif value >= 75:
            return "İYİ"
        elif value >= 55:
            return "ORTA"
        else:
            return "DÜŞÜK"

    def _section_scores(self, y):

        x = Layout.SIDEBAR.x + SidebarLayout.PADDING

        y = self._section_title(x, y, "ANALİZLER")

        chosen = self.rng.sample(self.METRIC_POOL, k=3)

        scores = [
            (label, self.rng.randint(58, 98))
            for label in chosen
        ]

        scores = [
            (label, value, self._status_for(value))
            for label, value in scores
        ]

        for label, value, status in scores:

            self.draw.text(
                (x, y),
                label,
                font=self.fonts["small"],
                fill=Theme.TEXT,
            )

            status_font = self.fonts["small"]

            bbox = self.draw.textbbox((0, 0), status, font=status_font)
            sw = bbox[2] - bbox[0]

            color = Theme.GREEN

            if value < 55:
                color = Theme.RED
            elif value < 75:
                color = Theme.ORANGE

            self.draw.text(
                (Layout.SIDEBAR.right - SidebarLayout.PADDING - sw, y),
                status,
                font=status_font,
                fill=color,
            )

            bar_y = y + 28

            bar_w = SidebarLayout.BAR_WIDTH

            self.draw.rounded_rectangle(
                (x, bar_y, x + bar_w, bar_y + SidebarLayout.BAR_HEIGHT),
                radius=4,
                fill=Theme.BAR_BACKGROUND,
            )

            fill_w = int(bar_w * max(0, min(100, value)) / 100)

            self.draw.rounded_rectangle(
                (x, bar_y, x + fill_w, bar_y + SidebarLayout.BAR_HEIGHT),
                radius=4,
                fill=color,
            )

            y += SidebarLayout.ITEM_GAP

        self.divider.draw_divider(
            x,
            y - 4,
            SidebarLayout.BAR_WIDTH,
        )

        return y + 6

    # --------------------------------------------------

    def _section_generated(self, y):

        x = Layout.SIDEBAR.x + SidebarLayout.PADDING

        y = self._section_title(x, y, "OLUŞTURULMA BİLGİSİ")

        now = datetime.now()

        date_text = now.strftime("%d %B %Y")
        time_text = now.strftime("%H:%M")

        self.draw.text(
            (x, y),
            date_text,
            font=self.fonts["small"],
            fill=Theme.TEXT_SECONDARY,
        )

        time_x = x + SidebarLayout.BAR_WIDTH // 2

        self.draw.text(
            (time_x, y),
            time_text,
            font=self.fonts["small"],
            fill=Theme.TEXT_SECONDARY,
        )

        return y + 40

    # --------------------------------------------------

    def _tagline(self):

        x = Layout.SIDEBAR.x + SidebarLayout.PADDING
        y = Layout.SIDEBAR.bottom - 64

        self.divider.draw_divider(x, y - 18, SidebarLayout.BAR_WIDTH)

        wrapped = "Daha iyi tasarımlar, daha fazla etkileşim.\nSoyTasarım ile fark yaratın!"

        self.draw.multiline_text(
            (x, y),
            wrapped,
            font=self.fonts["small"],
            fill=Theme.TEXT_SECONDARY,
            spacing=6,
        )