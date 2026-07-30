from PIL import Image

from .canvas import Canvas
from .theme import Theme

from .header import Header
from .cards import Cards
from .sidebar import Sidebar
from .footer import Footer

from .utils import (
    load_font,
    crop_thumbnail,
    circle_avatar,
)


class PreviewGenerator:

    def __init__(
        self,
        thumbnail,
        avatar=None,
        title="Video Başlığı",
        channel="SoyTasarım",
        duration="12:48",
    ):

        self.thumbnail = thumbnail
        self.avatar = avatar

        self.title = title
        self.channel = channel
        self.duration = duration

        self.canvas = Canvas()

        self.image = self.canvas.get_image()
        self.draw = self.canvas.get_draw()

        self.fonts = {
            "title": load_font(56, bold=True),
            "subtitle": load_font(28),
            "text": load_font(34, bold=True),
            "small": load_font(26),
            "tiny": load_font(22),
        }

    # --------------------------------------------------

    def _prepare_thumbnail(self):

        if isinstance(self.thumbnail, str):
            image = Image.open(self.thumbnail).convert("RGB")
        else:
            image = self.thumbnail.convert("RGB")

        return crop_thumbnail(
            image,
            (1280, 720),
        )

    # --------------------------------------------------

    def _prepare_avatar(self):

        if self.avatar is None:

            avatar = Image.new(
                "RGB",
                (256, 256),
                Theme.SURFACE_LIGHT,
            )

        elif isinstance(self.avatar, str):

            avatar = Image.open(
                self.avatar
            ).convert("RGB")

        else:

            avatar = self.avatar.convert("RGB")

        return circle_avatar(
            avatar,
            128,
        )

    # --------------------------------------------------

    def render(self):

        thumbnail = self._prepare_thumbnail()
        avatar = self._prepare_avatar()

        Header(
            self.draw,
            self.fonts,
        ).render()

        Cards(
            canvas=self.image,
            draw=self.draw,
            fonts=self.fonts,
            thumbnail=thumbnail,
            avatar=avatar,
            title=self.title,
            channel=self.channel,
            duration=self.duration,
        ).render()

        Sidebar(
            self.draw,
            self.fonts,
        ).render()

        Footer(
            self.draw,
            self.fonts,
        ).render()

        return self.image

    # --------------------------------------------------

    def save(
        self,
        output="preview.png",
    ):

        image = self.render()

        image.save(
            output,
            quality=100,
        )

        return output

    # --------------------------------------------------

    def show(self):

        self.render().show()

    # --------------------------------------------------

    @classmethod
    def generate(
        cls,
        thumbnail,
        output="preview.png",
        avatar=None,
        title="Video Başlığı",
        channel="SoyTasarım",
        duration="12:48",
    ):

        generator = cls(
            thumbnail=thumbnail,
            avatar=avatar,
            title=title,
            channel=channel,
            duration=duration,
        )

        return generator.save(output)
