/* ========== Main UI script (video stream + detectors + sleep UI) ========== */

console.log("UI Loaded Successfully!");

const API_BASE = "http://127.0.0.1:8000";
const VIDEO_STREAM_URL = API_BASE + "/video-stream";
const POLL_INTERVAL_MS = 800;

let pollTimer = null;
document.getElementById("btnStartMain").addEventListener("click", async () => { try { const res = await fetch(API_BASE + "/start-main", { method: "POST" }); const data = await res.json(); console.log("start-main:", data); if (data.status === "started" || data.status === "already_running") { attachVideoStream(); startPollingStats(); } } catch (err) { console.error(err); alert("Failed to start main: " + err); } });
/* ---------------------------
   Video stream attach
   --------------------------- */
function attachVideoStream() {
    const img = document.getElementById("videoStream");
    const fallback = document.querySelector(".video-fallback");
    if (!img) return;

    img.src = VIDEO_STREAM_URL + "?t=" + Date.now();

    img.onload = () => { if (fallback) fallback.style.display = "none"; };
    img.onerror = () => {
        if (fallback) {
            fallback.style.display = "block";
            fallback.innerText = "Camera stream not available.";
        }
    };
}

/* ---------------------------
   Polling stubs for volume/brightness
   (kept as you had; adjust if endpoints differ)
   --------------------------- */
function startPollingStats() {
    if (pollTimer) return;
    pollTimer = setInterval(() => {
        fetchVolume();
        fetchBrightness();
    }, POLL_INTERVAL_MS);
}

async function fetchVolume() {
    try {
        const r = await fetch(API_BASE + "/sys/volume");
        if (!r.ok) throw 0;
        const j = await r.json();
        updateVolume(j.percent);
    } catch {
        updateVolume(null);
    }
}

async function fetchBrightness() {
    try {
        const r = await fetch(API_BASE + "/sys/brightness");
        if (!r.ok) throw 0;
        const j = await r.json();
        updateBrightness(j.percent);
    } catch {
        updateBrightness(null);
    }
}

function updateVolume(v) {
    const el = document.getElementById("volumeBar");
    if (!el) return;
    el.style.width = (v == null) ? "0%" : `${v}%`;
}
function updateBrightness(v) {
    const el = document.getElementById("brightBar");
    if (!el) return;
    el.style.width = (v == null) ? "0%" : `${v}%`;
}

/* ============================
   SLEEP UI: audio + timer
   ============================ */

const audio = document.getElementById("sleepui-audio"); // <audio> element
const toggleImg = document.getElementById("sleepui-toggle-img");
const switchEl = document.getElementById("sleepui-switch");
const timerLabel = document.getElementById("sleepui-timer");
const exitBtn = document.getElementById("sleepui-exit-btn");

// state
let sleepActive = false;
let countdownSec = 60 * 60; // 60 minutes in seconds
let timerInterval = null;

// format mm:ss
function sleepui_formatTime(sec) {
    const m = Math.floor(sec / 60).toString().padStart(2, "0");
    const s = (sec % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
}

function sleepui_updateDisplay() {
    if (timerLabel) timerLabel.textContent = sleepui_formatTime(countdownSec);
}

// start timer (if already running do nothing)
function sleepui_startTimer() {
    if (timerInterval) return;

    // play audio (must be user-triggered - toggling image counts as user interaction)
    try {
        if (audio) {
            audio.currentTime = 0;
            // ensure loop in case song shorter than timer
            audio.loop = true;
            const playPromise = audio.play();
            if (playPromise && playPromise.catch) {
                playPromise.catch(e => {
                    console.warn("Audio play prevented:", e);
                });
            }
        }
    } catch (e) {
        console.warn("Audio start error:", e);
    }

    timerInterval = setInterval(() => {
        countdownSec--;
        if (countdownSec <= 0) {
            clearInterval(timerInterval);
            timerInterval = null;
            countdownSec = 0;
            sleepui_updateDisplay();

            // timer finished -> trigger shutdown endpoint
            fetch(`${API_BASE}/shutdown`, { method: "POST" })
                .catch((err) => console.error("Shutdown request failed:", err));
            // as fallback try to close window (if running in kiosk/electron)
            try { window.close(); } catch (e) {}
            return;
        }
        sleepui_updateDisplay();
    }, 1000);
}

// stop timer + reset
function sleepui_stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
    // reset countdown to 60 minutes
    countdownSec = 60 * 60;
    sleepui_updateDisplay();

    // stop audio and reset
    if (audio) {
        try {
            audio.pause();
            audio.currentTime = 0;
        } catch (e) { console.warn("audio stop error", e); }
    }
}

