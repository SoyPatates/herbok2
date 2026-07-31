from .theme import Theme
from .layout import Layout


class Footer:

    def __init__(self, draw, fonts):
        self.draw = draw
        self.fonts = fonts

    def render(self):

        rect = Layout.FOOTER

        self.draw.rounded_rectangle(
            (rect.x, rect.y, rect.right, rect.bottom),
            radius=14,
            fill=Theme.SURFACE,
            outline=Theme.BORDER,
            width=1,
        )

        star_size = 20
        star_x = rect.x + 20
        star_y = rect.y + rect.height / 2 - star_size / 2

        self._draw_star(star_x, star_y, star_size)

        text_x = star_x + star_size + 16
        # Star ile TAM ayni dikey merkez -- once buradaki -10 kaymasi
        # metni yukari itip yildizla hizasini bozuyordu.
        text_y = rect.y + rect.height / 2

        self.draw.text(
            (text_x, text_y),
            "Profesyonel önizlemeler, daha güçlü içerikler. ",
            font=self.fonts["small"],
            fill=Theme.TEXT_SECONDARY,
            anchor="lm",
        )

        bbox = self.draw.textbbox(
            (text_x, text_y),
            "Profesyonel önizlemeler, daha güçlü içerikler. ",
            font=self.fonts["small"],
            anchor="lm",
        )

        self.draw.text(
            (bbox[2], text_y),
            "SoyTasarım",
            font=self.fonts["small_bold"],
            fill=Theme.YOUTUBE_RED,
            anchor="lm",
        )

    def _draw_star(self, x, y, size):

        cx = x + size / 2
        cy = y + size / 2
        r = size / 2

        points = []

        import math

        for i in range(10):

            angle = math.pi / 2 + i * math.pi / 5
            radius = r if i % 2 == 0 else r * 0.45

            points.append(
                (
                    cx + radius * math.cos(angle),
                    cy - radius * math.sin(angle),
                )
            )

        self.draw.polygon(points, fill=Theme.YOUTUBE_RED)