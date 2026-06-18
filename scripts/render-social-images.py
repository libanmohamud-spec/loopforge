#!/usr/bin/env python3

from io import BytesIO
import json
from pathlib import Path
import sys

try:
    from PIL import __version__ as PILLOW_VERSION
    from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps
except ImportError as error:
    raise SystemExit(
        "Pillow is required to render social cards. Install it with "
        "`python3 -m pip install Pillow`."
    ) from error


WIDTH = 1200
HEIGHT = 630
EXPECTED_PILLOW_VERSION = "11.3.0"
FF_ORANGE = "#FF5033"
FF_CHARCOAL = "#101010"
FF_LIGHT = "#FAF8F7"
FF_VIOLET = "#CCA5FF"

ROOT = Path(__file__).resolve().parent.parent
SOURCE_PATH = ROOT / "scripts" / "assets" / "loop-library-social-source.png"
MARK_PATH = ROOT / "site" / "assets" / "ff-mark.png"
OUTPUT_PATH = ROOT / "site" / "assets" / "social"
FONT_ROOT = ROOT / "scripts" / "assets" / "fonts"
REGULAR_FONT_PATH = FONT_ROOT / "inter" / "Inter-Regular.ttf"
BOLD_FONT_PATH = FONT_ROOT / "inter" / "Inter-Bold.ttf"
MONO_FONT_PATH = FONT_ROOT / "ibm-plex-mono" / "IBMPlexMono-Regular.ttf"


def load_font(size, *, bold=False, mono=False):
    font_path = MONO_FONT_PATH if mono else BOLD_FONT_PATH if bold else REGULAR_FONT_PATH
    if not font_path.is_file():
        raise FileNotFoundError(f"Required social-card font is missing: {font_path}")
    return ImageFont.truetype(font_path, size=size)


def wrap_text(draw, text, font, max_width):
    lines = []
    current = ""

    for word in text.split():
        candidate = f"{current} {word}".strip()
        width = draw.textbbox((0, 0), candidate, font=font)[2]
        if current and width > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate

    if current:
        lines.append(current)

    return lines


def fitted_lines(draw, text, *, max_width, max_lines, max_size, min_size):
    for size in range(max_size, min_size - 1, -2):
        font = load_font(size, bold=True)
        lines = wrap_text(draw, text, font, max_width)
        if len(lines) <= max_lines:
            return font, lines

    font = load_font(min_size, bold=True)
    lines = wrap_text(draw, text, font, max_width)
    if len(lines) > max_lines:
        raise ValueError(f"Social-card title is too long to render: {text}")
    return font, lines


def draw_tracking_text(draw, position, text, font, fill, tracking=2):
    x, y = position
    for character in text:
        draw.text((x, y), character, font=font, fill=fill)
        x += draw.textlength(character, font=font) + tracking


def tracking_text_width(draw, text, font, tracking=2):
    return sum(draw.textlength(character, font=font) for character in text) + (
        max(0, len(text) - 1) * tracking
    )


def text_block(draw, position, lines, font, *, fill, spacing):
    x, y = position
    line_height = draw.textbbox((0, 0), "Ag", font=font)[3]
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height + spacing
    return y


def background(source, index):
    image = ImageOps.fit(
        source,
        (WIDTH, HEIGHT),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    ).convert("RGBA")
    image = ImageEnhance.Contrast(image).enhance(1.08)
    image = ImageEnhance.Color(image).enhance(0.92)

    alpha = Image.new("L", (WIDTH, 1))
    alpha.putdata(
        [
            round(214 - (196 * min(1, x / (WIDTH * 0.82))))
            for x in range(WIDTH)
        ]
    )
    alpha = alpha.resize((WIDTH, HEIGHT))
    veil = Image.new("RGBA", (WIDTH, HEIGHT), FF_CHARCOAL)
    veil.putalpha(alpha)
    image = Image.alpha_composite(image, veil)

    draw = ImageDraw.Draw(image)
    accent = FF_VIOLET if index and index % 5 == 0 else FF_ORANGE
    draw.rectangle((0, 0, 14, HEIGHT), fill=accent)
    draw.rectangle((14, 0, WIDTH, 5), fill=FF_ORANGE)
    return image


def draw_brand(image, draw, mark):
    image.alpha_composite(mark, (68, 56))
    draw_tracking_text(
        draw,
        (132, 59),
        "FORWARD FUTURE",
        load_font(22, bold=True),
        FF_LIGHT,
        tracking=1.5,
    )
    draw_tracking_text(
        draw,
        (132, 88),
        "LOOP LIBRARY",
        load_font(15, mono=True),
        FF_ORANGE,
        tracking=2.5,
    )


def draw_progress(draw, active, count):
    x = 70
    y = 574
    for position in range(1, count + 1):
        fill = FF_ORANGE if position == active else (250, 248, 247, 56)
        draw.rounded_rectangle((x, y, x + 17, y + 6), radius=3, fill=fill)
        x += 24


