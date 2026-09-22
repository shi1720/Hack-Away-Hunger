"""Generate disclosed synthetic narration from the approved scene script.

Requires OPENAI_API_KEY or --key-file. Credentials are never written to output.
"""

import argparse
import json
import os
import re
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--key-file", type=Path)
    args = parser.parse_args()
    key = args.key_file.read_text().strip() if args.key_file else os.environ["OPENAI_API_KEY"]
    out = ROOT / "tmp/video/audio"
    out.mkdir(parents=True, exist_ok=True)
    content = (ROOT / "submission/VIDEO-NARRATION.md").read_text()
    scenes = []
    for line in content.splitlines():
        if not re.match(r"^\| \d{2} \|", line):
            continue
        parts = [p.strip() for p in line.split("|")]
        number, text = parts[1], parts[3]
        scenes.append({"id": number, "text": text})
    if len(scenes) != 10:
        raise RuntimeError("Expected 10 approved narration scenes")
    for scene in scenes:
        path = out / f"scene-{scene['id']}.wav"
        meta = path.with_suffix(".json")
        if (
            path.exists()
            and meta.exists()
            and json.loads(meta.read_text()).get("text") == scene["text"]
        ):
            print(f"Reusing scene {scene['id']}", flush=True)
        else:
            body = {
                "model": "gpt-4o-mini-tts",
                "voice": "cedar",
                "input": scene["text"],
                "response_format": "wav",
                "instructions": "Speak in natural conversational English. Warm, grounded and clear, like a thoughtful founder explaining a practical product to a small group. Moderate pace, about 145 words per minute, with short pauses between sentences. Sound interested and human, without a sales announcer voice or exaggerated drama. Enunciate numbers clearly. Pronounce Pantry Relay as two normal English words. This is one continuous demo narration; do not introduce the section or add any words.",
            }
            req = urllib.request.Request(
                "https://api.openai.com/v1/audio/speech",
                data=json.dumps(body).encode(),
                headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=120) as response:
                path.write_bytes(response.read())
            meta.write_text(json.dumps(scene, indent=2))
            print(f"Generated scene {scene['id']}", flush=True)
        # Streaming WAV responses may carry a sentinel frame count. ffprobe uses actual media length.
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
                    str(path),
                ],
                text=True,
            ).strip()
        )
        scene["audio"] = str(path.relative_to(ROOT))
    (ROOT / "tmp/video/scenes.json").write_text(json.dumps(scenes, indent=2))
    print(f"Narration: {sum(x['duration'] for x in scenes):.1f} seconds", flush=True)


if __name__ == "__main__":
    main()
