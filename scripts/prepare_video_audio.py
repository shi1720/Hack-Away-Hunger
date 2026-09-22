"""Normalize the generated narration and create word-timed captions via the speech API."""

import argparse
import json
import os
import re
import subprocess
import textwrap
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(*args):
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def stamp(seconds):
    ms = round(seconds * 1000)
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--key-file", type=Path)
    args = p.parse_args()
    key = args.key_file.read_text().strip() if args.key_file else os.environ["OPENAI_API_KEY"]
    out = ROOT / "tmp/video"
    scenes = json.loads((out / "scenes.json").read_text())
    concat = []
    elapsed = 0
    for scene in scenes:
        target = out / "audio" / f"ready-{scene['id']}.wav"
        run(
            "ffmpeg",
            "-y",
            "-i",
            str(ROOT / scene["audio"]),
            "-af",
            "atempo=0.94,apad=pad_dur=0.65",
            "-ar",
            "24000",
            "-ac",
            "1",
            str(target),
        )
        scene["start"] = elapsed
        scene["duration"] = float(
            subprocess.check_output(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(target),
                ],
                text=True,
            )
        )
        elapsed += scene["duration"]
        scene["end"] = elapsed
        scene["ready_audio"] = str(target.relative_to(ROOT))
        concat.append(f"file '{target}'")
    (out / "audio/concat.txt").write_text("\n".join(concat))
    run(
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(out / "audio/concat.txt"),
        "-af",
        "loudnorm=I=-16:TP=-1.5:LRA=7",
        "-ar",
        "24000",
        "-ac",
        "1",
        str(out / "narration.wav"),
    )
    (out / "scenes.json").write_text(json.dumps(scenes, indent=2))
    dest = ROOT / "output"
    dest.mkdir(exist_ok=True)
    run(
        "ffmpeg",
        "-y",
        "-i",
        str(out / "narration.wav"),
        "-c:a",
        "libmp3lame",
        "-b:a",
        "160k",
        str(dest / "Pantry-Relay-Narration.mp3"),
    )
    transcript = out / "transcript.json"
    if not transcript.exists():
        boundary = "pantryrelay" + uuid.uuid4().hex
        chunks = []
        for name, value in [
            ("model", "whisper-1"),
            ("response_format", "verbose_json"),
            ("timestamp_granularities[]", "word"),
            ("language", "en"),
            (
                "prompt",
                "Pantry Relay. Cedar Grove. Eastside. Shivam Gupta. A pantry network, produce, protected reserves, 120 pounds, 112 pounds, 8 pounds.",
            ),
        ]:
            chunks.append(
                f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
            )
        chunks.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="narration.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode()
            + (out / "narration.wav").read_bytes()
            + b"\r\n"
        )
        chunks.append(f"--{boundary}--\r\n".encode())
        req = urllib.request.Request(
            "https://api.openai.com/v1/audio/transcriptions",
            data=b"".join(chunks),
            headers={
                "Authorization": "Bearer " + key,
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
        )
        with urllib.request.urlopen(req, timeout=180) as response:
            transcript.write_bytes(response.read())
    data = json.loads(transcript.read_text())
    # The word-timestamp response omits punctuation. Restore it from the aligned
    # transcript so sentence boundaries and currency amounts remain readable.
    tokens = data["text"].replace("-", " ").split()

    def normalize(value):
        return re.sub(r"[^a-z0-9]", "", value.lower())

    if len(tokens) != len(data["words"]) or any(
        normalize(token) != normalize(word["word"])
        for token, word in zip(tokens, data["words"], strict=True)
    ):
        raise ValueError("Transcript and word timing differ; review captions manually")
    words = [{**word, "word": token} for token, word in zip(tokens, data["words"], strict=True)]

    # Split complete sentences into balanced, two-line cues. A shortest-path
    # partition avoids a long cue followed by a flashing one-word remainder.
    def partition(sentence):
        count = len(sentence)
        best = [(float("inf"), []) for _ in range(count + 1)]
        best[count] = (0, [])
        for start in range(count - 1, -1, -1):
            for end in range(start + 1, count + 1):
                chunk = sentence[start:end]
                text = " ".join(word["word"] for word in chunk)
                duration = chunk[-1]["end"] - chunk[0]["start"]
                if len(textwrap.wrap(text, 42)) > 2 or duration > 5.8:
                    break
                cost = 1 + (len(text) - 62) ** 2 / 300
                cost += max(0, 1.3 - duration) * 8
                if chunk[-1]["word"].lower() in {
                    "the",
                    "a",
                    "an",
                    "and",
                    "with",
                    "its",
                    "to",
                    "of",
                }:
                    cost += 8
                cost += best[end][0]
                if cost < best[start][0]:
                    best[start] = (cost, [chunk] + best[end][1])
        if not best[0][1]:
            raise ValueError("A transcript sentence could not fit readable captions")
        return best[0][1]

    captions, sentence = [], []
    for word in words:
        sentence.append(word)
        if word["word"].endswith((".", "?", "!")):
            captions.extend(partition(sentence))
            sentence = []
    if sentence:
        captions.extend(partition(sentence))
    srt = []
    for i, group in enumerate(captions):
        line = " ".join(w["word"] for w in group)
        next_start = captions[i + 1][0]["start"] if i + 1 < len(captions) else elapsed
        stop = min(next_start, max(group[-1]["end"] + 0.15, group[0]["start"] + 1.2))
        srt.append(
            f"{i + 1}\n{stamp(group[0]['start'])} --> {stamp(stop)}\n"
            + "\n".join(textwrap.wrap(line, 42))
            + "\n"
        )
    (dest / "Pantry-Relay-Captions.srt").write_text("\n".join(srt))
    (out / "transcript.txt").write_text(data["text"])
    print(f"Prepared {elapsed:.1f}s narration and {len(captions)} timed captions", flush=True)


if __name__ == "__main__":
    main()