def save_card(image, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    output = BytesIO()
    image.convert("RGB").save(
        output,
        format="JPEG",
        quality=89,
        optimize=True,
        progressive=True,
        subsampling=0,
    )
    rendered = output.getvalue()

    if destination.exists():
        if destination.read_bytes() != rendered:
            raise RuntimeError(
                f"Refusing to replace {destination.name} under the existing "
                "socialImageVersion. Bump the version before changing artwork."
            )
        return

    destination.write_bytes(rendered)


def render_home(source, mark, site, loop_count):
    image = background(source, 0)
    draw = ImageDraw.Draw(image)
    draw_brand(image, draw, mark)

    label_font = load_font(17, mono=True)
    label = f"{loop_count:02d} READY-TO-RUN LOOPS"
    label_width = tracking_text_width(draw, label, label_font, tracking=1)
    draw.rounded_rectangle((68, 172, 100 + label_width, 208), radius=18, fill=FF_ORANGE)
    draw_tracking_text(draw, (84, 182), label, label_font, FF_CHARCOAL, tracking=1)

    title_font = load_font(86, bold=True)
    draw.text((64, 227), site["name"], font=title_font, fill=FF_LIGHT)
    draw.text(
        (68, 333),
        "Repeatable AI agent workflows",
        font=load_font(36, bold=True),
        fill=FF_LIGHT,
    )
    draw.text(
        (70, 391),
        "Practical prompts. Clear checks. Real stopping conditions.",
        font=load_font(23),
        fill=(250, 248, 247, 210),
    )

    draw.rectangle((70, 456, 328, 462), fill=FF_ORANGE)
    draw_tracking_text(
        draw,
        (70, 497),
        "SIGNALS.FORWARDFUTURE.AI",
        load_font(15, mono=True),
        (250, 248, 247, 172),
        tracking=1.4,
    )
    save_card(
        image,
        OUTPUT_PATH / f"loop-library-{site['socialImageVersion']}.jpg",
    )


def render_loop(source, mark, site, loop, index, loop_count):
    image = background(source, index)
    draw = ImageDraw.Draw(image)
    draw_brand(image, draw, mark)

    label_font = load_font(17, mono=True)
    label = f"LOOP {loop['number']}"
    label_width = tracking_text_width(draw, label, label_font, tracking=1.5)
    draw.rounded_rectangle((68, 164, 102 + label_width, 202), radius=19, fill=FF_ORANGE)
    draw_tracking_text(draw, (85, 174), label, label_font, FF_CHARCOAL, tracking=1.5)

    title_font, title_lines = fitted_lines(
        draw,
        loop["title"],
        max_width=625,
        max_lines=3,
        max_size=67,
        min_size=47,
    )
    title_bottom = text_block(
        draw,
        (66, 232),
        title_lines,
        title_font,
        fill=FF_LIGHT,
        spacing=4,
    )

    rule_y = min(483, title_bottom + 24)
    draw.rectangle((70, rule_y, 256 + (index * 13) % 260, rule_y + 6), fill=FF_ORANGE)
    draw.text(
        (70, rule_y + 24),
        loop["categoryLabel"],
        font=load_font(19, bold=True),
        fill=(250, 248, 247, 220),
    )
    draw.text(
        (70, rule_y + 54),
        f"Contributed by {loop['author']}",
        font=load_font(17),
        fill=(250, 248, 247, 168),
    )

    draw_progress(draw, index, loop_count)
    draw_tracking_text(
        draw,
        (890, 575),
        f"{index:02d} / {loop_count:02d}",
        load_font(15, mono=True),
        (250, 248, 247, 165),
        tracking=1.2,
    )
    save_card(
        image,
        OUTPUT_PATH / f"{loop['slug']}-{site['socialImageVersion']}.jpg",
    )


def main():
    if PILLOW_VERSION != EXPECTED_PILLOW_VERSION:
        raise SystemExit(
            f"Pillow {EXPECTED_PILLOW_VERSION} is required for deterministic "
            f"social cards; found {PILLOW_VERSION}. Install "
            "`python3 -m pip install -r scripts/requirements-social.txt`."
        )

    payload = json.load(sys.stdin)
    site = payload["site"]
    loops = payload["loops"]

    if not site.get("socialImageVersion"):
        raise SystemExit("site.socialImageVersion is required")

    source = Image.open(SOURCE_PATH).convert("RGB")
    mark = Image.open(MARK_PATH).convert("RGBA")
    mark.thumbnail((48, 48), Image.Resampling.LANCZOS)

    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    render_home(source, mark, site, len(loops))
    for index, loop in enumerate(loops, start=1):
        render_loop(source, mark, site, loop, index, len(loops))

    print(f"Generated {len(loops) + 1} social preview images in {OUTPUT_PATH}.")


if __name__ == "__main__":
    main()
