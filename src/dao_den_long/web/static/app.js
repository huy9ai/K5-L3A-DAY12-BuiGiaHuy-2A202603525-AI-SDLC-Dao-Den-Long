(() => {
  "use strict";

  const canvas = document.getElementById("scene-canvas");
  const tickEl = document.getElementById("stat-tick");
  const fireflyEl = document.getElementById("stat-fireflies");
  const glowEl = document.getElementById("stat-glow");
  const rendererEl = document.getElementById("stat-renderer");
  const pulseBtn = document.getElementById("btn-pulse");
  const resetBtn = document.getElementById("btn-reset");

  const camera = { yaw: 0.6, pitch: 0.42, distance: 7.5 };
  let dragging = false;
  let lastX = 0;
  let lastY = 0;
  let stateInFlight = false;
  let latestState = {
    tick: 0,
    lantern: { yaw: 0, bob: 0, glow: 1.0 },
    fireflies: [],
  };

  canvas.addEventListener("pointerdown", (e) => {
    dragging = true;
    lastX = e.clientX;
    lastY = e.clientY;
  });
  window.addEventListener("pointerup", () => {
    dragging = false;
  });
  window.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    camera.yaw += (e.clientX - lastX) * 0.008;
    camera.pitch = Math.max(0.15, Math.min(1.25, camera.pitch + (e.clientY - lastY) * 0.008));
    lastX = e.clientX;
    lastY = e.clientY;
  });

  async function postAction(path) {
    try {
      const res = await fetch(path, { method: "POST" });
      if (res.ok) {
        latestState = await res.json();
        updateHud();
      }
    } catch (_) {
      // Ignore transient network errors during rapid interactions
    }
  }

  pulseBtn.addEventListener("click", () => postAction("/api/pulse"));
  resetBtn.addEventListener("click", () => postAction("/api/reset"));
  window.addEventListener("keydown", (e) => {
    if (e.code === "Space") {
      e.preventDefault();
      postAction("/api/pulse");
    }
  });

  function updateHud() {
    tickEl.textContent = String(latestState.tick ?? 0);
    fireflyEl.textContent = String((latestState.fireflies || []).length);
    glowEl.textContent = Number(latestState.lantern?.glow ?? 1).toFixed(2);
  }

  async function pollState() {
    if (stateInFlight) return;
    stateInFlight = true;
    try {
      const res = await fetch("/api/state");
      if (res.ok) {
        latestState = await res.json();
        updateHud();
      }
    } catch (_) {
      // Keep rendering latest snapshot if poll fails
    } finally {
      stateInFlight = false;
    }
  }

  // Minimal 4x4 column-major matrix math
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

  function mat4Model(tx, ty, tz, yaw, sx, sy, sz) {
    const c = Math.cos(yaw);
    const s = Math.sin(yaw);
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
      verts.push(...top, 0.9, 0.9, 0.9, ...a, 0.7, 0.7, 0.7, ...b, 0.7, 0.7, 0.7);
      verts.push(...bot, 0.4, 0.4, 0.4, ...b, 0.65, 0.65, 0.65, ...a, 0.65, 0.65, 0.65);
    }
    return new Float32Array(verts);
  }

  function createIslandDiscData(segments) {
    const verts = [];
    const r = 4.2;
    for (let i = 0; i < segments; i++) {
      const a0 = (i / segments) * Math.PI * 2;
      const a1 = ((i + 1) / segments) * Math.PI * 2;
      verts.push(0, 0, 0, 0.14, 0.21, 0.34);
      verts.push(Math.cos(a0) * r, -0.08, Math.sin(a0) * r, 0.06, 0.09, 0.16);
      verts.push(Math.cos(a1) * r, -0.08, Math.sin(a1) * r, 0.06, 0.09, 0.16);
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
    const discMesh = makeMesh(createIslandDiscData(24));

    function drawMesh(mesh, mvp, r, g, b) {
      gl.bindVertexArray(mesh.vao);
      gl.uniformMatrix4fv(uMvp, false, mvp);
      gl.uniform3f(uTint, r, g, b);
      gl.drawArrays(gl.TRIANGLES, 0, mesh.count);
    }

    return function renderWebGL(width, height) {
      gl.viewport(0, 0, width, height);
      gl.enable(gl.DEPTH_TEST);
      gl.clearColor(0.03, 0.05, 0.09, 1.0);
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
      gl.useProgram(prog);

      const eye = [
        Math.cos(camera.pitch) * Math.sin(camera.yaw) * camera.distance,
        Math.sin(camera.pitch) * camera.distance + 0.8,
        Math.cos(camera.pitch) * Math.cos(camera.yaw) * camera.distance,
      ];
      const proj = mat4Perspective(0.9, width / Math.max(1, height), 0.1, 60.0);
      const view = mat4LookAt(eye, [0, 0.9, 0]);
      const vp = mat4Multiply(proj, view);

      // Island platform
      drawMesh(discMesh, vp, 0.95, 1.0, 1.1);

      // Central Lantern pedestal + glowing lantern core
      const lantern = latestState.lantern || { yaw: 0, bob: 0, glow: 1.0 };
      const pedestalMvp = mat4Multiply(vp, mat4Model(0, 0.25, 0, 0, 0.45, 0.25, 0.45));
      drawMesh(octMesh, pedestalMvp, 0.35, 0.42, 0.56);

      const glowScale = 0.52 * (0.85 + 0.15 * lantern.glow);
      const lanternMvp = mat4Multiply(
        vp,
        mat4Model(0, 1.1 + lantern.bob, 0, lantern.yaw, glowScale, glowScale * 1.35, glowScale)
      );
      const gBoost = Math.min(1.8, lantern.glow);
      drawMesh(octMesh, lanternMvp, 1.0 * gBoost, 0.76 * gBoost, 0.28 * gBoost);

      // Orbiting fireflies
      for (const ff of latestState.fireflies || []) {
        const ffMvp = mat4Multiply(vp, mat4Model(ff.x, ff.y, ff.z, lantern.yaw * 2, 0.13, 0.13, 0.13));
        drawMesh(octMesh, ffMvp, 1.0, 0.95, 0.48);
      }
    };
  }

  function initFallback2D() {
    rendererEl.textContent = "Canvas2D";
    const ctx = canvas.getContext("2d");
    return function render2D(width, height) {
      ctx.fillStyle = "#080d18";
      ctx.fillRect(0, 0, width, height);
      const cx = width * 0.5;
      const cy = height * 0.56;
      const lantern = latestState.lantern || { bob: 0, glow: 1.0 };

      ctx.fillStyle = "rgba(38, 56, 88, 0.65)";
      ctx.beginPath();
      ctx.ellipse(cx, cy + 70, 220, 60, 0, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = `rgba(255, 198, 92, ${Math.min(1, 0.7 * lantern.glow)})`;
      ctx.beginPath();
      ctx.arc(cx, cy - 30 - lantern.bob * 60, 26 * Math.sqrt(lantern.glow), 0, Math.PI * 2);
      ctx.fill();

      for (const ff of latestState.fireflies || []) {
        const px = cx + (ff.x * Math.cos(camera.yaw) - ff.z * Math.sin(camera.yaw)) * 55;
        const py = cy - ff.y * 45 + (ff.x * Math.sin(camera.yaw) + ff.z * Math.cos(camera.yaw)) * 18;
        ctx.fillStyle = "#ffe985";
        ctx.beginPath();
        ctx.arc(px, py, 6, 0, Math.PI * 2);
        ctx.fill();
      }
    };
  }

  const renderFrame = initWebGL2() || initFallback2D();
  let frameCounter = 0;

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

  function loop() {
    const { width, height } = resizeCanvas();
    renderFrame(width, height);
    frameCounter += 1;
    if (frameCounter % 2 === 0) {
      pollState();
    }
    requestAnimationFrame(loop);
  }

  pollState();
  requestAnimationFrame(loop);
})();
