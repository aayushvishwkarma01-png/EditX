from pathlib import Path
from uuid import uuid4
import shutil
import subprocess
import tempfile

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent
UPLOADS = BASE / "uploads"
OUTPUTS = BASE / "outputs"
STATIC = BASE / "static"
for folder in (UPLOADS, OUTPUTS, STATIC):
    folder.mkdir(exist_ok=True)

app = FastAPI(title="EditX")
app.mount("/static", StaticFiles(directory=STATIC), name="static")

@app.get("/")
def home():
    return FileResponse(STATIC / "index.html")

def save_upload(upload: UploadFile, destination: Path):
    suffix = Path(upload.filename or "").suffix.lower()
    allowed = {".mp4", ".mov", ".m4v", ".webm", ".mp3", ".wav", ".m4a", ".aac"}
    if suffix not in allowed:
        raise HTTPException(400, f"Unsupported file type: {suffix}")
    with destination.open("wb") as out:
        shutil.copyfileobj(upload.file, out)

@app.post("/api/render")
async def render_video(
    reference: UploadFile = File(...),
    clips: list[UploadFile] = File(...),
    music: UploadFile | None = File(None),
    aspect: str = Form("9:16"),
    resolution: str = Form("720"),
):
    if not clips:
        raise HTTPException(400, "Please upload at least one video clip.")
    if aspect not in {"9:16", "16:9", "1:1"}:
        raise HTTPException(400, "Invalid aspect ratio.")
    if resolution not in {"720", "1080"}:
        raise HTTPException(400, "Invalid resolution.")

    job_id = uuid4().hex
    work = Path(tempfile.mkdtemp(prefix=f"editx_{job_id}_", dir=UPLOADS))
    output = OUTPUTS / f"EditX_{job_id}.mp4"

    try:
        # Keep the reference in the job folder for the reference-based workflow.
        reference_path = work / f"reference{Path(reference.filename or '.mp4').suffix.lower()}"
        save_upload(reference, reference_path)

        clip_paths = []
        for index, clip in enumerate(clips):
            clip_path = work / f"clip_{index:03d}{Path(clip.filename or '.mp4').suffix.lower()}"
            save_upload(clip, clip_path)
            clip_paths.append(clip_path)

        music_path = None
        if music and music.filename:
            music_path = work / f"music{Path(music.filename).suffix.lower()}"
            save_upload(music, music_path)

        if aspect == "9:16":
            width, height = int(resolution) * 9 // 16, int(resolution)
            width -= width % 2
        elif aspect == "16:9":
            width, height = int(resolution), int(resolution) * 9 // 16
            height -= height % 2
        else:
            width = height = int(resolution)

        # Normalize clips to the chosen canvas, then concatenate in upload order.
        inputs = []
        for p in clip_paths:
            inputs += ["-i", str(p)]

        filters = []
        for i in range(len(clip_paths)):
            filters.append(
                f"[{i}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
                f"setsar=1,fps=30,format=yuv420p[v{i}]"
            )
            filters.append(f"[{i}:a]aresample=async=1:first_pts=0[a{i}]")
        concat_inputs = "".join(f"[v{i}][a{i}]" for i in range(len(clip_paths)))
        filters.append(f"{concat_inputs}concat=n={len(clip_paths)}:v=1:a=1[vout][aout]")

        cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filters),
               "-map", "[vout]", "-map", "[aout]"]

        if music_path:
            # Mix optional music with clip audio; loop music if it is shorter.
            cmd += ["-stream_loop", "-1", "-i", str(music_path)]
            music_input_index = len(clip_paths)
            cmd += ["-filter_complex",
                    f"[{music_input_index}:a]volume=0.22[music];[aout][music]amix=inputs=2:duration=first:dropout_transition=2[a_final]",
                    "-map", "[vout]", "-map", "[a_final]"]

        cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(output)]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        if result.returncode != 0 or not output.exists():
            detail = (result.stderr or "FFmpeg could not render the video.")[-1800:]
            raise HTTPException(500, detail)

        return {"download_url": f"/api/download/{output.name}", "filename": output.name}
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "Rendering took too long. Try fewer or shorter clips.")
    finally:
        shutil.rmtree(work, ignore_errors=True)

@app.get("/api/download/{filename}")
def download_video(filename: str):
    if Path(filename).name != filename or not filename.endswith(".mp4"):
        raise HTTPException(400, "Invalid filename.")
    path = OUTPUTS / filename
    if not path.exists():
        raise HTTPException(404, "Video not found. Please render again.")
    return FileResponse(path, media_type="video/mp4", filename=filename)