// Toggle handler for image version
if (toggleImg) {
    toggleImg.addEventListener("click", () => {
        sleepActive = !sleepActive;

        if (sleepActive) {
            toggleImg.src = "assets/on.png";
            sleepui_startTimer();
        } else {
            toggleImg.src = "assets/off.png";
            sleepui_stopTimer();
        }
    });
}

// Toggle handler for animated switch version
if (switchEl) {
    switchEl.addEventListener("click", () => {
        sleepActive = !sleepActive;
        switchEl.classList.toggle("sleepui-active");
        if (sleepActive) sleepui_startTimer();
        else sleepui_stopTimer();
    });
}

// Exit button behavior
if (exitBtn) {
    exitBtn.addEventListener("click", () => {
        // try to close window (may work in electron/kiosk or when opened via window.open)
        try { window.close(); } catch (e) { /* ignore */ }

        // try backend exit endpoint
        fetch(`${API_BASE}/app/exit`, { method: "POST" }).catch(e => {
            console.warn("app/exit failed:", e);
        });

        // for Electron (if available)
        try {
            if (window && window.require) {
                const { ipcRenderer } = window.require("electron");
                if (ipcRenderer) ipcRenderer.send("app-exit");
            }
        } catch (e) { /* ignore */ }
    });
}

// initialize UI values
sleepui_updateDisplay();

/* --------------------------
   Auto-start camera & polls
   -------------------------- */
window.addEventListener("load", () => {
    attachVideoStream();
    startPollingStats();
});
// ===========================================
// TIMER UI HANDLER
// ===========================================

let timerRemain = null;        // in seconds
let sisatimer = null;

// Format mm:ss
function ui_format(sec) {
    const m = Math.floor(sec / 60).toString().padStart(2, "0");
    const s = (sec % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
}

// Update display
function ui_update() {
    const el = document.getElementById("ui-timer");

    if (timerRemain === null || timerRemain === "") {
        el.textContent = "Set Timer";
        return;
    }

    el.textContent = ui_format(timerRemain);
}

// Start counting down
function ui_startLocalCountdown() {
    if (sisatimer) clearInterval(sisatimer);

    timerInterval = setInterval(() => {
        if (timerRemain > 0) {
            timerRemain--;
            ui_update();
        }
    }, 1000);
}

// ===========================================
// CLICK → CALL BACKEND
// ===========================================
const timerBtn = document.getElementById("timerui-toggle-img");

if (timerBtn) {
    timerBtn.onclick = async () => {
        try {
            // CALL ENDPOINT
            const res = await fetch("http://127.0.0.1:8000/voice-runned", {
                method: "POST"
            });

            const data = await res.json();   // expecting number or ""
            timerRemain = data.seconds;      // backend returns { seconds: X }

            // If still "", show "Set Timer"
            if (timerRemain === "" || timerRemain === null) {
                timerRemain = null;
                ui_update();
                return;
            }

            // Convert to number
            timerRemain = Number(timerRemain);

            ui_update();
            ui_startLocalCountdown();

        } catch (err) {
            console.log("Timer UI error:", err);
        }
    };
}

// Initialize UI text
ui_update();
function updateClock() {
    const options = {
        timeZone: "Asia/Jakarta",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false
    };

    const now = new Date().toLocaleTimeString("en-GB", options);
    const clock = document.getElementById("digital-clock");

    if (clock.innerText !== now) {
        clock.classList.remove("flip");
        void clock.offsetWidth; // restart animation
        clock.classList.add("flip");
    }

    clock.innerText = now;
}

setInterval(updateClock, 1000);
updateClock();
