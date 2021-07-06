# Adapted from https://github.com/kylefox/placeholder-pics/blob/master/placeholder_pics/placeholder.py

from PIL import Image, ImageDraw, ImageFont

from pathlib import Path
from typing import Tuple
from argparse import ArgumentParser

FONT = Path(__file__).resolve().parent.joinpath("Lato-Regular.ttf")


def WidthByHeight(raw: int) -> Tuple[int, int]:
    w, h = raw.split("x")
    return int(w), int(h)


def main():
    p = ArgumentParser()
    p.add_argument(
        "file", type=Path, help="Output path",
    )
    p.add_argument(
        "background", help="Hex value for background color", type=str,
    )
    p.add_argument(
        "size", help="WxH (integer) values for size in pixels", type=WidthByHeight,
    )
    p.add_argument(
        "--text", help="Text to render", type=str, default=None,
    )
    args = p.parse_args()

    img = Image.new(mode="RGB", size=args.size, color=args.background)
    if args.text is not None:
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(font=FONT.as_posix(), size=int(min(*args.size) * 0.3))
        tw, th = draw.textsize(args.text, font=font)
        xloc = (args.size[0] - tw) / 2
        yloc = (args.size[1] - (th * 1.25)) / 2
        draw.text(
            (xloc, yloc), args.text, "#ffffff", font=font,
        )
    img.save(args.file.as_posix())


if __name__ == "__main__":
    main()
