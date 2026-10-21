"use strict";

const $ = (id) => document.getElementById(id);
const ui = Object.fromEntries([
  "fileInput", "pickBtn", "replaceBtn", "dropzone", "sourceEmpty", "sourceViewer",
  "sourceImage", "sourceSize", "sourceName", "cornerOverlay", "resultEmpty",
  "resultImage", "resultViewer", "resultMeta", "scanSweep", "zoomIn", "zoomOut",
  "zoomLabel", "scanBtn", "manualBtn", "manualHint", "clearCornersBtn", "ocrBtn",
  "language", "ocrText", "ocrTime", "copyBtn", "downloadTextBtn",
  "downloadImageBtn", "statusText", "toast", "themeBtn", "resetBtn"
].map((id) => [id, $(id)]));

const state = {
  file: null, sourceUrl: null, resultData: null, resultBlob: null,
  mode: "color", corners: [], detectedCorners: [], imageWidth: 0, imageHeight: 0,
  manual: false, busy: false, zoom: 1, generation: 0, controller: null,
  toastTimer: null, ocrReady: false
};
const labels = {color: "Màu", gray: "Xám", bw: "Đen trắng"};
const SVG = "http://www.w3.org/2000/svg";

function setStatus(message, busy = false) {
  ui.statusText.textContent = message;
  document.querySelector(".status-line").classList.toggle("busy", busy);
}
function toast(message, error = false) {
  ui.toast.textContent = message;
  ui.toast.classList.toggle("error", error);
  ui.toast.classList.add("show");
  clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => ui.toast.classList.remove("show"), 3300);
}
function step(index) {
  document.querySelectorAll(".step").forEach((node, i) => {
    node.classList.toggle("active", i === index);
    node.classList.toggle("done", i < index);
  });
}
function setBusy(value, message = "") {
  state.busy = value;
  ui.scanBtn.disabled = value || !state.file;
  ui.manualBtn.disabled = value || !state.file;
  ui.ocrBtn.disabled = value || !state.resultBlob;
  ui.downloadImageBtn.disabled = value || !state.resultBlob;
  ui.copyBtn.disabled = value || !ui.ocrText.value.trim();
  ui.downloadTextBtn.disabled = value || !ui.ocrText.value.trim();
  ui.zoomIn.disabled = value || !state.resultData;
  ui.zoomOut.disabled = value || !state.resultData;
  ui.scanBtn.classList.toggle("loading", value);
  ui.ocrBtn.classList.toggle("loading", value);
  if (message) setStatus(message, value);
}
function clearResult() {
  state.resultData = null;
  state.resultBlob = null;
  state.ocrReady = false;
  ui.resultImage.removeAttribute("src");
  ui.resultImage.classList.add("hidden");
  ui.resultEmpty.classList.remove("hidden");
  ui.resultMeta.textContent = "Sẵn sàng xử lý";
  ui.ocrText.value = "";
  ui.ocrTime.textContent = "";
  setZoom(1);
  setBusy(false);
}
function cancelPending() {
  state.generation += 1;
  if (state.controller) state.controller.abort();
  state.controller = null;
  state.busy = false;
}
function resetAll() {
  cancelPending();
  if (state.sourceUrl) URL.revokeObjectURL(state.sourceUrl);
  state.sourceUrl = null;
  state.file = null;
  state.corners = [];
  state.detectedCorners = [];
  state.manual = false;
  state.imageWidth = 0;
  state.imageHeight = 0;
  ui.fileInput.value = "";
  ui.sourceImage.removeAttribute("src");
  ui.sourceViewer.classList.add("hidden");
  ui.sourceViewer.classList.remove("manual");
  ui.sourceEmpty.classList.remove("hidden");
  ui.sourceSize.textContent = "Chưa có ảnh";
  ui.sourceName.textContent = "Chưa chọn tệp";
  ui.replaceBtn.classList.add("hidden");
  ui.manualHint.classList.add("hidden");
  ui.manualBtn.textContent = "Chỉnh bốn góc nếu cần";
  ui.scanBtn.innerHTML = '<svg><use href="#i-spark"/></svg> Tự căn và quét <span class="button-arrow">→</span>';
  renderCorners();
  clearResult();
  step(0);
  setStatus("Sẵn sàng. Chọn một ảnh tài liệu để bắt đầu.");
}
function fileError(message) { toast(message, true); setStatus(message); }
async function chooseFile(file) {
  if (!file) return;
  if (!["image/jpeg", "image/png"].includes(file.type)) {
    fileError("Chỉ hỗ trợ ảnh JPG hoặc PNG.");
    return;
  }
  if (file.size === 0 || file.size > 25_000_000) {
    fileError("Ảnh phải nhỏ hơn 25 MB.");
    return;
  }
  cancelPending();
  if (state.sourceUrl) URL.revokeObjectURL(state.sourceUrl);
  state.file = file;
  state.sourceUrl = URL.createObjectURL(file);
  state.imageWidth = 0;
  state.imageHeight = 0;
  state.corners = [];
  state.detectedCorners = [];
  state.manual = false;
  ui.manualHint.classList.add("hidden");
  ui.manualBtn.textContent = "Chỉnh bốn góc nếu cần";
  ui.scanBtn.innerHTML = '<svg><use href="#i-spark"/></svg> Tự căn và quét <span class="button-arrow">→</span>';
  ui.sourceImage.src = state.sourceUrl;
  ui.sourceEmpty.classList.add("hidden");
  ui.sourceViewer.classList.remove("hidden", "manual");
  ui.replaceBtn.classList.remove("hidden");
  ui.sourceName.textContent = file.name;
  ui.sourceName.title = file.name;
  ui.sourceSize.textContent = (file.size / (1024 * 1024)).toFixed(1) + " MB";
  renderCorners();
  clearResult();
  step(1);
  setStatus("Ảnh đã sẵn sàng. Nhấn Tự căn và quét để tìm bốn góc.");
  toast("Đã mở ảnh. Sẵn sàng tự căn bốn góc.");
}
function renderCorners() {
  const overlay = ui.cornerOverlay;
  overlay.replaceChildren();
  if (!state.imageWidth || !state.imageHeight) return;
  overlay.setAttribute("viewBox", `0 0 ${state.imageWidth} ${state.imageHeight}`);
  const points = state.manual ? state.corners : state.detectedCorners;
  if (points.length > 1) {
    const line = document.createElementNS(SVG, "polygon");
    line.setAttribute("points", points.map((p) => p.join(",")).join(" "));
    overlay.appendChild(line);
  }
  points.forEach(([x, y], index) => {
    const circle = document.createElementNS(SVG, "circle");
    circle.setAttribute("cx", x);
    circle.setAttribute("cy", y);
    circle.setAttribute("r", Math.max(8, Math.min(state.imageWidth, state.imageHeight) * .013));
    overlay.appendChild(circle);
    const text = document.createElementNS(SVG, "text");
    text.setAttribute("x", x);
    text.setAttribute("y", y);
    text.textContent = String(index + 1);
    overlay.appendChild(text);
  });
}
function setManual(value) {
  state.manual = value;
  state.corners = [];
  ui.sourceViewer.classList.toggle("manual", value);
  ui.manualHint.classList.toggle("hidden", !value);
  ui.manualBtn.textContent = value ? "Dùng tự căn góc" : "Chỉnh bốn góc nếu cần";
  ui.scanBtn.innerHTML = value ? '<svg><use href="#i-scan"/></svg> Quét theo góc đã chọn <span class="button-arrow">→</span>' : '<svg><use href="#i-spark"/></svg> Tự căn và quét <span class="button-arrow">→</span>';
  renderCorners();
  setStatus(value ? "Nhấp lần lượt bốn góc của trang trên ảnh gốc." : "Đã bật lại tự căn bốn góc.");
}
function setZoom(value) {
  state.zoom = Math.max(1, Math.min(2.5, Math.round(value * 10) / 10));
  ui.resultImage.style.setProperty("--zoom", String(state.zoom));
  ui.zoomLabel.textContent = Math.round(state.zoom * 100) + "%";
}
function download(data, name) {
  const link = document.createElement("a");
  link.href = data;
  link.download = name;
  document.body.append(link);
  link.click();
  link.remove();
  step(3);
}
function baseName() {
  return (state.file?.name || "tai-lieu").replace(/\.[^.]+$/, "").replace(/[\\/:*?"<>|]+/g, "_");
}
async function request(path, body, mime, controller) {
  const response = await fetch(path, {method: "POST", headers: {"Content-Type": mime}, body, signal: controller.signal});
  let payload;
  try { payload = await response.json(); } catch { throw new Error("Máy quét trả về dữ liệu không hợp lệ."); }
  if (!response.ok) throw new Error(payload.message || "Xử lý chưa hoàn tất.");
  return payload;
}
function pngDataUrlToBlob(dataUrl) {
  // Fetching a data: URL is blocked by the page's connect-src 'self' policy.
  const encoded = dataUrl.split(",", 2)[1];
  if (!dataUrl.startsWith("data:image/png;base64,") || !encoded) {
    throw new Error("Ảnh quét trả về không hợp lệ.");
  }
  const binary = atob(encoded);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
  return new Blob([bytes], {type: "image/png"});
}
async function scan() {
  if (state.busy || !state.file) return;
  if (state.manual && state.corners.length !== 4) {
    fileError("Hãy chọn đủ bốn góc trên ảnh gốc.");
    return;
  }
  const generation = ++state.generation;
  const controller = new AbortController();
  state.controller = controller;
  const query = new URLSearchParams({mode: state.mode});
  if (state.manual) query.set("corners", JSON.stringify(state.corners));
  clearResult();
  setBusy(true, "Đang tìm bốn góc và tạo bản quét…");
  try {
    const payload = await request(`/api/scan?${query}`, state.file, state.file.type, controller);
    if (generation !== state.generation) return;
    state.resultData = payload.image;
    state.resultBlob = pngDataUrlToBlob(payload.image);
    ui.resultImage.src = payload.image;
    ui.resultImage.classList.remove("hidden");
    ui.resultEmpty.classList.add("hidden");
    ui.resultMeta.textContent = `${labels[state.mode]} · ${payload.method === "manual" ? "góc đã chọn" : "tự căn góc"}`;
    state.detectedCorners = payload.corners || [];
    state.imageWidth = payload.width;
    state.imageHeight = payload.height;
    renderCorners();
    setBusy(false, payload.message + ". Có thể nhận dạng chữ hoặc tải ảnh PNG.");
    step(2);
    ui.scanSweep.classList.remove("hidden");
    ui.scanSweep.style.animation = "none";
    void ui.scanSweep.offsetWidth;
    ui.scanSweep.style.animation = "";
    setTimeout(() => ui.scanSweep.classList.add("hidden"), 1100);
    toast("Đã tạo bản quét và tự căn bốn góc.");
  } catch (error) {
    if (generation !== state.generation || error.name === "AbortError") return;
    setBusy(false, error.message);
    toast(error.message, true);
    if (error.message.includes("bốn góc") || error.message.includes("viền")) {
      ui.manualBtn.focus();
    }
  } finally {
    if (generation === state.generation) state.controller = null;
  }
}
async function ocr() {
  if (state.busy || !state.resultBlob) return;
  const generation = ++state.generation;
  const controller = new AbortController();
  state.controller = controller;
  ui.ocrText.value = "";
  ui.ocrTime.textContent = "";
  setBusy(true, "Đang nhận dạng chữ. Quá trình này có thể mất vài giây…");
  try {
    const language = encodeURIComponent(ui.language.value);
    const payload = await request(`/api/ocr?lang=${language}`, state.resultBlob, "image/png", controller);
    if (generation !== state.generation) return;
    ui.ocrText.value = payload.text || "";
    ui.ocrTime.textContent = payload.elapsed_seconds ? `${payload.elapsed_seconds} giây` : "";
    state.ocrReady = Boolean(payload.text?.trim());
    setBusy(false, payload.message);
    if (state.ocrReady) { step(3); toast("Đã nhận dạng chữ. Hãy kiểm tra văn bản trước khi sử dụng."); }
    else toast(payload.message, true);
  } catch (error) {
    if (generation !== state.generation || error.name === "AbortError") return;
    setBusy(false, error.message);
    toast(error.message, true);
  } finally {
    if (generation === state.generation) state.controller = null;
  }
}

ui.pickBtn.addEventListener("click", (event) => {event.stopPropagation(); ui.fileInput.click();});
ui.replaceBtn.addEventListener("click", () => ui.fileInput.click());
ui.fileInput.addEventListener("change", () => chooseFile(ui.fileInput.files?.[0]));
ui.dropzone.addEventListener("click", (event) => {if (!state.file && !event.target.closest("button")) ui.fileInput.click();});
["dragenter", "dragover"].forEach((name) => ui.dropzone.addEventListener(name, (event) => {event.preventDefault(); ui.dropzone.classList.add("dragover");}));
["dragleave", "drop"].forEach((name) => ui.dropzone.addEventListener(name, (event) => {event.preventDefault(); ui.dropzone.classList.remove("dragover");}));
ui.dropzone.addEventListener("drop", (event) => chooseFile(event.dataTransfer.files?.[0]));
document.addEventListener("paste", (event) => {const file = [...(event.clipboardData?.files || [])].find((item) => item.type.startsWith("image/")); if (file && event.target !== ui.ocrText) chooseFile(file);});
ui.sourceImage.addEventListener("load", () => {state.imageWidth = ui.sourceImage.naturalWidth; state.imageHeight = ui.sourceImage.naturalHeight; renderCorners();});
ui.cornerOverlay.addEventListener("click", (event) => {
  if (!state.manual || state.busy || !state.imageWidth) return;
  if (state.corners.length === 4) state.corners = [];
  const rect = ui.cornerOverlay.getBoundingClientRect();
  const x = Math.max(0, Math.min(state.imageWidth - 1, Math.round((event.clientX - rect.left) / rect.width * state.imageWidth)));
  const y = Math.max(0, Math.min(state.imageHeight - 1, Math.round((event.clientY - rect.top) / rect.height * state.imageHeight)));
  state.corners.push([x, y]);
  renderCorners();
  setStatus(state.corners.length === 4 ? "Đã chọn đủ bốn góc. Nhấn Quét theo góc đã chọn." : `Đã chọn ${state.corners.length}/4 góc.`);
});
document.querySelectorAll(".mode-button").forEach((button) => button.addEventListener("click", () => {
  if (state.busy) return;
  state.mode = button.dataset.mode;
  document.querySelectorAll(".mode-button").forEach((item) => {const selected = item === button; item.classList.toggle("selected", selected); item.setAttribute("aria-pressed", String(selected));});
  if (state.resultData) {clearResult(); state.detectedCorners = []; renderCorners(); step(1); setStatus("Đã đổi chế độ ảnh. Nhấn Tự căn và quét để cập nhật bản quét.");}
}));
ui.manualBtn.addEventListener("click", () => setManual(!state.manual));
ui.clearCornersBtn.addEventListener("click", () => {state.corners = []; renderCorners(); setStatus("Hãy chọn lại bốn góc trên ảnh gốc.");});
ui.scanBtn.addEventListener("click", scan);
ui.ocrBtn.addEventListener("click", ocr);
ui.language.addEventListener("change", () => {if (ui.ocrText.value) {ui.ocrText.value = ""; ui.ocrTime.textContent = ""; state.ocrReady = false; ui.copyBtn.disabled = true; ui.downloadTextBtn.disabled = true; if (state.resultBlob) step(2); setStatus("Đã đổi ngôn ngữ. Nhấn Nhận dạng chữ để cập nhật văn bản.");}});
ui.zoomIn.addEventListener("click", () => setZoom(state.zoom + .2));
ui.zoomOut.addEventListener("click", () => setZoom(state.zoom - .2));
ui.resultImage.addEventListener("dblclick", () => setZoom(1));
ui.downloadImageBtn.addEventListener("click", () => {if (state.resultBlob) {const url = URL.createObjectURL(state.resultBlob); download(url, `${baseName()}_ban-quet.png`); setTimeout(() => URL.revokeObjectURL(url), 30000); toast("Đã tải ảnh PNG.");}});
ui.ocrText.addEventListener("input", () => {const ready = Boolean(ui.ocrText.value.trim()); ui.copyBtn.disabled = !ready; ui.downloadTextBtn.disabled = !ready;});
ui.copyBtn.addEventListener("click", async () => {try {await navigator.clipboard.writeText(ui.ocrText.value); toast("Đã sao chép văn bản.");} catch {toast("Không thể sao chép. Hãy chọn và sao chép văn bản thủ công.", true);}});
ui.downloadTextBtn.addEventListener("click", () => {const url = URL.createObjectURL(new Blob([ui.ocrText.value], {type: "text/plain;charset=utf-8"})); download(url, `${baseName()}_van-ban.txt`); setTimeout(() => URL.revokeObjectURL(url), 30000); toast("Đã tải văn bản UTF-8.");});
ui.resetBtn.addEventListener("click", resetAll);
ui.themeBtn.addEventListener("click", () => {const dark = document.documentElement.dataset.theme !== "dark"; document.documentElement.dataset.theme = dark ? "dark" : "light"; ui.themeBtn.innerHTML = dark ? '<svg><use href="#i-sun"/></svg>' : '<svg><use href="#i-moon"/></svg>'; try {localStorage.setItem("tgmt-theme", dark ? "dark" : "light");} catch { /* Theme remains usable without storage. */ }});
document.addEventListener("keydown", (event) => {if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "o") {event.preventDefault(); ui.fileInput.click();} else if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {event.preventDefault(); scan();} else if (event.key === "Escape" && state.busy) {cancelPending(); setBusy(false, "Đã hủy thao tác đang chờ."); toast("Đã hủy thao tác.");}});
try {if (localStorage.getItem("tgmt-theme") === "dark") {document.documentElement.dataset.theme = "dark"; ui.themeBtn.innerHTML = '<svg><use href="#i-sun"/></svg>';}} catch { /* Default theme is light. */ }
resetAll();
