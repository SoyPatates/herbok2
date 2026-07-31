import hashlib

from PIL import Image, ImageDraw

from .theme import Theme
from .layout import Layout

from .header import Header
from .rows import Rows
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

        self.image = Image.new(
            "RGB",
            (Layout.WIDTH, Layout.HEIGHT),
            Theme.BACKGROUND,
        )

        self.draw = ImageDraw.Draw(self.image)

        self.fonts = {
            "brand": load_font(34, bold=True),
            "headline": load_font(28, bold=True),
            "sidebar_brand": load_font(26, bold=True),
            "section_title": load_font(20, bold=True),
            "row_label": load_font(22, bold=True),
            "card_title": load_font(28, bold=True),
            "value": load_font(24, bold=True),
            "small": load_font(19),
            "small_bold": load_font(19, bold=True),
            "tiny": load_font(17),
        }

    # --------------------------------------------------

    def _prepare_thumbnail(self):

        if isinstance(self.thumbnail, str):
            image = Image.open(self.thumbnail).convert("RGB")
        else:
            image = self.thumbnail.convert("RGB")

        return crop_thumbnail(image, (1280, 720))

    # --------------------------------------------------

    def _prepare_avatar(self):

        if self.avatar is None:
            avatar = Image.new("RGB", (256, 256), Theme.SURFACE_LIGHT)
        elif isinstance(self.avatar, str):
            avatar = Image.open(self.avatar).convert("RGB")
        else:
            avatar = self.avatar.convert("RGB")

        return circle_avatar(avatar, 128)

    # --------------------------------------------------

    def _analysis_seed(self, thumbnail):

        # Ayni gorsel + ayni baslik = ayni seed = ayni analiz sonucu.
        # Farkli bir video/tasarim icin thumbnail baytlari veya
        # baslik degistigi an seed de degisir, analiz de degisir.
        hasher = hashlib.md5()

        hasher.update(thumbnail.tobytes())
        hasher.update(self.title.encode("utf-8"))
        hasher.update(self.channel.encode("utf-8"))

        return int(hasher.hexdigest(), 16) % (2 ** 32)

    # --------------------------------------------------

    def render(self):

        thumbnail = self._prepare_thumbnail()
        avatar = self._prepare_avatar()

        Header(self.draw, self.fonts).render()

        Rows(
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
            seed=self._analysis_seed(thumbnail),
        ).render()

        Footer(self.draw, self.fonts).render()

        return self.image

    # --------------------------------------------------

    def save(self, output="preview.png"):

        image = self.render()
        image.save(output, quality=100)
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