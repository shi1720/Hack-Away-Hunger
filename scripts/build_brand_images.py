"""Render original branded submission images from the real application screenshot."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

R = Path(__file__).resolve().parent.parent
OUT = R / "artifacts" / "brand"
OUT.mkdir(parents=True, exist_ok=True)
FONT = Path("/System/Library/Fonts/Supplemental")


def f(name, size):
    return ImageFont.truetype(str(FONT / name), size)


for file, width, height in [("devpost-cover.png", 1200, 800), ("youtube-thumbnail.png", 1280, 720)]:
    im = Image.new("RGB", (width, height), "#173e32")
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((48, 42, 100, 94), radius=12, fill="#d9ed9c")
    d.line((74, 80, 74, 57), fill="#173e32", width=4)
    d.ellipse((58, 52, 75, 68), fill="#173e32")
    d.ellipse((75, 48, 91, 64), fill="#173e32")
    d.text((118, 44), "pantryrelay.", font=f("Arial Bold.ttf", 43), fill="#f5f3e9")
    d.text((50, 125), "Make the food already", font=f("Georgia.ttf", 60), fill="#f5f3e9")
    d.text((50, 200), "here go further.", font=f("Georgia.ttf", 60), fill="#f5f3e9")
    d.text(
        (53, 293),
        "From nearby surplus to a confirmed pantry handoff.",
        font=f("Arial.ttf", 25),
        fill="#c8d5c8",
    )
    screen = Image.open(R / "artifacts/screenshots/overview.png").convert("RGB")
    # Show the actual dashboard's upper section, never invented product screens.
    screen = screen.crop((0, 0, screen.width, min(screen.height, 790)))
    panel_w = width - 104
    panel_h = int(panel_w * screen.height / screen.width)
    screen = screen.resize((panel_w, panel_h), Image.Resampling.LANCZOS)
    panel_top = 358
    im.paste(screen, (52, panel_top))
    # Footer is deliberately outside the visible screenshot region.
    d = ImageDraw.Draw(im)
    d.rectangle((0, height - 50, width, height), fill="#173e32")
    d.text(
        (52, height - 34),
        "SHIVAM GUPTA  /  HACK AWAY HUNGER 2026",
        font=f("Arial.ttf", 18),
        fill="#d9ed9c",
    )
    d.text(
        (width - 260, height - 34), "Fictitious demo data", font=f("Arial.ttf", 17), fill="#c8d5c8"
    )
    im.save(OUT / file, optimize=True)
print("Brand images created")
