from tempfile import NamedTemporaryFile
from PIL import Image, ImageDraw, ImageFont
import os
import textwrap


def wrap_text(draw, text, font, max_width, charwidth=50):
    lines = []

    for line in text.split('\n'):
        wrapped_lines = textwrap.wrap(line, width=charwidth)
        lines.extend(wrapped_lines)

    for line in lines:
        if draw.textlength(line, font=font) > max_width:
            return wrap_text(draw, text, font, max_width, charwidth - 1)

    return lines


def create_og_image(title, subtitle):
    canvas = Image.open(
        os.path.join(
            os.path.dirname(__file__),
            'fixtures',
            'og_canvas.png'
        )
    )

    max_width = 1000
    draw = ImageDraw.Draw(canvas)
    title_font = ImageFont.truetype(
        os.path.join(
            os.path.dirname(__file__),
            'fixtures',
            'Merriweather.ttf'
        ),
        size=72
    )

    subtitle_font = ImageFont.truetype(
        os.path.join(
            os.path.dirname(__file__),
            'fixtures',
            'Inter.ttf'
        ),
        size=48
    )

    wrapped_title = wrap_text(draw, title, title_font, max_width)
    wrapped_subtitle = wrap_text(draw, subtitle, subtitle_font, max_width)
    bottom_padding = 50
    left_padding = 50

    subtitle_height = (len(wrapped_subtitle) * 58) - 10
    title_height = len(wrapped_title) * 86
    subtitle_y_start = canvas.height - subtitle_height - bottom_padding + 20
    title_y_start = subtitle_y_start - title_height - 12
    y = title_y_start

    for line in wrapped_title:
        draw.text(
            (left_padding, y),
            line,
            font=title_font,
            fill='#0E323A'
        )

        y += 86

    y = subtitle_y_start

    for line in wrapped_subtitle:
        draw.text(
            (left_padding, y),
            line,
            font=subtitle_font,
            fill='#0E323A'
        )

        y += 48

    with NamedTemporaryFile(suffix='.png', delete=False) as f:
        canvas.save(f, format='PNG')

    return f.name
