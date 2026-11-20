(() => {
  "use strict";

  const canvas = document.getElementById("scene-canvas");
  const hudRoot = document.getElementById("hud-root");
  const flamesEl = document.getElementById("hud-flames");
  const nightLabelEl = document.getElementById("hud-night-label");
  const timerEl = document.getElementById("hud-timer");
  const windBadgeEl = document.getElementById("hud-wind-badge");
  const lanternsEl = document.getElementById("hud-lanterns");
  const scoreEl = document.getElementById("hud-score");
  const fpsEl = document.getElementById("hud-fps");
  const moteSlotsEl = document.getElementById("hud-mote-slots");
  const moteTextEl = document.getElementById("hud-mote-text");
  const dashEl = document.getElementById("hud-dash");
  const pulseEl = document.getElementById("hud-pulse");
  const charmEl = document.getElementById("hud-charm");
  const promptEl = document.getElementById("context-prompt");
  const arrowEl = document.getElementById("offscreen-arrow");

  const screenMenu = document.getElementById("screen-menu");
  const screenIntro = document.getElementById("screen-intro");
  const screenPause = document.getElementById("screen-pause");
  const screenSettings = document.getElementById("screen-settings");
  const screenResult = document.getElementById("screen-result");

  const introBadge = document.getElementById("intro-night-badge");
  const introTitle = document.getElementById("intro-title");
  const introQuote = document.getElementById("intro-quote");
  const resultBadge = document.getElementById("result-badge");
  const resultTitle = document.getElementById("result-title");
  const resultDesc = document.getElementById("result-desc");
  const resultScore = document.getElementById("result-score");
  const btnNextNight = document.getElementById("btn-next-night");

  const volInput = document.getElementById("input-volume");
  const sensInput = document.getElementById("input-sens");
  const volLabel = document.getElementById("lbl-volume");
  const sensLabel = document.getElementById("lbl-sens");

  // Build 10 firefly HUD slots
  const slotEls = [];
  for (let i = 0; i < 10; i++) {
    const el = document.createElement("div");
    el.className = "mote-slot";
    moteSlotsEl.appendChild(el);
    slotEls.push(el);
  }

  // Persistent settings
  const SETTINGS_KEY = "dao_den_long_settings_v1";
  const settings = { volume: 0.7, mouseSens: 1.0 };
  try {
    const saved = JSON.parse(localStorage.getItem(SETTINGS_KEY) || "{}");
    if (typeof saved.volume === "number") settings.volume = Math.max(0, Math.min(1, saved.volume));
    if (typeof saved.mouseSens === "number") settings.mouseSens = Math.max(0.2, Math.min(2.5, saved.mouseSens));
  } catch (_) {}
  volInput.value = String(Math.round(settings.volume * 100));
  sensInput.value = String(Math.round(settings.mouseSens * 10));
  volLabel.textContent = `${volInput.value}%`;
  sensLabel.textContent = `${settings.mouseSens.toFixed(1)}x`;

  let settingsReturnTo = "menu";
  function saveSettings() {
    settings.volume = Number(volInput.value) / 100;
    settings.mouseSens = Number(sensInput.value) / 10;
    volLabel.textContent = `${volInput.value}%`;
    sensLabel.textContent = `${settings.mouseSens.toFixed(1)}x`;
    try { localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings)); } catch (_) {}
  }
  volInput.addEventListener("input", saveSettings);
  sensInput.addEventListener("input", saveSettings);

  // Audio Engine (Web Audio API procedural SFX + subtle night drone)
  let audioCtx = null;
  let ambientStarted = false;
  function ensureAudio() {
    if (settings.volume <= 0.01) return null;
    if (!audioCtx) {
      const Ctx = window.AudioContext || window.webkitAudioContext;
      if (Ctx) audioCtx = new Ctx();
    }
    if (audioCtx && audioCtx.state === "suspended") {
      audioCtx.resume().catch(() => {});
    }
    if (audioCtx && !ambientStarted) {
      ambientStarted = true;
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = "sine";
      osc.frequency.value = 110;
      gain.gain.value = 0.015 * settings.volume;
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
    }
    return audioCtx;
  }

  function playSfx(freq, dur, type = "sine", vol = 0.12, endFreq = freq) {
    const ctx = ensureAudio();
    if (!ctx) return;
    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, now);
    if (endFreq !== freq) osc.frequency.exponentialRampToValueAtTime(Math.max(40, endFreq), now + dur);
    gain.gain.setValueAtTime(vol * settings.volume, now);
    gain.gain.exponentialRampToValueAtTime(0.0005, now + dur);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + dur);
  }

  let uiMode = "menu"; // "menu" | "intro" | "playing" | "paused" | "settings" | "result"
  const keys = new Set();
  const camera = { yawDeg: 0, pitch: 0.42, distance: 12.5 };
  let dragging = false;
  let lastX = 0;
  let lastY = 0;
  let jumpLatched = false;
  let dashLatched = false;
  let interactLatched = false;
  let pulseLatched = false;
  let pauseLatched = false;
  let pulseWave = 0.0;
  let animTime = 0.0;
  let tickInFlight = false;
  let lastCountdownSec = -1;
  let fpsCount = 0;
  let fpsTimer = 0;

  let gameData = {
    snapshot: {
      tick: 0, sim_tick: 0, night: 1, state: "playing", time_left_s: 300, score: 0,
      wind: { active: false, dir_deg: 0 },
      player: { pos: [0, 0, 0], vel: [0, 0, 0], grounded: true, invuln: false, flames: 3, carried: 0, dash_cd_s: 0, pulse_cd_s: 0, charm_s: 0 },
      lanterns: [], shades: [], motes: [], drifters: [], charms: [],
    },
    tuning: { carry_capacity: 10, lantern_cost: 10, interact_radius: 2.0, pulse_cost: 3, pulse_radius: 5.0, safe_radius: 6.0, flames: 3 },
    meta: { map_name: "Đêm 1 — Đảo Bến", intro_quote: "", campaign_score: 0, wind_warning: false, facing_yaw_deg: 0, ramps: [], launch_pads: [], charms_pos: [] },
  };

  function showScreen(mode) {
    uiMode = mode;
    screenMenu.classList.toggle("hidden", mode !== "menu");
    screenIntro.classList.toggle("hidden", mode !== "intro");
    screenPause.classList.toggle("hidden", mode !== "paused");
    screenSettings.classList.toggle("hidden", mode !== "settings");
    screenResult.classList.toggle("hidden", mode !== "result");
    hudRoot.classList.toggle("hidden", mode !== "playing" && mode !== "paused");
    if (mode !== "playing") {
      promptEl.classList.add("hidden");
      arrowEl.classList.add("hidden");
    }
  }

  async function apiPost(path, body = {}) {
    const res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return res.ok ? res.json() : null;
  }

  async function startNight(night, resetCampaign = false) {
    ensureAudio();
    const data = await apiPost("/api/reset", { night, reset_campaign: resetCampaign });
    if (data) {
      gameData = data;
      camera.yawDeg = 0;
      lastCountdownSec = -1;
      introBadge.textContent = `Đêm ${night} / 3`;
      introTitle.textContent = data.meta?.map_name || `Đêm ${night}`;
      introQuote.textContent = data.meta?.intro_quote || "";
      showScreen("intro");
      updateHud();
    }
  }

  document.getElementById("btn-start-campaign").addEventListener("click", () => startNight(1, true));
  document.getElementById("btn-play-n1").addEventListener("click", () => startNight(1, true));
  document.getElementById("btn-play-n2").addEventListener("click", () => startNight(2, true));
  document.getElementById("btn-play-n3").addEventListener("click", () => startNight(3, true));
  document.getElementById("btn-enter-night").addEventListener("click", () => { ensureAudio(); showScreen("playing"); });

  document.getElementById("btn-pause-hud").addEventListener("click", () => { pauseLatched = true; });
  document.getElementById("btn-resume").addEventListener("click", () => { pauseLatched = true; });
  document.getElementById("btn-restart-night-pause").addEventListener("click", () => startNight(gameData.snapshot.night, false));
  document.getElementById("btn-back-menu-pause").addEventListener("click", () => showScreen("menu"));

  document.getElementById("btn-open-settings-menu").addEventListener("click", () => { settingsReturnTo = "menu"; showScreen("settings"); });
  document.getElementById("btn-open-settings-pause").addEventListener("click", () => { settingsReturnTo = "paused"; showScreen("settings"); });
  document.getElementById("btn-close-settings").addEventListener("click", () => showScreen(settingsReturnTo));

  document.getElementById("btn-retry-night").addEventListener("click", () => startNight(gameData.snapshot.night, false));
  document.getElementById("btn-result-menu").addEventListener("click", () => showScreen("menu"));
  btnNextNight.addEventListener("click", async () => {
    const data = await apiPost("/api/next_night", {});
    if (data) {
      gameData = data;
      camera.yawDeg = 0;
      introBadge.textContent = `Đêm ${data.snapshot.night} / 3`;
      introTitle.textContent = data.meta?.map_name || "";
      introQuote.textContent = data.meta?.intro_quote || "";
      showScreen("intro");
      updateHud();
    }
  });

  canvas.addEventListener("pointerdown", (e) => {
    if (uiMode !== "playing") return;
    ensureAudio();
    if (e.button === 2) { dashLatched = true; return; }
    dragging = true;
    lastX = e.clientX;
    lastY = e.clientY;
  });
  canvas.addEventListener("contextmenu", (e) => e.preventDefault());
  window.addEventListener("pointerup", () => { dragging = false; });
  window.addEventListener("pointermove", (e) => {
    if (!dragging || uiMode !== "playing") return;
    camera.yawDeg = (camera.yawDeg - (e.clientX - lastX) * 0.35 * settings.mouseSens) % 360;
    camera.pitch = Math.max(0.18, Math.min(1.15, camera.pitch + (e.clientY - lastY) * 0.005 * settings.mouseSens));
    lastX = e.clientX;
    lastY = e.clientY;
  });
  canvas.addEventListener("wheel", (e) => {
    camera.distance = Math.max(7.0, Math.min(26.0, camera.distance + e.deltaY * 0.01));
  }, { passive: true });

  window.addEventListener("keydown", (e) => {
    ensureAudio();
    const code = e.code;
    if (["Space", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(code)) e.preventDefault();
    if (!e.repeat) {
      if (code === "Space") jumpLatched = true;
      if (code === "ShiftLeft" || code === "ShiftRight") dashLatched = true;
      if (code === "KeyE" || code === "KeyF") interactLatched = true;
      if (code === "KeyQ") pulseLatched = true;
      if (code === "Escape" || code === "KeyP") {
        if (uiMode === "playing" || uiMode === "paused") pauseLatched = true;
      }
    }
    keys.add(code);
  });
  window.addEventListener("keyup", (e) => { keys.delete(e.code); });

  function handleEvents(events) {
    for (const ev of events || []) {
      if (ev.name === "paused") showScreen("paused");
      else if (ev.name === "resumed") showScreen("playing");
      else if (ev.name === "mote_picked") playSfx(720 + (ev.data?.carried || 1) * 40, 0.14, "sine", 0.10, 960);
      else if (ev.name === "charm_picked") { playSfx(880, 0.25, "triangle", 0.13, 1320); }
      else if (ev.name === "deposit") playSfx(460, 0.15, "triangle", 0.11, 600);
      else if (ev.name === "lantern_lit") {
        playSfx(523.25, 0.28, "triangle", 0.14);
        setTimeout(() => playSfx(659.25, 0.3, "sine", 0.13), 80);
        setTimeout(() => playSfx(783.99, 0.4, "sine", 0.13), 160);
      } else if (ev.name === "pulse") { pulseWave = 1.0; playSfx(420, 0.28, "sine", 0.13, 180); }
      else if (ev.name === "dash") playSfx(320, 0.12, "triangle", 0.11, 680);
      else if (ev.name === "shade_spawned") playSfx(120, 0.35, "sawtooth", 0.08, 90);
      else if (ev.name === "player_hit") playSfx(140, 0.25, "sawtooth", 0.12, 70);
      else if (ev.name === "game_over") {
        const won = ev.data?.result === "won";
        if (won) { playSfx(523.25, 0.35); setTimeout(() => playSfx(783.99, 0.5), 140); }
        else { playSfx(210, 0.5, "triangle", 0.12, 105); }
      }
    }
  }

  function updateHud() {
    const snap = gameData.snapshot;
    const t = gameData.tuning;
    const p = snap.player;
    const litCount = (snap.lanterns || []).filter((l) => l.lit).length;
    const totalLanterns = (snap.lanterns || []).length || 5;

    flamesEl.textContent = `${"🔥".repeat(Math.max(0, p.flames))} ${p.flames}/${t.flames}`;
    nightLabelEl.textContent = gameData.meta?.map_name || `Đêm ${snap.night}`;

    const secsLeft = Math.max(0, Math.ceil(snap.time_left_s));
    const m = Math.floor(secsLeft / 60);
    const s = secsLeft % 60;
    timerEl.textContent = `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
    timerEl.classList.toggle("urgent", snap.time_left_s <= 30.0);
    if (uiMode === "playing" && secsLeft <= 10 && secsLeft > 0 && secsLeft !== lastCountdownSec) {
      lastCountdownSec = secsLeft;
      playSfx(980, 0.08, "sine", 0.07);
    }

    const windWarn = Boolean(gameData.meta?.wind_warning);
    const windActive = Boolean(snap.wind?.active);
    if (windActive) {
      windBadgeEl.textContent = "Gió mạnh đang thổi!";
      windBadgeEl.classList.remove("hidden");
    } else if (windWarn) {
      windBadgeEl.textContent = "Cảnh báo: Gió sắp thổi!";
      windBadgeEl.classList.remove("hidden");
    } else {
      windBadgeEl.classList.add("hidden");
    }

    lanternsEl.textContent = `${litCount} / ${totalLanterns}`;
    scoreEl.textContent = String(snap.score);

    for (let i = 0; i < slotEls.length; i++) {
      slotEls[i].classList.toggle("filled", i < p.carried);
    }
    moteTextEl.textContent = `Đom đóm: ${p.carried} / ${t.carry_capacity}`;

    dashEl.textContent = p.charm_s > 0 ? "0s (Bùa!)" : (p.dash_cd_s > 0.05 ? `${p.dash_cd_s.toFixed(1)}s` : "Sẵn sàng");
    pulseEl.textContent = p.pulse_cd_s > 0.05 ? `${p.pulse_cd_s.toFixed(1)}s` : (p.carried < t.pulse_cost ? `Thiếu` : "Sẵn sàng");
    charmEl.classList.toggle("hidden", p.charm_s <= 0);
    if (p.charm_s > 0) charmEl.textContent = `Bùa Gió: ${p.charm_s.toFixed(1)}s`;

    // Prompt for nearest unlit lantern inside interact_radius
    let nearUnlit = null;
    for (const l of snap.lanterns || []) {
      if (l.lit) continue;
      if (Math.hypot(p.pos[0] - l.pos[0], p.pos[2] - l.pos[2]) <= t.interact_radius) {
        nearUnlit = l;
        break;
      }
    }
    if (nearUnlit && uiMode === "playing") {
      promptEl.textContent = `E — Nạp ánh sáng (${nearUnlit.deposited}/${t.lantern_cost})`;
      promptEl.classList.remove("hidden");
    } else {
      promptEl.classList.add("hidden");
    }

    if ((snap.state === "won" || snap.state === "lost") && uiMode !== "result") {
      showScreen("result");
      const total = gameData.meta?.campaign_score ?? snap.score;
      if (snap.state === "won") {
        if (snap.night === 3) {
          resultBadge.textContent = "Bình Minh";
          resultTitle.textContent = "Ba hòn đảo đã tỏa sáng!";
          resultDesc.textContent = "Mây đã vượt qua cả 3 Đêm và xua tan màn sương đen. Bình minh đã trở lại!";
          btnNextNight.classList.add("hidden");
        } else {
          resultBadge.textContent = `Thắng Đêm ${snap.night}`;
          resultTitle.textContent = `${gameData.meta?.map_name || ""} rực sáng!`;
          resultDesc.textContent = "Sẵn sàng chèo thuyền sang hòn đảo tiếp theo.";
          btnNextNight.classList.remove("hidden");
        }
      } else {
        resultBadge.textContent = `Thua Đêm ${snap.night}`;
        resultTitle.textContent = "Sương đen đã phủ kín";
        resultDesc.textContent = p.flames <= 0 ? "Mây đã mất hết Ngọn Lửa." : "Bình minh lên trước khi thắp đủ đèn.";
        btnNextNight.classList.add("hidden");
      }
      resultScore.textContent = `${snap.score} / ${total}`;
    }
  }

  function buildMoveVector() {
    let mx = 0;
    let mz = 0;
    if (keys.has("KeyW") || keys.has("ArrowUp")) mz += 1;
    if (keys.has("KeyS") || keys.has("ArrowDown")) mz -= 1;
    // Right-handed view: camera looks toward +Z, +X is screen-left, -X is screen-right
    if (keys.has("KeyD")) mx -= 1;
    if (keys.has("KeyA")) mx += 1;
    return [mx, mz];
  }

  async function sendTick(steps = 1) {
    if (tickInFlight) return;
    if (uiMode !== "playing" && !pauseLatched) return;
    tickInFlight = true;
    const payload = {
      move: buildMoveVector(),
      cam_yaw_deg: camera.yawDeg,
      jump: jumpLatched || keys.has("Space"),
      dash: dashLatched,
      interact: interactLatched || keys.has("KeyE") || keys.has("KeyF"),
      pulse: pulseLatched || keys.has("KeyQ"),
      pause: pauseLatched,
      steps,
    };
    jumpLatched = false;
    dashLatched = false;
    interactLatched = false;
    pulseLatched = false;
    pauseLatched = false;
    try {
      const next = await apiPost("/api/tick", payload);
      if (next) {
        handleEvents(next.events);
        gameData = next;
        updateHud();
      }
    } catch (_) {
    } finally {
      tickInFlight = false;
    }
  }

  // Right-handed 4x4 matrix math (fixed mat4LookAt!)
  function mat4Multiply(a, b) {
    const out = new Float32Array(16);
    for (let col = 0; col < 4; col++) {
      for (let row = 0; row < 4; row++) {
        out[col * 4 + row] =
          a[row] * b[col * 4] +
          a[4 + row] * b[col * 4 + 1] +
          a[8 + row] * b[col * 4 + 2] +
          a[12 + row] * b[col * 4 + 3];
      }
    }
    return out;
  }

  function mat4Perspective(fovRad, aspect, near, far) {
    const f = 1.0 / Math.tan(fovRad / 2);
    const nf = 1 / (near - far);
    return new Float32Array([f / aspect, 0, 0, 0, 0, f, 0, 0, 0, 0, (far + near) * nf, -1, 0, 0, 2 * far * near * nf, 0]);
  }

  function mat4LookAt(eye, target) {
    let zx = eye[0] - target[0];
    let zy = eye[1] - target[1];
    let zz = eye[2] - target[2];
    const zLen = Math.hypot(zx, zy, zz) || 1;
    zx /= zLen; zy /= zLen; zz /= zLen;

    // Right-handed: x_cam = normalize(cross(worldUp=(0,1,0), z_cam)) = (zz, 0, -zx)
    let xx = zz;
    let xz = -zx;
    const xLen = Math.hypot(xx, xz) || 1;
    xx /= xLen; xz /= xLen;

    const yx = zy * xz;
    const yy = zz * xx - zx * xz;
    const yz = -zy * xx;

    return new Float32Array([
      xx, yx, zx, 0,
      0, yy, zy, 0,
      xz, yz, zz, 0,
      -(xx * eye[0] + xz * eye[2]),
      -(yx * eye[0] + yy * eye[1] + yz * eye[2]),
      -(zx * eye[0] + zy * eye[1] + zz * eye[2]),
      1,
    ]);
  }

  function mat4Model(tx, ty, tz, yawRad, sx, sy, sz) {
    const c = Math.cos(yawRad), s = Math.sin(yawRad);
    return new Float32Array([c * sx, 0, -s * sx, 0, 0, sy, 0, 0, s * sz, 0, c * sz, 0, tx, ty, tz, 1]);
  }

  // Procedural meshes
  function createBoxData() {
    const p = [
      [-1,-1,1],[1,-1,1],[1,1,1],[-1,-1,1],[1,1,1],[-1,1,1],
      [1,-1,-1],[-1,-1,-1],[-1,1,-1],[1,-1,-1],[-1,1,-1],[1,1,-1],
      [-1,1,1],[1,1,1],[1,1,-1],[-1,1,1],[1,1,-1],[-1,1,-1],
      [-1,-1,-1],[1,-1,-1],[1,-1,1],[-1,-1,-1],[1,-1,1],[-1,-1,1],
      [1,-1,1],[1,-1,-1],[1,1,-1],[1,-1,1],[1,1,-1],[1,1,1],
      [-1,-1,-1],[-1,-1,1],[-1,1,1],[-1,-1,-1],[-1,1,1],[-1,1,-1],
    ];
    const verts = [];
    for (let i = 0; i < p.length; i++) {
      const sh = p[i][1] > 0 ? 1.0 : 0.68;
      verts.push(p[i][0], p[i][1], p[i][2], sh, sh, sh);
    }
    return new Float32Array(verts);
  }

  function createOctahedronData() {
    const top = [0, 1, 0], bot = [0, -1, 0], ring = [[1,0,0],[0,0,1],[-1,0,0],[0,0,-1]];
    const verts = [];
    for (let i = 0; i < 4; i++) {
      const a = ring[i], b = ring[(i + 1) % 4];
      verts.push(...top, 1,1,1, ...a, 0.78,0.78,0.78, ...b, 0.78,0.78,0.78);
      verts.push(...bot, 0.5,0.5,0.5, ...b, 0.7,0.7,0.7, ...a, 0.7,0.7,0.7);
    }
    return new Float32Array(verts);
  }

  function createConeData(seg) {
    const verts = [];
    for (let i = 0; i < seg; i++) {
      const a0 = (i / seg) * Math.PI * 2, a1 = ((i + 1) / seg) * Math.PI * 2;
      const sh = 0.82 + 0.16 * Math.sin(a0);
      verts.push(0,1,0, 1,1,1, Math.cos(a0),0,Math.sin(a0), sh,sh,sh, Math.cos(a1),0,Math.sin(a1), sh,sh,sh);
    }
    return new Float32Array(verts);
  }

  function createRingData(seg, innerR, outerR) {
    const verts = [];
    for (let i = 0; i < seg; i++) {
      const a0 = (i / seg) * Math.PI * 2, a1 = ((i + 1) / seg) * Math.PI * 2;
      const c0 = Math.cos(a0), s0 = Math.sin(a0), c1 = Math.cos(a1), s1 = Math.sin(a1);
      verts.push(c0*innerR,0,s0*innerR, 0.9,0.9,0.9, c0*outerR,0,s0*outerR, 1,1,1, c1*outerR,0,s1*outerR, 1,1,1);
      verts.push(c0*innerR,0,s0*innerR, 0.9,0.9,0.9, c1*outerR,0,s1*outerR, 1,1,1, c1*innerR,0,s1*innerR, 0.9,0.9,0.9);
    }
    return new Float32Array(verts);
  }

  function createArcSectorData(seg, innerR, outerR, startDeg, endDeg, yTop) {
    const verts = [];
    for (let i = 0; i < seg; i++) {
      const a0 = ((startDeg + ((endDeg - startDeg) * i) / seg) * Math.PI) / 180;
      const a1 = ((startDeg + ((endDeg - startDeg) * (i + 1)) / seg) * Math.PI) / 180;
      const c0 = Math.cos(a0), s0 = Math.sin(a0), c1 = Math.cos(a1), s1 = Math.sin(a1);
      // Top surface
      verts.push(c0*innerR, yTop, s0*innerR, 0.96,0.96,0.96, c0*outerR, yTop, s0*outerR, 1,1,1, c1*outerR, yTop, s1*outerR, 1,1,1);
      verts.push(c0*innerR, yTop, s0*innerR, 0.96,0.96,0.96, c1*outerR, yTop, s1*outerR, 1,1,1, c1*innerR, yTop, s1*innerR, 0.96,0.96,0.96);
      // Outer cliff wall
      verts.push(c0*outerR, 0, s0*outerR, 0.55,0.55,0.55, c1*outerR, 0, s1*outerR, 0.55,0.55,0.55, c1*outerR, yTop, s1*outerR, 0.72,0.72,0.72);
      verts.push(c0*outerR, 0, s0*outerR, 0.55,0.55,0.55, c1*outerR, yTop, s1*outerR, 0.72,0.72,0.72, c0*outerR, yTop, s0*outerR, 0.72,0.72,0.72);
      // Inner cliff wall
      if (innerR > 0.01) {
        verts.push(c0*innerR, 0, s0*innerR, 0.5,0.5,0.5, c1*innerR, yTop, s1*innerR, 0.68,0.68,0.68, c1*innerR, 0, s1*innerR, 0.5,0.5,0.5);
        verts.push(c0*innerR, 0, s0*innerR, 0.5,0.5,0.5, c0*innerR, yTop, s0*innerR, 0.68,0.68,0.68, c1*innerR, yTop, s1*innerR, 0.68,0.68,0.68);
      }
    }
    return new Float32Array(verts);
  }

  function createRampData(angleDeg, innerR, outerR, halfW, topY) {
    const rad = (angleDeg * Math.PI) / 180;
    const ux = Math.cos(rad), uz = Math.sin(rad);
    const tx = -uz * halfW, tz = ux * halfW;
    const p00 = [ux * outerR - tx, 0, uz * outerR - tz];
    const p01 = [ux * outerR + tx, 0, uz * outerR + tz];
    const p10 = [ux * innerR - tx, topY, uz * innerR - tz];
    const p11 = [ux * innerR + tx, topY, uz * innerR + tz];
    return new Float32Array([
      ...p00, 0.85,0.85,0.85, ...p01, 0.85,0.85,0.85, ...p11, 1,1,1,
      ...p00, 0.85,0.85,0.85, ...p11, 1,1,1, ...p10, 1,1,1,
    ]);
  }

  function updateOffscreenArrow(vp, snap) {
    if (uiMode !== "playing") { arrowEl.classList.add("hidden"); return; }
    const p = snap.player.pos;
    let nearest = null, bestD = Infinity;
    for (const l of snap.lanterns || []) {
      if (l.lit) continue;
      const d = Math.hypot(l.pos[0] - p[0], l.pos[2] - p[2]);
      if (d < bestD) { bestD = d; nearest = l; }
    }
    if (!nearest) { arrowEl.classList.add("hidden"); return; }

    const lx = nearest.pos[0], ly = nearest.pos[1] + 2.2, lz = nearest.pos[2];
    const cx = vp[0] * lx + vp[4] * ly + vp[8] * lz + vp[12];
    const cy = vp[1] * lx + vp[5] * ly + vp[9] * lz + vp[13];
    const cw = vp[3] * lx + vp[7] * ly + vp[11] * lz + vp[15];
    let ndcX = cx / (Math.abs(cw) > 1e-4 ? cw : 1e-4);
    let ndcY = cy / (Math.abs(cw) > 1e-4 ? cw : 1e-4);
    if (cw < 0) { ndcX = -ndcX; ndcY = -ndcY; }

    if (cw > 0 && Math.abs(ndcX) <= 0.92 && Math.abs(ndcY) <= 0.92) {
      arrowEl.classList.add("hidden");
      return;
    }
    const maxC = Math.max(Math.abs(ndcX), Math.abs(ndcY), 1e-4);
    const sx = (ndcX / maxC) * 0.86;
    const sy = (ndcY / maxC) * 0.82;
    const px = (sx * 0.5 + 0.5) * window.innerWidth - 14;
    const py = (-sy * 0.5 + 0.5) * window.innerHeight - 14;
    const ang = Math.atan2(sx, sy);
    arrowEl.style.left = `${px}px`;
    arrowEl.style.top = `${py}px`;
    arrowEl.style.transform = `rotate(${ang}rad)`;
    arrowEl.classList.remove("hidden");
  }

  function initWebGL2() {
    const gl = canvas.getContext("webgl2", { antialias: true });
    if (!gl) return null;

    const vsSrc = `#version 300 es
      layout(location = 0) in vec3 aPos;
      layout(location = 1) in vec3 aShade;
      uniform mat4 uMvp;
      uniform vec3 uTint;
      uniform float uLitBoost;
      out vec3 vColor;
      void main() {
        gl_Position = uMvp * vec4(aPos, 1.0);
        vColor = aShade * uTint * uLitBoost;
      }`;
    const fsSrc = `#version 300 es
      precision mediump float;
      in vec3 vColor;
      out vec4 fragColor;
      void main() { fragColor = vec4(vColor, 1.0); }`;

    function compile(type, src) {
      const s = gl.createShader(type);
      gl.shaderSource(s, src);
      gl.compileShader(s);
      return s;
    }
    const prog = gl.createProgram();
    gl.attachShader(prog, compile(gl.VERTEX_SHADER, vsSrc));
    gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, fsSrc));
    gl.linkProgram(prog);
    const uMvp = gl.getUniformLocation(prog, "uMvp");
    const uTint = gl.getUniformLocation(prog, "uTint");
    const uLitBoost = gl.getUniformLocation(prog, "uLitBoost");

    function makeMesh(data) {
      const vao = gl.createVertexArray(), vbo = gl.createBuffer();
      gl.bindVertexArray(vao);
      gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
      gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW);
      gl.enableVertexAttribArray(0);
      gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 24, 0);
      gl.enableVertexAttribArray(1);
      gl.vertexAttribPointer(1, 3, gl.FLOAT, false, 24, 12);
      return { vao, count: data.length / 6 };
    }

    const boxMesh = makeMesh(createBoxData());
    const octMesh = makeMesh(createOctahedronData());
    const coneMesh = makeMesh(createConeData(12));
    const ringMesh = makeMesh(createRingData(36, 0.94, 1.0));
    const discMesh = makeMesh(createArcSectorData(48, 0.0, 1.0, 0, 360, 0.0));
    const tier1Mesh = makeMesh(createArcSectorData(28, 12.0, 24.0, 0, 180, 3.0));
    const tier2Mesh = makeMesh(createArcSectorData(28, 0.0, 8.0, 0, 360, 6.0));
    const ramp30 = makeMesh(createRampData(30, 24, 30, 1.5, 3.0));
    const ramp150 = makeMesh(createRampData(150, 24, 30, 1.5, 3.0));

    function draw(mesh, mvp, r, g, b, boost = 1.0) {
      gl.bindVertexArray(mesh.vao);
      gl.uniformMatrix4fv(uMvp, false, mvp);
      gl.uniform3f(uTint, r, g, b);
      gl.uniform1f(uLitBoost, boost);
      gl.drawArrays(gl.TRIANGLES, 0, mesh.count);
    }

    return function render(width, height) {
      const snap = gameData.snapshot;
      const t = gameData.tuning;
      const litCount = (snap.lanterns || []).filter((l) => l.lit).length;
      const totalLanterns = Math.max(1, (snap.lanterns || []).length);
      // Ticket-02 ambient formula: 0.15 + 0.55 * (lit / total)
      const ambient = 0.15 + 0.55 * (litCount / totalLanterns);
      const envBoost = 0.55 + ambient * 0.9;

      gl.viewport(0, 0, width, height);
      gl.enable(gl.DEPTH_TEST);
      // Sky #0E1430 -> blends slightly brighter toward #1B2350 as lanterns light up
      gl.clearColor(0.055 + ambient * 0.06, 0.078 + ambient * 0.07, 0.188 + ambient * 0.10, 1.0);
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
      gl.useProgram(prog);

      const pPos = snap.player?.pos || [0, 0, 0];
      const yawRad = (camera.yawDeg * Math.PI) / 180;
      const eye = [
        pPos[0] - Math.sin(yawRad) * Math.cos(camera.pitch) * camera.distance,
        pPos[1] + 1.5 + Math.sin(camera.pitch) * camera.distance,
        pPos[2] - Math.cos(yawRad) * Math.cos(camera.pitch) * camera.distance,
      ];
      const proj = mat4Perspective(0.95, width / Math.max(1, height), 0.2, 240.0);
      const view = mat4LookAt(eye, [pPos[0], pPos[1] + 1.1, pPos[2]]);
      const vp = mat4Multiply(proj, view);
      updateOffscreenArrow(vp, snap);

      // Cloud sea below (#12384A)
      draw(boxMesh, mat4Multiply(vp, mat4Model(25, -10.5, 0, 0, 180, 0.2, 180)), 0.071, 0.220, 0.290, 0.8 + ambient * 0.35);

      // Night-specific island geometry
      if (snap.night === 1) {
        draw(discMesh, mat4Multiply(vp, mat4Model(0, -0.02, 0, 0, 40, 1, 40)), 0.184, 0.365, 0.314, envBoost);
      } else if (snap.night === 2) {
        draw(discMesh, mat4Multiply(vp, mat4Model(0, -0.02, 0, 0, 28, 1, 28)), 0.184, 0.365, 0.314, envBoost);
        draw(discMesh, mat4Multiply(vp, mat4Model(70, -0.02, 0, 0, 28, 1, 28)), 0.788, 0.706, 0.541, envBoost);
        // Bamboo bridge x in [26, 44], z in [-2, 2]
        draw(boxMesh, mat4Multiply(vp, mat4Model(35, -0.1, 0, 0, 9.0, 0.1, 2.0)), 0.420, 0.290, 0.184, envBoost);
      } else if (snap.night === 3) {
        draw(discMesh, mat4Multiply(vp, mat4Model(0, -0.02, 0, 0, 45, 1, 45)), 0.184, 0.365, 0.314, envBoost);
        draw(tier1Mesh, vp, 0.788, 0.706, 0.541, envBoost);
        draw(tier2Mesh, vp, 0.788, 0.706, 0.541, envBoost);
        draw(ramp30, vp, 0.420, 0.290, 0.184, envBoost);
        draw(ramp150, vp, 0.420, 0.290, 0.184, envBoost);
        // Bell Tower cylinder at (0, 6..14, 0)
        draw(boxMesh, mat4Multiply(vp, mat4Model(0, 10.0, 0, 0, 1.8, 4.0, 1.8)), 0.420, 0.290, 0.184, envBoost);
        draw(coneMesh, mat4Multiply(vp, mat4Model(0, 14.0, 0, 0, 2.5, 2.2, 2.5)), 0.784, 0.063, 0.180, envBoost);
      }

      // Launch pads
      for (const pad of gameData.meta?.launch_pads || []) {
        draw(ringMesh, mat4Multiply(vp, mat4Model(pad.x, pad.y + 0.06, pad.z, 0, pad.radius, 1, pad.radius)), 0.949, 0.757, 0.306, 1.25);
        draw(discMesh, mat4Multiply(vp, mat4Model(pad.x, pad.y + 0.04, pad.z, 0, pad.radius * 0.7, 1, pad.radius * 0.7)), 1.0, 0.702, 0.278, 1.2);
      }

      // Great Lanterns
      for (const l of snap.lanterns || []) {
        const lx = l.pos[0], ly = l.pos[1], lz = l.pos[2];
        draw(boxMesh, mat4Multiply(vp, mat4Model(lx, ly + 0.9, lz, 0, 0.35, 0.9, 0.35)), 0.357, 0.373, 0.431, envBoost);
        const r = l.lit ? 1.0 : 0.357, g = l.lit ? 0.702 : 0.373, b = l.lit ? 0.278 : 0.431;
        draw(octMesh, mat4Multiply(vp, mat4Model(lx, ly + 2.2, lz, animTime * 0.5, 0.7, 0.9, 0.7)), r, g, b, l.lit ? 1.25 : 0.9);
        if (l.lit) {
          draw(octMesh, mat4Multiply(vp, mat4Model(lx, ly + 2.2, lz, -animTime, 0.35, 0.45, 0.35)), 1.0, 0.914, 0.690, 1.35);
          draw(ringMesh, mat4Multiply(vp, mat4Model(lx, ly + 0.05, lz, 0, t.safe_radius, 1, t.safe_radius)), 1.0, 0.702, 0.278, 1.0);
        } else {
          draw(ringMesh, mat4Multiply(vp, mat4Model(lx, ly + 0.05, lz, 0, t.interact_radius, 1, t.interact_radius)), 0.357, 0.373, 0.431, 1.0);
        }
      }

      // Wind Charms (#C8102E + #F2C14E)
      for (const c of gameData.meta?.charms_pos || []) {
        if (!c.available) continue;
        const cp = c.pos;
        const bob = 0.8 + 0.2 * Math.sin(animTime * 3.0);
        draw(boxMesh, mat4Multiply(vp, mat4Model(cp[0], cp[1] + bob, cp[2], animTime * 2.0, 0.25, 0.42, 0.06)), 0.784, 0.063, 0.180, 1.2);
        draw(ringMesh, mat4Multiply(vp, mat4Model(cp[0], cp[1] + 0.05, cp[2], 0, 1.0, 1, 1.0)), 0.949, 0.757, 0.306, 1.1);
      }

      // Motes (#FFF6C2 / #FFE58A)
      for (let i = 0; i < (snap.motes || []).length; i++) {
        const m = snap.motes[i];
        const bob = 0.6 + 0.16 * Math.sin(animTime * 3.8 + i);
        draw(octMesh, mat4Multiply(vp, mat4Model(m.pos[0], m.pos[1] + bob, m.pos[2], animTime * 2 + i, 0.24, 0.28, 0.24)), 1.0, 0.965, 0.761, 1.25);
      }

      // Shades (#120A1A body, #7A3CFF rim, #3A3450 stunned)
      for (let i = 0; i < (snap.shades || []).length; i++) {
        const s = snap.shades[i];
        const stunned = s.state === "stunned";
        const bob = 0.95 + 0.18 * Math.sin(animTime * (stunned ? 14 : 3.2) + i);
        const col = stunned ? [0.227, 0.204, 0.314] : [0.071, 0.039, 0.102];
        draw(octMesh, mat4Multiply(vp, mat4Model(s.pos[0], s.pos[1] + bob, s.pos[2], animTime * 1.6, 0.78, 1.05, 0.78)), col[0], col[1], col[2], 1.1);
        draw(ringMesh, mat4Multiply(vp, mat4Model(s.pos[0], s.pos[1] + 0.06, s.pos[2], 0, 0.85, 1, 0.85)), 0.478, 0.235, 1.0, stunned ? 0.5 : 1.1);
      }

      // Drifters (#8FA3B8 ribbons)
      for (let i = 0; i < (snap.drifters || []).length; i++) {
        const d = snap.drifters[i];
        draw(boxMesh, mat4Multiply(vp, mat4Model(d.pos[0], d.pos[1] + 1.3 + 0.2 * Math.sin(animTime * 6 + i), d.pos[2], animTime * 4, 0.95, 0.12, 0.25)), 0.561, 0.639, 0.722, 1.2);
      }

      // Wind leaf particles (Night 3)
      if (snap.wind?.active || gameData.meta?.wind_warning) {
        const wr = ((snap.wind?.dir_deg || 0) * Math.PI) / 180;
        const speed = snap.wind?.active ? 14.0 : 4.0;
        for (let i = 0; i < 12; i++) {
          const tShift = (animTime * speed + i * 3.1) % 30.0 - 15.0;
          const px = pPos[0] + Math.cos(wr) * tShift - Math.sin(wr) * ((i - 6) * 1.4);
          const pz = pPos[2] + Math.sin(wr) * tShift + Math.cos(wr) * ((i - 6) * 1.4);
          draw(boxMesh, mat4Multiply(vp, mat4Model(px, pPos[1] + 1.2 + (i % 3) * 0.5, pz, animTime * 5 + i, 0.18, 0.04, 0.12)), 0.788, 0.706, 0.541, 1.1);
        }
      }

      // Player May (#E8E2D0 cloak, #C8102E scarf, non la + small lantern)
      const pYaw = ((gameData.meta?.facing_yaw_deg || 0) * Math.PI) / 180;
      const blink = snap.player?.invuln && Math.floor(animTime * 16) % 2 === 0;
      if (!blink) {
        draw(coneMesh, mat4Multiply(vp, mat4Model(pPos[0], pPos[1] + 0.05, pPos[2], pYaw, 0.45, 1.35, 0.45)), 0.910, 0.886, 0.816, 1.0);
        draw(ringMesh, mat4Multiply(vp, mat4Model(pPos[0], pPos[1] + 1.02, pPos[2], pYaw, 0.36, 1, 0.36)), 0.784, 0.063, 0.180, 1.1);
        draw(coneMesh, mat4Multiply(vp, mat4Model(pPos[0], pPos[1] + 1.35, pPos[2], pYaw, 0.76, 0.46, 0.76)), 0.788, 0.706, 0.541, 1.05);
        const hx = pPos[0] + Math.sin(pYaw) * 0.65, hz = pPos[2] + Math.cos(pYaw) * 0.65;
        draw(octMesh, mat4Multiply(vp, mat4Model(hx, pPos[1] + 1.15, hz, animTime * 3, 0.15, 0.2, 0.15)), 1.0, 0.702, 0.278, 1.3);
      }

      if (pulseWave > 0.02) {
        const r = (1.0 - pulseWave) * (t.pulse_radius || 5.0);
        draw(ringMesh, mat4Multiply(vp, mat4Model(pPos[0], pPos[1] + 0.12, pPos[2], 0, Math.max(0.4, r), 1, Math.max(0.4, r))), 1.0, 0.914, 0.690, 1.4 * pulseWave);
      }
    };
  }

  const renderFrame = initWebGL2() || (() => {});

  function resizeCanvas() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const width = Math.max(1, Math.floor(canvas.clientWidth * dpr));
    const height = Math.max(1, Math.floor(canvas.clientHeight * dpr));
    if (canvas.width !== width || canvas.height !== height) {
      canvas.width = width;
      canvas.height = height;
    }
    return { width, height };
  }

  let lastTs = performance.now();
  let accumulator = 0;

  function loop(now) {
    const dtSec = Math.min(0.1, (now - lastTs) / 1000);
    lastTs = now;
    animTime += dtSec;
    pulseWave = Math.max(0, pulseWave - dtSec * 2.5);

    fpsCount += 1;
    fpsTimer += dtSec;
    if (fpsTimer >= 0.5) {
      fpsEl.textContent = `FPS: ${Math.round(fpsCount / fpsTimer)}`;
      fpsCount = 0;
      fpsTimer = 0;
    }

    if (uiMode === "playing") {
      if (keys.has("ArrowLeft")) camera.yawDeg = (camera.yawDeg + 110 * dtSec) % 360;
      if (keys.has("ArrowRight")) camera.yawDeg = (camera.yawDeg - 110 * dtSec) % 360;
    }

    accumulator += dtSec;
    const steps = Math.min(4, Math.floor(accumulator * 60));
    if (steps > 0) {
      accumulator -= steps / 60;
      sendTick(steps);
    }

    const { width, height } = resizeCanvas();
    renderFrame(width, height);
    requestAnimationFrame(loop);
  }

  fetch("/api/state")
    .then((r) => (r.ok ? r.json() : null))
    .then((data) => { if (data) { gameData = data; updateHud(); } })
    .catch(() => {})
    .finally(() => {
      showScreen("menu");
      requestAnimationFrame(loop);
    });
})();
