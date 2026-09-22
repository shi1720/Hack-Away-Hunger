"""Edit real browser footage into a narrated 1080p demonstration with visible captions.

Requires FFmpeg and Pillow. Caption bars are rendered directly, so libass is optional.
"""

import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
TMP = ROOT / "tmp/video"
OUT = ROOT / "output"
FONT = Path("/System/Library/Fonts/Supplemental/Arial.ttf")


def run(args):
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL)


def seconds(value):
    h, m, s = value.replace(",", ".").split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


record = json.loads((TMP / "recording.json").read_text())
if record["errors"]:
    raise RuntimeError("Recording contains browser errors")
clips = []
for item in record["timeline"]:
    length = item["end"] - item["start"]
    speed = item["targetDuration"] / length
    target = TMP / f"clip-{item['id']}.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-ss",
            str(item["start"]),
            "-t",
            str(length),
            "-i",
            str(TMP / "raw-demo.webm"),
            "-an",
            "-vf",
            f"setpts={speed}*(PTS-STARTPTS),scale=1840:920:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:40:color=0x173e32,fps=30",
            "-t",
            str(item["targetDuration"]),
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "19",
            "-pix_fmt",
            "yuv420p",
            str(target),
        ]
    )
    clips.append(f"file '{target}'")
(TMP / "clips.txt").write_text("\n".join(clips))
run(
    [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(TMP / "clips.txt"),
        "-c",
        "copy",
        str(TMP / "silent.mp4"),
    ]
)
font = ImageFont.truetype(str(FONT), 42)
blank = TMP / "caption-blank.png"
Image.new("RGB", (1920, 120), "#173e32").save(blank)
captions = []


def add_caption_segment(file, start, stop):
    frames = round(stop * 30) - round(start * 30)
    if frames > 0:
        captions.extend([f"file '{file}'", "option framerate 30", f"duration {frames / 30:.9f}"])


end = 0
for i, block in enumerate((OUT / "Pantry-Relay-Captions.srt").read_text().strip().split("\n\n")):
    lines = block.splitlines()
    start, stop = [seconds(x) for x in lines[1].split(" --> ")]
    if start > end:
        add_caption_segment(blank, end, start)
    image = Image.new("RGB", (1920, 120), "#173e32")
    d = ImageDraw.Draw(image)
    text = lines[2:]
    y = (120 - len(text) * 49) / 2
    for line in text:
        box = d.textbbox((0, 0), line, font=font)
        width = box[2] - box[0]
        d.text(((1920 - width) / 2, y), line, font=font, fill="white")
        y += 49
    file = TMP / f"caption-{i:03}.png"
    image.save(file)
    add_caption_segment(file, start, stop)
    end = stop
full = sum(x["targetDuration"] for x in record["timeline"])
if full > end:
    add_caption_segment(blank, end, full)
captions.extend([f"file '{blank}'", "option framerate 30"])
(TMP / "captions.txt").write_text("\n".join(captions))
run(
    [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(TMP / "captions.txt"),
        "-vf",
        "fps=30",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "16",
        "-pix_fmt",
        "yuv420p",
        "-t",
        str(full),
        str(TMP / "caption-bar.mp4"),
    ]
)
disclosure = Image.new("RGBA", (1920, 40), "#173e32")
d = ImageDraw.Draw(disclosure)
d.text(
    (40, 7),
    "Fictional demo records | Synthetic narration",
    font=ImageFont.truetype(str(FONT), 23),
    fill="white",
)
disclosure.save(TMP / "disclosure.png")
run(
    [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-i",
        str(TMP / "silent.mp4"),
        "-i",
        str(TMP / "narration.wav"),
        "-i",
        str(TMP / "caption-bar.mp4"),
        "-loop",
        "1",
        "-i",
        str(TMP / "disclosure.png"),
        "-filter_complex",
        "[0:v][2:v]overlay=0:960[v];[v][3:v]overlay=0:0:enable='lt(t,32)'[outv]",
        "-map",
        "[outv]",
        "-map",
        "1:a",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "20",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-t",
        str(full),
        "-movflags",
        "+faststart",
        str(OUT / "Pantry-Relay-Demo.mp4"),
    ]
)
print("Created output/Pantry-Relay-Demo.mp4")
