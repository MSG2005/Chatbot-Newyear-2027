"""Local greeting-card renderer. No external image-generation API."""

import math
import re
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


BASE_DIR = Path(__file__).resolve().parent
FONTS = BASE_DIR / "fonts"

WIDTH = 1080
HEIGHT = 1350


def font(size, serif=False):
    filename = (
        "DejaVuSerif.ttf"
        if serif
        else "DejaVuSans.ttf"
    )

    return ImageFont.truetype(
        str(FONTS / filename),
        size,
    )


def card_text(text):
    """Remove decorative emoji while preserving the message wording."""
    return re.sub(
        r"[\U0001F000-\U0001FAFF"
        r"\u2600-\u27BF\uFE0E\uFE0F\u200D]",
        "",
        str(text),
    ).strip()


def wrap(draw, text, face, width):
    """Wrap paragraphs and split individual words only when necessary."""
    lines = []

    for paragraph in text.split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue

        line = ""

        for word in paragraph.split():
            candidate = (line + " " + word).strip()

            if draw.textlength(candidate, font=face) <= width:
                line = candidate
                continue

            if line:
                lines.append(line)
                line = ""

            for character in word:
                if (
                    line
                    and draw.textlength(
                        line + character,
                        font=face,
                    ) > width
                ):
                    lines.append(line)
                    line = ""

                line += character

        if line.strip():
            lines.append(line.rstrip())

    return lines


def fit_text(
    draw,
    text,
    width,
    height,
    maximum_size,
    minimum_size,
    serif=False,
):
    """Find a font size that fits all text without truncating it."""
    for size in range(
        maximum_size,
        minimum_size - 1,
        -1,
    ):
        face = font(size, serif)
        lines = wrap(draw, text, face, width)
        line_height = math.ceil(size * 1.45)

        if (
            len(lines) * line_height <= height
            and all(
                draw.textlength(line, font=face) <= width
                for line in lines
            )
        ):
            return face, lines, line_height

    raise ValueError("Text does not fit the card")


def separate_signature(text, sender_name=""):
    """
    Support both calling styles:

    Existing main.py:
        render_card(signed_greeting, flow, 0, recipient)

    Explicit sender argument:
        render_card(greeting, flow, 0, recipient, sender)
    """
    message = card_text(text)
    sender = " ".join(card_text(sender_name).split())

    # The latest main.py appends the sender as a separate paragraph.
    match = re.search(
        r"\n[ \t]*\nFrom[ \t]+([^\n]+)\s*\Z",
        message,
    )

    if match:
        embedded_sender = match.group(1).strip()

        # Extract only the trailing signature paragraph.
        if not sender or embedded_sender == sender:
            sender = sender or embedded_sender
            message = message[:match.start()].rstrip()

    return message, sender


def render_card(
    text,
    flow_id="1",
    variant=0,
    recipient_name="",
    sender_name="",
):
    message, sender = separate_signature(
        text,
        sender_name,
    )

    if not message or len(message) > 2200:
        raise ValueError(
            "No usable greeting or greeting too long"
        )

    recipient_name = " ".join(
        card_text(recipient_name).split()
    )

    if len(recipient_name) > 60 or len(sender) > 60:
        raise ValueError(
            "Recipient and sender names must be at most 60 characters"
        )

    fid = (
        str(flow_id)
        if str(flow_id) in {"1", "2", "3", "4", "5"}
        else "1"
    )

    variant = int(variant) % 2

    background_path = (
        BASE_DIR
        / "assets"
        / "cards"
        / f"theme-{fid}.png"
    )

    with Image.open(background_path) as source:
        image = source.convert("RGB").resize(
            (WIDTH, HEIGHT),
            Image.Resampling.LANCZOS,
        )

    if variant:
        image = ImageOps.mirror(image)

    image = image.convert("RGBA")

    accent = {
        "1": "#1d584a",
        "2": "#a73e1d",
        "3": "#503279",
        "4": "#964755",
        "5": "#79502d",
    }[fid]

    ink = "#fff7e7"
    gold = "#f0d697"

    overlay = Image.new(
        "RGBA",
        image.size,
        (0, 0, 0, 0),
    )
    panel = ImageDraw.Draw(overlay)

    # Solid panel keeps the text readable over every illustration.
    panel.rounded_rectangle(
        (88, 390, 992, 1145),
        radius=34,
        fill=accent,
    )

    panel.rounded_rectangle(
        (104, 406, 976, 1129),
        radius=26,
        outline="#d9b76f",
        width=2,
    )

    image = Image.alpha_composite(
        image,
        overlay,
    )
    draw = ImageDraw.Draw(image)

    def center(y, label, face, color):
        text_width = draw.textlength(
            label,
            font=face,
        )

        draw.text(
            ((WIDTH - text_width) / 2, y),
            label,
            font=face,
            fill=color,
        )

    # Recipient name.
    recipient_label = (
        f"For {recipient_name}"
        if recipient_name
        else "MADE JUST FOR YOU"
    )

    recipient_font, recipient_lines, recipient_step = fit_text(
        draw,
        recipient_label,
        width=780,
        height=58,
        maximum_size=29,
        minimum_size=14,
    )

    recipient_top = (
        435
        + (58 - len(recipient_lines) * recipient_step) // 2
    )

    for line in recipient_lines:
        center(
            recipient_top,
            line,
            recipient_font,
            gold,
        )
        recipient_top += recipient_step

    # Main heading.
    center(
        505,
        "Happy New Year",
        font(55, True),
        ink,
    )

    center(
        567,
        "2027",
        font(82, True),
        gold,
    )

    draw.line(
        (410, 685, 670, 685),
        fill=gold,
        width=2,
    )

    # Reserve a separate area for the sender signature.
    body_top = 710
    body_height = 240 if sender else 290

    body_font, body_lines, body_step = fit_text(
        draw,
        message,
        width=750,
        height=body_height,
        maximum_size=34,
        minimum_size=18,
        serif=True,
    )

    current_y = (
        body_top
        + (body_height - len(body_lines) * body_step) // 2
    )

    for line in body_lines:
        center(
            current_y,
            line,
            body_font,
            ink,
        )
        current_y += body_step

    # Sender signature, separate from the generated greeting.
    if sender:
        signature = f"From {sender}"

        signature_font, signature_lines, signature_step = fit_text(
            draw,
            signature,
            width=750,
            height=64,
            maximum_size=28,
            minimum_size=14,
            serif=True,
        )

        signature_top = (
            958
            + (64 - len(signature_lines) * signature_step) // 2
        )

        for line in signature_lines:
            center(
                signature_top,
                line,
                signature_font,
                gold,
            )
            signature_top += signature_step

    # Keep fictional experiences clearly labelled.
    if fid in {"3", "5"}:
        center(
            1033,
            "AN IMAGINARY MESSAGE · JUST FOR FUN",
            font(16),
            gold,
        )

    center(
        1086,
        "Made with Digital Catalyst",
        font(19),
        gold,
    )

    data = BytesIO()

    image.convert("RGB").save(
        data,
        format="JPEG",
        quality=90,
        optimize=True,
    )

    return data.getvalue()
