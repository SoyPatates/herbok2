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


class Layout:

    WIDTH = 1920
    HEIGHT = 1080

    PADDING = 48
    GAP = 42

    HEADER_HEIGHT = 130
    FOOTER_HEIGHT = 36

    SIDEBAR_WIDTH = 430

    CONTENT_WIDTH = (
        WIDTH
        - SIDEBAR_WIDTH
        - PADDING * 3
        - 24
    )

    HEADER = Rect(
        PADDING,
        28,
        WIDTH - PADDING * 2,
        HEADER_HEIGHT,
    )

    FOOTER = Rect(
        PADDING,
        HEIGHT - 48,
        WIDTH - PADDING * 2,
        FOOTER_HEIGHT,
    )

    SIDEBAR = Rect(
        WIDTH - SIDEBAR_WIDTH - PADDING,
        HEADER.bottom + 28,
        SIDEBAR_WIDTH,
        HEIGHT - HEADER.bottom - 76,
    )

    CONTENT = Rect(
        PADDING,
        HEADER.bottom + 28,
        CONTENT_WIDTH,
        HEIGHT - HEADER.bottom - 76,
    )


class HomePage:

    AREA = Rect(
        Layout.CONTENT.x,
        Layout.CONTENT.y,
        Layout.CONTENT.width,
        590,
    )

    LABEL_Y = AREA.y

    THUMBNAIL = Rect(
        AREA.x,
        AREA.y + 28,
        AREA.width,
        470,
    )

    AVATAR_X = THUMBNAIL.x

    AVATAR_Y = THUMBNAIL.bottom + 20

    TITLE_X = AVATAR_X + 66

    TITLE_Y = AVATAR_Y

    CHANNEL_X = TITLE_X

    CHANNEL_Y = TITLE_Y + 42

    META_X = TITLE_X

    META_Y = CHANNEL_Y + 30


class SmallCards:

    TOP = HomePage.THUMBNAIL.bottom + 150

    WIDTH = (
        Layout.CONTENT.width - Layout.GAP
    ) // 2

    HEIGHT = 250

    LEFT = Rect(
        Layout.CONTENT.x,
        TOP,
        WIDTH,
        HEIGHT,
    )

    RIGHT = Rect(
        LEFT.right + Layout.GAP,
        TOP,
        WIDTH,
        HEIGHT,
    )

    THUMB_HEIGHT = 180

    AVATAR_SIZE = 42

    TITLE_OFFSET = 14

    META_OFFSET = 60


class SidebarLayout:

    PADDING = 26

    TITLE_Y = Layout.SIDEBAR.y + 24

    DIVIDER_Y = TITLE_Y + 54

    SECTION_GAP = 34

    BAR_WIDTH = 290

    BAR_HEIGHT = 12

    ITEM_GAP = 92


class HeaderLayout:

    TITLE_X = Layout.HEADER.x + 28

    TITLE_Y = Layout.HEADER.y + 12

    SUBTITLE_X = TITLE_X

    SUBTITLE_Y = TITLE_Y + 42

    BADGE_HEIGHT = 34

    BADGE_PADDING = 14


class FooterLayout:

    TEXT_X = Layout.FOOTER.x

    TEXT_Y = Layout.FOOTER.y


class Thumbnail:

    RADIUS = 16

    DURATION_PADDING = 8

    DURATION_MARGIN = 12

    BORDER_WIDTH = 1


class Avatar:

    SIZE = 48

    BORDER = 2


class Title:

    MAX_LINES = 2

    LINE_SPACING = 6

    MAX_WIDTH = 700


class Channel:

    VERIFIED_SIZE = 15

    VERIFIED_MARGIN = 8


class Meta:

    OFFSET = 28

    BULLET_MARGIN = 12


class Progress:

    WIDTH = 300

    HEIGHT = 12

    RADIUS = 6

    TITLE_MARGIN = 18

    STATUS_MARGIN = 22

    ITEM_GAP = 82