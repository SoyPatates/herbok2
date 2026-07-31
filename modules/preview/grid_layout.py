"""
3 bolumlu (Buyuk Ekran / Kucuk Ekran / Mobil) youtube anasayfa
onizlemesi icin dinamik layout hesaplamalari.

Hicbir thumbnail esnetilmez: her karttaki gorsel her zaman
gercek 16:9 oranindadir; sadece kart genisligi degisir.
"""

from .layout import Rect


WIDTH = 1920

PADDING = 48
GRID_GAP = 32

TOP_HEADER_HEIGHT = 170

SECTION_LABEL_HEIGHT = 56
SECTION_MARGIN = 64

FOOTER_HEIGHT = 60
BOTTOM_MARGIN = 48


def _thumb_height(card_width):
    return round(card_width * 9 / 16)


class CardSpec:
    """
    Tek bir kartin (thumbnail + avatar + baslik + meta) tum olcumlerini
    tasar. width disinda hicbir sey esnetilmez; thumb_height her zaman
    width * 9/16 olarak hesaplanir.
    """

    def __init__(
        self,
        width,
        avatar_size,
        info_height,
        gap_thumb_info=14,
    ):
        self.width = width
        self.thumb_height = _thumb_height(width)
        self.avatar_size = avatar_size
        self.info_height = info_height
        self.gap_thumb_info = gap_thumb_info

    @property
    def height(self):
        return (
            self.thumb_height
            + self.gap_thumb_info
            + self.info_height
        )


class GridSpec:
    """
    Sabit sutun sayili bir grid (buyuk/kucuk ekran) tanimi.
    """

    def __init__(
        self,
        x,
        y,
        container_width,
        columns,
        rows,
        avatar_size,
        info_height,
    ):
        self.x = x
        self.y = y
        self.container_width = container_width
        self.columns = columns
        self.rows = rows

        card_width = (
            container_width - GRID_GAP * (columns - 1)
        ) // columns

        self.card = CardSpec(
            card_width,
            avatar_size,
            info_height,
        )

    def card_rect_index(self, index):

        col = index % self.columns
        row = index // self.columns

        cw = self.card.width
        ch = self.card.height

        x = self.x + col * (cw + GRID_GAP)
        y = self.y + row * (ch + GRID_GAP)

        return x, y

    @property
    def height(self):
        ch = self.card.height
        return ch * self.rows + GRID_GAP * (self.rows - 1)

    @property
    def bottom(self):
        return self.y + self.height

    @property
    def count(self):
        return self.columns * self.rows


class ListSpec:
    """
    Tek sutunlu (mobil) dikey liste tanimi.
    """

    def __init__(
        self,
        x,
        y,
        width,
        items,
        avatar_size,
        info_height,
        gap=24,
    ):
        self.x = x
        self.y = y
        self.width = width
        self.items = items
        self.gap = gap

        self.card = CardSpec(
            width,
            avatar_size,
            info_height,
        )

    def card_rect_index(self, index):

        ch = self.card.height

        x = self.x
        y = self.y + index * (ch + self.gap)

        return x, y

    @property
    def height(self):
        ch = self.card.height
        return ch * self.items + self.gap * (self.items - 1)

    @property
    def bottom(self):
        return self.y + self.height

    @property
    def count(self):
        return self.items


def build_layout():
    """
    Butun sayfa boyunca 3 bolumu hesaplayip, gerekli toplam canvas
    yuksekligiyle birlikte doner.
    """

    content_x = PADDING
    content_width = WIDTH - PADDING * 2

    # --------------------------------------------------
    # Buyuk ekran grid'i (3 sutun x 2 satir)
    # --------------------------------------------------

    large_y = TOP_HEADER_HEIGHT + SECTION_LABEL_HEIGHT

    large = GridSpec(
        x=content_x,
        y=large_y,
        container_width=content_width,
        columns=3,
        rows=2,
        avatar_size=40,
        info_height=118,
    )

    # --------------------------------------------------
    # Kucuk ekran grid'i (dar bir "pencere" simule edilir)
    # --------------------------------------------------

    small_container_width = 1280

    small_x = content_x + (content_width - small_container_width) // 2

    small_y = (
        large.bottom
        + SECTION_MARGIN
        + SECTION_LABEL_HEIGHT
    )

    small = GridSpec(
        x=small_x,
        y=small_y,
        container_width=small_container_width,
        columns=3,
        rows=2,
        avatar_size=32,
        info_height=96,
    )

    # --------------------------------------------------
    # Mobil liste (tek sutun, telefon genisliginde)
    # --------------------------------------------------

    mobile_frame_width = 420
    mobile_inner_padding = 18

    mobile_x = content_x + (content_width - mobile_frame_width) // 2

    mobile_y = (
        small.bottom
        + SECTION_MARGIN
        + SECTION_LABEL_HEIGHT
    )

    mobile_card_width = mobile_frame_width - mobile_inner_padding * 2

    mobile = ListSpec(
        x=mobile_x + mobile_inner_padding,
        y=mobile_y + mobile_inner_padding,
        width=mobile_card_width,
        items=3,
        avatar_size=30,
        info_height=76,
        gap=22,
    )

    mobile_frame = Rect(
        mobile_x,
        mobile_y,
        mobile_frame_width,
        mobile.height + mobile_inner_padding * 2,
    )

    total_height = (
        mobile_frame.bottom
        + SECTION_MARGIN
        + FOOTER_HEIGHT
        + BOTTOM_MARGIN
    )

    return {
        "width": WIDTH,
        "height": total_height,
        "content_x": content_x,
        "content_width": content_width,
        "large": large,
        "small": small,
        "mobile": mobile,
        "mobile_frame": mobile_frame,
        "large_label_y": large_y - SECTION_LABEL_HEIGHT + 8,
        "small_label_y": small_y - SECTION_LABEL_HEIGHT + 8,
        "mobile_label_y": mobile_y - SECTION_LABEL_HEIGHT + 8,
    }