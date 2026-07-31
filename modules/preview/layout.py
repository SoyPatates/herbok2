from dataclasses import dataclass


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    width: int
    height: int

    @property
    def right(self):
        return self.x + self.width

    @property
    def bottom(self):
        return self.y + self.height


class Thumbnail:

    RADIUS = 14
    DURATION_MARGIN = 10


class Title:

    LINE_SPACING = 6


class Layout:

    WIDTH = 1920
    HEIGHT = 1080

    PADDING = 44
    GAP = 24

    HEADER_HEIGHT = 108

    SIDEBAR_WIDTH = 400

    HEADER = Rect(
        PADDING,
        36,
        WIDTH - PADDING * 2,
        HEADER_HEIGHT,
    )

    CONTENT_TOP = HEADER.bottom + 26

    FOOTER_HEIGHT = 58

    FOOTER = Rect(
        PADDING,
        HEIGHT - FOOTER_HEIGHT - 24,
        WIDTH - SIDEBAR_WIDTH - PADDING * 2 - 24,
        FOOTER_HEIGHT,
    )

    CONTENT_BOTTOM = FOOTER.y - 20

    SIDEBAR = Rect(
        WIDTH - SIDEBAR_WIDTH - PADDING,
        CONTENT_TOP,
        SIDEBAR_WIDTH,
        HEIGHT - CONTENT_TOP - 24,
    )

    CONTENT = Rect(
        PADDING,
        CONTENT_TOP,
        SIDEBAR.x - PADDING - 24,
        CONTENT_BOTTOM - CONTENT_TOP,
    )


class HeaderLayout:

    LOGO_SIZE = 56

    LOGO_X = Layout.HEADER.x
    LOGO_Y = Layout.HEADER.y + 2

    TITLE_X = LOGO_X + LOGO_SIZE + 22
    TITLE_Y = Layout.HEADER.y

    DIVIDER_X = TITLE_X + 250

    HEADLINE_X = DIVIDER_X + 24
    HEADLINE_Y = Layout.HEADER.y + 4

    SUBTITLE_X = HEADLINE_X
    SUBTITLE_Y = HEADLINE_Y + 40


class RowsLayout:

    COUNT = 3
    GAP = Layout.GAP

    ROW_HEIGHT = (
        Layout.CONTENT.height - GAP * (COUNT - 1)
    ) // COUNT

    PADDING = 26

    ICON_SIZE = 56

    LEFT_WIDTH = 310

    THUMB_HEIGHT = ROW_HEIGHT - PADDING * 2
    THUMB_WIDTH = round(THUMB_HEIGHT * 16 / 9)

    INFO_GAP = 28

    # Gercek YouTube thumbnail boyutlari (piksel). Buyuk ekrandaki
    # ilk boyut referans alinir, digerleri bu orana gore kuculur --
    # boylece 3 satir da GERCEKTEN farkli buyuklukte gorunur.
    ROWS = [
        {
            "icon": "home",
            "label": "ANA SAYFA",
            "size_label": "360 × 205",
            "real_size": (360, 205),
            "description": "Videonuzun YouTube ana sayfasındaki görünümü.",
        },
        {
            "icon": "monitor",
            "label": "KÜÇÜK ANA SAYFA",
            "size_label": "240 × 135",
            "real_size": (240, 135),
            "description": "Ana sayfada daha küçük görünen hâli.",
        },
        {
            "icon": "play",
            "label": "ÖNERİLEN VİDEOLAR",
            "size_label": "168 × 94",
            "real_size": (168, 94),
            "description": "Önerilen videolar listesinde görünen hâli.",
        },
    ]

    # İlk satırın thumbnail genişliği bu değere sabitlenir, diğer
    # satırlar real_size oranına göre buna göre küçülür.
    BASE_THUMB_WIDTH = THUMB_WIDTH

    @staticmethod
    def thumb_size(index):

        real_w, real_h = RowsLayout.ROWS[index]["real_size"]

        base_real_w = RowsLayout.ROWS[0]["real_size"][0]

        scale = RowsLayout.BASE_THUMB_WIDTH / base_real_w

        return (
            round(real_w * scale),
            round(real_h * scale),
        )

    @staticmethod
    def row_rect(index):

        y = (
            Layout.CONTENT.y
            + index * (RowsLayout.ROW_HEIGHT + RowsLayout.GAP)
        )

        return Rect(
            Layout.CONTENT.x,
            y,
            Layout.CONTENT.width,
            RowsLayout.ROW_HEIGHT,
        )


class SidebarLayout:

    PADDING = 26

    LOGO_SIZE = 44

    LOGO_X = Layout.SIDEBAR.x + PADDING
    LOGO_Y = Layout.SIDEBAR.y + PADDING

    TITLE_X = LOGO_X + LOGO_SIZE + 16
    TITLE_Y = LOGO_Y - 2

    SUBTITLE_X = TITLE_X
    SUBTITLE_Y = TITLE_Y + 32

    SECTION_START_Y = LOGO_Y + LOGO_SIZE + 30

    SECTION_GAP = 30

    ITEM_GAP = 38

    BAR_WIDTH = Layout.SIDEBAR.width - PADDING * 2
    BAR_HEIGHT = 8


class FooterLayout:

    ICON_SIZE = 34