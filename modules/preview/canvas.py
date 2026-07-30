from PIL import Image, ImageDraw

from .theme import Theme
from .layout import Layout


class Canvas:

    def __init__(self):

        self.image = Image.new(
            "RGB",
            (
                Layout.WIDTH,
                Layout.HEIGHT,
            ),
            Theme.BACKGROUND,
        )

        self.draw = ImageDraw.Draw(self.image)

    # --------------------------------------------------

    def get_image(self):

        return self.image

    # --------------------------------------------------

    def get_draw(self):

        return self.draw

    # --------------------------------------------------

    def clear(self):

        self.draw.rectangle(
            (
                0,
                0,
                Layout.WIDTH,
                Layout.HEIGHT,
            ),
            fill=Theme.BACKGROUND,
        )

    # --------------------------------------------------

    def save(
        self,
        path,
        quality=100,
    ):

        self.image.save(
            path,
            quality=quality,
        )

    # --------------------------------------------------

    @property
    def width(self):

        return Layout.WIDTH

    # --------------------------------------------------

    @property
    def height(self):

        return Layout.HEIGHT