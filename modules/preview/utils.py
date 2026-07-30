import os

from PIL import (
    Image,
    ImageDraw,
    ImageFont,
    ImageFilter,
    ImageOps,
)


# --------------------------------------------------------
# FONT
# --------------------------------------------------------

def load_font(
    size: int,
    bold: bool = False,
):

    fonts = [

        "assets/fonts/Roboto-Bold.ttf"
        if bold
        else "assets/fonts/Roboto-Regular.ttf",

        "Roboto-Bold.ttf"
        if bold
        else "Roboto-Regular.ttf",

        "arialbd.ttf"
        if bold
        else "arial.ttf",

    ]

    for font in fonts:

        try:

            return ImageFont.truetype(
                font,
                size
            )

        except:

            pass

    return ImageFont.load_default()


# --------------------------------------------------------
# ROUNDED RECTANGLE
# --------------------------------------------------------

def rounded_rectangle(
    draw,
    box,
    radius,
    fill,
    outline=None,
    width=1,
):

    draw.rounded_rectangle(
        box,
        radius=radius,
        fill=fill,
        outline=outline,
        width=width,
    )


# --------------------------------------------------------
# FIT TEXT
# --------------------------------------------------------
def fit_text(
    draw,
    text,
    font,
    max_width,
    max_lines=1,
):

    words = text.split()

    if not words:
        return ""

    lines = []
    current = ""

    for word in words:

        test = word if not current else current + " " + word

        if draw.textlength(test, font=font) <= max_width:
            current = test
        else:
            lines.append(current)
            current = word

            if len(lines) == max_lines:
                break

    if len(lines) < max_lines and current:
        lines.append(current)

    if len(lines) > max_lines:
        lines = lines[:max_lines]

    if len(lines) == max_lines and " ".join(lines).strip() != text.strip():

        while draw.textlength(lines[-1] + "...", font=font) > max_width and lines[-1]:
            lines[-1] = lines[-1][:-1]

        lines[-1] += "..."

    return "\n".join(lines)
# --------------------------------------------------------
# THUMBNAIL
# --------------------------------------------------------

def crop_thumbnail(
    image,
    size,
):

    return ImageOps.fit(
        image,
        size,
        method=Image.Resampling.LANCZOS,
    )


# --------------------------------------------------------
# AVATAR
# --------------------------------------------------------

def circle_avatar(
    avatar,
    size,
):

    avatar = ImageOps.fit(
        avatar,
        (
            size,
            size,
        ),
        method=Image.Resampling.LANCZOS,
    )

    mask = Image.new(
        "L",
        (
            size,
            size,
        ),
        0,
    )

    ImageDraw.Draw(mask).ellipse(
        (
            0,
            0,
            size,
            size,
        ),
        fill=255,
    )

    result = Image.new(
        "RGBA",
        (
            size,
            size,
        )
    )

    result.paste(
        avatar,
        (
            0,
            0,
        ),
        mask,
    )

    return result


# --------------------------------------------------------
# SHADOW
# --------------------------------------------------------

def shadow(
    image,
    radius=18,
):

    return image.filter(
        ImageFilter.GaussianBlur(radius)
    )


# --------------------------------------------------------
# CENTER
# --------------------------------------------------------

def center_x(
    container_width,
    object_width,
):

    return (
        container_width - object_width
    ) // 2


# --------------------------------------------------------
# CLAMP
# --------------------------------------------------------

def clamp(
    value,
    minimum,
    maximum,
):

    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


# --------------------------------------------------------
# RGB
# --------------------------------------------------------

def rgb(hex_color):

    hex_color = hex_color.replace(
        "#",
        "",
    )

    return tuple(

        int(
            hex_color[i:i + 2],
            16,
        )

        for i in (
            0,
            2,
            4,
        )

    )