from pathlib import Path

from PIL import Image, ImageOps

LOGO_PATH = Path(__file__).with_name("custom-logo.png")


def draw_pillow_logo(
    canvas: Image.Image,
    x: float,
    y: float,
    width: float,
    height: float,
) -> None:
    bounds = (max(1, round(width)), max(1, round(height)))
    with Image.open(LOGO_PATH) as source:
        logo = ImageOps.contain(
            source.convert("RGBA"),
            bounds,
            method=Image.Resampling.LANCZOS,
        )

    position = (
        round(x + (width - logo.width) / 2),
        round(y + (height - logo.height) / 2),
    )
    if canvas.mode == "RGBA":
        canvas.alpha_composite(logo, position)
    else:
        canvas.paste(logo.convert(canvas.mode), position, logo.getchannel("A"))


def draw_reportlab_logo(canvas, x: float, y: float, width: float, height: float) -> None:
    canvas.drawImage(
        str(LOGO_PATH),
        x,
        y,
        width,
        height,
        preserveAspectRatio=True,
        anchor="c",
        mask="auto",
    )
