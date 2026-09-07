const TRACE_LEN = 280;
const SAMPLE_DT = 0.008;

const state = {
  page: "home",
  t: 0,
  frames: 0,
  hr: 72,
  rr: 16,
  spo2: 98,
  temp: 36.5,
  nibp: 118,
  alarm: false,
  status: "Waiting for MCU / Python host…",
  ecg: Array(TRACE_LEN).fill(128),
  resp: Array(TRACE_LEN).fill(128),
  spo2w: Array(TRACE_LEN).fill(128),
};

const $ = (id) => document.getElementById(id);

function gauss(x, center, width, height) {
  return height * Math.exp(-((x - center) ** 2) / (2 * width * width));
}

function ecgSample(t, heartRate) {
  const hr = Math.max(40, Math.min(180, heartRate));
  const period = 60 / hr;
  const x = (t % period) / period;
  const y =
    gauss(x, 0.18, 0.025, 12) -
    gauss(x, 0.34, 0.012, 18) +
    gauss(x, 0.4, 0.01, 95) -
    gauss(x, 0.45, 0.014, 28) +
    gauss(x, 0.62, 0.045, 22);
  return Math.max(0, Math.min(255, Math.round(128 + y)));
}

function respSample(t, respRate) {
  const rr = Math.max(8, Math.min(40, respRate));
  const y = 40 * Math.sin(2 * Math.PI * t * (rr / 60));
  return Math.max(0, Math.min(255, Math.round(128 + y)));
}

function spo2Sample(t, heartRate) {
  const hr = Math.max(40, Math.min(180, heartRate));
  const period = 60 / hr;
  const x = (t % period) / period;
  const rise = Math.exp(-((x - 0.22) ** 2) / 0.004) * 70;
  const notch = Math.exp(-((x - 0.38) ** 2) / 0.003) * 18;
  return Math.max(0, Math.min(255, Math.round(128 + rise - notch)));
}

function push(arr, value) {
  arr.push(value);
  if (arr.length > TRACE_LEN) arr.shift();
}

function drawWave(canvas, samples, color) {
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  if (samples.length < 2) return;
  ctx.beginPath();
  ctx.lineWidth = 2;
  ctx.strokeStyle = color;
  ctx.lineJoin = "round";
  samples.forEach((value, i) => {
    const x = (i / (samples.length - 1)) * (w - 2);
    const y = h - 4 - (Math.max(0, Math.min(255, value)) / 255) * (h - 8);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
}

function setPage(name) {
  state.page = name;
  ["home", "dash", "system"].forEach((key) => {
    $(`page-${key}`).classList.toggle("hidden", key !== name);
  });
  document.querySelectorAll("[data-go]").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.go === name);
  });
  window.scrollTo({ top: 0, behavior: "auto" });
  updateScrollButton();
}

function updateVitals(now) {
  const t = now / 1000;
  state.hr = Math.round(72 + 8 * Math.sin(t / 1.6));
  state.spo2 = Math.round(98 + 1.2 * Math.sin(t / 2.4));
  state.temp = (365 + 6 * Math.sin(t / 7)) / 10;
  state.nibp = Math.round(118 + 6 * Math.sin(t / 3.1));
  state.rr = Math.round(16 + 2 * Math.sin(t / 5));
  state.alarm = state.hr >= 78;
  state.status = state.alarm ? "HR HIGH  —  MONITOR" : "ALL VITALS NORMAL";
  $("val-hr").textContent = String(state.hr);
  $("val-rr").textContent = String(state.rr);
  $("val-spo2").textContent = String(state.spo2);
  $("val-temp").textContent = state.temp.toFixed(1);
  $("val-nibp").textContent = String(state.nibp);
  $("val-status").textContent = state.status;
  $("val-detail").textContent =
    `TX ${String(state.frames).padStart(5, "0")}   PAGE ${state.page === "system" ? 1 : 0}   WEB HOST`;
  $("status-card").classList.toggle("alarm", state.alarm);
  $("clock").textContent = new Date().toLocaleTimeString("en-GB");
}

function tick(now) {
  if (state.page !== "home") {
    const samples = 4;
    for (let i = 0; i < samples; i += 1) {
      state.t += SAMPLE_DT;
      push(state.ecg, ecgSample(state.t, state.hr));
      push(state.resp, respSample(state.t, state.rr));
      push(state.spo2w, spo2Sample(state.t, state.hr));
    }
    state.frames += 1;
    updateVitals(now);
    drawWave($("wave-ecg"), state.ecg, "#00dc78");
    drawWave($("wave-resp"), state.resp, "#f0dc50");
    drawWave($("wave-spo2"), state.spo2w, "#00d2e6");
  }
  requestAnimationFrame(tick);
}

function resizeCanvases() {
  ["wave-ecg", "wave-resp", "wave-spo2"].forEach((id) => {
    const canvas = $(id);
    const box = canvas.getBoundingClientRect();
    const nextW = Math.max(280, Math.round(box.width || 860));
    const nextH = Math.max(96, Math.round(box.height || 128));
    if (canvas.width !== nextW || canvas.height !== nextH) {
      canvas.width = nextW;
      canvas.height = nextH;
    }
  });
}

function pageOverflows() {
  return document.documentElement.scrollHeight > window.innerHeight + 24;
}

function nearBottom() {
  const leftover =
    document.documentElement.scrollHeight - window.innerHeight - window.scrollY;
  return leftover < 48;
}

function updateScrollButton() {
  const btn = $("scroll-more");
  btn.hidden = state.page === "home";
  btn.classList.toggle("up", pageOverflows() && nearBottom());
  const goingUp = btn.classList.contains("up");
  btn.setAttribute("aria-label", goingUp ? "Back to top" : "Show more");
  btn.querySelector("small").textContent = goingUp ? "Top" : "More";
}

document.querySelectorAll("[data-go]").forEach((btn) => {
  btn.addEventListener("click", () => setPage(btn.dataset.go));
});
$("btn-start").addEventListener("click", () => setPage("dash"));
$("scroll-more").addEventListener("click", () => {
  if (nearBottom()) {
    window.scrollTo({ top: 0, behavior: "smooth" });
    return;
  }
  window.scrollTo({
    top: document.documentElement.scrollHeight,
    behavior: "smooth",
  });
});
window.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && state.page === "home") setPage("dash");
  if (event.key === "Escape") setPage("home");
});
window.addEventListener("resize", () => {
  resizeCanvases();
  updateScrollButton();
});
window.addEventListener("scroll", updateScrollButton, { passive: true });

setPage("home");
resizeCanvases();
updateScrollButton();
requestAnimationFrame(tick);
