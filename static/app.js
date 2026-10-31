const form = document.getElementById("editForm");
const reference = document.getElementById("reference");
const clips = document.getElementById("clips");
const music = document.getElementById("music");
const statusText = document.getElementById("status");
const createBtn = document.getElementById("createBtn");
const progress = document.getElementById("progress");
const download = document.getElementById("download");

reference.addEventListener("change", () => {
  document.getElementById("referenceName").textContent = reference.files[0]?.name || "No file selected";
});
clips.addEventListener("change", () => {
  document.getElementById("clipsName").textContent = clips.files.length
    ? `${clips.files.length} clip(s) selected` : "No clips selected";
});
music.addEventListener("change", () => {
  document.getElementById("musicName").textContent = music.files[0]?.name || "Choose music file";
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!reference.files.length || !clips.files.length) {
    statusText.textContent = "Please add a reference video and at least one clip.";
    return;
  }

  const data = new FormData();
  data.append("reference", reference.files[0]);
  [...clips.files].forEach(file => data.append("clips", file));
  if (music.files[0]) data.append("music", music.files[0]);
  data.append("aspect", form.elements.aspect.value);
  data.append("resolution", form.elements.resolution.value);

  createBtn.disabled = true;
  download.classList.add("hidden");
  progress.classList.remove("hidden");
  statusText.textContent = "Rendering your video. Keep this tab open...";
  try {
    const response = await fetch("/api/render", { method: "POST", body: data });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || "Could not create the video.");
    download.href = result.download_url;
    download.download = result.filename;
    download.classList.remove("hidden");
    statusText.textContent = "Your video is ready. Select Download MP4.";
  } catch (error) {
    statusText.textContent = `Error: ${error.message}`;
  } finally {
    createBtn.disabled = false;
    progress.classList.add("hidden");
  }
});
