from .theme import Theme
from .layout import FooterLayout


class Footer:

    def __init__(
        self,
        draw,
        fonts,
    ):

        self.draw = draw
        self.fonts = fonts

    # --------------------------------------------------

    def render(self):

        self._left()

        self._right()

    # --------------------------------------------------

    def _left(self):

        self.draw.text(
            (
                FooterLayout.TEXT_X,
                FooterLayout.TEXT_Y,
            ),
            "SoyTasarım • Ön İzleme Motoru",
            fill=Theme.TEXT_MUTED,
            font=self.fonts["tiny"],
        )

    # --------------------------------------------------

    def _right(self):

        text = "v2.0"

        bbox = self.draw.textbbox(
            (0, 0),
            text,
            font=self.fonts["tiny"],
        )

        width = bbox[2] - bbox[0]

        x = (
            1920
            - 48
            - width
        )

        self.draw.text(
            (
                x,
                FooterLayout.TEXT_Y,
            ),
            text,
            fill=Theme.TEXT_MUTED,
            font=self.fonts["tiny"],
        )