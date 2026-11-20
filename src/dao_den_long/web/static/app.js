(() => {
  "use strict";

  const urlParams = new URLSearchParams(window.location.search);
  const isBenchMode = urlParams.get("mode") === "bench";
  const benchSeed = Number(urlParams.get("seed") || 42);
  const benchDurationSec = Math.max(0.5, Number(urlParams.get("duration") || 30));
  const benchWarmupSec = Math.max(0.0, Number(urlParams.get("warmup") ?? 3.0));

  const canvas = document.getElementById("scene-canvas");
  const screenFlashEl = document.getElementById("screen-flash");
  const fuelBarsLayer = document.getElementById("fuel-bars-layer");
  const hudRoot = document.getElementById("hud-root");
  const flamesEl = document.getElementById("hud-flames");
  const nightLabelEl = document.getElementById("hud-night-label");
  const timerEl = document.getElementById("hud-timer");
  const goalEl = document.getElementById("hud-goal");
  const windBadgeEl = document.getElementById("hud-wind-badge");
  const lanternsEl = document.getElementById("hud-lanterns");
  const scoreEl = document.getElementById("hud-score");
  const fpsEl = document.getElementById("hud-fps");
  const moteSlotsEl = document.getElementById("hud-mote-slots");
  const moteTextEl = document.getElementById("hud-mote-text");
  const dashEl = document.getElementById("hud-dash");
  const pulseEl = document.getElementById("hud-pulse");
  const charmEl = document.getElementById("hud-charm");
  const lblKeyDash = document.getElementById("lbl-key-dash");
  const lblKeyPulse = document.getElementById("lbl-key-pulse");
  const subtitleBannerEl = document.getElementById("subtitle-banner");
  const promptEl = document.getElementById("context-prompt");
  const arrowEl = document.getElementById("offscreen-arrow");
  const shadeArrowEl = document.getElementById("shade-edge-arrow");
  const menuControlsHint = document.getElementById("menu-controls-hint");

  const screenMenu = document.getElementById("screen-menu");
  const screenIntro = document.getElementById("screen-intro");
  const screenPause = document.getElementById("screen-pause");
  const screenSettings = document.getElementById("screen-settings");
  const screenLeaderboard = document.getElementById("screen-leaderboard");
  const screenResult = document.getElementById("screen-result");

  const introBadge = document.getElementById("intro-night-badge");
  const introTitle = document.getElementById("intro-title");
  const introQuote = document.getElementById("intro-quote");
  const resultBadge = document.getElementById("result-badge");
  const resultTitle = document.getElementById("result-title");
  const resultDesc = document.getElementById("result-desc");
  const resultScore = document.getElementById("result-score");
  const btnNextNight = document.getElementById("btn-next-night");

  const lbSaveBox = document.getElementById("leaderboard-save-box");
  const inputPlayerName = document.getElementById("input-player-name");
  const btnSaveScore = document.getElementById("btn-save-score");
  const lbMsg = document.getElementById("leaderboard-msg");
  const lbTbody = document.getElementById("leaderboard-tbody");

  const volInput = document.getElementById("input-volume");
  const sensInput = document.getElementById("input-sens");
  const colorblindInput = document.getElementById("input-colorblind");
  const reducedMotionInput = document.getElementById("input-reduced-motion");
  const largeTextInput = document.getElementById("input-large-text");
  const subtitlesInput = document.getElementById("input-subtitles");
  const volLabel = document.getElementById("lbl-volume");
  const sensLabel = document.getElementById("lbl-sens");
  const keybindGrid = document.getElementById("keybind-grid");
  const keybindError = document.getElementById("keybind-error");
  const btnResetKeys = document.getElementById("btn-reset-keys");

  // Default key bindings for all 9 actions (Ticket-04 §4)
  const DEFAULT_KEYBINDS = {
    moveUp: "KeyW",
    moveDown: "KeyS",
    moveLeft: "KeyA",
    moveRight: "KeyD",
    jump: "Space",
    dash: "ShiftLeft",
    interact: "KeyE",
    pulse: "KeyQ",
    pause: "KeyP",
  };

  const ACTION_LABELS = {
    moveUp: "Đi tiến",
    moveDown: "Đi lùi",
    moveLeft: "Qua trái",
    moveRight: "Qua phải",
    jump: "Nhảy",
    dash: "Lướt nhanh",
    interact: "Tương tác / Châm dầu",
    pulse: "Tỏa Sáng",
    pause: "Tạm dừng",
  };

  function prettyKey(code) {
    if (!code) return "?";
    return code
      .replace(/^Key/, "")
      .replace(/^Digit/, "")
      .replace("ShiftLeft", "L-Shift")
      .replace("ShiftRight", "R-Shift")
      .replace("ArrowUp", "↑")
      .replace("ArrowDown", "↓")
      .replace("ArrowLeft", "←")
      .replace("ArrowRight", "→");
  }

  // Persistent settings & accessibility options
  const SETTINGS_KEY = "dao_den_long_settings_v3";
  const settings = {
    volume: 0.7,
    mouseSens: 1.0,
    colorblind: false,
    reducedMotion: false,
    largeText: false,
    subtitles: true,
    keybinds: { ...DEFAULT_KEYBINDS },
  };

  try {
    const saved = JSON.parse(localStorage.getItem(SETTINGS_KEY) || "{}");
    if (typeof saved.volume === "number") settings.volume = Math.max(0, Math.min(1, saved.volume));
    if (typeof saved.mouseSens === "number") settings.mouseSens = Math.max(0.2, Math.min(2.5, saved.mouseSens));
    if (typeof saved.colorblind === "boolean") settings.colorblind = saved.colorblind;
    if (typeof saved.reducedMotion === "boolean") settings.reducedMotion = saved.reducedMotion;
    if (typeof saved.largeText === "boolean") settings.largeText = saved.largeText;
    if (typeof saved.subtitles === "boolean") settings.subtitles = saved.subtitles;
    if (saved.keybinds && typeof saved.keybinds === "object") {
      for (const act of Object.keys(DEFAULT_KEYBINDS)) {
        if (typeof saved.keybinds[act] === "string" && saved.keybinds[act]) {
          settings.keybinds[act] = saved.keybinds[act];
        }
      }
    }
  } catch (_) {}

  volInput.value = String(Math.round(settings.volume * 100));
  sensInput.value = String(Math.round(settings.mouseSens * 10));
  colorblindInput.checked = settings.colorblind;
  reducedMotionInput.checked = settings.reducedMotion;
  largeTextInput.checked = settings.largeText;
  subtitlesInput.checked = settings.subtitles;

  function findKeybindConflicts(binds) {
    const byKey = {};
    const conflicts = [];
    for (const [act, code] of Object.entries(binds)) {
      if (!byKey[code]) byKey[code] = [];
      byKey[code].push(act);
    }
    for (const [code, acts] of Object.entries(byKey)) {
      if (acts.length > 1) {
        conflicts.push(`${prettyKey(code)} (${acts.map((a) => ACTION_LABELS[a]).join(", ")})`);
      }
    }
    return conflicts;
  }

  let listeningAction = null;
  function renderKeybindGrid() {
    const conflicts = findKeybindConflicts(settings.keybinds);
    const usedCount = {};
    for (const code of Object.values(settings.keybinds)) {
      usedCount[code] = (usedCount[code] || 0) + 1;
    }

    if (conflicts.length > 0) {
      keybindError.textContent = `⚠ Phát hiện trùng phím: ${conflicts.join(" · ")}. Vui lòng chọn phím khác!`;
      keybindError.classList.remove("hidden");
    } else {
      keybindError.classList.add("hidden");
    }

    keybindGrid.innerHTML = "";
    for (const [act, label] of Object.entries(ACTION_LABELS)) {
      const code = settings.keybinds[act];
      const item = document.createElement("div");
      item.className = `keybind-item${usedCount[code] > 1 ? " conflict" : ""}`;
      const span = document.createElement("span");
      span.textContent = label;
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = `keybind-btn${listeningAction === act ? " listening" : ""}`;
      btn.textContent = listeningAction === act ? "Nhấn phím..." : prettyKey(code);
      btn.addEventListener("click", () => {
        listeningAction = listeningAction === act ? null : act;
        renderKeybindGrid();
      });
      item.appendChild(span);
      item.appendChild(btn);
      keybindGrid.appendChild(item);
    }

    const kb = settings.keybinds;
    lblKeyDash.textContent = prettyKey(kb.dash);
    lblKeyPulse.textContent = prettyKey(kb.pulse);
    menuControlsHint.textContent =
      `${prettyKey(kb.moveUp)}/${prettyKey(kb.moveLeft)}/${prettyKey(kb.moveDown)}/${prettyKey(kb.moveRight)}: Di chuyển · ` +
      `${prettyKey(kb.jump)}: Nhảy · ${prettyKey(kb.dash)}/Chuột phải: Lướt · ` +
      `${prettyKey(kb.interact)}: Nạp/Châm dầu · ${prettyKey(kb.pulse)}: Tỏa Sáng · ${prettyKey(kb.pause)}/Esc: Tạm dừng`;
  }

  function applySettingsToDom() {
    volLabel.textContent = `${volInput.value}%`;
    sensLabel.textContent = `${settings.mouseSens.toFixed(1)}x`;
    document.body.classList.toggle("colorblind", settings.colorblind);
    document.body.classList.toggle("reduced-motion", settings.reducedMotion);
    document.documentElement.classList.toggle("large-text", settings.largeText);
    document.body.classList.toggle("large-text", settings.largeText);
    renderKeybindGrid();
  }

  function saveSettings() {
    settings.volume = Number(volInput.value) / 100;
    settings.mouseSens = Number(sensInput.value) / 10;
    settings.colorblind = Boolean(colorblindInput.checked);
    settings.reducedMotion = Boolean(reducedMotionInput.checked);
    settings.largeText = Boolean(largeTextInput.checked);
    settings.subtitles = Boolean(subtitlesInput.checked);
    applySettingsToDom();
    try { localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings)); } catch (_) {}
  }

  volInput.addEventListener("input", saveSettings);
  sensInput.addEventListener("input", saveSettings);
  colorblindInput.addEventListener("change", saveSettings);
  reducedMotionInput.addEventListener("change", saveSettings);
  largeTextInput.addEventListener("change", saveSettings);
  subtitlesInput.addEventListener("change", saveSettings);
  btnResetKeys.addEventListener("click", () => {
    listeningAction = null;
    settings.keybinds = { ...DEFAULT_KEYBINDS };
    saveSettings();
  });
  applySettingsToDom();

  // Dynamic capacity firefly slots (10..20)
  let renderedCapacity = 0;
  let slotEls = [];
  function syncCapacitySlots(cap, carried) {
    if (cap !== renderedCapacity) {
      renderedCapacity = cap;
      moteSlotsEl.innerHTML = "";
      slotEls = [];
      for (let i = 0; i < cap; i++) {
        const el = document.createElement("div");
        el.className = "mote-slot";
        moteSlotsEl.appendChild(el);
        slotEls.push(el);
      }
    }
    for (let i = 0; i < slotEls.length; i++) {
      slotEls[i].classList.toggle("filled", i < carried);
    }
  }

  // Procedural Web Audio API SFX & subtle night ambience
  let audioCtx = null;
  let ambientStarted = false;
  function ensureAudio() {
    if (isBenchMode || settings.volume <= 0.01) return null;
    if (!audioCtx) {
      const Ctx = window.AudioContext || window.webkitAudioContext;
      if (Ctx) audioCtx = new Ctx();
    }
    if (audioCtx && audioCtx.state === "suspended") audioCtx.resume().catch(() => {});
    if (audioCtx && !ambientStarted) {
      ambientStarted = true;
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = "sine";
      osc.frequency.value = 110;
      gain.gain.value = 0.014 * settings.volume;
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

  let uiMode = "menu";
  let settingsReturnTo = "menu";
  const keys = new Set();
  const camera = { yawDeg: 0, pitch: 0.40, distance: 12.0 };
  let dragging = false;
  let lastX = 0;
  let lastY = 0;
  let jumpLatched = false;
  let dashLatched = false;
  let interactLatched = false;
  let pulseLatched = false;
  let pauseLatched = false;
  let pulseWave = 0.0;
  let shakeTimer = 0.0;
  let flashTimer = 0.0;
  let shadeSpawnAlertTimer = 0.0;
  let lastSpawnedShadeId = null;
  let animTime = 0.0;
  let tickInFlight = false;
  let lastCountdownSec = -1;
  let fpsCount = 0;
  let fpsTimer = 0;
  let scoreSavedForRun = false;

  let gameData = {
    snapshot: {
      tick: 0, sim_tick: 0, night: 1, state: "playing", time_left_s: 240, score: 0,
      wind: { active: false, dir_deg: 0 },
      player: { pos: [0, 0, 0], vel: [0, 0, 0], grounded: true, invuln: false, flames: 3, carried: 0, capacity: 10, dash_cd_s: 0, pulse_cd_s: 0, charm_s: 0 },
      lanterns: [], shades: [], motes: [], drifters: [], charms: [],
    },
    tuning: { carry_capacity: 10, lantern_cost: 10, relight_cost: 5, interact_radius: 2.0, pulse_cost: 3, pulse_radius: 5.0, safe_radius: 6.0, flames: 3, low_fuel_threshold: 30, fuel_max: 100 },
    meta: { map_name: "Đêm 1 — Đảo Bến", intro_quote: "", win_needed: 3, campaign_score: 0, nights_won: 0, seed: 42, wind_warning: false, facing_yaw_deg: 0, shades_target: {}, ramps: [], launch_pads: [], charms_pos: [] },
  };

  function showScreen(mode) {
    uiMode = mode;
    screenMenu.classList.toggle("hidden", mode !== "menu");
    screenIntro.classList.toggle("hidden", mode !== "intro");
    screenPause.classList.toggle("hidden", mode !== "paused");
    screenSettings.classList.toggle("hidden", mode !== "settings");
    screenLeaderboard.classList.toggle("hidden", mode !== "leaderboard");
    screenResult.classList.toggle("hidden", mode !== "result");
    hudRoot.classList.toggle("hidden", mode !== "playing" && mode !== "paused" && mode !== "bench");
    if (mode !== "playing") {
      promptEl.classList.add("hidden");
      arrowEl.classList.add("hidden");
      shadeArrowEl.classList.add("hidden");
      subtitleBannerEl.classList.add("hidden");
      fuelBarsLayer.innerHTML = "";
    }
  }

  async function apiGet(path) {
    const res = await fetch(path);
    return res.ok ? res.json() : null;
  }

  async function apiPost(path, body = {}) {
    const res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => null);
    return { ok: res.ok, data };
  }

  async function loadLeaderboardTable() {
    const data = await apiGet("/api/leaderboard");
    const entries = data?.entries || [];
    if (entries.length === 0) {
      lbTbody.innerHTML = '<tr><td colspan="6">Chưa có kỷ lục nào. Hãy là người đầu tiên!</td></tr>';
      return;
    }
    lbTbody.innerHTML = entries
      .map(
        (e, idx) =>
          `<tr>
            <td><strong>#${idx + 1}</strong></td>
            <td>${e.name}</td>
            <td class="gold"><strong>${e.score}</strong></td>
            <td>${e.nights_won} / 3</td>
            <td>${e.seed}</td>
            <td>${(e.achieved_at || "").replace("T", " ").slice(0, 19)}</td>
          </tr>`
      )
      .join("");
  }

  async function startNight(night, resetCampaign = false) {
    ensureAudio();
    const { ok, data } = await apiPost("/api/reset", { night, reset_campaign: resetCampaign });
    if (ok && data) {
      gameData = data;
      camera.yawDeg = 0;
      lastCountdownSec = -1;
      scoreSavedForRun = false;
      lbMsg.textContent = "";
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

  document.getElementById("btn-open-settings-menu").addEventListener("click", () => { settingsReturnTo = "menu"; listeningAction = null; renderKeybindGrid(); showScreen("settings"); });
  document.getElementById("btn-open-settings-pause").addEventListener("click", () => { settingsReturnTo = "paused"; listeningAction = null; renderKeybindGrid(); showScreen("settings"); });
  document.getElementById("btn-close-settings").addEventListener("click", () => { listeningAction = null; showScreen(settingsReturnTo); });

  document.getElementById("btn-open-leaderboard").addEventListener("click", async () => {
    await loadLeaderboardTable();
    showScreen("leaderboard");
  });
  document.getElementById("btn-result-leaderboard").addEventListener("click", async () => {
    await loadLeaderboardTable();
    showScreen("leaderboard");
  });
  document.getElementById("btn-close-leaderboard").addEventListener("click", () => showScreen("menu"));

  btnSaveScore.addEventListener("click", async () => {
    if (scoreSavedForRun) return;
    const rawName = (inputPlayerName.value || "").trim();
    const { ok, data } = await apiPost("/api/leaderboard", {
      name: rawName,
      score: gameData.meta?.campaign_score ?? 0,
      nights_won: gameData.meta?.nights_won ?? 0,
      seed: gameData.meta?.seed ?? 42,
    });
    if (!ok) {
      lbMsg.textContent = data?.error || "Tên không hợp lệ (3–12 ký tự chữ, số hoặc _).";
      lbMsg.classList.add("err");
      return;
    }
    scoreSavedForRun = true;
    btnSaveScore.disabled = true;
    lbMsg.textContent = "✓ Đã lưu vào Bảng xếp hạng Top 10!";
    lbMsg.classList.remove("err");
    await loadLeaderboardTable();
  });

  document.getElementById("btn-retry-night").addEventListener("click", () => startNight(gameData.snapshot.night, false));
  document.getElementById("btn-result-menu").addEventListener("click", () => showScreen("menu"));
  btnNextNight.addEventListener("click", async () => {
    const { ok, data } = await apiPost("/api/next_night", {});
    if (ok && data) {
      gameData = data;
      camera.yawDeg = 0;
      scoreSavedForRun = false;
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
    if (uiMode !== "playing") return;
    camera.distance = Math.max(6.5, Math.min(26.0, camera.distance + e.deltaY * 0.01));
  }, { passive: true });

  window.addEventListener("keydown", (e) => {
    if (document.activeElement === inputPlayerName) return;
    ensureAudio();
    const code = e.code;

    // Interactive key remapping listener
    if (uiMode === "settings" && listeningAction) {
      e.preventDefault();
      if (code !== "Escape") {
        settings.keybinds[listeningAction] = code;
      }
      listeningAction = null;
      saveSettings();
      return;
    }

    if (["Space", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(code)) e.preventDefault();
    const kb = settings.keybinds;
    if (!e.repeat) {
      if (code === kb.jump) jumpLatched = true;
      if (code === kb.dash || code === "ShiftRight") dashLatched = true;
      if (code === kb.interact || code === "KeyF") interactLatched = true;
      if (code === kb.pulse) pulseLatched = true;
      if (code === kb.pause || code === "Escape") {
        if (uiMode === "playing" || uiMode === "paused") pauseLatched = true;
      }
    }
    keys.add(code);
  });
  window.addEventListener("keyup", (e) => { keys.delete(e.code); });

  function triggerVisualFeedback(shakeDur, flashDur) {
    if (settings.reducedMotion) return;
    shakeTimer = Math.max(shakeTimer, shakeDur);
    flashTimer = Math.max(flashTimer, flashDur);
  }

  function handleEvents(events) {
    for (const ev of events || []) {
      if (ev.name === "paused") showScreen("paused");
      else if (ev.name === "resumed") showScreen("playing");
      else if (ev.name === "mote_picked") playSfx(720 + (ev.data?.carried || 1) * 35, 0.14, "sine", 0.10, 960);
      else if (ev.name === "charm_picked") playSfx(880, 0.25, "triangle", 0.13, 1320);
      else if (ev.name === "deposit" || ev.name === "refuel") playSfx(480, 0.14, "triangle", 0.11, 640);
      else if (ev.name === "lantern_lit") {
        playSfx(523.25, 0.28, "triangle", 0.14);
        setTimeout(() => playSfx(659.25, 0.3, "sine", 0.13), 80);
        setTimeout(() => playSfx(783.99, 0.4, "sine", 0.13), 160);
      } else if (ev.name === "lantern_out") {
        playSfx(190, 0.38, "triangle", 0.12, 95);
        triggerVisualFeedback(0.25, 0.15);
      } else if (ev.name === "pulse") {
        pulseWave = 1.0;
        playSfx(420, 0.28, "sine", 0.13, 180);
        triggerVisualFeedback(0.18, 0.18);
      } else if (ev.name === "dash") playSfx(320, 0.12, "triangle", 0.11, 680);
      else if (ev.name === "shade_spawned") {
        shadeSpawnAlertTimer = 3.5;
        lastSpawnedShadeId = ev.data?.id || null;
        playSfx(120, 0.35, "sawtooth", 0.08, 90);
      } else if (ev.name === "player_hit") {
        playSfx(140, 0.25, "sawtooth", 0.12, 70);
        triggerVisualFeedback(0.35, 0.28);
      } else if (ev.name === "game_over") {
        const won = ev.data?.result === "won";
        if (won) { playSfx(523.25, 0.35); setTimeout(() => playSfx(783.99, 0.5), 140); }
        else playSfx(210, 0.5, "triangle", 0.12, 105);
      }
    }
  }

  function updateHud() {
    const snap = gameData.snapshot;
    const t = gameData.tuning;
    const p = snap.player;
    const litCount = (snap.lanterns || []).filter((l) => l.lit).length;
    const totalLanterns = (snap.lanterns || []).length || 5;
    const winNeeded = gameData.meta?.win_needed || Math.ceil(0.6 * totalLanterns);
    const warnPrefix = "⚠ ";

    flamesEl.textContent = `${p.flames <= 1 ? warnPrefix : ""}${"🔥".repeat(Math.max(0, p.flames))} ${p.flames}/${t.flames}`;
    flamesEl.classList.toggle("danger", p.flames <= 1);
    nightLabelEl.textContent = isBenchMode
      ? "Benchmark 1280×720 — Đêm 1 (200 Bóng Mực · 100 Đom đóm)"
      : (gameData.meta?.map_name || `Đêm ${snap.night}`);
    goalEl.textContent = `Giữ ≥ ${winNeeded}/${totalLanterns} đèn sáng tới bình minh`;

    const secsLeft = Math.max(0, Math.ceil(snap.time_left_s));
    const m = Math.floor(secsLeft / 60);
    const s = secsLeft % 60;
    const urgent = snap.time_left_s <= 30.0;
    timerEl.textContent = `${urgent ? warnPrefix : ""}${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
    timerEl.classList.toggle("urgent", urgent);
    if (uiMode === "playing" && secsLeft <= 10 && secsLeft > 0 && secsLeft !== lastCountdownSec) {
      lastCountdownSec = secsLeft;
      playSfx(980, 0.08, "sine", 0.07);
    }

    const windWarn = Boolean(gameData.meta?.wind_warning);
    const windActive = Boolean(snap.wind?.active);
    if (windActive) {
      windBadgeEl.textContent = `${warnPrefix}Gió mạnh đang thổi!`;
      windBadgeEl.classList.remove("hidden");
    } else if (windWarn) {
      windBadgeEl.textContent = `${warnPrefix}Gió sắp thổi!`;
      windBadgeEl.classList.remove("hidden");
    } else {
      windBadgeEl.classList.add("hidden");
    }

    lanternsEl.textContent = `${litCount} / ${totalLanterns}`;
    scoreEl.textContent = String(snap.score);

    const cap = p.capacity || t.carry_capacity;
    syncCapacitySlots(cap, p.carried);
    moteTextEl.textContent = `Đom đóm: ${p.carried} / ${cap}`;

    dashEl.textContent = p.charm_s > 0 ? "0s (Bùa!)" : (p.dash_cd_s > 0.05 ? `${p.dash_cd_s.toFixed(1)}s` : "Sẵn sàng");
    pulseEl.textContent = p.pulse_cd_s > 0.05 ? `${p.pulse_cd_s.toFixed(1)}s` : (p.carried < t.pulse_cost ? "Thiếu" : "Sẵn sàng");
    charmEl.classList.toggle("hidden", p.charm_s <= 0);
    if (p.charm_s > 0) charmEl.textContent = `Bùa Gió: ${p.charm_s.toFixed(1)}s`;

    // Accessibility Subtitles / Visual Indicators (Ticket-04 §4)
    if (uiMode === "playing" && settings.subtitles) {
      const alerts = [];
      if (shadeSpawnAlertTimer > 0) {
        alerts.push("⚠ [Phụ đề] Bóng Mực vừa xuất hiện! (Xem mũi tên cảnh báo ở mép màn hình)");
      }
      if (windActive) {
        alerts.push("⚠ [Phụ đề] Gió mạnh đang thổi trên Đảo Chuông!");
      } else if (windWarn) {
        alerts.push("⚠ [Phụ đề] Gió sắp thổi trong 2 giây!");
      }
      if (secsLeft <= 10 && secsLeft > 0) {
        alerts.push(`⚠ [Phụ đề] 10 giây cuối: Còn ${secsLeft}s tới bình minh!`);
      }
      const lowThresh = t.low_fuel_threshold || 30;
      const lowLanterns = (snap.lanterns || []).filter((l) => l.lit && l.fuel < lowThresh);
      if (lowLanterns.length > 0) {
        alerts.push(
          `⚠ [Phụ đề] Đèn sắp cạn dầu (< 30): ${lowLanterns.map((l) => `${l.id} (${l.fuel.toFixed(0)}%)`).join(", ")}`
        );
      }
      if (alerts.length > 0) {
        subtitleBannerEl.textContent = alerts.join("   |   ");
        subtitleBannerEl.classList.remove("hidden");
      } else {
        subtitleBannerEl.classList.add("hidden");
      }
    } else {
      subtitleBannerEl.classList.add("hidden");
    }

    // Context prompt for nearest interactable lantern
    let nearL = null, nearD = Infinity;
    for (const l of snap.lanterns || []) {
      const d = Math.hypot(p.pos[0] - l.pos[0], p.pos[2] - l.pos[2]);
      if (d > t.interact_radius) continue;
      if (l.lit && l.fuel >= 100) continue;
      if (d < nearD) { nearD = d; nearL = l; }
    }
    const keyInt = prettyKey(settings.keybinds.interact);
    if (nearL && uiMode === "playing") {
      if (nearL.lit) {
        promptEl.textContent = `${keyInt} — Châm dầu ${nearL.id} (${nearL.fuel.toFixed(0)}/100)`;
      } else {
        const cost = nearL.ever_lit ? (t.relight_cost || 5) : (t.lantern_cost || 10);
        promptEl.textContent = `${keyInt} — ${nearL.ever_lit ? "Thắp lại" : "Nạp ánh sáng"} (${nearL.deposited}/${cost})`;
      }
      promptEl.classList.remove("hidden");
    } else {
      promptEl.classList.add("hidden");
    }

    if (!isBenchMode && (snap.state === "won" || snap.state === "lost") && uiMode !== "result") {
      showScreen("result");
      const total = gameData.meta?.campaign_score ?? snap.score;
      const nightsWon = gameData.meta?.nights_won ?? (snap.state === "won" ? 1 : 0);
      const canSaveLeaderboard = snap.state === "lost" || (snap.state === "won" && snap.night === 3);

      lbSaveBox.classList.toggle("hidden", !canSaveLeaderboard);
      btnSaveScore.disabled = false;
      lbMsg.textContent = "";

      if (snap.state === "won") {
        if (snap.night === 3) {
          resultBadge.textContent = "Bình Minh v1.0.0";
          resultTitle.textContent = "Ánh sáng đã giữ trọn qua 3 Đêm!";
          resultDesc.textContent = "Mây đã giữ đủ đèn sáng tới tận bình minh trên cả ba hòn đảo. Hãy lưu tên vào Bảng xếp hạng!";
          btnNextNight.classList.add("hidden");
        } else {
          resultBadge.textContent = `Bình minh Đêm ${snap.night}`;
          resultTitle.textContent = `${gameData.meta?.map_name || ""} vượt qua bình minh!`;
          resultDesc.textContent = `Đèn sáng lúc bình minh: ${litCount}/${totalLanterns} (cần ≥ ${winNeeded}).`;
          btnNextNight.classList.remove("hidden");
        }
      } else {
        resultBadge.textContent = `Thua Đêm ${snap.night}`;
        resultTitle.textContent = "Sương đen đã phủ kín";
        resultDesc.textContent =
          p.flames <= 0
            ? "Mây đã mất hết Ngọn Lửa."
            : `Bình minh tới khi mới có ${litCount}/${totalLanterns} đèn sáng (cần ≥ ${winNeeded}).`;
        btnNextNight.classList.add("hidden");
      }
      resultScore.textContent = `${snap.score} / Tổng thắng (${nightsWon} Đêm): ${total}`;
    }
  }

  function buildMoveVector() {
    let mx = 0, mz = 0;
    const kb = settings.keybinds;
    if (keys.has(kb.moveUp) || keys.has("ArrowUp")) mz += 1;
    if (keys.has(kb.moveDown) || keys.has("ArrowDown")) mz -= 1;
    if (keys.has(kb.moveRight)) mx -= 1;
    if (keys.has(kb.moveLeft)) mx += 1;
    return [mx, mz];
  }

  async function sendTick(steps = 1) {
    if (tickInFlight || isBenchMode) return;
    if (uiMode !== "playing" && !pauseLatched) return;
    tickInFlight = true;
    const kb = settings.keybinds;
    const payload = {
      move: buildMoveVector(),
      cam_yaw_deg: camera.yawDeg,
      jump: jumpLatched || keys.has(kb.jump),
      dash: dashLatched,
      interact: interactLatched || keys.has(kb.interact) || keys.has("KeyF"),
      pulse: pulseLatched || keys.has(kb.pulse),
      pause: pauseLatched,
      steps,
    };
    jumpLatched = dashLatched = interactLatched = pulseLatched = pauseLatched = false;
    try {
      const { ok, data } = await apiPost("/api/tick", payload);
      if (ok && data) {
        handleEvents(data.events);
        gameData = data;
        updateHud();
      }
    } catch (_) {
    } finally {
      tickInFlight = false;
    }
  }

  // Right-handed 4x4 matrix math (mat4LookAt keeps map upright and A/D aligned)
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
    let zx = eye[0] - target[0], zy = eye[1] - target[1], zz = eye[2] - target[2];
    const zLen = Math.hypot(zx, zy, zz) || 1;
    zx /= zLen; zy /= zLen; zz /= zLen;

    // Right-handed: x_cam = normalize(cross((0,1,0), z_cam)) = (zz, 0, -zx)
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

  function mat4ModelPitch(tx, ty, tz, yawRad, pitchRad, sx, sy, sz) {
    const cy = Math.cos(yawRad), syaw = Math.sin(yawRad);
    const cp = Math.cos(pitchRad), sp = Math.sin(pitchRad);
    return new Float32Array([
      cy * sx, 0, -syaw * sx, 0,
      syaw * sp * sy, cp * sy, cy * sp * sy, 0,
      syaw * cp * sz, -sp * sz, cy * cp * sz, 0,
      tx, ty, tz, 1,
    ]);
  }

  // Geometry builders
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
      const sh = p[i][1] > 0 ? 1.0 : 0.72;
      verts.push(p[i][0], p[i][1], p[i][2], sh, sh, sh);
    }
    return new Float32Array(verts);
  }

  function createOctahedronData() {
    const top = [0, 1, 0], bot = [0, -1, 0], ring = [[1,0,0],[0,0,1],[-1,0,0],[0,0,-1]];
    const verts = [];
    for (let i = 0; i < 4; i++) {
      const a = ring[i], b = ring[(i + 1) % 4];
      verts.push(...top, 1,1,1, ...a, 0.82,0.82,0.82, ...b, 0.82,0.82,0.82);
      verts.push(...bot, 0.55,0.55,0.55, ...b, 0.75,0.75,0.75, ...a, 0.75,0.75,0.75);
    }
    return new Float32Array(verts);
  }

  function createConeData(seg) {
    const verts = [];
    for (let i = 0; i < seg; i++) {
      const a0 = (i / seg) * Math.PI * 2, a1 = ((i + 1) / seg) * Math.PI * 2;
      const sh = 0.84 + 0.14 * Math.sin(a0);
      verts.push(0,1,0, 1,1,1, Math.cos(a0),0,Math.sin(a0), sh,sh,sh, Math.cos(a1),0,Math.sin(a1), sh,sh,sh);
    }
    return new Float32Array(verts);
  }

  function createCylinderData(seg) {
    const verts = [];
    for (let i = 0; i < seg; i++) {
      const a0 = (i / seg) * Math.PI * 2, a1 = ((i + 1) / seg) * Math.PI * 2;
      const c0 = Math.cos(a0), s0 = Math.sin(a0), c1 = Math.cos(a1), s1 = Math.sin(a1);
      const sh = 0.82 + 0.15 * Math.cos(a0);
      verts.push(c0,0,s0, sh*0.85,sh*0.85,sh*0.85, c1,0,s1, sh*0.85,sh*0.85,sh*0.85, c1,1,s1, sh,sh,sh);
      verts.push(c0,0,s0, sh*0.85,sh*0.85,sh*0.85, c1,1,s1, sh,sh,sh, c0,1,s0, sh,sh,sh);
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
      verts.push(c0*innerR, yTop, s0*innerR, 0.95,0.95,0.95, c0*outerR, yTop, s0*outerR, 1,1,1, c1*outerR, yTop, s1*outerR, 1,1,1);
      verts.push(c0*innerR, yTop, s0*innerR, 0.95,0.95,0.95, c1*outerR, yTop, s1*outerR, 1,1,1, c1*innerR, yTop, s1*innerR, 0.95,0.95,0.95);
      verts.push(c0*outerR, 0, s0*outerR, 0.56,0.56,0.56, c1*outerR, 0, s1*outerR, 0.56,0.56,0.56, c1*outerR, yTop, s1*outerR, 0.74,0.74,0.74);
      verts.push(c0*outerR, 0, s0*outerR, 0.56,0.56,0.56, c1*outerR, yTop, s1*outerR, 0.74,0.74,0.74, c0*outerR, yTop, s0*outerR, 0.74,0.74,0.74);
      if (innerR > 0.01) {
        verts.push(c0*innerR, 0, s0*innerR, 0.52,0.52,0.52, c1*innerR, yTop, s1*innerR, 0.7,0.7,0.7, c1*innerR, 0, s1*innerR, 0.52,0.52,0.52);
        verts.push(c0*innerR, 0, s0*innerR, 0.52,0.52,0.52, c0*innerR, yTop, s0*innerR, 0.7,0.7,0.7, c1*innerR, yTop, s1*innerR, 0.7,0.7,0.7);
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

  const starPositions = [];
  for (let i = 0; i < 60; i++) {
    const a = (i * 137.508 * Math.PI) / 180;
    const dist = 85 + (i % 5) * 14;
    const y = 22 + (i % 7) * 8;
    starPositions.push([Math.cos(a) * dist, y, Math.sin(a) * dist, 0.25 + (i % 3) * 0.12]);
  }

  function projectToScreen(vp, wx, wy, wz) {
    const cx = vp[0] * wx + vp[4] * wy + vp[8] * wz + vp[12];
    const cy = vp[1] * wx + vp[5] * wy + vp[9] * wz + vp[13];
    const cw = vp[3] * wx + vp[7] * wy + vp[11] * wz + vp[15];
    return { ndcX: cx / (Math.abs(cw) > 1e-4 ? cw : 1e-4), ndcY: cy / (Math.abs(cw) > 1e-4 ? cw : 1e-4), cw };
  }

  function positionEdgeArrow(el, vp, wx, wy, wz, alwaysShowAtEdge = false) {
    const pr = projectToScreen(vp, wx, wy, wz);
    let nx = pr.ndcX, ny = pr.ndcY;
    if (pr.cw < 0) { nx = -nx; ny = -ny; }
    if (!alwaysShowAtEdge && pr.cw > 0 && Math.abs(nx) <= 0.90 && Math.abs(ny) <= 0.90) {
      el.classList.add("hidden");
      return;
    }
    const maxC = Math.max(Math.abs(nx), Math.abs(ny), 1e-4);
    const sx = (nx / maxC) * 0.86, sy = (ny / maxC) * 0.82;
    el.style.left = `${(sx * 0.5 + 0.5) * window.innerWidth - 17}px`;
    el.style.top = `${(-sy * 0.5 + 0.5) * window.innerHeight - 17}px`;
    el.style.transform = `rotate(${Math.atan2(sx, sy)}rad)`;
    el.classList.remove("hidden");
  }

  function updateOverlays3D(vp, snap) {
    if (uiMode !== "playing") {
      arrowEl.classList.add("hidden");
      shadeArrowEl.classList.add("hidden");
      fuelBarsLayer.innerHTML = "";
      return;
    }

    const p = snap.player.pos;

    // 1. Offscreen directional arrow toward nearest priority lantern (weak <30 or unlit)
    let nearestL = null, bestLD = Infinity;
    for (const l of snap.lanterns || []) {
      if (l.lit && l.fuel >= 30) continue;
      const d = Math.hypot(l.pos[0] - p[0], l.pos[2] - p[2]);
      if (d < bestLD) { bestLD = d; nearestL = l; }
    }
    if (!nearestL) {
      arrowEl.classList.add("hidden");
    } else {
      positionEdgeArrow(arrowEl, vp, nearestL.pos[0], nearestL.pos[1] + 2.2, nearestL.pos[2], false);
    }

    // 2. Accessibility Shade Spawn / Threat Edge Arrow (Ticket-04 §4)
    let targetShade = null;
    if (shadeSpawnAlertTimer > 0 && lastSpawnedShadeId) {
      targetShade = (snap.shades || []).find((s) => s.id === lastSpawnedShadeId) || null;
    }
    if (!targetShade && settings.subtitles) {
      let bestSD = Infinity;
      for (const s of snap.shades || []) {
        const d = Math.hypot(s.pos[0] - p[0], s.pos[2] - p[2]);
        if (d < bestSD && (shadeSpawnAlertTimer > 0 || d <= 16.0)) {
          bestSD = d;
          targetShade = s;
        }
      }
    }
    if (targetShade && settings.subtitles) {
      positionEdgeArrow(
        shadeArrowEl,
        vp,
        targetShade.pos[0],
        targetShade.pos[1] + 1.2,
        targetShade.pos[2],
        shadeSpawnAlertTimer > 0
      );
    } else {
      shadeArrowEl.classList.add("hidden");
    }

    // 3. Overhead fuel bars above every lit lantern
    const lowThresh = gameData.tuning.low_fuel_threshold || 30;
    const warnIcon = "⚠ ";
    let html = "";
    for (const l of snap.lanterns || []) {
      if (!l.lit) continue;
      const pr = projectToScreen(vp, l.pos[0], l.pos[1] + 3.6, l.pos[2]);
      if (pr.cw <= 0 || Math.abs(pr.ndcX) > 1.05 || Math.abs(pr.ndcY) > 1.05) continue;
      const sx = (pr.ndcX * 0.5 + 0.5) * window.innerWidth;
      const sy = (-pr.ndcY * 0.5 + 0.5) * window.innerHeight;
      const isLow = l.fuel < lowThresh;
      const pct = Math.max(0, Math.min(100, l.fuel));
      html += `<div class="fuel-tag${isLow ? " low" : ""}" style="left:${sx.toFixed(0)}px;top:${sy.toFixed(0)}px">
        <div>${isLow ? warnIcon : ""}${l.id} ${pct.toFixed(0)}%</div>
        <div class="fuel-bar-track"><div class="fuel-bar-fill" style="width:${pct.toFixed(1)}%"></div></div>
      </div>`;
    }
    fuelBarsLayer.innerHTML = html;
  }

  // Local 60Hz wander stepper for benchmark mode (200 shades moving without HTTP latency)
  function stepBenchmarkLocal(dtSec) {
    const snap = gameData.snapshot;
    const shades = snap.shades || [];
    const lanterns = snap.lanterns || [];
    const unlit = lanterns.filter((l) => !l.lit);
    const litSafe = lanterns.filter((l) => l.lit && l.fuel >= 30);
    const stepM = 2.0 * dtSec;

    for (let i = 0; i < shades.length; i++) {
      const s = shades[i];
      if (typeof s._ang !== "number") s._ang = (i * 1.618) % (Math.PI * 2);
      let dx = 0, dz = 0;
      if (unlit.length > 0) {
        let bestL = unlit[0], bestD = Infinity;
        for (const u of unlit) {
          const d = Math.hypot(s.pos[0] - u.pos[0], s.pos[2] - u.pos[2]);
          if (d < bestD) { bestD = d; bestL = u; }
        }
        if (bestD > 1.5) {
          dx = ((bestL.pos[0] - s.pos[0]) / bestD) * stepM;
          dz = ((bestL.pos[2] - s.pos[2]) / bestD) * stepM;
        }
      }
      if (dx === 0 && dz === 0) {
        s._ang += 0.4 * dtSec;
        dx = Math.cos(s._ang) * stepM;
        dz = Math.sin(s._ang) * stepM;
      }
      let nx = s.pos[0] + dx, nz = s.pos[2] + dz;
      const r = Math.hypot(nx, nz);
      if (r > 39.5) {
        nx = (nx / r) * 39.5;
        nz = (nz / r) * 39.5;
        s._ang += Math.PI * 0.75;
      }
      for (const l of litSafe) {
        const ld = Math.hypot(nx - l.pos[0], nz - l.pos[2]);
        if (ld < 6.02 && ld > 1e-5) {
          nx = l.pos[0] + ((nx - l.pos[0]) / ld) * 6.02;
          nz = l.pos[2] + ((nz - l.pos[2]) / ld) * 6.02;
          s._ang += Math.PI * 0.5;
        }
      }
      s.pos[0] = nx;
      s.pos[2] = nz;
    }
  }

  let webglRendererName = "WebGL2 1280x720";

  function initWebGL2() {
    const gl = canvas.getContext("webgl2", { antialias: true, powerPreference: "high-performance" });
    if (!gl) return null;

    try {
      const dbg = gl.getExtension("WEBGL_debug_renderer_info");
      const unmasked = dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
      webglRendererName = `WebGL2 (${unmasked || gl.getParameter(gl.VERSION)})`;
    } catch (_) {}

    const vsSrc = `#version 300 es
      layout(location = 0) in vec3 aPos;
      layout(location = 1) in vec3 aShade;
      uniform mat4 uVp;
      uniform mat4 uModel;
      out vec3 vShade;
      out vec3 vWorldPos;
      void main() {
        vec4 world = uModel * vec4(aPos, 1.0);
        vWorldPos = world.xyz;
        vShade = aShade;
        gl_Position = uVp * world;
      }`;

    const fsSrc = `#version 300 es
      precision mediump float;
      in vec3 vShade;
      in vec3 vWorldPos;
      uniform vec3 uTint;
      uniform vec3 uEyePos;
      uniform vec3 uFogColor;
      uniform float uAmbient;
      uniform float uEmissive;
      uniform vec4 uLights[7];
      out vec4 fragColor;
      void main() {
        vec3 base = vShade * uTint;
        vec3 litColor = base * (0.45 + uAmbient * 0.95);
        vec3 warmGlow = vec3(0.0);
        for (int i = 0; i < 7; i++) {
          float strength = uLights[i].w;
          if (strength > 0.01) {
            float d = length(vWorldPos - uLights[i].xyz);
            float att = strength / (1.0 + 0.045 * d + 0.012 * d * d);
            warmGlow += vec3(1.0, 0.72, 0.30) * att;
          }
        }
        vec3 color = mix(litColor + base * warmGlow * 0.95, base * 1.15, uEmissive);
        float camDist = length(vWorldPos - uEyePos);
        float fog = clamp((camDist - 42.0) / 140.0, 0.0, 0.78) * (1.0 - uEmissive * 0.85);
        fragColor = vec4(mix(color, uFogColor, fog), 1.0);
      }`;

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
    const uVp = gl.getUniformLocation(prog, "uVp");
    const uModel = gl.getUniformLocation(prog, "uModel");
    const uTint = gl.getUniformLocation(prog, "uTint");
    const uEyePos = gl.getUniformLocation(prog, "uEyePos");
    const uFogColor = gl.getUniformLocation(prog, "uFogColor");
    const uAmbient = gl.getUniformLocation(prog, "uAmbient");
    const uEmissive = gl.getUniformLocation(prog, "uEmissive");
    const uLights = gl.getUniformLocation(prog, "uLights");

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

    const IDENTITY = new Float32Array([1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]);
    const boxMesh = makeMesh(createBoxData());
    const octMesh = makeMesh(createOctahedronData());
    const coneMesh = makeMesh(createConeData(16));
    const cylMesh = makeMesh(createCylinderData(14));
    const ringMesh = makeMesh(createRingData(36, 0.93, 1.0));
    const discMesh = makeMesh(createArcSectorData(48, 0.0, 1.0, 0, 360, 0.0));
    const tier1Mesh = makeMesh(createArcSectorData(28, 12.0, 24.0, 0, 180, 3.0));
    const tier2Mesh = makeMesh(createArcSectorData(28, 0.0, 8.0, 0, 360, 6.0));
    const ramp30 = makeMesh(createRampData(30, 24, 30, 1.5, 3.0));
    const ramp150 = makeMesh(createRampData(150, 24, 30, 1.5, 3.0));

    function draw(mesh, model, r, g, b, emissive = 0.0) {
      gl.bindVertexArray(mesh.vao);
      gl.uniformMatrix4fv(uModel, false, model);
      gl.uniform3f(uTint, r, g, b);
      gl.uniform1f(uEmissive, emissive);
      gl.drawArrays(gl.TRIANGLES, 0, mesh.count);
    }

    // Traditional Vietnamese Áo Dài + Nón Lá for Mây
    function drawMayAoDai(pPos, pYaw, speedRatio) {
      const px = pPos[0], py = pPos[1], pz = pPos[2];
      const sway = Math.sin(animTime * 9.0) * 0.16 * speedRatio;
      const walkBob = Math.abs(Math.sin(animTime * 9.0)) * 0.05 * speedRatio;
      const fwdX = Math.sin(pYaw), fwdZ = Math.cos(pYaw);
      const rightX = Math.cos(pYaw), rightZ = -Math.sin(pYaw);

      draw(cylMesh, mat4Model(px + rightX * 0.11, py + 0.02, pz + rightZ * 0.11, pYaw, 0.13, 0.68, 0.14), 0.95, 0.94, 0.91, 0.0);
      draw(cylMesh, mat4Model(px - rightX * 0.11, py + 0.02, pz - rightZ * 0.11, pYaw, 0.13, 0.68, 0.14), 0.95, 0.94, 0.91, 0.0);
      draw(cylMesh, mat4Model(px, py + 0.68 + walkBob, pz, pYaw, 0.25, 0.56, 0.18), 0.910, 0.886, 0.816, 0.0);
      draw(cylMesh, mat4Model(px, py + 1.22 + walkBob, pz, pYaw, 0.13, 0.10, 0.13), 0.910, 0.886, 0.816, 0.0);
      draw(boxMesh, mat4ModelPitch(px + rightX * 0.30, py + 0.98 + walkBob, pz + rightZ * 0.30, pYaw, sway, 0.08, 0.28, 0.09), 0.910, 0.886, 0.816, 0.0);
      draw(boxMesh, mat4ModelPitch(px - rightX * 0.30, py + 0.98 + walkBob, pz - rightZ * 0.30, pYaw, -sway, 0.08, 0.28, 0.09), 0.910, 0.886, 0.816, 0.0);

      const panelFrontPitch = -0.08 - sway * 0.7;
      const panelBackPitch = 0.14 + speedRatio * 0.24 + sway * 0.6;
      draw(boxMesh, mat4ModelPitch(px + fwdX * 0.19, py + 0.42 + walkBob, pz + fwdZ * 0.19, pYaw, panelFrontPitch, 0.23, 0.38, 0.03), 0.910, 0.886, 0.816, 0.0);
      draw(boxMesh, mat4ModelPitch(px + fwdX * 0.23, py + 0.07 + walkBob, pz + fwdZ * 0.23, pYaw, panelFrontPitch, 0.235, 0.03, 0.032), 0.949, 0.757, 0.306, 0.18);
      draw(boxMesh, mat4ModelPitch(px - fwdX * 0.20, py + 0.42 + walkBob, pz - fwdZ * 0.20, pYaw, panelBackPitch, 0.24, 0.40, 0.03), 0.910, 0.886, 0.816, 0.0);
      draw(boxMesh, mat4ModelPitch(px - fwdX * 0.25, py + 0.06 + walkBob, pz - fwdZ * 0.25, pYaw, panelBackPitch, 0.245, 0.03, 0.032), 0.949, 0.757, 0.306, 0.18);

      draw(ringMesh, mat4Model(px, py + 1.22 + walkBob, pz, pYaw, 0.22, 1.0, 0.22), 0.784, 0.063, 0.180, 0.08);
      draw(boxMesh, mat4ModelPitch(px - fwdX * 0.24, py + 1.04 + walkBob, pz - fwdZ * 0.24, pYaw, 0.35 + speedRatio * 0.45 + Math.sin(animTime * 8) * 0.12, 0.07, 0.26, 0.025), 0.784, 0.063, 0.180, 0.1);

      draw(octMesh, mat4Model(px, py + 1.44 + walkBob, pz, pYaw, 0.16, 0.17, 0.16), 0.96, 0.84, 0.73, 0.0);
      draw(octMesh, mat4Model(px - fwdX * 0.14, py + 1.44 + walkBob, pz - fwdZ * 0.14, pYaw, 0.10, 0.10, 0.10), 0.11, 0.09, 0.12, 0.0);

      draw(coneMesh, mat4Model(px, py + 1.50 + walkBob, pz, pYaw, 0.78, 0.46, 0.78), 0.847, 0.745, 0.478, 0.05);
      draw(ringMesh, mat4Model(px, py + 1.50 + walkBob, pz, pYaw, 0.78, 1.0, 0.78), 0.65, 0.52, 0.30, 0.05);
      draw(ringMesh, mat4Model(px, py + 1.66 + walkBob, pz, pYaw, 0.50, 1.0, 0.50), 0.72, 0.60, 0.36, 0.05);
      const hx = px + fwdX * 0.70, hz = pz + fwdZ * 0.70;
      const swing = Math.sin(animTime * 4.5) * 0.04;
      draw(boxMesh, mat4Model(hx, py + 1.38 + walkBob, hz, pYaw, 0.015, 0.11, 0.015), 0.784, 0.063, 0.180, 0.1);
      draw(octMesh, mat4Model(hx + swing, py + 1.22 + walkBob, hz, animTime * 2.5, 0.15, 0.20, 0.15), 1.0, 0.74, 0.28, 0.95);
    }

    return function render(width, height, benchElapsedSec = null) {
      const snap = gameData.snapshot;
      const t = gameData.tuning;
      const lanterns = snap.lanterns || [];
      const litCount = lanterns.filter((l) => l.lit).length;
      const totalLanterns = Math.max(1, lanterns.length);
      const ambient = 0.15 + 0.55 * (litCount / totalLanterns);
      const blink1Hz = settings.reducedMotion ? true : (Math.sin(animTime * Math.PI * 2.0) > 0);
      const lowThresh = t.low_fuel_threshold || 30;

      const lightBuf = new Float32Array(7 * 4);
      for (let i = 0; i < Math.min(7, lanterns.length); i++) {
        const l = lanterns[i];
        lightBuf[i * 4 + 0] = l.pos[0];
        lightBuf[i * 4 + 1] = l.pos[1] + 2.4;
        lightBuf[i * 4 + 2] = l.pos[2];
        const lowFlicker = l.fuel < lowThresh ? (blink1Hz ? 0.85 : 0.25) : 1.0;
        lightBuf[i * 4 + 3] = l.lit ? 1.45 * lowFlicker : 0.0;
      }

      gl.viewport(0, 0, width, height);
      gl.enable(gl.DEPTH_TEST);
      const skyR = 0.055 + ambient * 0.055;
      const skyG = 0.078 + ambient * 0.065;
      const skyB = 0.188 + ambient * 0.10;
      gl.clearColor(skyR, skyG, skyB, 1.0);
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
      gl.useProgram(prog);

      const pPos = snap.player?.pos || [0, 0, 0];
      let eye, target;
      if (isBenchMode && typeof benchElapsedSec === "number") {
        // Ticket-04 §1: orbit center (0,0,0), r=30m, Y=15m, look at (0,0,0), start 0 deg (30,15,0), CCW 15s/rev
        const theta = (2.0 * Math.PI * benchElapsedSec) / 15.0;
        eye = [30.0 * Math.cos(theta), 15.0, 30.0 * Math.sin(theta)];
        target = [0.0, 0.0, 0.0];
      } else {
        const yawRad = (camera.yawDeg * Math.PI) / 180;
        const shakeX = (!settings.reducedMotion && shakeTimer > 0) ? (Math.sin(animTime * 48) * 0.14 * shakeTimer) : 0;
        const shakeY = (!settings.reducedMotion && shakeTimer > 0) ? (Math.cos(animTime * 54) * 0.10 * shakeTimer) : 0;
        eye = [
          pPos[0] - Math.sin(yawRad) * Math.cos(camera.pitch) * camera.distance + shakeX,
          pPos[1] + 1.5 + Math.sin(camera.pitch) * camera.distance + shakeY,
          pPos[2] - Math.cos(yawRad) * Math.cos(camera.pitch) * camera.distance,
        ];
        target = [pPos[0] + shakeX * 0.5, pPos[1] + 1.15 + shakeY * 0.5, pPos[2]];
      }

      const proj = mat4Perspective(0.95, width / Math.max(1, height), 0.2, 260.0);
      const view = mat4LookAt(eye, target);
      const vp = mat4Multiply(proj, view);

      gl.uniformMatrix4fv(uVp, false, vp);
      gl.uniform3f(uEyePos, eye[0], eye[1], eye[2]);
      gl.uniform3f(uFogColor, 0.106 + ambient * 0.04, 0.137 + ambient * 0.04, 0.314 + ambient * 0.05);
      gl.uniform1f(uAmbient, ambient);
      gl.uniform4fv(uLights, lightBuf);

      updateOverlays3D(vp, snap);

      // Ticket-04: disable extra creative props during standardized benchmark
      if (!isBenchMode) {
        draw(octMesh, mat4Model(pPos[0] - 55, 58, pPos[2] + 95, animTime * 0.1, 4.2, 4.2, 4.2), 1.0, 0.93, 0.72, 1.0);
        for (let i = 0; i < starPositions.length; i++) {
          const st = starPositions[i];
          const tw = 0.75 + 0.25 * Math.sin(animTime * 2.5 + i);
          draw(octMesh, mat4Model(pPos[0] + st[0], st[1], pPos[2] + st[2], 0, st[3], st[3], st[3]), tw, tw * 0.96, tw * 0.82, 1.0);
        }
      }

      // Sea of Clouds (#12384A)
      draw(boxMesh, mat4Model(25, -10.5, 0, 0, 210, 0.2, 210), 0.071, 0.220, 0.290, 0.05);

      // Island geometry
      if (snap.night === 1) {
        draw(cylMesh, mat4Model(0, -3.2, 0, 0, 39.8, 3.18, 39.8), 0.26, 0.23, 0.22, 0.0);
        draw(discMesh, mat4Model(0, -0.02, 0, 0, 40, 1, 40), 0.184, 0.365, 0.314, 0.0);
        draw(ringMesh, mat4Model(0, 0.03, 0, 0, 39.8, 1, 39.8), 0.788, 0.706, 0.541, 0.0);
        if (!isBenchMode) {
          for (let i = 0; i < 12; i++) {
            const a = (i * 30 * Math.PI) / 180;
            const bx = Math.cos(a) * 38.2, bz = Math.sin(a) * 38.2;
            draw(cylMesh, mat4Model(bx, 0, bz, 0, 0.16, 3.2, 0.16), 0.16, 0.34, 0.26, 0.0);
            draw(coneMesh, mat4Model(bx, 2.8, bz, 0, 0.95, 1.4, 0.95), 0.19, 0.40, 0.32, 0.0);
          }
        }
      } else if (snap.night === 2) {
        draw(cylMesh, mat4Model(0, -3.0, 0, 0, 27.8, 2.98, 27.8), 0.26, 0.23, 0.22, 0.0);
        draw(cylMesh, mat4Model(70, -3.0, 0, 0, 27.8, 2.98, 27.8), 0.32, 0.27, 0.22, 0.0);
        draw(discMesh, mat4Model(0, -0.02, 0, 0, 28, 1, 28), 0.184, 0.365, 0.314, 0.0);
        draw(discMesh, mat4Model(70, -0.02, 0, 0, 28, 1, 28), 0.788, 0.706, 0.541, 0.0);
        draw(boxMesh, mat4Model(35, -0.1, 0, 0, 9.0, 0.1, 2.0), 0.420, 0.290, 0.184, 0.0);
      } else if (snap.night === 3) {
        draw(cylMesh, mat4Model(0, -3.4, 0, 0, 44.8, 3.38, 44.8), 0.26, 0.23, 0.22, 0.0);
        draw(discMesh, mat4Model(0, -0.02, 0, 0, 45, 1, 45), 0.184, 0.365, 0.314, 0.0);
        draw(tier1Mesh, IDENTITY, 0.788, 0.706, 0.541, 0.0);
        draw(tier2Mesh, IDENTITY, 0.788, 0.706, 0.541, 0.0);
        draw(ramp30, IDENTITY, 0.420, 0.290, 0.184, 0.0);
        draw(ramp150, IDENTITY, 0.420, 0.290, 0.184, 0.0);
        draw(cylMesh, mat4Model(0, 6.0, 0, 0, 1.9, 8.0, 1.9), 0.420, 0.290, 0.184, 0.0);
        draw(coneMesh, mat4Model(0, 14.0, 0, 0, 2.7, 2.4, 2.7), 0.784, 0.063, 0.180, 0.08);
      }

      for (const pad of gameData.meta?.launch_pads || []) {
        draw(ringMesh, mat4Model(pad.x, pad.y + 0.06, pad.z, 0, pad.radius, 1, pad.radius), 0.949, 0.757, 0.306, 0.85);
        draw(discMesh, mat4Model(pad.x, pad.y + 0.04, pad.z, 0, pad.radius * 0.72, 1, pad.radius * 0.72), 1.0, 0.702, 0.278, 0.75);
      }

      // Great Lanterns
      const lanternById = {};
      for (const l of lanterns) {
        lanternById[l.id] = l;
        const lx = l.pos[0], ly = l.pos[1], lz = l.pos[2];
        draw(cylMesh, mat4Model(lx, ly, lz, 0, 0.42, 1.7, 0.42), 0.357, 0.373, 0.431, 0.0);
        if (l.lit) {
          const isLow = l.fuel < lowThresh;
          const visGlow = isLow ? (blink1Hz ? 0.95 : 0.32) : 0.92;
          draw(octMesh, mat4Model(lx, ly + 2.35, lz, animTime * 0.45, 0.74, 0.95, 0.74), 1.0, 0.702, 0.278, visGlow);
          draw(octMesh, mat4Model(lx, ly + 2.35, lz, -animTime, 0.38, 0.48, 0.38), 1.0, 0.914, 0.690, visGlow);
          draw(coneMesh, mat4Model(lx, ly + 3.15, lz, 0, 0.95, 0.45, 0.95), 0.420, 0.290, 0.184, 0.05);
          if (!isLow) {
            draw(ringMesh, mat4Model(lx, ly + 0.05, lz, 0, t.safe_radius, 1, t.safe_radius), 1.0, 0.702, 0.278, 0.65);
          }
        } else {
          draw(octMesh, mat4Model(lx, ly + 2.15, lz, 0.3, 0.78, 0.76, 0.78), 0.357, 0.373, 0.431, 0.0);
          draw(boxMesh, mat4ModelPitch(lx + 0.56, ly + 2.15, lz, 0.4, 0.65, 0.05, 0.42, 0.14), 0.06, 0.05, 0.09, 0.0);
          draw(boxMesh, mat4ModelPitch(lx - 0.56, ly + 2.15, lz, -0.4, -0.65, 0.05, 0.42, 0.14), 0.06, 0.05, 0.09, 0.0);
          draw(coneMesh, mat4Model(lx, ly + 2.82, lz, 0, 0.92, 0.40, 0.92), 0.32, 0.24, 0.18, 0.0);
          draw(ringMesh, mat4Model(lx, ly + 0.05, lz, 0, t.interact_radius, 1, t.interact_radius), 0.357, 0.373, 0.431, 0.35);
        }
      }

      for (const c of gameData.meta?.charms_pos || []) {
        if (!c.available) continue;
        const cp = c.pos;
        const bob = 0.85 + 0.2 * Math.sin(animTime * 3.0);
        draw(boxMesh, mat4Model(cp[0], cp[1] + bob, cp[2], animTime * 2.0, 0.26, 0.42, 0.06), 0.784, 0.063, 0.180, 0.85);
        draw(ringMesh, mat4Model(cp[0], cp[1] + 0.05, cp[2], 0, 1.0, 1, 1.0), 0.949, 0.757, 0.306, 0.7);
      }

      for (let i = 0; i < (snap.motes || []).length; i++) {
        const m = snap.motes[i];
        const bob = 0.6 + 0.16 * Math.sin(animTime * 3.8 + i);
        draw(octMesh, mat4Model(m.pos[0], m.pos[1] + bob, m.pos[2], animTime * 2 + i, 0.24, 0.28, 0.24), 1.0, 0.965, 0.761, 0.95);
      }

      // Shades (#120A1A body; rim & eyes #7A3CFF or #00B3FF in colorblind mode; stunned #3A3450)
      const shadeRim = settings.colorblind ? [0.0, 0.702, 1.0] : [0.478, 0.235, 1.0];
      const shadeTargets = gameData.meta?.shades_target || {};
      for (let i = 0; i < (snap.shades || []).length; i++) {
        const s = snap.shades[i];
        const stunned = s.state === "stunned";
        const draining = s.state === "drain";
        const bob = 0.95 + 0.18 * Math.sin(animTime * (stunned ? 14 : 3.2) + i);
        const col = stunned ? [0.227, 0.204, 0.314] : [0.071, 0.039, 0.102];
        draw(octMesh, mat4Model(s.pos[0], s.pos[1] + bob, s.pos[2], animTime * 1.6, 0.78, 1.08, 0.78), col[0], col[1], col[2], 0.15);
        draw(octMesh, mat4Model(s.pos[0], s.pos[1] + bob + 0.28, s.pos[2], -animTime, 0.24, 0.16, 0.24), shadeRim[0], shadeRim[1], shadeRim[2], 0.95);
        draw(ringMesh, mat4Model(s.pos[0], s.pos[1] + 0.06, s.pos[2], 0, 0.88, 1, 0.88), shadeRim[0], shadeRim[1], shadeRim[2], stunned ? 0.35 : 0.85);
        if (draining && shadeTargets[s.id] && lanternById[shadeTargets[s.id]]) {
          const tl = lanternById[shadeTargets[s.id]];
          const mx = (s.pos[0] + tl.pos[0]) * 0.5, my = (s.pos[1] + tl.pos[1] + 2.6) * 0.5, mz = (s.pos[2] + tl.pos[2]) * 0.5;
          draw(octMesh, mat4Model(mx, my, mz, animTime * 8, 0.22, 0.22, 0.22), shadeRim[0], shadeRim[1], shadeRim[2], 0.95);
        }
      }

      for (let i = 0; i < (snap.drifters || []).length; i++) {
        const d = snap.drifters[i];
        draw(boxMesh, mat4Model(d.pos[0], d.pos[1] + 1.3 + 0.2 * Math.sin(animTime * 6 + i), d.pos[2], animTime * 4, 0.95, 0.12, 0.25), 0.561, 0.639, 0.722, 0.8);
      }

      if (snap.wind?.active || gameData.meta?.wind_warning) {
        const wr = ((snap.wind?.dir_deg || 0) * Math.PI) / 180;
        const speed = snap.wind?.active ? 14.0 : 4.0;
        for (let i = 0; i < 14; i++) {
          const tShift = ((animTime * speed + i * 3.1) % 30.0) - 15.0;
          const wx = pPos[0] + Math.cos(wr) * tShift - Math.sin(wr) * ((i - 7) * 1.3);
          const wz = pPos[2] + Math.sin(wr) * tShift + Math.cos(wr) * ((i - 7) * 1.3);
          draw(boxMesh, mat4Model(wx, pPos[1] + 1.2 + (i % 3) * 0.5, wz, animTime * 5 + i, 0.2, 0.04, 0.12), 0.788, 0.706, 0.541, 0.65);
        }
      }

      const pYaw = ((gameData.meta?.facing_yaw_deg || 0) * Math.PI) / 180;
      const pVel = snap.player?.vel || [0, 0, 0];
      const speedRatio = Math.min(1.0, Math.hypot(pVel[0], pVel[2]) / 6.0);
      const blink = !settings.reducedMotion && snap.player?.invuln && Math.floor(animTime * 16) % 2 === 0;
      if (!blink) {
        drawMayAoDai(pPos, pYaw, speedRatio);
      }

      if (!isBenchMode) {
        const carriedCount = Math.min(20, snap.player?.carried || 0);
        for (let i = 0; i < carriedCount; i++) {
          const outer = i >= 10;
          const ringN = outer ? Math.max(1, carriedCount - 10) : Math.min(10, carriedCount);
          const idx = outer ? i - 10 : i;
          const rad = outer ? 1.45 : 1.05;
          const spd = outer ? -2.1 : 2.6;
          const a = animTime * spd + (idx * Math.PI * 2) / ringN;
          draw(octMesh, mat4Model(pPos[0] + Math.cos(a) * rad, pPos[1] + (outer ? 1.35 : 0.98) + 0.16 * Math.sin(animTime * 5 + i), pPos[2] + Math.sin(a) * rad, a, 0.11, 0.11, 0.11), 1.0, 0.96, 0.72, 1.0);
        }
      }

      if (pulseWave > 0.02) {
        const r = (1.0 - pulseWave) * (t.pulse_radius || 5.0);
        draw(ringMesh, mat4Model(pPos[0], pPos[1] + 0.14, pPos[2], 0, Math.max(0.4, r), 1, Math.max(0.4, r)), 1.0, 0.914, 0.690, 1.0);
      }
    };
  }

  const renderFrame = initWebGL2() || (() => {});

  function resizeCanvas() {
    if (isBenchMode) {
      if (canvas.width !== 1280 || canvas.height !== 720) {
        canvas.width = 1280;
        canvas.height = 720;
      }
      return { width: 1280, height: 720 };
    }
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const width = Math.max(1, Math.floor(canvas.clientWidth * dpr));
    const height = Math.max(1, Math.floor(canvas.clientHeight * dpr));
    if (canvas.width !== width || canvas.height !== height) {
      canvas.width = width;
      canvas.height = height;
    }
    return { width, height };
  }

  // Standardized 1280x720 Benchmark runner in browser (?mode=bench)
  async function startBrowserBenchmark() {
    const data = await apiGet(`/api/bench_init?seed=${benchSeed}`);
    if (data) gameData = data;
    showScreen("bench");
    updateHud();

    let benchStartTs = null;
    let lastBenchTs = performance.now();
    const dtsMs = [];
    let reported = false;

    function benchStep() {
      const now = performance.now();
      if (benchStartTs === null) benchStartTs = now;
      const elapsedSec = (now - benchStartTs) / 1000.0;
      const dtMs = Math.max(0.05, now - lastBenchTs);
      const dtSec = Math.min(0.05, dtMs / 1000.0);
      lastBenchTs = now;
      animTime += dtSec;

      stepBenchmarkLocal(dtSec);
      const { width, height } = resizeCanvas();
      renderFrame(width, height, elapsedSec);

      fpsCount += 1;
      fpsTimer += dtSec;
      if (fpsTimer >= 0.4) {
        fpsEl.textContent = `FPS: ${Math.round(fpsCount / fpsTimer)}`;
        fpsCount = 0;
        fpsTimer = 0;
      }

      if (elapsedSec >= benchWarmupSec) {
        dtsMs.push(dtMs);
      }

      if (elapsedSec >= benchWarmupSec + benchDurationSec && !reported) {
        reported = true;
        apiPost("/api/bench_report", {
          dts_ms: dtsMs,
          vsync_off: true,
          renderer: webglRendererName,
        }).finally(() => {
          try { window.close(); } catch (_) {}
        });
        return;
      }
      setTimeout(benchStep, 0);
    }

    setTimeout(benchStep, 0);
  }

  let lastTs = performance.now();
  let accumulator = 0;

  function loop(now) {
    const dtSec = Math.min(0.1, (now - lastTs) / 1000);
    lastTs = now;
    animTime += dtSec;
    pulseWave = Math.max(0, pulseWave - dtSec * 2.5);
    shakeTimer = Math.max(0, shakeTimer - dtSec);
    flashTimer = Math.max(0, flashTimer - dtSec);
    shadeSpawnAlertTimer = Math.max(0, shadeSpawnAlertTimer - dtSec);
    screenFlashEl.classList.toggle("hidden", settings.reducedMotion || flashTimer <= 0.01);

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
    renderFrame(width, height, null);
    requestAnimationFrame(loop);
  }

  if (isBenchMode) {
    startBrowserBenchmark();
  } else {
    fetch("/api/state")
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => { if (data) { gameData = data; updateHud(); } })
      .catch(() => {})
      .finally(() => {
        showScreen("menu");
        requestAnimationFrame(loop);
      });
  }
})();
