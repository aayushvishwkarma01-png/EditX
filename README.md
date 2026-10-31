# EditX — AI Video Creator (starter version)

## What works in this version
- Upload a reference video (stored during render as the style reference input).
- Upload one or more video clips.
- Optionally add background music.
- Choose 9:16, 16:9, or 1:1 output and 720p/1080p.
- Render an MP4 and download it with one click.
- Responsive browser interface with `Product: AyushVsk` in the bottom-right footer.

## Important limitation
This is the first working editing foundation, not yet automatic AI style replication. The reference video is accepted and retained for the render workflow, but this starter does not yet analyze its cuts, transitions, text, or generate new footage. Those AI features need to be added in a later phase and may require third-party services with free-tier limits.

## Requirements
- Python 3.10+
- FFmpeg installed and available on PATH

## Run on Windows
1. Install Python and FFmpeg.
2. Open this folder in VS Code.
3. Open Terminal in VS Code.
4. Run:
   `py -m venv .venv`
   ` .venv\Scripts\activate`
   `py -m pip install -r requirements.txt`
   `py -m uvicorn main:app --reload`
5. Open http://127.0.0.1:8000

## Notes
- This local starter saves rendered files in `outputs/`.
- Do not upload private or sensitive footage to a public server.
- Before public deployment, add authentication, upload size limits, job cleanup, storage limits, and a production render queue.
