# Artifact source

The editable PowerPoint and PDFs are in `output/`. `build_pitch.mjs` is the original slide source and requires the Codex presentation runtime (`@oai/artifact-tool`) and skill finalizer. Set `PANTRY_PRESENTATION_SKILL` and `PANTRY_ARTIFACT_PYTHON` for the installed runtime. To avoid overwriting a finalized presentation, supply a new `PANTRY_PITCH_FILENAME` for revisions. The program uses the actual product screenshots in `artifacts/screenshots/` and writes preview PNGs into `tmp/slides/rendered/`.

The video cards are ordinary editable HTML. The browser capture in `browser-tests/record-demo.mjs` records real product interactions. Copy these two cards to `tmp/video/card-09.html` and `tmp/video/card-10.html` when reproducing that recording.

Narration source: `submission/VIDEO-NARRATION.md`. The speech generation and caption alignment scripts read `OPENAI_API_KEY` or an explicit private `--key-file`. The key is never included in the app, generated media, source, or output metadata. `scripts/render_demo_video.py` joins the actual capture with the generated audio and burns the timed SRT captions into the video. It uses FFmpeg, Pillow and the macOS Arial font. Caption strips are rendered as images and overlaid, so libass is not required. Change the explicit font path for another platform.

The final narration is synthetic and is disclosed in the recording and its YouTube description. It does not imitate Shivam's voice. All recorded pantry data is fictional.
