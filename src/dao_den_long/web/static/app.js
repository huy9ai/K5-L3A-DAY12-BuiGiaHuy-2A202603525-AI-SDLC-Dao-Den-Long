(() => {
  "use strict";

  const canvas = document.getElementById("scene-canvas");
  const flamesEl = document.getElementById("hud-flames");
  const carriedEl = document.getElementById("hud-carried");
  const lanternsEl = document.getElementById("hud-lanterns");
  const timeEl = document.getElementById("hud-time");
  const scoreEl = document.getElementById("hud-score");
  const pulseEl = document.getElementById("hud-pulse");
  const hintEl = document.getElementById("hud-hint");
  const promptEl = document.getElementById("context-prompt");
  const overlayEl = document.getElementById("gameover-overlay");
  const overlayBadge = document.getElementById("overlay-badge");
  const overlayTitle = document.getElementById("overlay-title");
  const overlayReason = document.getElementById("overlay-reason");
  const overlayScore = document.getElementById("overlay-score");
  const audioBtn = document.getElementById("btn-audio");
  const resetBtn = document.getElementById("btn-reset");
  const replayBtn = document.getElementById("btn-replay");

  const keys = new Set();
  const camera = { yawDeg: 0, pitch: 0.42, distance: 12.5 };
  let dragging = false;
  let lastX = 0;
  let lastY = 0;
  let jumpLatched = false;
  let interactLatched = false;
  let pulseLatched = false;
  let audioEnabled = true;
  let audioCtx = null;

  let pulseWave = 0.0;
  let hitFlash = 0.0;
  let animTime = 0.0;
  let tickInFlight = false;

  let gameData = {
    snapshot: {
      tick: 0,
      state: "playing",
      time_left_s: 300,
      score: 0,
      player: { pos: [0, 0, 0], flames: 3, carried: 0 },
      lanterns: [],
      shades: [],
      motes_active: 0,
      motes: [],
    },
    tuning: {
      carry_capacity: 6,
      lantern_cost: 4,
      lantern_count_night1: 5,
      interact_radius: 3.0,
      pulse_cost: 2,
      pulse_radius: 7.0,
      safe_radius: 5.0,
      flames: 3,
    },
    cooldowns: { pulse_s: 0, invuln_s: 0 },
    facing_yaw_deg: 0,
  };

  function ensureAudio() {
    if (!audioEnabled) return null;
    if (!audioCtx) {
      const Ctx = window.AudioContext || window.webkitAudioContext;
      if (Ctx) audioCtx = new Ctx();
    }
    if (audioCtx && audioCtx.state === "suspended") {
      audioCtx.resume().catch(() => {});
    }
    return audioCtx;
  }

  function playTone(freq, dur, type = "sine", gainVal = 0.08, endFreq = freq) {
    const ctx = ensureAudio();
    if (!ctx) return;
    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, now);
    if (endFreq !== freq) {
      osc.frequency.exponentialRampToValueAtTime(Math.max(40, endFreq), now + dur);
    }
    gain.gain.setValueAtTime(gainVal, now);
    gain.gain.exponentialRampToValueAtTime(0.0005, now + dur);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + dur);
  }

  function handleEvents(events) {
    for (const ev of events || []) {
      if (ev.name === "mote_picked") {
        playTone(660 + (ev.data?.carried || 1) * 55, 0.14, "sine", 0.07, 920);
      } else if (ev.name === "deposit") {
        playTone(440, 0.16, "triangle", 0.08, 560);
      } else if (ev.name === "lantern_lit") {
        playTone(523.25, 0.32, "triangle", 0.11);
        setTimeout(() => playTone(659.25, 0.35, "sine", 0.10), 80);
        setTimeout(() => playTone(783.99, 0.45, "sine", 0.10), 160);
        hintEl.textContent = `Đã thắp sáng ${ev.data?.lantern_id || "Đèn Lồng"}! Vùng sáng an toàn đã mở rộng.`;
      } else if (ev.name === "pulse") {
        pulseWave = 1.0;
        playTone(420, 0.28, "sine", 0.10, 180);
      } else if (ev.name === "player_hit") {
        hitFlash = 1.0;
        playTone(150, 0.25, "sawtooth", 0.09, 75);
      } else if (ev.name === "game_over") {
        if (ev.data?.result === "won") {
          playTone(523.25, 0.4, "sine", 0.11);
          setTimeout(() => playTone(783.99, 0.5, "sine", 0.11), 120);
        } else {
          playTone(220, 0.55, "triangle", 0.09, 110);
        }
      }
    }
  }

  function toggleAudio() {
    audioEnabled = !audioEnabled;
    audioBtn.textContent = `Âm thanh: ${audioEnabled ? "Bật" : "Tắt"} (M)`;
  }

  async function resetGame() {
    try {
      const res = await fetch("/api/reset", { method: "POST", body: "{}" });
      if (res.ok) {
        gameData = await res.json();
        pulseWave = 0;
        hitFlash = 0;
        overlayEl.classList.add("hidden");
        hintEl.textContent = "Thu thập đom đóm vàng cam, né Bóng Mực tím đen và thắp sáng đủ 5 Đèn Lồng Lớn!";
        updateHud();
      }
    } catch (_) {}
  }

  audioBtn.addEventListener("click", toggleAudio);
  resetBtn.addEventListener("click", resetGame);
  replayBtn.addEventListener("click", resetGame);

  canvas.addEventListener("pointerdown", (e) => {
    if (e.button === 2) {
      pulseLatched = true;
      return;
    }
    dragging = true;
    lastX = e.clientX;
    lastY = e.clientY;
  });
  canvas.addEventListener("contextmenu", (e) => e.preventDefault());
  window.addEventListener("pointerup", () => {
    dragging = false;
  });
  window.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    camera.yawDeg = (camera.yawDeg - (e.clientX - lastX) * 0.35) % 360;
    camera.pitch = Math.max(0.18, Math.min(1.15, camera.pitch + (e.clientY - lastY) * 0.006));
    lastX = e.clientX;
    lastY = e.clientY;
  });
  canvas.addEventListener("wheel", (e) => {
    camera.distance = Math.max(6.5, Math.min(24.0, camera.distance + e.deltaY * 0.01));
  }, { passive: true });

  window.addEventListener("keydown", (e) => {
    ensureAudio();
    const code = e.code;
    if (["Space", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(code)) {
      e.preventDefault();
    }
    if (!e.repeat) {
      if (code === "Space") jumpLatched = true;
      if (code === "KeyE" || code === "KeyF") interactLatched = true;
      if (code === "KeyQ" || code === "ShiftLeft" || code === "ShiftRight") pulseLatched = true;
      if (code === "KeyR") resetGame();
      if (code === "KeyM") toggleAudio();
    }
    keys.add(code);
  });

  window.addEventListener("keyup", (e) => {
    keys.delete(e.code);
  });

  function formatTime(sec) {
    const s = Math.max(0, Math.ceil(sec));
    const m = Math.floor(s / 60);
    const rem = s % 60;
    return `${String(m).padStart(2, "0")}:${String(rem).padStart(2, "0")}`;
  }

  function updateHud() {
    const snap = gameData.snapshot;
    const t = gameData.tuning;
    const p = snap.player;
    const litCount = (snap.lanterns || []).filter((l) => l.lit).length;
    const totalLanterns = (snap.lanterns || []).length || t.lantern_count_night1;

    flamesEl.textContent = `${"🔥".repeat(Math.max(0, p.flames))} (${p.flames}/${t.flames})`;
    carriedEl.textContent = `${p.carried} / ${t.carry_capacity}`;
    lanternsEl.textContent = `${litCount} / ${totalLanterns}`;
    timeEl.textContent = formatTime(snap.time_left_s);
    scoreEl.textContent = String(snap.score);

    const pulseCd = gameData.cooldowns?.pulse_s || 0;
    if (pulseCd > 0.05) {
      pulseEl.textContent = `Hồi ${pulseCd.toFixed(1)}s`;
    } else if (p.carried < t.pulse_cost) {
      pulseEl.textContent = `Thiếu (${t.pulse_cost})`;
    } else {
      pulseEl.textContent = "Sẵn sàng!";
    }

    // Nearest unlit lantern interaction prompt
    let nearUnlit = null;
    for (const l of snap.lanterns || []) {
      if (l.lit) continue;
      const dist = Math.hypot(p.pos[0] - l.pos[0], p.pos[2] - l.pos[2]);
      if (dist <= t.interact_radius + 0.3) {
        nearUnlit = l;
        break;
      }
    }
    if (nearUnlit && snap.state === "playing") {
      const need = t.lantern_cost - nearUnlit.deposited;
      promptEl.textContent =
        p.carried > 0
          ? `Nhấn [E] để nạp ánh sáng vào ${nearUnlit.id} (${nearUnlit.deposited}/${t.lantern_cost}, cần thêm ${need})`
          : `${nearUnlit.id}: cần thêm ${need} đom đóm để thắp sáng`;
      promptEl.classList.remove("hidden");
    } else {
      promptEl.classList.add("hidden");
    }

    if (snap.state !== "playing") {
      overlayEl.classList.remove("hidden");
      overlayScore.textContent = String(snap.score);
      if (snap.state === "won") {
        overlayBadge.textContent = "Chiến thắng";
        overlayTitle.textContent = "Đảo Bến đã rực sáng!";
        overlayReason.textContent = `Mây đã thắp sáng toàn bộ ${totalLanterns} Đèn Lồng Lớn trước khi bình minh tới.`;
      } else {
        overlayBadge.textContent = "Thất bại";
        overlayTitle.textContent = "Sương đen nuốt trọn hòn đảo";
        overlayReason.textContent =
          p.flames <= 0
            ? "Mây đã mất hết ngọn lửa khi chạm Bóng Mực."
            : "Bình minh đã tới trước khi thắp đủ 5 Đèn Lồng Lớn.";
      }
    } else {
      overlayEl.classList.add("hidden");
    }
  }

  function buildMoveVector() {
    let mx = 0;
    let mz = 0;
    if (keys.has("KeyW") || keys.has("ArrowUp")) mz += 1;
    if (keys.has("KeyS") || keys.has("ArrowDown")) mz -= 1;
    // Screen right aligns with -X when looking toward +Z (see Contract C yaw formula)
    if (keys.has("KeyD")) mx -= 1;
    if (keys.has("KeyA")) mx += 1;
    return [mx, mz];
  }

  async function sendTick(steps = 1) {
    if (tickInFlight || gameData.snapshot.state !== "playing") return;
    tickInFlight = true;
    const payload = {
      move: buildMoveVector(),
      cam_yaw_deg: camera.yawDeg,
      jump: jumpLatched || keys.has("Space"),
      interact: interactLatched || keys.has("KeyE") || keys.has("KeyF"),
      pulse: pulseLatched || keys.has("KeyQ") || keys.has("ShiftLeft") || keys.has("ShiftRight"),
      steps,
    };
    jumpLatched = false;
    interactLatched = false;
    pulseLatched = false;
    try {
      const res = await fetch("/api/tick", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const next = await res.json();
        handleEvents(next.events);
        gameData = next;
        updateHud();
      }
    } catch (_) {
    } finally {
      tickInFlight = false;
    }
  }

  // Matrix & mesh helpers
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
    return new Float32Array([
      f / aspect, 0, 0, 0,
      0, f, 0, 0,
      0, 0, (far + near) * nf, -1,
      0, 0, 2 * far * near * nf, 0,
    ]);
  }

  function mat4LookAt(eye, target) {
    let zx = eye[0] - target[0];
    let zy = eye[1] - target[1];
    let zz = eye[2] - target[2];
    const zLen = Math.hypot(zx, zy, zz) || 1;
    zx /= zLen; zy /= zLen; zz /= zLen;

    let xx = -zz;
    let xy = 0;
    let xz = zx;
    const xLen = Math.hypot(xx, xy, xz) || 1;
    xx /= xLen; xz /= xLen;

    const yx = zy * xz - zz * xy;
    const yy = zz * xx - zx * xz;
    const yz = zx * xy - zy * xx;

    return new Float32Array([
      xx, yx, zx, 0,
      xy, yy, zy, 0,
      xz, yz, zz, 0,
      -(xx * eye[0] + xy * eye[1] + xz * eye[2]),
      -(yx * eye[0] + yy * eye[1] + yz * eye[2]),
      -(zx * eye[0] + zy * eye[1] + zz * eye[2]),
      1,
    ]);
  }

  function mat4Model(tx, ty, tz, yawRad, sx, sy, sz) {
    const c = Math.cos(yawRad);
    const s = Math.sin(yawRad);
    return new Float32Array([
      c * sx, 0, -s * sx, 0,
      0, sy, 0, 0,
      s * sz, 0, c * sz, 0,
      tx, ty, tz, 1,
    ]);
  }

  function createOctahedronData() {
    const top = [0, 1, 0];
    const bot = [0, -1, 0];
    const ring = [[1, 0, 0], [0, 0, 1], [-1, 0, 0], [0, 0, -1]];
    const verts = [];
    for (let i = 0; i < 4; i++) {
      const a = ring[i];
      const b = ring[(i + 1) % 4];
      verts.push(...top, 0.95, 0.95, 0.95, ...a, 0.72, 0.72, 0.72, ...b, 0.72, 0.72, 0.72);
      verts.push(...bot, 0.42, 0.42, 0.42, ...b, 0.65, 0.65, 0.65, ...a, 0.65, 0.65, 0.65);
    }
    return new Float32Array(verts);
  }

  function createConeData(segments) {
    const verts = [];
    for (let i = 0; i < segments; i++) {
      const a0 = (i / segments) * Math.PI * 2;
      const a1 = ((i + 1) / segments) * Math.PI * 2;
      const shade = 0.75 + 0.2 * Math.sin(a0);
      verts.push(0, 1, 0, 1.0, 1.0, 0.95);
      verts.push(Math.cos(a0), 0, Math.sin(a0), shade, shade, shade);
      verts.push(Math.cos(a1), 0, Math.sin(a1), shade, shade, shade);
      verts.push(0, 0, 0, 0.45, 0.45, 0.45);
      verts.push(Math.cos(a1), 0, Math.sin(a1), 0.55, 0.55, 0.55);
      verts.push(Math.cos(a0), 0, Math.sin(a0), 0.55, 0.55, 0.55);
    }
    return new Float32Array(verts);
  }

  function createRingData(segments, innerR, outerR) {
    const verts = [];
    for (let i = 0; i < segments; i++) {
      const a0 = (i / segments) * Math.PI * 2;
      const a1 = ((i + 1) / segments) * Math.PI * 2;
      const c0 = Math.cos(a0), s0 = Math.sin(a0);
      const c1 = Math.cos(a1), s1 = Math.sin(a1);
      verts.push(c0 * innerR, 0, s0 * innerR, 0.9, 0.9, 0.9);
      verts.push(c0 * outerR, 0, s0 * outerR, 1.0, 1.0, 1.0);
      verts.push(c1 * outerR, 0, s1 * outerR, 1.0, 1.0, 1.0);
      verts.push(c0 * innerR, 0, s0 * innerR, 0.9, 0.9, 0.9);
      verts.push(c1 * outerR, 0, s1 * outerR, 1.0, 1.0, 1.0);
      verts.push(c1 * innerR, 0, s1 * innerR, 0.9, 0.9, 0.9);
    }
    return new Float32Array(verts);
  }

  function createIslandDiscData(segments, radius) {
    const verts = [];
    for (let i = 0; i < segments; i++) {
      const a0 = (i / segments) * Math.PI * 2;
      const a1 = ((i + 1) / segments) * Math.PI * 2;
      verts.push(0, 0, 0, 0.14, 0.18, 0.28);
      verts.push(Math.cos(a0) * radius, -0.02, Math.sin(a0) * radius, 0.05, 0.07, 0.12);
      verts.push(Math.cos(a1) * radius, -0.02, Math.sin(a1) * radius, 0.05, 0.07, 0.12);
    }
    return new Float32Array(verts);
  }

  function initWebGL2() {
    const gl = canvas.getContext("webgl2", { antialias: true });
    if (!gl) return null;

    const vsSrc = `#version 300 es
      layout(location = 0) in vec3 aPos;
      layout(location = 1) in vec3 aShade;
      uniform mat4 uMvp;
      uniform vec3 uTint;
      out vec3 vColor;
      void main() {
        gl_Position = uMvp * vec4(aPos, 1.0);
        vColor = aShade * uTint;
      }`;

    const fsSrc = `#version 300 es
      precision mediump float;
      in vec3 vColor;
      out vec4 fragColor;
      void main() {
        fragColor = vec4(vColor, 1.0);
      }`;

    function compile(type, src) {
      const shader = gl.createShader(type);
      gl.shaderSource(shader, src);
      gl.compileShader(shader);
      return shader;
    }

    const prog = gl.createProgram();
    gl.attachShader(prog, compile(gl.VERTEX_SHADER, vsSrc));
    gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, fsSrc));
    gl.linkProgram(prog);
    const uMvp = gl.getUniformLocation(prog, "uMvp");
    const uTint = gl.getUniformLocation(prog, "uTint");

    function makeMesh(data) {
      const vao = gl.createVertexArray();
      const vbo = gl.createBuffer();
      gl.bindVertexArray(vao);
      gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
      gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW);
      gl.enableVertexAttribArray(0);
      gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 24, 0);
      gl.enableVertexAttribArray(1);
      gl.vertexAttribPointer(1, 3, gl.FLOAT, false, 24, 12);
      return { vao, count: data.length / 6 };
    }

    const octMesh = makeMesh(createOctahedronData());
    const coneMesh = makeMesh(createConeData(12));
    const ringMesh = makeMesh(createRingData(36, 0.94, 1.0));
    const islandMesh = makeMesh(createIslandDiscData(48, 50.0));

    function draw(mesh, mvp, r, g, b) {
      gl.bindVertexArray(mesh.vao);
      gl.uniformMatrix4fv(uMvp, false, mvp);
      gl.uniform3f(uTint, r, g, b);
      gl.drawArrays(gl.TRIANGLES, 0, mesh.count);
    }

    return function render(width, height) {
      const snap = gameData.snapshot;
      const t = gameData.tuning;
      const litCount = (snap.lanterns || []).filter((l) => l.lit).length;
      const warmth = litCount / Math.max(1, t.lantern_count_night1 || 5);

      gl.viewport(0, 0, width, height);
      gl.enable(gl.DEPTH_TEST);
      gl.clearColor(
        0.03 + warmth * 0.08 + hitFlash * 0.16,
        0.04 + warmth * 0.06,
        0.09 + warmth * 0.08,
        1.0
      );
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
      gl.useProgram(prog);

      const pPos = snap.player?.pos || [0, 0, 0];
      const yawRad = (camera.yawDeg * Math.PI) / 180;
      const fwdX = Math.sin(yawRad);
      const fwdZ = Math.cos(yawRad);
      const horizDist = Math.cos(camera.pitch) * camera.distance;
      const eye = [
        pPos[0] - fwdX * horizDist,
        pPos[1] + 1.5 + Math.sin(camera.pitch) * camera.distance,
        pPos[2] - fwdZ * horizDist,
      ];
      const target = [pPos[0], pPos[1] + 1.0, pPos[2]];

      const proj = mat4Perspective(0.95, width / Math.max(1, height), 0.2, 160.0);
      const view = mat4LookAt(eye, target);
      const vp = mat4Multiply(proj, view);

      // Circular island floor + boundary glow ring
      draw(
        islandMesh,
        vp,
        0.75 + warmth * 0.45,
        0.8 + warmth * 0.35,
        0.95 + warmth * 0.15
      );
      draw(ringMesh, mat4Multiply(vp, mat4Model(0, 0.03, 0, 0, 50.0, 1, 50.0)), 0.22, 0.3, 0.48);
      draw(ringMesh, mat4Multiply(vp, mat4Model(0, 0.03, 0, 0, 25.0, 1, 25.0)), 0.18, 0.24, 0.38);

      // Great Lanterns (L1..L5)
      for (const l of snap.lanterns || []) {
        const lx = l.pos[0], lz = l.pos[2];
        const ratio = Math.min(1, (l.deposited || 0) / Math.max(1, t.lantern_cost || 4));
        // Stone pillar
        draw(octMesh, mat4Multiply(vp, mat4Model(lx, 1.0, lz, 0, 0.65, 1.0, 0.65)), 0.34, 0.38, 0.48);
        // Paper lantern head
        const lanternScale = l.lit ? 0.95 : 0.72;
        const lr = l.lit ? 1.15 : 0.28 + ratio * 0.7;
        const lg = l.lit ? 0.76 : 0.24 + ratio * 0.42;
        const lb = l.lit ? 0.24 : 0.42 - ratio * 0.16;
        draw(
          octMesh,
          mat4Multiply(vp, mat4Model(lx, 2.45, lz, animTime * 0.6, lanternScale, lanternScale * 1.25, lanternScale)),
          lr,
          lg,
          lb
        );
        // Safe radius ground ring when lit
        if (l.lit) {
          draw(
            ringMesh,
            mat4Multiply(vp, mat4Model(lx, 0.04, lz, 0, t.safe_radius, 1, t.safe_radius)),
            1.0,
            0.72,
            0.25
          );
        } else {
          draw(
            ringMesh,
            mat4Multiply(vp, mat4Model(lx, 0.04, lz, 0, t.interact_radius, 1, t.interact_radius)),
            0.35,
            0.45,
            0.65
          );
        }
      }

      // Motes (floating warm fireflies)
      for (let i = 0; i < (snap.motes || []).length; i++) {
        const m = snap.motes[i];
        const bob = 0.65 + 0.18 * Math.sin(animTime * 3.5 + i);
        draw(
          octMesh,
          mat4Multiply(vp, mat4Model(m.pos[0], bob, m.pos[2], animTime * 2.0 + i, 0.28, 0.34, 0.28)),
          1.1,
          0.86,
          0.28
        );
      }

      // Shades (Bong Muc — dark purple-black)
      for (let i = 0; i < (snap.shades || []).length; i++) {
        const s = snap.shades[i];
        const stunned = s.state === "stunned";
        const bob = 0.95 + (stunned ? 0.12 * Math.sin(animTime * 16.0) : 0.2 * Math.sin(animTime * 3.0 + i));
        const sx = stunned ? 0.65 : 0.92;
        const sy = stunned ? 0.58 : 1.15;
        draw(
          octMesh,
          mat4Multiply(vp, mat4Model(s.pos[0], bob, s.pos[2], animTime * (stunned ? 8.0 : 1.5), sx, sy, sx)),
          stunned ? 0.65 : 0.34,
          stunned ? 0.52 : 0.08,
          stunned ? 0.88 : 0.45
        );
        // Inner core / eye accent
        draw(
          octMesh,
          mat4Multiply(vp, mat4Model(s.pos[0], bob + 0.3, s.pos[2], -animTime, 0.25, 0.25, 0.25)),
          stunned ? 0.9 : 0.82,
          stunned ? 0.8 : 0.22,
          1.0
        );
      }

      // Player: May + non la hat + small hanging lantern + carried fireflies
      const pYaw = ((gameData.facing_yaw_deg || 0) * Math.PI) / 180;
      const blink = gameData.cooldowns?.invuln_s > 0 && Math.floor(animTime * 16) % 2 === 0;
      const bodyTint = blink ? [1.2, 0.5, 0.5] : [0.35, 0.72, 0.78];
      // Cloak body
      draw(
        coneMesh,
        mat4Multiply(vp, mat4Model(pPos[0], pPos[1] + 0.05, pPos[2], pYaw, 0.48, 1.35, 0.48)),
        ...bodyTint
      );
      // Non la (conical leaf hat)
      draw(
        coneMesh,
        mat4Multiply(vp, mat4Model(pPos[0], pPos[1] + 1.38, pPos[2], pYaw, 0.78, 0.48, 0.78)),
        0.95,
        0.82,
        0.48
      );
      // Small hanging lantern attached to hat rim
      const hx = pPos[0] + Math.sin(pYaw) * 0.68;
      const hz = pPos[2] + Math.cos(pYaw) * 0.68;
      draw(
        octMesh,
        mat4Multiply(vp, mat4Model(hx, pPos[1] + 1.16, hz, animTime * 3.0, 0.16, 0.22, 0.16)),
        1.1,
        0.8,
        0.25
      );
      // Carried fireflies orbiting May
      const carriedCount = snap.player?.carried || 0;
      for (let i = 0; i < carriedCount; i++) {
        const a = animTime * 2.8 + (i * Math.PI * 2) / Math.max(1, carriedCount);
        const cx = pPos[0] + Math.cos(a) * 0.95;
        const cz = pPos[2] + Math.sin(a) * 0.95;
        const cy = pPos[1] + 0.9 + 0.15 * Math.sin(animTime * 5 + i);
        draw(octMesh, mat4Multiply(vp, mat4Model(cx, cy, cz, a, 0.12, 0.12, 0.12)), 1.0, 0.9, 0.35);
      }

      // Expanding pulse shockwave ring
      if (pulseWave > 0.02) {
        const r = (1.0 - pulseWave) * (t.pulse_radius || 7.0);
        draw(
          ringMesh,
          mat4Multiply(vp, mat4Model(pPos[0], pPos[1] + 0.1, pPos[2], 0, Math.max(0.4, r), 1, Math.max(0.4, r))),
          1.1 * pulseWave,
          0.85 * pulseWave,
          0.35 * pulseWave
        );
      }
    };
  }

  function initFallback2D() {
    const ctx = canvas.getContext("2d");
    return function render2D(width, height) {
      ctx.fillStyle = "#090c18";
      ctx.fillRect(0, 0, width, height);
      const snap = gameData.snapshot;
      const cx = width * 0.5;
      const cy = height * 0.5;
      const scale = 8;
      const p = snap.player?.pos || [0, 0, 0];

      ctx.strokeStyle = "rgba(120,160,220,0.35)";
      ctx.beginPath();
      ctx.arc(cx, cy, 50 * scale, 0, Math.PI * 2);
      ctx.stroke();

      for (const l of snap.lanterns || []) {
        ctx.fillStyle = l.lit ? "#ffb84d" : "#445577";
        ctx.beginPath();
        ctx.arc(cx + l.pos[0] * scale, cy + l.pos[2] * scale, 10, 0, Math.PI * 2);
        ctx.fill();
      }
      for (const m of snap.motes || []) {
        ctx.fillStyle = "#ffe066";
        ctx.beginPath();
        ctx.arc(cx + m.pos[0] * scale, cy + m.pos[2] * scale, 4, 0, Math.PI * 2);
        ctx.fill();
      }
      for (const s of snap.shades || []) {
        ctx.fillStyle = s.state === "stunned" ? "#a680ff" : "#5e178f";
        ctx.beginPath();
        ctx.arc(cx + s.pos[0] * scale, cy + s.pos[2] * scale, 8, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.fillStyle = "#5ad2e6";
      ctx.beginPath();
      ctx.arc(cx + p[0] * scale, cy + p[2] * scale, 7, 0, Math.PI * 2);
      ctx.fill();
    };
  }

  const renderFrame = initWebGL2() || initFallback2D();

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
    pulseWave = Math.max(0, pulseWave - dtSec * 2.4);
    hitFlash = Math.max(0, hitFlash - dtSec * 3.0);

    if (keys.has("ArrowLeft")) camera.yawDeg = (camera.yawDeg - 110 * dtSec) % 360;
    if (keys.has("ArrowRight")) camera.yawDeg = (camera.yawDeg + 110 * dtSec) % 360;

    accumulator += dtSec;
    const stepDt = 1 / 60;
    const steps = Math.min(4, Math.floor(accumulator / stepDt));
    if (steps > 0) {
      accumulator -= steps * stepDt;
      sendTick(steps);
    }

    const { width, height } = resizeCanvas();
    renderFrame(width, height);
    requestAnimationFrame(loop);
  }

  fetch("/api/state")
    .then((r) => (r.ok ? r.json() : null))
    .then((data) => {
      if (data) {
        gameData = data;
        updateHud();
      }
    })
    .catch(() => {})
    .finally(() => {
      requestAnimationFrame(loop);
    });
})();
