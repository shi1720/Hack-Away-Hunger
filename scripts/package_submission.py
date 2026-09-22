#!/usr/bin/env python3
"""Build the public Devpost attachment from an explicit, reproducible allowlist.

No credentials, environment variables, directory walks or external services are read.
Run from any directory: python3 /path/to/repository/scripts/package_submission.py
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "Pantry-Relay-Submission-Kit.zip"
LIMIT_BYTES = 35_000_000
FIXED_ZIP_TIME = (2026, 9, 22, 0, 0, 0)

# Archive names are fixed and relative. Internal eligibility, outreach-to-organizer
# drafts, credentials, database contents and logs are deliberately not in this list.
FILES = (
    ("output/Pantry-Relay-Demo.mp4", "media/Pantry-Relay-Demo.mp4"),
    ("output/Pantry-Relay-Captions.srt", "media/Pantry-Relay-Captions.srt"),
    ("output/Pantry-Relay-Pitch.pdf", "presentation/Pantry-Relay-Pitch.pdf"),
    ("output/Pantry-Relay-Pitch.pptx", "presentation/Pantry-Relay-Pitch.pptx"),
    ("output/Pantry-Relay-Brief.pdf", "presentation/Pantry-Relay-Brief.pdf"),
    ("submission/VIDEO-NARRATION.md", "docs/VIDEO-NARRATION.md"),
    ("submission/TESTING-INSTRUCTIONS.md", "docs/TESTING-INSTRUCTIONS.md"),
    ("docs/BUSINESS-MODEL.md", "docs/BUSINESS-MODEL.md"),
    ("docs/PILOT-PLAN.md", "docs/PILOT-PLAN.md"),
    ("docs/VERIFICATION.md", "docs/VERIFICATION.md"),
)

JUDGE_README = """# Pantry Relay: judge submission kit

Project lead: Shivam Gupta
Event: Hack Away Hunger 2026

Live application: https://pantryrelay.web.app
Video walkthrough and pitch: https://pantryrelay.web.app/demo
Public YouTube demo: https://www.youtube.com/watch?v=dSc6ToJ2z6Y
Submitted project: https://devpost.com/software/pantry-relay
Source code: https://github.com/shi1720/Hack-Away-Hunger

Pantry Relay helps an approved pantry network fill upcoming category gaps with
food another pantry can spare. It protects the sender's own reserve, explains
possible transfers, and records what the receiver actually accepted.

## Start here

1. Watch media/Pantry-Relay-Demo.mp4, approximately 2 minutes 51 seconds.
   Matching captions are in media/Pantry-Relay-Captions.srt.
2. Open the live application and select Explore the live demo. No shared password
   or API key is needed. Registration also creates a separate empty network.
3. Follow docs/TESTING-INSTRUCTIONS.md for the exact walkthrough and expected
   results, account and driver tests, recovery paths and automated checks.
4. Read presentation/Pantry-Relay-Pitch.pdf or Pantry-Relay-Brief.pdf for the
   problem, product and pilot. An editable PowerPoint version is included.

The central demonstration reserves and dispatches 120 pounds, accepts 112 pounds,
records an 8-pound exception and leaves the remaining need visible. The app counts
accepted pounds, not unverified meals, people fed or avoided waste.

## Evidence and plans

docs/VERIFICATION.md records completed backend, browser, deployment and media
checks with their limits. docs/BUSINESS-MODEL.md explains the proposed $149 monthly
network price and cost assumptions. docs/PILOT-PLAN.md describes a proposed
six-week supervised pilot. Pricing, willingness to pay and field impact remain
unvalidated. This is working software for a supervised pilot, not a certified
production service or a claim of nonprofit adoption.

## Demonstration and credit

All pantry names, food records and operational results shown in the demonstration
are fictional sample data. No household records are required or included.
The video uses synthetic narration, not a recording of Shivam's voice. Shivam
directed the project, priorities and quality requirements; AI tools assisted
extensively with research, implementation, testing and documentation.

The archive contains selected public presentation and evaluation materials.
Application source and its MIT license are in the linked repository. No private
credentials, account databases or internal eligibility correspondence are included.
SHA256SUMS.txt lists the contents' integrity hashes.
"""


def zip_entry(name: str, contents: bytes) -> tuple[ZipInfo, bytes]:
    info = ZipInfo(name, date_time=FIXED_ZIP_TIME)
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    info.compress_type = ZIP_DEFLATED
    return info, contents


def main() -> None:
    payloads = {"README.md": JUDGE_README.encode("utf-8")}
    source_states: dict[Path, tuple[int, int]] = {}
    for source_name, archive_name in FILES:
        source = (ROOT / source_name).resolve(strict=True)
        if not source.is_relative_to(ROOT) or not source.is_file():
            raise ValueError(f"Expected a repository file: {source_name}")
        before = source.stat()
        contents = source.read_bytes()
        after = source.stat()
        state = (after.st_mtime_ns, after.st_size)
        if (before.st_mtime_ns, before.st_size) != state or len(contents) != after.st_size:
            raise RuntimeError(f"Source changed while packaging: {source_name}")
        source_states[source] = state
        if archive_name in payloads:
            raise ValueError(f"Duplicate archive entry: {archive_name}")
        payloads[archive_name] = contents

    manifest = "".join(
        f"{hashlib.sha256(contents).hexdigest()}  {name}\n"
        for name, contents in sorted(payloads.items())
    )
    payloads["SHA256SUMS.txt"] = manifest.encode("utf-8")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_suffix(".zip.tmp")
    try:
        with ZipFile(temporary, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
            for name, contents in sorted(payloads.items()):
                info, contents = zip_entry(name, contents)
                archive.writestr(info, contents, compress_type=ZIP_DEFLATED, compresslevel=9)
        if temporary.stat().st_size >= LIMIT_BYTES:
            raise ValueError("Submission archive exceeds the strict 35,000,000-byte limit")
        for source, state in source_states.items():
            current = source.stat()
            if (current.st_mtime_ns, current.st_size) != state:
                raise RuntimeError(f"Source changed before archive completion: {source.name}")
        with ZipFile(temporary) as archive:
            if archive.testzip() is not None:
                raise RuntimeError("Archive integrity check failed")
            if set(archive.namelist()) != set(payloads):
                raise RuntimeError("Archive contents differ from the allowlist")
        temporary.replace(OUTPUT)
    finally:
        temporary.unlink(missing_ok=True)
    archive_hash = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    print(f"Created {OUTPUT}")
    print(f"{OUTPUT.stat().st_size:,} bytes; {len(payloads)} entries; below 35 MB")
    print(f"SHA-256: {archive_hash}")


if __name__ == "__main__":
    main()
